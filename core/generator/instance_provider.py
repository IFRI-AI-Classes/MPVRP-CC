import random
import os
import numpy as np

def generer_instance():
    print("--- Générateur d'instance MPVRP-CC ---")
    
    # 1. Saisie des paramètres de base
    id_inst = input("Identifiant de l'instance (ex: 01) : ")
    nb_v = int(input("Nombre de véhicules : "))
    nb_d = int(input("Nombre de dépôts : "))
    nb_g = int(input("Nombre de garages : "))
    nb_s = int(input("Nombre de stations : "))
    nb_p = int(input("Nombre de produits : "))
    max_coord = float(input("Taille de la grille (ex: 100 pour une grille 100x100) : "))
    
    # Paramètres pour la hétérogénéité de la flotte
    min_capacite = 10000
    max_capacite = 25000
    max_demand = 5000
    
    # Nom du fichier selon la nomenclature demandée
    filename = f"MPVRP_{id_inst}_s{nb_s}_d{nb_d}_p{nb_p}.dat"
    instances_dir = "../../data/instances"
    
    # Créer le dossier instances s'il n'existe pas
    if not os.path.exists(instances_dir):
        os.makedirs(instances_dir)
    
    filepath = os.path.join(instances_dir, filename)
    
    # 1. Paramètres globaux (1 ligne)
    params = np.array([nb_p, nb_d, nb_g, nb_s, nb_v])
    
    # 2. Matrice de coûts de transition (NbProduits x NbProduits)
    transition_costs = np.zeros((nb_p, nb_p))
    for i in range(nb_p):
        for j in range(nb_p):
            if i == j:
                transition_costs[i, j] = 0.0
            else:
                transition_costs[i, j] = round(random.uniform(10, 80), 1)
    
    # 3. Véhicules (NbVehicules x 4: capacity, garage_id, product_init, et un placeholder pour ID)
    vehicles = []
    for i in range(1, nb_v + 1):
        capacity = random.randint(min_capacite, max_capacite)  # Capacités variables
        garage_id = random.randint(1, nb_g)
        product_init = random.randint(1, nb_p)
        vehicles.append([i, capacity, garage_id, product_init])
    vehicles = np.array(vehicles)
    
    # 4. Stations d'abord pour calculer les demandes totales (NbStations x (3 + NbProduits))
    stations = []
    total_demands = np.zeros(nb_p)  # Somme des demandes par produit
    for i in range(1, nb_s + 1):
        x = round(random.uniform(0, max_coord), 1)
        y = round(random.uniform(0, max_coord), 1)
        demands = [random.choice([0, random.randint(500, max_demand)]) for _ in range(nb_p)]
        stations.append([i, x, y] + demands)
        total_demands += np.array(demands)
    stations = np.array(stations)
    
    # 5. Dépôts avec stocks garantissant la faisabilité (NbDepots x (3 + NbProduits))
    depots = []
    for i in range(1, nb_d + 1):
        x = round(random.uniform(0, max_coord), 1)
        y = round(random.uniform(0, max_coord), 1)
        # Distribuer les stocks de manière à garantir la faisabilité
        stocks = []
        for p in range(nb_p):
            # Chaque dépôt fournit au moins sa part de la demande totale + une marge
            min_stock = int(total_demands[p] / nb_d) + random.randint(1000, 5000)
            stocks.append(min_stock)
        depots.append([i, x, y] + stocks)
    depots = np.array(depots)
    
    # 6. Garages (NbGarages x 3)
    garages = []
    for i in range(1, nb_g + 1):
        x = round(random.uniform(0, max_coord), 1)
        y = round(random.uniform(0, max_coord), 1)
        garages.append([i, x, y])
    garages = np.array(garages)
    
    # Écriture du fichier avec les tableaux numpy
    with open(filepath, 'w') as f:
        np.savetxt(f, params.reshape(1, -1), fmt='%d', delimiter='\t')
        
        np.savetxt(f, transition_costs, fmt='%.1f', delimiter='\t')
        
        np.savetxt(f, vehicles, fmt='%d', delimiter='\t')
        
        np.savetxt(f, depots, fmt='%g', delimiter='\t')
        
        np.savetxt(f, garages, fmt='%g', delimiter='\t')
        
        np.savetxt(f, stations, fmt='%g', delimiter='\t')

    print(f"\nSuccès ! Fichier généré : {filepath}")

if __name__ == "__main__":
    generer_instance()

