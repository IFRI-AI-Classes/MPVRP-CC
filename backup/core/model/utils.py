import math

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


if __name__ == "__main__":
    # Exemple d'utilisation
    instance = parse_instance("/home/rosas/Documents/IFRI/Labo/MPVRP-CC/data/instances/medium/MPVRP_M_006_s50_d3_p6.dat")
    # recuperer l'ID des camions
    for camion_id in instance.camions.values():
        print(f"Camion ID: {camion_id.id}")