"""
MPVRP-CRP Solver
================
Solveur pour le Problème de Tournée de Véhicules Multi-Produits Multi-Dépôts
avec Coût de Changement de Produit (CRP)

Implémentation fidèle de la modélisation PLNEM avec PuLP
Exporte la solution optimale en JSON pour vérification externe.

Structure des dossiers:
    data/       - Fichiers d'instance (.dat)
    solutions/  - Solutions exportées (.json)
    visu/       - Visualisations

Usage:
    python mpvrp_solver.py
    (Le programme demande le nom du fichier instance à l'exécution)
"""

import pulp
import math
import json
import networkx as nx
from typing import Dict, List, Tuple
from dataclasses import dataclass


# =============================================================================
# STRUCTURES DE DONNÉES
# =============================================================================

@dataclass
class Vehicle:
    id: int
    capacity: float
    garage_id: int
    initial_product: int


@dataclass
class Depot:
    id: int
    x: float
    y: float
    stocks: Dict[int, float]


@dataclass
class Station:
    id: int
    x: float
    y: float
    demands: Dict[int, float]


@dataclass
class Garage:
    id: int
    x: float
    y: float


@dataclass
class Instance:
    num_vehicles: int
    num_garages: int
    num_products: int
    num_stations: int
    num_depots: int
    vehicles: List[Vehicle]
    garages: List[Garage]
    depots: List[Depot]
    stations: List[Station]
    change_costs: Dict[Tuple[int, int], float]


# =============================================================================
# PARSING DES INSTANCES
# =============================================================================

def parse_instance(filepath: str) -> Instance:
    """Parse un fichier d'instance au format .dat"""
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    line_idx = 0
    
    parts = lines[line_idx].split()
    num_vehicles = int(parts[0])
    num_depots = int(parts[1])
    num_products = int(parts[2])
    num_stations = int(parts[3])
    num_garages = int(parts[4])
    line_idx += 1
    
    print(f"  Dimensions: {num_vehicles} véhicules, {num_depots} dépôts, "
          f"{num_products} produits, {num_stations} stations, {num_garages} garages")
    
    change_costs = {}
    for p1 in range(num_products):
        costs = list(map(float, lines[line_idx].split()))
        for p2, cost in enumerate(costs):
            change_costs[(p1, p2)] = cost
        line_idx += 1
    
    vehicles = []
    for _ in range(num_vehicles):
        parts = lines[line_idx].split()
        vehicles.append(Vehicle(
            id=int(parts[0]), capacity=float(parts[1]),
            garage_id=int(parts[2]), initial_product=int(parts[3])
        ))
        line_idx += 1
    
    depots = []
    for _ in range(num_depots):
        parts = lines[line_idx].split()
        stocks = {p: float(parts[3 + p]) for p in range(num_products)}
        depots.append(Depot(id=int(parts[0]), x=float(parts[1]), y=float(parts[2]), stocks=stocks))
        line_idx += 1
    
    garages = []
    for _ in range(num_garages):
        parts = lines[line_idx].split()
        garages.append(Garage(id=int(parts[0]), x=float(parts[1]), y=float(parts[2])))
        line_idx += 1
    
    stations = []
    for _ in range(num_stations):
        parts = lines[line_idx].split()
        demands = {p: float(parts[3 + p]) for p in range(num_products)}
        stations.append(Station(id=int(parts[0]), x=float(parts[1]), y=float(parts[2]), demands=demands))
        line_idx += 1
    
    return Instance(
        num_vehicles=num_vehicles, num_garages=num_garages, num_products=num_products,
        num_stations=num_stations, num_depots=num_depots, vehicles=vehicles,
        garages=garages, depots=depots, stations=stations, change_costs=change_costs
    )


# =============================================================================
# CALCUL DES DISTANCES
# =============================================================================

def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def compute_distances(instance: Instance) -> Dict[Tuple[str, str], float]:
    distances = {}
    nodes = {}
    for g in instance.garages:
        nodes[f"G{g.id}"] = (g.x, g.y)
    for d in instance.depots:
        nodes[f"D{d.id}"] = (d.x, d.y)
    for s in instance.stations:
        nodes[f"S{s.id}"] = (s.x, s.y)
    
    for n1, (x1, y1) in nodes.items():
        for n2, (x2, y2) in nodes.items():
            distances[(n1, n2)] = euclidean_distance(x1, y1, x2, y2) if n1 != n2 else 0.0
    
    return distances


# =============================================================================
# SOLVEUR MPVRP-CRP
# =============================================================================

class MPVRPSolver:
    """Solveur MPVRP-CRP utilisant PuLP"""
    
    def __init__(self, instance: Instance, max_positions: int = None):
        self.instance = instance
        self.distances = compute_distances(instance)
        
        self.K = [v.id for v in instance.vehicles]
        self.P = list(range(instance.num_products))
        self.G = [f"G{g.id}" for g in instance.garages]
        self.D = [f"D{d.id}" for d in instance.depots]
        self.S = [f"S{s.id}" for s in instance.stations]
        self.V = self.D + self.S
        
        if max_positions is None:
            max_positions = len(self.P) * len(self.S)
        self.T = list(range(1, max_positions + 1))
        
        self.C = {v.id: v.capacity for v in instance.vehicles}
        self.g_k = {v.id: f"G{v.garage_id}" for v in instance.vehicles}
        self.P_initial = {v.id: v.initial_product - 1 for v in instance.vehicles}
        
        self.demand = {(f"S{s.id}", p): d for s in instance.stations for p, d in s.demands.items()}
        self.stock = {(f"D{d.id}", p): s for d in instance.depots for p, s in d.stocks.items()}
        self.change_cost = instance.change_costs
        self.M = sum(self.C.values()) * 10
        self.model = None
        
    def _get_distance(self, i: str, j: str) -> float:
        return self.distances.get((i, j), 0.0)
    
    def build_model(self):
        """Construit le modèle PLNEM complet"""
        print("Construction du modèle...")
        self.model = pulp.LpProblem("MPVRP_CRP", pulp.LpMinimize)
        
        # === VARIABLES ===
        self.x = {(i, j, k, p): pulp.LpVariable(f"x_{i}_{j}_{k}_{p}", cat=pulp.LpBinary)
                  for i in self.V for j in self.V if i != j for k in self.K for p in self.P}
        
        self.Load = {(d, k, t, p): pulp.LpVariable(f"Load_{d}_{k}_{t}_{p}", cat=pulp.LpBinary)
                     for d in self.D for k in self.K for t in self.T for p in self.P}
        
        self.Deliv = {(s, p, k): pulp.LpVariable(f"Deliv_{s}_{p}_{k}", lowBound=0)
                      for s in self.S for p in self.P for k in self.K}
        
        self.QLoad = {(d, k, t, p): pulp.LpVariable(f"QLoad_{d}_{k}_{t}_{p}", lowBound=0)
                      for d in self.D for k in self.K for t in self.T for p in self.P}
        
        self.Switch = {(k, t, p1, p2): pulp.LpVariable(f"Switch_{k}_{t}_{p1}_{p2}", cat=pulp.LpBinary)
                       for k in self.K for t in self.T for p1 in self.P for p2 in self.P if p1 != p2}
        
        self.Start = {(self.g_k[k], d, k): pulp.LpVariable(f"Start_{self.g_k[k]}_{d}_{k}", cat=pulp.LpBinary)
                      for k in self.K for d in self.D}
        
        # Fin restreint aux stations uniquement (s ∈ S, pas i ∈ V)
        # Force le véhicule à terminer depuis une station, pas depuis un dépôt
        self.Fin = {(s, self.g_k[k], k, p): pulp.LpVariable(f"Fin_{s}_{self.g_k[k]}_{k}_{p}", cat=pulp.LpBinary)
                    for k in self.K for s in self.S for p in self.P}
        
        self.Used = {(k, t): pulp.LpVariable(f"Used_{k}_{t}", cat=pulp.LpBinary)
                     for k in self.K for t in self.T}
        
        self.Prod = {(k, t, p): pulp.LpVariable(f"Prod_{k}_{t}_{p}", cat=pulp.LpBinary)
                     for k in self.K for t in self.T for p in self.P}
        
        # Position fictive t=0 : produit initial (paramètre fixe, pas une variable)
        # Prod[k,0,p] = 1 si p == P_initial[k], 0 sinon
        
        # === FONCTION OBJECTIF ===
        routing_cost = pulp.lpSum(self._get_distance(i, j) * self.x[i, j, k, p]
                                  for i in self.V for j in self.V if i != j for k in self.K for p in self.P)
        switch_cost = pulp.lpSum(self.change_cost.get((p1, p2), 0) * self.Switch[k, t, p1, p2]
                                 for k in self.K for t in self.T for p1 in self.P for p2 in self.P if p1 != p2)
        start_cost = pulp.lpSum(self._get_distance(self.g_k[k], d) * self.Start[self.g_k[k], d, k]
                                for k in self.K for d in self.D)
        # Coût de fin : somme sur les stations uniquement (s ∈ S)
        end_cost = pulp.lpSum(self._get_distance(s, self.g_k[k]) * self.Fin[s, self.g_k[k], k, p]
                              for k in self.K for s in self.S for p in self.P)
        
        self.model += routing_cost + switch_cost + start_cost + end_cost, "Total_Cost"
        
        # === CONTRAINTES ===
        
        # C1: Satisfaction de la demande
        for s in self.S:
            for p in self.P:
                if self.demand.get((s, p), 0) > 0:
                    self.model += pulp.lpSum(self.Deliv[s, p, k] for k in self.K) == self.demand[(s, p)], f"C1_{s}_{p}"
        
        # C2: Début de tournée
        for k in self.K:
            g = self.g_k[k]
            self.model += pulp.lpSum(self.Start[g, d, k] for d in self.D) == self.Used[k, 1], f"C2_{k}"
        
        # C3: Fin de tournée (depuis une station uniquement)
        for k in self.K:
            g = self.g_k[k]
            self.model += pulp.lpSum(self.Fin[s, g, k, p] for s in self.S for p in self.P) == self.Used[k, 1], f"C3_{k}"
        
        # C4: Conservation du flot aux stations (par produit)
        for s in self.S:
            for k in self.K:
                for p in self.P:
                    inflow = pulp.lpSum(self.x[i, s, k, p] for i in self.V if i != s)
                    outflow = pulp.lpSum(self.x[s, j, k, p] for j in self.V if j != s)
                    fin_term = self.Fin[s, self.g_k[k], k, p]
                    self.model += inflow == outflow + fin_term, f"C4_{s}_{k}_{p}"
        
        # C5: Conservation du flot aux dépôts (par véhicule - somme sur produits)
        # Pas de terme Fin ici : le véhicule ne peut PAS terminer depuis un dépôt
        for d in self.D:
            for k in self.K:
                g = self.g_k[k]
                start_term = self.Start[g, d, k]
                inflow = pulp.lpSum(self.x[i, d, k, p] for i in self.V if i != d for p in self.P)
                outflow = pulp.lpSum(self.x[d, j, k, p] for j in self.V if j != d for p in self.P)
                self.model += start_term + inflow == outflow, f"C5_{d}_{k}"
        
        # C6: Unicité de visite
        for s in self.S:
            for k in self.K:
                for p in self.P:
                    self.model += pulp.lpSum(self.x[i, s, k, p] for i in self.V if i != s) <= 1, f"C6_{s}_{k}_{p}"
        
        # C7: Lien chargement et mini-tournée
        for d in self.D:
            for k in self.K:
                for p in self.P:
                    self.model += (pulp.lpSum(self.x[d, j, k, p] for j in self.V if j != d) ==
                                   pulp.lpSum(self.Load[d, k, t, p] for t in self.T)), f"C7_{d}_{k}_{p}"
        
        # C8: Lien livraison et inflow (on ne peut livrer que si on ARRIVE à la station)
        for s in self.S:
            for k in self.K:
                for p in self.P:
                    self.model += self.Deliv[s, p, k] <= self.M * pulp.lpSum(
                        self.x[i, s, k, p] for i in self.V if i != s), f"C8_{s}_{k}_{p}"
        
        # C9: Conservation quantité chargée/livrée
        for k in self.K:
            for p in self.P:
                self.model += (pulp.lpSum(self.Deliv[s, p, k] for s in self.S) ==
                               pulp.lpSum(self.QLoad[d, k, t, p] for d in self.D for t in self.T)), f"C9_{k}_{p}"
        
        # C10: Lien QLoad et Load
        for d in self.D:
            for k in self.K:
                for t in self.T:
                    for p in self.P:
                        self.model += self.QLoad[d, k, t, p] <= self.M * self.Load[d, k, t, p], f"C10_{d}_{k}_{t}_{p}"
        
        # C11: Contrainte de stock
        for d in self.D:
            for p in self.P:
                self.model += pulp.lpSum(self.QLoad[d, k, t, p] for k in self.K for t in self.T) <= self.stock.get((d, p), 0), f"C11_{d}_{p}"
        
        # C12: Capacité du véhicule
        for k in self.K:
            for t in self.T:
                self.model += pulp.lpSum(self.QLoad[d, k, t, p] for d in self.D for p in self.P) <= self.C[k] * self.Used[k, t], f"C12_{k}_{t}"
        
        # C13: Un seul produit par position
        for k in self.K:
            for t in self.T:
                self.model += pulp.lpSum(self.Load[d, k, t, p] for p in self.P for d in self.D) == self.Used[k, t], f"C13_{k}_{t}"
        
        # C13bis: Identification du produit par position
        for k in self.K:
            for t in self.T:
                for p in self.P:
                    self.model += self.Prod[k, t, p] == pulp.lpSum(self.Load[d, k, t, p] for d in self.D), f"C13b_{k}_{t}_{p}"
        
        # C14: Ordonnancement des positions
        for k in self.K:
            for t in self.T[:-1]:
                self.model += self.Used[k, t] >= self.Used[k, t + 1], f"C14_{k}_{t}"
        
        # C15: Détection changement de produit (généralisée avec position fictive t=0)
        # Pour t >= 2 : utilise Prod[k, t-1, p1]
        # Pour t = 1 : utilise Prod[k, 0, p1] = 1 si p1 == P_initial[k], 0 sinon
        for k in self.K:
            for t in self.T:
                for p1 in self.P:
                    for p2 in self.P:
                        if p1 != p2:
                            if t == 1:
                                # Position t=0 fictive : Prod[k,0,p1] = 1 ssi p1 == P_initial[k]
                                prod_prev = 1 if p1 == self.P_initial[k] else 0
                                self.model += self.Switch[k, t, p1, p2] >= prod_prev + self.Prod[k, t, p2] - 1, f"C15_{k}_{t}_{p1}_{p2}"
                            else:
                                self.model += self.Switch[k, t, p1, p2] >= self.Prod[k, t-1, p1] + self.Prod[k, t, p2] - 1, f"C15_{k}_{t}_{p1}_{p2}"
        
        # C16: Connectivité inter-produits (Anti-Téléportation)
        # Pour charger un produit p au dépôt d à la position t (après avoir utilisé p' à t-1),
        # le véhicule doit être ARRIVÉ au dépôt d avec le produit p'.
        # Inflow(d, p') >= Load(d, t, p) + Prod(t-1, p') - 1
        for d in self.D:
            for k in self.K:
                for t in self.T:
                    if t > 1:
                        for p in self.P:
                            for p_prime in self.P:
                                if p != p_prime:
                                    inflow_p_prime = pulp.lpSum(self.x[i, d, k, p_prime] for i in self.V if i != d)
                                    self.model += inflow_p_prime >= self.Load[d, k, t, p] + self.Prod[k, t-1, p_prime] - 1, f"C16_{d}_{k}_{t}_{p}_{p_prime}"
        
        print(f"Modèle construit: {len(self.model.variables())} variables, {len(self.model.constraints)} contraintes")
    
    def add_subtour_elimination(self) -> bool:
        """Détecte et élimine les sous-tournées"""
        cuts_added = False
        for k in self.K:
            for p in self.P:
                G = nx.DiGraph()
                for i in self.V:
                    for j in self.V:
                        if i != j and (i, j, k, p) in self.x:
                            val = pulp.value(self.x[i, j, k, p])
                            if val is not None and val > 0.5:
                                G.add_edge(i, j)
                
                if G.number_of_edges() == 0:
                    continue
                
                for comp in nx.weakly_connected_components(G):
                    if not any(node in self.D for node in comp) and len(comp) >= 2:
                        comp_list = list(comp)
                        self.model += (pulp.lpSum(self.x[i, j, k, p] for i in comp_list for j in comp_list
                                                  if i != j and (i, j, k, p) in self.x) <= len(comp) - 1,
                                       f"SEC_{k}_{p}_{hash(frozenset(comp))}")
                        cuts_added = True
                        print(f"  Coupe SEC ajoutée pour k={k}, p={p}: {comp}")
        return cuts_added
    
    def solve(self, time_limit: int = 3600, gap: float = 0.01) -> Dict:
        """Résout le modèle avec élimination itérative des sous-tournées"""
        if self.model is None:
            self.build_model()
        
        print(f"\nRésolution (time_limit={time_limit}s, gap={gap})...")
        solver = pulp.PULP_CBC_CMD(msg=1, timeLimit=time_limit, gapRel=gap)
        
        for iteration in range(1, 101):
            print(f"\n--- Itération {iteration} ---")
            status = self.model.solve(solver)
            
            if status != pulp.LpStatusOptimal:
                print(f"Statut: {pulp.LpStatus[status]}")
                return None
            
            print(f"Objectif courant: {pulp.value(self.model.objective):.2f}")
            
            if not self.add_subtour_elimination():
                print("Solution optimale trouvée!")
                break
        
        return self.extract_solution()
    
    def extract_solution(self) -> Dict:
        """Extrait la solution complète"""
        if self.model.status != pulp.LpStatusOptimal:
            return None
        
        solution = {
            'objective': pulp.value(self.model.objective),
            'status': 'optimal',
            'variables': {'x': {}, 'Deliv': {}, 'Load': {}, 'QLoad': {}, 
                          'Switch': {}, 'Start': {}, 'Fin': {}, 'Used': {}, 'Prod': {}},
            'routes': {},
            'summary': {'deliveries': {}, 'loads': {}, 'switches': []}
        }
        
        # Extraire les variables actives
        for key, var in self.x.items():
            val = pulp.value(var)
            if val and val > 0.5:
                solution['variables']['x'][str(key)] = 1
        
        for key, var in self.Deliv.items():
            val = pulp.value(var)
            if val and val > 0.01:
                solution['variables']['Deliv'][str(key)] = val
        
        for key, var in self.Load.items():
            val = pulp.value(var)
            if val and val > 0.5:
                solution['variables']['Load'][str(key)] = 1
        
        for key, var in self.QLoad.items():
            val = pulp.value(var)
            if val and val > 0.01:
                solution['variables']['QLoad'][str(key)] = val
        
        for key, var in self.Switch.items():
            val = pulp.value(var)
            if val and val > 0.5:
                solution['variables']['Switch'][str(key)] = 1
        
        for key, var in self.Start.items():
            val = pulp.value(var)
            if val and val > 0.5:
                solution['variables']['Start'][str(key)] = 1
        
        for key, var in self.Fin.items():
            val = pulp.value(var)
            if val and val > 0.5:
                solution['variables']['Fin'][str(key)] = 1
        
        for key, var in self.Used.items():
            val = pulp.value(var)
            if val and val > 0.5:
                solution['variables']['Used'][str(key)] = 1
        
        for key, var in self.Prod.items():
            val = pulp.value(var)
            if val and val > 0.5:
                solution['variables']['Prod'][str(key)] = 1
        
        # Routes lisibles
        for k in self.K:
            routes_k = []
            
            # 1. Start
            current_node = None
            g = self.g_k[k]
            for d in self.D:
                if pulp.value(self.Start[g, d, k]) and pulp.value(self.Start[g, d, k]) > 0.5:
                    routes_k.append({'type': 'start', 'from': g, 'to': d})
                    current_node = d
                    break
            
            if current_node:
                # 2. Products sequence based on Prod[k, t, p]
                for t in self.T:
                    # Find active product for this position
                    active_p = None
                    for p in self.P:
                        if (k, t, p) in self.Prod and pulp.value(self.Prod[k, t, p]) > 0.5:
                            active_p = p
                            break
                    
                    if active_p is not None:
                        # Get all arcs for this vehicle and product
                        raw_arcs = []
                        for i in self.V:
                            for j in self.V:
                                if i != j and (i, j, k, active_p) in self.x:
                                    val = pulp.value(self.x[i, j, k, active_p])
                                    if val and val > 0.5:
                                        raw_arcs.append([i, j])
                        
                        # Sort arcs to form a path starting at current_node
                        ordered_arcs = []
                        while raw_arcs:
                            # Find arc starting at current_node
                            found = False
                            for idx, arc in enumerate(raw_arcs):
                                if arc[0] == current_node:
                                    ordered_arcs.append(arc)
                                    current_node = arc[1]
                                    raw_arcs.pop(idx)
                                    found = True
                                    break
                            if not found:
                                # Stop if we can't find a connecting arc (maybe belongs to another tour)
                                break
                        
                        if ordered_arcs:
                            routes_k.append({'product': active_p, 'arcs': ordered_arcs})

                # 3. End
                for s in self.S:
                    for p in self.P:
                        if (s, g, k, p) in self.Fin and pulp.value(self.Fin[s, g, k, p]) and pulp.value(self.Fin[s, g, k, p]) > 0.5:
                            if s == current_node:
                                routes_k.append({'type': 'end', 'from': s, 'to': g, 'product': p})
            
            solution['routes'][k] = routes_k
        
        # Résumés
        for s in self.S:
            for p in self.P:
                for k in self.K:
                    val = pulp.value(self.Deliv[s, p, k])
                    if val and val > 0.01:
                        solution['summary']['deliveries'][f"{s}_{p}_{k}"] = val
        
        for d in self.D:
            for k in self.K:
                for t in self.T:
                    for p in self.P:
                        val = pulp.value(self.QLoad[d, k, t, p])
                        if val and val > 0.01:
                            solution['summary']['loads'][f"{d}_{k}_{t}_{p}"] = val
        
        for k in self.K:
            for t in self.T:
                for p1 in self.P:
                    for p2 in self.P:
                        if p1 != p2 and (k, t, p1, p2) in self.Switch:
                            val = pulp.value(self.Switch[k, t, p1, p2])
                            if val and val > 0.5:
                                solution['summary']['switches'].append({
                                    'vehicle': k, 'position': t, 'from_product': p1, 'to_product': p2
                                })
        
        return solution
    
    def export_solution(self, solution: Dict, filepath: str):
        """Exporte la solution en JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(solution, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Solution exportée: {filepath}")
    
    def print_solution(self, solution: Dict):
        """Affiche la solution"""
        if not solution:
            print("Pas de solution.")
            return
        
        print("\n" + "="*60)
        print("SOLUTION OPTIMALE")
        print("="*60)
        print(f"Coût total: {solution['objective']:.2f}")
        
        print("\n--- Routes ---")
        for k, routes in solution['routes'].items():
            print(f"\nVéhicule {k}:")
            for r in routes:
                if 'type' in r:
                    print(f"  {r['type'].upper()}: {r['from']} -> {r['to']}")
                else:
                    print(f"  Produit {r['product']}: {r['arcs']}")
        
        print("\n--- Livraisons ---")
        for key, qty in solution['summary']['deliveries'].items():
            s, p, k = key.split('_')
            print(f"  Station {s}, Produit {p}, Véhicule {k}: {qty:.1f}")
        
        print("\n--- Chargements ---")
        for key, qty in solution['summary']['loads'].items():
            d, k, t, p = key.split('_')
            print(f"  Dépôt {d}, Véhicule {k}, Position {t}, Produit {p}: {qty:.1f}")
        
        if solution['summary']['switches']:
            print("\n--- Changements de produit ---")
            for sw in solution['summary']['switches']:
                print(f"  Véhicule {sw['vehicle']}, Position {sw['position']}: "
                      f"Produit {sw['from_product']} -> {sw['to_product']}")


# =============================================================================
# MAIN
# =============================================================================

def main():
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
    
    # Construire le chemin complet vers l'instance
    instance_file = os.path.join(data_dir, instance_name)
    
    if not os.path.exists(instance_file):
        print(f"Erreur: Le fichier '{instance_file}' n'existe pas.")
        return
    
    # Nom du fichier de sortie dans solutions/
    base_name = os.path.splitext(instance_name)[0]
    output_file = os.path.join(solutions_dir, f"{base_name}_solution.json")
    
    print(f"\nLecture de l'instance: {instance_file}")
    instance = parse_instance(instance_file)
    
    print(f"\nInstance: {instance.num_vehicles} véhicules, {instance.num_garages} garages, "
          f"{instance.num_products} produits, {instance.num_stations} stations, {instance.num_depots} dépôts")
    
    solver = MPVRPSolver(instance, max_positions=5)
    solver.build_model()
    solution = solver.solve(time_limit=300)
    
    if solution:
        solver.print_solution(solution)
        solver.export_solution(solution, output_file)
        print(f"\nSolution exportée vers: {output_file}")


if __name__ == "__main__":
    main()
