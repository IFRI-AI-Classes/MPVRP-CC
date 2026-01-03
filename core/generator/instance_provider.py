import random
import os
import sys
import re
import argparse
import uuid
import numpy as np


def parse_args():
    """Parse les arguments en ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Générateur d'instances MPVRP-CC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
                Exemples d'utilisation:
                python instance_provider.py                           # Mode interactif
                python instance_provider.py -i 01 -v 3 -d 2 -g 2 -s 5 -p 3   # Mode ligne de commande
                python instance_provider.py -i 01 -v 3 -d 2 -g 2 -s 5 -p 3 --grid 200
                """
    )
    parser.add_argument('-i', '--id', type=str, help="Identifiant de l'instance (ex: 01)")
    parser.add_argument('-v', '--vehicles', type=int, help="Nombre de véhicules")
    parser.add_argument('-d', '--depots', type=int, help="Nombre de dépôts")
    parser.add_argument('-g', '--garages', type=int, help="Nombre de garages")
    parser.add_argument('-s', '--stations', type=int, help="Nombre de stations")
    parser.add_argument('-p', '--products', type=int, help="Nombre de produits")
    parser.add_argument('--grid', type=float, default=100.0, help="Taille de la grille (défaut: 100)")
    parser.add_argument('--min-capacity', type=int, default=10000, help="Capacité min véhicule (défaut: 10000)")
    parser.add_argument('--max-capacity', type=int, default=25000, help="Capacité max véhicule (défaut: 25000)")
    parser.add_argument('--max-demand', type=int, default=5000, help="Demande max par station (défaut: 5000)")
    parser.add_argument('--seed', type=int, help="Graine aléatoire pour reproductibilité")
    parser.add_argument('--force', '-f', action='store_true', help="Écraser le fichier existant sans confirmation")
    
    return parser.parse_args()


def get_existing_instance_ids(instances_dir):
    """
    Récupère tous les IDs d'instances existants dans le dossier.
    
    Args:
        instances_dir: Chemin vers le dossier des instances
    
    Returns:
        set: Ensemble des IDs existants
    """
    existing_ids = set()
    if not os.path.exists(instances_dir):
        return existing_ids
    
    # Pattern: MPVRP_{ID}_s{X}_d{Y}_p{Z}.dat
    pattern = re.compile(r'^MPVRP_(.+?)_s\d+_d\d+_p\d+\.dat$')
    
    for filename in os.listdir(instances_dir):
        match = pattern.match(filename)
        if match:
            existing_ids.add(match.group(1))
    
    return existing_ids


def validate_instance(params, vehicles, depots, garages, stations, transition_costs, nb_p):
    """Valide l'instance avant écriture"""
    errors = []
    warnings = []
    
    nb_p_val, nb_d, nb_g, nb_s, nb_v = params
    
    # Vérifications minimales
    if nb_v < 1:
        errors.append("Au moins 1 véhicule requis")
    if nb_d < 1:
        errors.append("Au moins 1 dépôt requis")
    if nb_g < 1:
        errors.append("Au moins 1 garage requis")
    if nb_s < 1:
        errors.append("Au moins 1 station requise")
    if nb_p_val < 1:
        errors.append("Au moins 1 produit requis")
    
    # Vérification IDs uniques
    for name, data in [('véhicules', vehicles), ('dépôts', depots), ('garages', garages), ('stations', stations)]:
        ids = [int(row[0]) for row in data]
        if len(ids) != len(set(ids)):
            errors.append(f"IDs dupliqués pour {name}")
    
    # Vérification garages utilisés existent
    garage_ids = set(int(g[0]) for g in garages)
    for v in vehicles:
        if int(v[2]) not in garage_ids:
            errors.append(f"Véhicule {int(v[0])} utilise garage inexistant {int(v[2])}")
    
    # Vérification produits initiaux valides
    product_ids = set(range(1, nb_p + 1))
    for v in vehicles:
        if int(v[3]) not in product_ids:
            errors.append(f"Véhicule {int(v[0])} a produit initial invalide {int(v[3])}")
    
    # Vérification diagonale matrice de transition = 0
    diag = np.diag(transition_costs)
    if not np.allclose(diag, 0):
        errors.append("Diagonale de la matrice de transition non nulle")
    
    # Vérification faisabilité stocks >= demandes
    total_demand = np.zeros(nb_p)
    for s in stations:
        total_demand += np.array(s[3:])
    
    total_stock = np.zeros(nb_p)
    for d in depots:
        total_stock += np.array(d[3:])
    
    for p in range(nb_p):
        if total_stock[p] < total_demand[p]:
            errors.append(f"Produit {p+1}: Stock ({total_stock[p]:.0f}) < Demande ({total_demand[p]:.0f})")
    
    # Vérification capacités positives
    if not np.all(vehicles[:, 1] > 0):
        errors.append("Capacités de véhicules non positives détectées")
    
    return errors, warnings


def generer_instance(id_inst=None, nb_v=None, nb_d=None, nb_g=None, nb_s=None, nb_p=None,
                     max_coord=100.0, min_capacite=10000, max_capacite=25000, max_demand=5000, 
                     seed=None, force_overwrite=False):
    """
    Génère une instance MPVRP-CC.
    
    Si les paramètres sont None, mode interactif activé.
    Sinon, utilise les paramètres fournis.
    
    Args:
        id_inst: Identifiant de l'instance
        nb_v: Nombre de véhicules
        nb_d: Nombre de dépôts
        nb_g: Nombre de garages
        nb_s: Nombre de stations
        nb_p: Nombre de produits
        max_coord: Taille de la grille
        min_capacite: Capacité minimale des véhicules
        max_capacite: Capacité maximale des véhicules
        max_demand: Demande maximale par station
        seed: Graine aléatoire pour reproductibilité
        force_overwrite: Si True, écrase le fichier existant sans confirmation
    
    Returns:
        str: Chemin du fichier généré, ou None si erreur
    """
    # Mode interactif si paramètres manquants
    interactive = any(p is None for p in [id_inst, nb_v, nb_d, nb_g, nb_s, nb_p])
    
    if interactive:
        print("--- Générateur d'instance MPVRP-CC (Mode Interactif) ---\n")
        id_inst = input("Identifiant de l'instance (ex: 01) : ") if id_inst is None else id_inst
        nb_v = int(input("Nombre de véhicules : ")) if nb_v is None else nb_v
        nb_d = int(input("Nombre de dépôts : ")) if nb_d is None else nb_d
        nb_g = int(input("Nombre de garages : ")) if nb_g is None else nb_g
        nb_s = int(input("Nombre de stations : ")) if nb_s is None else nb_s
        nb_p = int(input("Nombre de produits : ")) if nb_p is None else nb_p
        max_coord = float(input("Taille de la grille (ex: 100 pour une grille 100x100) : "))
    else:
        print(f"--- Génération instance MPVRP-CC ---")
        print(f"Paramètres: id={id_inst}, v={nb_v}, d={nb_d}, g={nb_g}, s={nb_s}, p={nb_p}")
    
    # Seed pour reproductibilité
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        print(f"Seed: {seed}")
    
    # Nom du fichier selon la nomenclature demandée
    filename = f"MPVRP_{id_inst}_s{nb_s}_d{nb_d}_p{nb_p}.dat"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    instances_dir = os.path.join(script_dir, "../../data/instances")
    
    # Créer le dossier instances s'il n'existe pas
    if not os.path.exists(instances_dir):
        os.makedirs(instances_dir)
    
    filepath = os.path.join(instances_dir, filename)
    
    # Récupérer les IDs existants
    existing_ids = get_existing_instance_ids(instances_dir)
    
    # Vérification ID unique (indépendamment du nom de fichier complet)
    if id_inst in existing_ids and not force_overwrite:
        if interactive:
            print(f"\n⚠️ L'ID '{id_inst}' est déjà utilisé par une autre instance.")
            print(f"   IDs existants : {sorted(existing_ids)}")
            response = input("Voulez-vous quand même utiliser cet ID ? (o/N) : ").strip().lower()
            if response not in ['o', 'oui', 'y', 'yes']:
                # Proposer un nouvel identifiant
                print("\n💡 Suggestion : choisissez un identifiant différent.")
                new_id = input(f"Nouvel identifiant (actuel: {id_inst}) : ").strip()
                if new_id and new_id not in existing_ids:
                    id_inst = new_id
                    filename = f"MPVRP_{id_inst}_s{nb_s}_d{nb_d}_p{nb_p}.dat"
                    filepath = os.path.join(instances_dir, filename)
                elif new_id in existing_ids:
                    print(f"❌ L'ID '{new_id}' existe également. Abandon.")
                    return None
                else:
                    print("❌ Génération annulée.")
                    return None
        else:
            # Mode non-interactif sans --force
            print(f"❌ L'ID '{id_inst}' est déjà utilisé.")
            print(f"   IDs existants : {sorted(existing_ids)}")
            print("   Utilisez --force pour forcer ou choisissez un autre ID (-i).")
            return None
    
    # Vérification fichier existant (même nom complet)
    if os.path.exists(filepath) and not force_overwrite:
        if interactive:
            print(f"\n⚠️ Le fichier '{filename}' existe déjà.")
            response = input("Voulez-vous l'écraser ? (o/N) : ").strip().lower()
            if response not in ['o', 'oui', 'y', 'yes']:
                print("❌ Génération annulée.")
                return None
        else:
            print(f"❌ Le fichier '{filename}' existe déjà.")
            print("   Utilisez --force pour écraser ou changez l'identifiant (-i).")
            return None
    
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
    
    # 3. Véhicules (NbVehicules x 4: ID, capacity, garage_id, product_init)
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
    
    # 7. Validation avant écriture
    print("\n🔍 Validation de l'instance...")
    errors, warnings = validate_instance(params, vehicles, depots, garages, stations, transition_costs, nb_p)
    
    if errors:
        print("\n❌ Erreurs de validation détectées :")
        for error in errors:
            print(f"  - {error}")
        print("\n⚠️ Instance non générée. Corrigez les paramètres.")
        return None
    
    if warnings:
        print("\n⚠️ Avertissements :")
        for warning in warnings:
            print(f"  - {warning}")
    
    print("✅ Validation réussie !")
    
    # 8. Génération de l'UUID v4 unique pour cette instance
    instance_uuid = str(uuid.uuid4())
    print(f"🔑 UUID généré : {instance_uuid}")
    
    # 9. Écriture du fichier avec les tableaux numpy
    with open(filepath, 'w') as f:
        # Écrire l'UUID en commentaire
        f.write(f"# {instance_uuid}\n")
        
        np.savetxt(f, params.reshape(1, -1), fmt='%d', delimiter='\t')
        
        np.savetxt(f, transition_costs, fmt='%.1f', delimiter='\t')
        
        np.savetxt(f, vehicles, fmt='%d', delimiter='\t')
        
        np.savetxt(f, depots, fmt='%g', delimiter='\t')
        
        np.savetxt(f, garages, fmt='%g', delimiter='\t')
        
        np.savetxt(f, stations, fmt='%g', delimiter='\t')

    print(f"\n✅ Succès ! Fichier généré : {filepath}")
    return filepath


if __name__ == "__main__":
    args = parse_args()
    
    # Si tous les args requis sont fournis, mode non-interactif
    if all([args.id, args.vehicles, args.depots, args.garages, args.stations, args.products]):
        generer_instance(
            id_inst=args.id,
            nb_v=args.vehicles,
            nb_d=args.depots,
            nb_g=args.garages,
            nb_s=args.stations,
            nb_p=args.products,
            max_coord=args.grid,
            min_capacite=args.min_capacity,
            max_capacite=args.max_capacity,
            max_demand=args.max_demand,
            seed=args.seed,
            force_overwrite=args.force
        )
    else:
        # Mode interactif
        generer_instance()
