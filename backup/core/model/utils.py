import math

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any

from .schemas import Camion, Depot, Garage, Station, Instance


def euclidean_distance(point1: tuple, point2: tuple) -> float:
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def parse_instance(filepath: str) -> Instance:
    """
    Extraire les données du fichier .dat et les organiser dans une instance de la classe Instance.
    
    Parameters
    ----------
    filepath: str
        Chemin vers le fichier .dat contenant les données de l'instance.

    Returns
    -------
    Instance
        Une instance de la classe Instance contenant toutes les données extraites.
    """""
    try:
        # Extraire toutes les lignes du fichier
        with open(filepath, 'r') as file:
            lines = [line.strip() for line in file.readlines()]

        # 1ère ligne: UUID de l'instance
        # instance_id = lines[0]

        # 2ème ligne: Nombre de produits, depôts, garages, stations, camions
        num_products, num_depots, num_garages, num_stations, num_camions = map(int, lines[1].split())

        # num_products lignes suivantes: Matrice des coûts de transition de produits taille NbProduits × NbProduits
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

    Parameters
    ----------
    instance: Instance
        Une instance de la classe Instance contenant les données.

    Returns
    -------
    dict
        Un dictionnaire avec les distances entre chaque paire de points.
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

    distances = {}
    ids = list(locations.keys())
    for i in range(len(ids)):
        for j in range(len(ids)):
            from_id = ids[i]
            to_id = ids[j]
            distances[(from_id, to_id)] = euclidean_distance(locations[from_id], locations[to_id])

    return distances


@dataclass(frozen=True)
class ParsedSolutionVehicle:
    vehicle_id: int
    nodes: List[Dict[str, Any]]
    products: List[Tuple[int, float]]


@dataclass(frozen=True)
class ParsedSolutionDat:
    vehicles: List[ParsedSolutionVehicle]
    metrics: Dict[str, Any]


def _parse_solution_route_token(token: str) -> Dict[str, Any]:
    """Parse one token from route line: "id", "id [q]", "id (q)"."""
    token = token.strip()
    if not token:
        raise ValueError("Empty token")

    if "[" in token and "]" in token:
        # depot
        left, right = token.split("[", 1)
        node_id = int(left.strip())
        qty = int(right.split("]", 1)[0].strip())
        return {"kind": "depot", "id": node_id, "qty": qty}

    if "(" in token and ")" in token:
        # station
        left, right = token.split("(", 1)
        node_id = int(left.strip())
        qty = int(right.split(")", 1)[0].strip())
        return {"kind": "station", "id": node_id, "qty": qty}

    # garage (no quantity)
    return {"kind": "garage", "id": int(token), "qty": 0}


def _parse_solution_product_token(token: str) -> Tuple[int, float]:
    """Parse one token from product line: "p(cost)"."""
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
    if kind == "garage":
        return f"G{node_id}"
    if kind == "depot":
        return f"D{node_id}"
    if kind == "station":
        return f"S{node_id}"
    raise ValueError(f"Unknown kind: {kind}")


def parse_solution_dat(filepath: str) -> ParsedSolutionDat:
    """Parse a solution file following data/solutions/README.md format."""
    with open(filepath, "r") as f:
        raw_lines = [line.rstrip("\n") for line in f]

    # Keep blank lines to split vehicle blocks; trim trailing empty lines
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()

    vehicles: List[ParsedSolutionVehicle] = []
    i = 0

    def _is_vehicle_line(line: str) -> bool:
        return ":" in line

    # Parse vehicle blocks: two lines with same prefix "k:"
    while i < len(raw_lines) and raw_lines[i].strip() and _is_vehicle_line(raw_lines[i]):
        line1 = raw_lines[i].strip()
        if i + 1 >= len(raw_lines):
            raise ValueError("Unexpected EOF while reading vehicle block")
        line2 = raw_lines[i + 1].strip()

        if ":" not in line1 or ":" not in line2:
            raise ValueError("Vehicle block must have two prefixed lines")

        v1, route_part = line1.split(":", 1)
        v2, prod_part = line2.split(":", 1)
        vehicle_id = int(v1.strip())
        if int(v2.strip()) != vehicle_id:
            raise ValueError(f"Mismatched vehicle ids: {v1} vs {v2}")

        route_tokens = [t.strip() for t in route_part.split("-")]
        route_tokens = [t for t in route_tokens if t]
        nodes = [_parse_solution_route_token(t) for t in route_tokens]

        prod_tokens = [t.strip() for t in prod_part.split("-")]
        prod_tokens = [t for t in prod_tokens if t]
        products = [_parse_solution_product_token(t) for t in prod_tokens]

        vehicles.append(ParsedSolutionVehicle(vehicle_id=vehicle_id, nodes=nodes, products=products))

        i += 2
        # optional blank separator line
        while i < len(raw_lines) and not raw_lines[i].strip():
            i += 1

    # Remaining non-empty lines are metrics (6 lines)
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


if __name__ == "__main__":
    # Exemple d'utilisation
    instance = parse_instance("/home/rosas/Documents/IFRI/Labo/MPVRP-CC/data/instances/medium/MPVRP_M_006_s50_d3_p6.dat")
    # recuperer l'ID des camions
    for camion_id in instance.camions.values():
        print(f"Camion ID: {camion_id.id}")