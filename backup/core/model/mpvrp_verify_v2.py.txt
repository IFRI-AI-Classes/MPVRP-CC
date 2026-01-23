"""
MPVRP-CRP Vérificateur v2
=========================
Vérification robuste par RECONSTRUCTION DE TRAJET
au lieu de simple vérification de contraintes.

Ce vérificateur:
1. Reconstitue le chemin physique complet de chaque véhicule
2. Vérifie la continuité spatiale (pas de téléportation)
3. Vérifie les stocks et demandes
4. Recalcule le coût total de manière indépendante
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Instance:
    num_vehicles: int
    num_garages: int
    num_products: int
    num_stations: int
    num_depots: int
    vehicles: List[dict]
    garages: List[dict]
    depots: List[dict]
    stations: List[dict]
    change_costs: Dict[Tuple[int, int], float]


def parse_instance(filepath: str) -> Instance:
    """Parse le fichier d'instance"""
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    idx = 0
    parts = lines[idx].split()
    num_vehicles = int(parts[0])
    num_depots = int(parts[1])
    num_products = int(parts[2])
    num_stations = int(parts[3])
    num_garages = int(parts[4])
    idx += 1
    
    change_costs = {}
    for p1 in range(num_products):
        costs = list(map(float, lines[idx].split()))
        for p2, cost in enumerate(costs):
            change_costs[(p1, p2)] = cost
        idx += 1
    
    vehicles = []
    for _ in range(num_vehicles):
        parts = lines[idx].split()
        vehicles.append({
            'id': int(parts[0]),
            'capacity': float(parts[1]),
            'garage_id': int(parts[2]),
            'initial_product': int(parts[3]) - 1  # 0-indexed
        })
        idx += 1
    
    depots = []
    for _ in range(num_depots):
        parts = lines[idx].split()
        stocks = {p: float(parts[3 + p]) for p in range(num_products)}
        depots.append({
            'id': int(parts[0]),
            'x': float(parts[1]),
            'y': float(parts[2]),
            'stocks': stocks
        })
        idx += 1
    
    garages = []
    for _ in range(num_garages):
        parts = lines[idx].split()
        garages.append({
            'id': int(parts[0]),
            'x': float(parts[1]),
            'y': float(parts[2])
        })
        idx += 1
    
    stations = []
    for _ in range(num_stations):
        parts = lines[idx].split()
        demands = {p: float(parts[3 + p]) for p in range(num_products)}
        stations.append({
            'id': int(parts[0]),
            'x': float(parts[1]),
            'y': float(parts[2]),
            'demands': demands
        })
        idx += 1
    
    return Instance(
        num_vehicles=num_vehicles,
        num_garages=num_garages,
        num_products=num_products,
        num_stations=num_stations,
        num_depots=num_depots,
        vehicles=vehicles,
        garages=garages,
        depots=depots,
        stations=stations,
        change_costs=change_costs
    )


def get_coords(instance: Instance, node: str) -> Tuple[float, float]:
    """Retourne les coordonnées d'un nœud"""
    if node.startswith('G'):
        g_id = int(node[1:])
        for g in instance.garages:
            if g['id'] == g_id:
                return (g['x'], g['y'])
    elif node.startswith('D'):
        d_id = int(node[1:])
        for d in instance.depots:
            if d['id'] == d_id:
                return (d['x'], d['y'])
    elif node.startswith('S'):
        s_id = int(node[1:])
        for s in instance.stations:
            if s['id'] == s_id:
                return (s['x'], s['y'])
    raise ValueError(f"Nœud inconnu: {node}")


def distance(instance: Instance, n1: str, n2: str) -> float:
    """Calcule la distance euclidienne entre deux nœuds"""
    x1, y1 = get_coords(instance, n1)
    x2, y2 = get_coords(instance, n2)
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def reconstruct_vehicle_path(instance: Instance, solution: Dict, vehicle_id: int) -> Dict:
    """
    Reconstruit le chemin physique complet d'un véhicule.
    Retourne un dictionnaire avec:
    - path: liste des nœuds visités dans l'ordre
    - arcs: liste des arcs (from, to, product)
    - errors: liste des erreurs de continuité
    - loads: chargements effectués
    - deliveries: livraisons effectuées
    """
    result = {
        'vehicle': vehicle_id,
        'path': [],
        'arcs': [],
        'errors': [],
        'loads': {},      # {(depot, position, product): quantity}
        'deliveries': {}, # {(station, product): quantity}
        'switches': [],
        'costs': {
            'routing': 0.0,
            'switches': 0.0,
            'start': 0.0,
            'end': 0.0
        }
    }
    
    v_data = solution.get('variables', {})
    
    # Trouver le garage du véhicule
    vehicle_info = None
    for v in instance.vehicles:
        if v['id'] == vehicle_id:
            vehicle_info = v
            break
    
    if vehicle_info is None:
        result['errors'].append(f"Véhicule {vehicle_id} non trouvé dans l'instance")
        return result
    
    garage = f"G{vehicle_info['garage_id']}"
    initial_product = vehicle_info['initial_product']
    
    # Vérifier si le véhicule est utilisé
    used = v_data.get('Used', {})
    is_used = any(k.startswith(f"({vehicle_id},") and v == 1 for k, v in used.items())
    
    if not is_used:
        result['path'] = [garage]
        return result
    
    # 1. Trouver le Start (Garage -> Dépôt)
    start_data = v_data.get('Start', {})
    start_depot = None
    for key, val in start_data.items():
        if val == 1 and f", {vehicle_id})" in key:
            # Parser le tuple string
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 3:
                start_depot = parts[1]
                result['costs']['start'] = distance(instance, garage, start_depot)
                break
    
    if start_depot is None:
        result['errors'].append("Pas de Start trouvé pour un véhicule utilisé")
        return result
    
    result['path'].append(garage)
    result['path'].append(start_depot)
    result['arcs'].append((garage, start_depot, 'start'))
    
    # 2. Extraire les arcs x par produit
    x_data = v_data.get('x', {})
    arcs_by_product = {p: [] for p in range(instance.num_products)}
    
    for key, val in x_data.items():
        if val == 1:
            # Parser "('D1', 'S2', 1, 0)"
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                i, j, k, p = parts[0], parts[1], int(parts[2]), int(parts[3])
                if k == vehicle_id:
                    arcs_by_product[p].append((i, j))
    
    # 3. Extraire les chargements (Load et QLoad)
    load_data = v_data.get('Load', {})
    qload_data = v_data.get('QLoad', {})
    
    positions_info = {}  # {position: {'depot': d, 'product': p, 'quantity': q}}
    
    for key, val in load_data.items():
        if val == 1:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                d, k, t, p = parts[0], int(parts[1]), int(parts[2]), int(parts[3])
                if k == vehicle_id:
                    positions_info[t] = {'depot': d, 'product': p, 'quantity': 0}
    
    for key, val in qload_data.items():
        if val and val > 0:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                d, k, t, p = parts[0], int(parts[1]), int(parts[2]), int(parts[3])
                if k == vehicle_id and t in positions_info:
                    positions_info[t]['quantity'] = val
                    result['loads'][(d, t, p)] = val
    
    # 4. Extraire les livraisons
    deliv_data = v_data.get('Deliv', {})
    for key, val in deliv_data.items():
        if val and val > 0:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 3:
                s, p, k = parts[0], int(parts[1]), int(parts[2])
                if k == vehicle_id:
                    result['deliveries'][(s, p)] = val
    
    # 5. Extraire les switches
    switch_data = v_data.get('Switch', {})
    for key, val in switch_data.items():
        if val == 1:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                k, t, p1, p2 = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                if k == vehicle_id:
                    result['switches'].append({'position': t, 'from': p1, 'to': p2})
                    result['costs']['switches'] += instance.change_costs.get((p1, p2), 0)
    
    # 6. Extraire le Fin
    fin_data = v_data.get('Fin', {})
    fin_node = None
    fin_product = None
    for key, val in fin_data.items():
        if val == 1:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                i, g, k, p = parts[0], parts[1], int(parts[2]), int(parts[3])
                if k == vehicle_id:
                    fin_node = i
                    fin_product = p
                    result['costs']['end'] = distance(instance, fin_node, garage)
                    break
    
    # 7. Reconstituer le chemin complet en suivant les arcs
    # Triez les positions
    sorted_positions = sorted(positions_info.keys())
    
    current_node = start_depot
    current_product = initial_product
    
    for pos in sorted_positions:
        pos_info = positions_info[pos]
        depot = pos_info['depot']
        product = pos_info['product']
        
        # Si changement de produit, on doit être au dépôt
        if product != current_product:
            # Vérifier qu'on est bien arrivé au dépôt
            if current_node != depot:
                result['errors'].append(
                    f"Position {pos}: Switch {current_product}->{product} au dépôt {depot}, "
                    f"mais véhicule à {current_node} (TÉLÉPORTATION!)"
                )
            current_product = product
        
        # Suivre les arcs de ce produit depuis le dépôt
        product_arcs = arcs_by_product[product].copy()
        
        # Trouver le chemin depuis le dépôt
        visited_in_product = set()
        node = depot
        
        while product_arcs:
            # Chercher un arc sortant de node
            found = False
            for arc in product_arcs:
                if arc[0] == node:
                    result['arcs'].append((arc[0], arc[1], product))
                    result['costs']['routing'] += distance(instance, arc[0], arc[1])
                    result['path'].append(arc[1])
                    node = arc[1]
                    product_arcs.remove(arc)
                    found = True
                    break
            
            if not found:
                if product_arcs:
                    result['errors'].append(
                        f"Position {pos}, Produit {product}: Arcs restants {product_arcs} "
                        f"non connectés depuis {node}"
                    )
                break
        
        current_node = node
    
    # 8. Vérifier que le Fin est cohérent
    if fin_node:
        if current_node != fin_node:
            result['errors'].append(
                f"Fin déclaré depuis {fin_node}, mais véhicule à {current_node}"
            )
        result['path'].append(garage)
        result['arcs'].append((fin_node, garage, 'end'))
    
    return result


def verify_demands(instance: Instance, solution: Dict) -> List[str]:
    """Vérifie que toutes les demandes sont satisfaites"""
    errors = []
    
    # Calculer les livraisons totales par station/produit
    total_deliveries = {}
    v_data = solution.get('variables', {})
    deliv_data = v_data.get('Deliv', {})
    
    for key, val in deliv_data.items():
        if val and val > 0:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 3:
                s, p = parts[0], int(parts[1])
                if (s, p) not in total_deliveries:
                    total_deliveries[(s, p)] = 0
                total_deliveries[(s, p)] += val
    
    # Comparer aux demandes
    for station in instance.stations:
        s_id = f"S{station['id']}"
        for p, demand in station['demands'].items():
            if demand > 0:
                delivered = total_deliveries.get((s_id, p), 0)
                if abs(delivered - demand) > 0.01:
                    errors.append(
                        f"Station {s_id}, Produit {p}: Demande={demand}, Livré={delivered}"
                    )
    
    return errors


def verify_stocks(instance: Instance, solution: Dict) -> List[str]:
    """Vérifie que les stocks des dépôts ne sont pas dépassés"""
    errors = []
    
    # Calculer les prélèvements totaux par dépôt/produit
    total_loads = {}
    v_data = solution.get('variables', {})
    qload_data = v_data.get('QLoad', {})
    
    for key, val in qload_data.items():
        if val and val > 0:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                d, p = parts[0], int(parts[3])
                if (d, p) not in total_loads:
                    total_loads[(d, p)] = 0
                total_loads[(d, p)] += val
    
    # Comparer aux stocks
    for depot in instance.depots:
        d_id = f"D{depot['id']}"
        for p, stock in depot['stocks'].items():
            loaded = total_loads.get((d_id, p), 0)
            if loaded > stock + 0.01:
                errors.append(
                    f"Dépôt {d_id}, Produit {p}: Stock={stock}, Prélevé={loaded}"
                )
    
    return errors


def verify_capacity(instance: Instance, solution: Dict) -> List[str]:
    """Vérifie que la capacité des véhicules n'est pas dépassée"""
    errors = []
    
    v_data = solution.get('variables', {})
    qload_data = v_data.get('QLoad', {})
    
    # Grouper par véhicule et position
    loads_by_vt = {}
    for key, val in qload_data.items():
        if val and val > 0:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                k, t = int(parts[1]), int(parts[2])
                if (k, t) not in loads_by_vt:
                    loads_by_vt[(k, t)] = 0
                loads_by_vt[(k, t)] += val
    
    # Vérifier les capacités
    for (k, t), total_load in loads_by_vt.items():
        capacity = None
        for v in instance.vehicles:
            if v['id'] == k:
                capacity = v['capacity']
                break
        if capacity and total_load > capacity + 0.01:
            errors.append(
                f"Véhicule {k}, Position {t}: Chargé={total_load}, Capacité={capacity}"
            )
    
    return errors


def calculate_cost(instance: Instance, solution: Dict) -> Dict:
    """Recalcule le coût total de manière indépendante"""
    costs = {
        'routing': 0.0,
        'switches': 0.0,
        'start': 0.0,
        'end': 0.0,
        'total': 0.0
    }
    
    v_data = solution.get('variables', {})
    
    # Coût de routage
    x_data = v_data.get('x', {})
    for key, val in x_data.items():
        if val == 1:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                i, j = parts[0], parts[1]
                costs['routing'] += distance(instance, i, j)
    
    # Coût des switches
    switch_data = v_data.get('Switch', {})
    for key, val in switch_data.items():
        if val == 1:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                p1, p2 = int(parts[2]), int(parts[3])
                costs['switches'] += instance.change_costs.get((p1, p2), 0)
    
    # Coût de départ
    start_data = v_data.get('Start', {})
    for key, val in start_data.items():
        if val == 1:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 3:
                g, d = parts[0], parts[1]
                costs['start'] += distance(instance, g, d)
    
    # Coût de fin
    fin_data = v_data.get('Fin', {})
    for key, val in fin_data.items():
        if val == 1:
            parts = key.strip("()").replace("'", "").split(", ")
            if len(parts) >= 4:
                i, g = parts[0], parts[1]
                costs['end'] += distance(instance, i, g)
    
    costs['total'] = costs['routing'] + costs['switches'] + costs['start'] + costs['end']
    
    return costs


def main():
    import sys
    import os
    
    # Répertoires du projet
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    solutions_dir = os.path.join(script_dir, "solutions")
    
    # Vérifier que le dossier data/ existe
    if not os.path.exists(data_dir):
        print(f"Erreur: Le dossier '{data_dir}' n'existe pas.")
        return

    # Lister les fichiers disponibles dans data/
    available_files = [f for f in os.listdir(data_dir) if f.endswith('.dat')]
    if available_files:
        print("Fichiers d'instance disponibles dans data/:")
        for f in available_files:
            print(f"  - {f}")
        print()
    
    # Demander le nom du fichier instance
    instance_name = input("Entrez le nom du fichier instance (sans chemin, ex: instance_1.dat): ").strip()
    
    # Construire les chemins complets
    instance_file = os.path.join(data_dir, instance_name)
    
    # Nom du fichier de solution attendu
    base_name = os.path.splitext(instance_name)[0]
    solution_name = f"{base_name}_solution.json"
    solution_file = os.path.join(solutions_dir, solution_name)
    
    if not os.path.exists(instance_file):
        print(f"Erreur: Le fichier instance '{instance_file}' n'existe pas.")
        return
        
    if not os.path.exists(solution_file):
        print(f"Erreur: Le fichier solution '{solution_file}' n'existe pas.")
        print(f"Assurez-vous d'avoir exécuté le solveur pour cette instance.")
        return
    
    print(f"Instance: {instance_file}")
    print(f"Solution: {solution_file}")
    
    instance = parse_instance(instance_file)
    
    with open(solution_file, 'r') as f:
        solution = json.load(f)
    
    print(f"\n{'='*60}")
    print("INFORMATIONS INSTANCE")
    print(f"{'='*60}")
    print(f"Véhicules: {instance.num_vehicles}")
    print(f"Produits: {instance.num_products}")
    print(f"Stations: {instance.num_stations}")
    print(f"Dépôts: {instance.num_depots}")
    
    print(f"\nCoûts de changement de produit:")
    for (p1, p2), cost in instance.change_costs.items():
        if p1 != p2:
            print(f"  {p1} -> {p2}: {cost}")
    
    print(f"\nVéhicules:")
    for v in instance.vehicles:
        print(f"  V{v['id']}: Garage G{v['garage_id']}, Produit initial {v['initial_product']}, Capacité {v['capacity']}")
    
    print(f"\n{'='*60}")
    print("RECONSTRUCTION DES TRAJETS")
    print(f"{'='*60}")
    
    all_errors = []
    
    for v in instance.vehicles:
        result = reconstruct_vehicle_path(instance, solution, v['id'])
        
        print(f"\n--- Véhicule {v['id']} ---")
        if len(result['path']) <= 1:
            print("  Non utilisé")
            continue
        
        print(f"  Chemin: {' -> '.join(result['path'])}")
        print(f"  Arcs: {result['arcs']}")
        
        if result['loads']:
            print(f"  Chargements:")
            for (d, t, p), q in result['loads'].items():
                print(f"    Position {t}: {q} de produit {p} au dépôt {d}")
        
        if result['deliveries']:
            print(f"  Livraisons:")
            for (s, p), q in result['deliveries'].items():
                print(f"    {q} de produit {p} à station {s}")
        
        if result['switches']:
            print(f"  Switches:")
            for sw in result['switches']:
                cost = instance.change_costs.get((sw['from'], sw['to']), 0)
                print(f"    Position {sw['position']}: {sw['from']} -> {sw['to']} (coût: {cost})")
        
        if result['errors']:
            print(f"  ❌ ERREURS:")
            for err in result['errors']:
                print(f"    - {err}")
                all_errors.append(err)
        else:
            print(f"  ✅ Trajet continu et cohérent")
    
    print(f"\n{'='*60}")
    print("VÉRIFICATION DES CONTRAINTES PHYSIQUES")
    print(f"{'='*60}")
    
    # Vérifier les demandes
    demand_errors = verify_demands(instance, solution)
    if demand_errors:
        print("\n❌ Erreurs de demande:")
        for err in demand_errors:
            print(f"  - {err}")
        all_errors.extend(demand_errors)
    else:
        print("\n✅ Toutes les demandes satisfaites")
    
    # Vérifier les stocks
    stock_errors = verify_stocks(instance, solution)
    if stock_errors:
        print("\n❌ Erreurs de stock:")
        for err in stock_errors:
            print(f"  - {err}")
        all_errors.extend(stock_errors)
    else:
        print("\n✅ Stocks respectés")
    
    # Vérifier les capacités
    capacity_errors = verify_capacity(instance, solution)
    if capacity_errors:
        print("\n❌ Erreurs de capacité:")
        for err in capacity_errors:
            print(f"  - {err}")
        all_errors.extend(capacity_errors)
    else:
        print("\n✅ Capacités respectées")
    
    print(f"\n{'='*60}")
    print("VÉRIFICATION DU COÛT")
    print(f"{'='*60}")
    
    costs = calculate_cost(instance, solution)
    reported_cost = solution.get('objective', 0)
    
    print(f"\nDécomposition du coût calculé:")
    print(f"  Routage:   {costs['routing']:.2f}")
    print(f"  Switches:  {costs['switches']:.2f}")
    print(f"  Départs:   {costs['start']:.2f}")
    print(f"  Retours:   {costs['end']:.2f}")
    print(f"  TOTAL:     {costs['total']:.2f}")
    print(f"\nCoût rapporté: {reported_cost:.2f}")
    
    if abs(costs['total'] - reported_cost) > 0.01:
        print(f"\n❌ ÉCART DE COÛT: {abs(costs['total'] - reported_cost):.2f}")
        all_errors.append(f"Écart de coût: calculé={costs['total']:.2f}, rapporté={reported_cost:.2f}")
    else:
        print("\n✅ Coût vérifié")
    
    print(f"\n{'='*60}")
    print("RÉSUMÉ")
    print(f"{'='*60}")
    
    if all_errors:
        print(f"\n❌ SOLUTION NON VALIDE - {len(all_errors)} erreur(s) trouvée(s)")
        for i, err in enumerate(all_errors, 1):
            print(f"  {i}. {err}")
    else:
        print("\n✅ SOLUTION VALIDE ET COHÉRENTE")


if __name__ == "__main__":
    main()
