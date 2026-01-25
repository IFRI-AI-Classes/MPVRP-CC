import math

from typing import Dict, List, Tuple, Any

from .schemas import Camion, Depot, Garage, Station, Instance, ParsedSolutionDat, ParsedSolutionVehicle


def euclidean_distance(point1: tuple, point2: tuple) -> float:
    """Calculer la distance euclidienne entre deux points 2D."""
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def parse_instance(filepath: str) -> Instance:
    """Extraire les données du fichier .dat et les organiser dans une instance de la classe Instance."""
    try:
        # Extraire toutes les lignes du fichier
        with open(filepath, 'r') as file:
            lines = [line.strip() for line in file.readlines()]

        # 1ère ligne: UUID de l'instance
        # instance_id = lines[0]

        # 2ème ligne: Nombre de produits, depôts, garages, stations, camions
        num_products, num_depots, num_garages, num_stations, num_camions = map(int, lines[1].split())

        # num_products lignes suivantes : Matrice des coûts de transition de produits
        # Dimension : NbProduits × NbProduits
        # Représente le coût de changement du produit i vers le produit j
        costs = {}
        cost_start_line = 2
        for i in range(num_products):
            cost_values = list(map(float, lines[cost_start_line + i].split()))
            for j in range(num_products):
                costs[(i, j)] = cost_values[j]

        current_line = cost_start_line + num_products

        # Camions (num_camions lignes) : ID  Capacité  GarageOrigine  ProduitInitial
        camions = {}
        for i in range(num_camions):
            camion_data = lines[current_line + i].split()
            camion_id = f"K{int(camion_data[0])}"
            capacity = float(camion_data[1])
            garage_id = f"G{int(camion_data[2])}"
            initial_product = int(camion_data[3])
            camions[camion_id] = Camion(camion_id, capacity, garage_id, initial_product)

        current_line += num_camions

        # Depôts (num_depots lignes) : ID  X  Y  StockProduit1  StockProduit2  ...  StockProduitN
        depots = {}
        for i in range(num_depots):
            depot_data = lines[current_line + i].split()
            depot_id = f"D{int(depot_data[0])}"
            x = float(depot_data[1])
            y = float(depot_data[2])
            stocks = {pid: int(depot_data[3 + pid]) for pid in range(num_products)}
            depots[depot_id] = Depot(depot_id, (x, y), stocks)

        current_line += num_depots

        # Garages (num_garages lignes) : ID  X  Y
        garages = {}
        for i in range(num_garages):
            garage_data = lines[current_line + i].split()
            garage_id = f"G{int(garage_data[0])}"
            x = float(garage_data[1])
            y = float(garage_data[2])
            garages[garage_id] = Garage(garage_id, (x, y))

        current_line += num_garages

        # Stations (num_stations lignes) : ID  X  Y  DemandeProduit1  DemandeProduit2  ...  DemandeProduitN
        stations = {}
        for i in range(num_stations):
            station_data = lines[current_line + i].split()
            station_id = f"S{int(station_data[0])}"
            x = float(station_data[1])
            y = float(station_data[2])
            demand = {pid: int(station_data[3 + pid]) for pid in range(num_products)}
            stations[station_id] = Station(station_id, (x, y), demand)

        instance = Instance(
            num_products=num_products,
            num_camions=num_camions,
            num_depots=num_depots,
            num_garages=num_garages,
            num_stations=num_stations,
            camions=camions,
            depots=depots,
            garages=garages,
            stations=stations,
            costs=costs,
            distances={}
        )

        # Calculer et ajouter les distances euclidiennes entre tous les nœuds du réseau
        distances = compute_distances(instance)
        instance.distances = distances

        return instance

    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier {filepath} est introuvable.")

    except Exception as e:
        raise RuntimeError(f"Une erreur est survenue lors de l'analyse du fichier {filepath}: {e}")


def compute_distances(instance: Instance) -> dict:
    """
    Calculer les distances euclidiennes entre tous les points (dépôts, garages, stations) de l'instance.

    Retourne un dictionnaire avec les clés (id_noeud_i, id_noeud_j) et les valeurs = distance euclidienne.
    Cette matrice de distances est utilisée pour calculer les coûts de déplacement dans le modèle.
    """
    locations = {}

    # Ajouter les emplacements des dépôts
    for depot in instance.depots.values():
        locations[depot.id] = depot.location

    # Ajouter les emplacements des garages
    for garage in instance.garages.values():
        locations[garage.id] = garage.location

    # Ajouter les emplacements des stations
    for station in instance.stations.values():
        locations[station.id] = station.location

    # Calculer les distances euclidiennes entre tous les points
    # Complexité : O(n²) où n = nombre total de nœuds (dépôts + garages + stations)
    distances = {}
    ids = list(locations.keys())
    for i in range(len(ids)):
        for j in range(len(ids)):
            from_id = ids[i]
            to_id = ids[j]
            distances[(from_id, to_id)] = euclidean_distance(locations[from_id], locations[to_id])

    return distances


def _parse_solution_route_token(token: str) -> Dict[str, Any]:
    """
    Traiter un token de la ligne de route dans un fichier de solution.

    Formats supportés :
    - "id[qty]" : Dépôt avec quantité chargée (ex: "1[500]")
    - "id(qty)" : Station avec quantité livrée (ex: "5(300)")
    - "id"      : Garage sans quantité (ex: "2")

    Retourne un dictionnaire avec kind (depot/station/garage), id (int), qty (float).
    """
    token = token.strip()
    if not token:
        raise ValueError("Empty token")

    if "[" in token and "]" in token:
        # Dépôt : format id[qty]
        left, right = token.split("[", 1)
        node_id = int(left.strip())
        qty = int(right.split("]", 1)[0].strip())
        return {"kind": "depot", "id": node_id, "qty": qty}

    if "(" in token and ")" in token:
        # Station : format id(qty)
        left, right = token.split("(", 1)
        node_id = int(left.strip())
        qty = int(right.split(")", 1)[0].strip())
        return {"kind": "station", "id": node_id, "qty": qty}

    # Garage : format id (pas de quantité)
    return {"kind": "garage", "id": int(token), "qty": 0}


def _parse_solution_product_token(token: str) -> Tuple[int, float]:
    """
    Analyser un token de la ligne de produits dans un fichier de solution.

    Format : "p(cost)" où p est l'ID du produit et cost est le coût cumulé.
    Exemple : "2(150.5)" signifie produit 2 avec un coût cumulé de 150.5

    Retourne : (product_id, cumulative_cost)
    """
    token = token.strip()
    if not token:
        raise ValueError("Empty token")
    if "(" not in token or ")" not in token:
        raise ValueError(f"Invalid product token: {token}")
    p_str, rest = token.split("(", 1)
    product = int(p_str.strip())
    cost = float(rest.split(")", 1)[0].strip())
    return product, cost


def solution_node_key(kind: str, node_id: int) -> str:
    """
    Convertir un type de nœud et un ID numérique en clé de nœud formatée.

    Exemples :
    - ("garage", 1) -> "G1"
    - ("depot", 3) -> "D3"
    - ("station", 5) -> "S5"
    """
    if kind == "garage":
        return f"G{node_id}"
    if kind == "depot":
        return f"D{node_id}"
    if kind == "station":
        return f"S{node_id}"
    raise ValueError(f"Unknown kind: {kind}")


def parse_solution_dat(filepath: str) -> ParsedSolutionDat:
    """
    Analyser un fichier de solution (.dat) contenant les tournées des véhicules et les métriques.

    Structure du fichier de solution :

    - Blocs de véhicules (2 lignes par véhicule) :

      * Ligne 1 : "k: noeud1 - noeud2 - ... - noeudN"
      * Ligne 2 : "k: produit1(coût) - produit2(coût) - ... - produitN(coût)"

    - 6 lignes de métriques finales :

      * Nombre de véhicules utilisés
      * Nombre total de changements de produits
      * Coût total des changements
      * Distance totale parcourue
      * Processeur utilisé
      * Temps d'exécution

    Retourne un objet ParsedSolutionDat avec les tournées et les métriques.
    """
    with open(filepath, "r") as f:
        raw_lines = [line.rstrip("\n") for line in f]

    # Conserver les lignes vides pour séparer les blocs de véhicules ; supprimer les lignes vides finales
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()

    vehicles: List[ParsedSolutionVehicle] = []
    i = 0

    def _is_vehicle_line(line: str) -> bool:
        return ":" in line

    # Analyser les blocs de véhicules : deux lignes avec le même préfixe "k:"
    while i < len(raw_lines) and raw_lines[i].strip() and _is_vehicle_line(raw_lines[i]):
        line1 = raw_lines[i].strip()
        if i + 1 >= len(raw_lines):
            raise ValueError("Unexpected EOF while reading vehicle block")
        line2 = raw_lines[i + 1].strip()

        if ":" not in line1 or ":" not in line2:
            raise ValueError("Vehicle block must have two prefixed lines")

        # Extraire l'ID du véhicule et les données de route/produits
        v1, route_part = line1.split(":", 1)
        v2, prod_part = line2.split(":", 1)
        vehicle_id = int(v1.strip())
        if int(v2.strip()) != vehicle_id:
            raise ValueError(f"Mismatched vehicle ids: {v1} vs {v2}")

        # Analyser la séquence de nœuds visités (route)
        route_tokens = [t.strip() for t in route_part.split("-")]
        route_tokens = [t for t in route_tokens if t]
        nodes = [_parse_solution_route_token(t) for t in route_tokens]

        # Analyser la séquence de produits transportés avec coûts cumulés
        prod_tokens = [t.strip() for t in prod_part.split("-")]
        prod_tokens = [t for t in prod_tokens if t]
        products = [_parse_solution_product_token(t) for t in prod_tokens]

        vehicles.append(ParsedSolutionVehicle(vehicle_id=vehicle_id, nodes=nodes, products=products))

        i += 2
        # Ligne de séparation optionnelle entre les blocs de véhicules
        while i < len(raw_lines) and not raw_lines[i].strip():
            i += 1

    # Les lignes non vides restantes contiennent les métriques (6 lignes)
    metrics_lines = [l.strip() for l in raw_lines[i:] if l.strip()]
    if len(metrics_lines) != 6:
        raise ValueError(f"Expected 6 metric lines, got {len(metrics_lines)}")

    metrics = {
        "used_vehicles": int(metrics_lines[0]),
        "total_changes": int(metrics_lines[1]),
        "total_switch_cost": float(metrics_lines[2]),
        "distance_total": float(metrics_lines[3]),
        "processor": metrics_lines[4],
        "time": float(metrics_lines[5]),
    }

    return ParsedSolutionDat(vehicles=vehicles, metrics=metrics)
