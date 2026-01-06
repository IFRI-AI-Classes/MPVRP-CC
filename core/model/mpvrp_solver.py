"""
MPVRP-CRP Solver (Multi-Product Vehicle Routing Problem with Compartments)
==========================================================================

Ce module implémente un solveur pour le problème de tournée de véhicules multi-produits
avec compartiments (MPVRP-CRP) en utilisant la programmation linéaire en nombres entiers (PLNE).

Le modèle mathématique est basé sur une formulation de type flot avec des variables
décrivant les trajets, les chargements, les livraisons et les changements de produits.

Dépendances:
    - pulp: Pour la modélisation et la résolution PLNE.
    - networkx: Pour des opérations de graphe (optionnel).
    - dataclasses: Pour la structure des données.

"""

import pulp
import math
import networkx as nx
from typing import Dict, List, Tuple
from dataclasses import dataclass
import platform
import time

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

def parse_instance(filepath: str) -> Instance:
    """Parse un fichier d'instance au format .dat"""
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    line_idx = 1
    
    parts = lines[line_idx].split()
    num_products = int(parts[0])   # Produits en premier
    num_depots = int(parts[1])     # Dépôts en deuxième
    num_garages = int(parts[2])    # Garages en troisième
    num_stations = int(parts[3])   # Stations en quatrième
    num_vehicles = int(parts[4])   # Véhicules en dernier
    line_idx += 1
    
    print(f"  Dimensions: {num_vehicles} véhicules, {num_depots} dépôts, "
          f"{num_products} produits, {num_stations} stations, {num_garages} garages")
    
    # Matrice des coûts de changement de produit (NbProduits x NbProduits)
    change_costs = {}
    for p1 in range(num_products):
        costs = list(map(float, lines[line_idx].split()))
        for p2, cost in enumerate(costs):
            change_costs[(p1, p2)] = cost
        line_idx += 1
    
    # Bloc 3 : Véhicules
    vehicles = []
    for _ in range(num_vehicles):
        parts = lines[line_idx].split()
        vehicles.append(Vehicle(
            id=int(parts[0]), 
            capacity=float(parts[1]),
            garage_id=int(parts[2]), 
            initial_product=int(parts[3])
        ))
        line_idx += 1
    
    # Bloc 4 : Dépôts
    depots = []
    for _ in range(num_depots):
        parts = lines[line_idx].split()
        stocks = {p: float(parts[3 + p]) for p in range(num_products)}
        depots.append(Depot(
            id=int(parts[0]), 
            x=float(parts[1]), 
            y=float(parts[2]), 
            stocks=stocks
        ))
        line_idx += 1
    
    # Bloc 5 : Garages
    garages = []
    for _ in range(num_garages):
        parts = lines[line_idx].split()
        garages.append(Garage(
            id=int(parts[0]), 
            x=float(parts[1]), 
            y=float(parts[2])
        ))
        line_idx += 1
    
    # Bloc 6 : Stations
    stations = []
    for _ in range(num_stations):
        parts = lines[line_idx].split()
        demands = {p: float(parts[3 + p]) for p in range(num_products)}
        stations.append(Station(
            id=int(parts[0]), 
            x=float(parts[1]), 
            y=float(parts[2]), 
            demands=demands
        ))
        line_idx += 1
    
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

class MPVRPSolver:
    """
    Solveur pour le problème MPVRP-CRP utilisant la bibliothèque PuLP.
    
    Cette classe encapsule la logique de construction du modèle mathématique,
    la résolution via un solveur externe (CBC, Gurobi, CPLEX, etc.), et
    l'exportation des résultats.
    
    Attributes:
        instance (Instance): L'instance du problème à résoudre.
        distances (Dict): Matrice des distances pré-calculées entre les nœuds.
        model (pulp.LpProblem): Le modèle PLNE PuLP.
        status (int): Le statut de la résolution (Optimal, Infeasible, etc.).
    """
    
    def __init__(self, instance: Instance, max_positions: int = None):
        """
        Initialise le solveur avec une instance donnée.
        
        Args:
            instance (Instance): L'objet contenant toutes les données du problème (véhicules, stations, etc.).
            max_positions (int, optional): Nombre maximum de positions (étapes) dans une tournée.
                                           Si None, une valeur par défaut est calculée.
        """
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
        """
        Construit le modèle de Programmation Linéaire en Nombres Entiers (PLNE) complet.
        
        Cette méthode définit :
        1. Les variables de décision (x, Load, Deliv, QLoad, Switch, Start, Fin, Used, Prod).
        2. La fonction objectif (minimisation des coûts de routage, de changement de produit, etc.).
        3. L'ensemble des contraintes (demande, capacité, flot, conservation, etc.).
        
        Le modèle est stocké dans l'attribut self.model.
        """
        print("Construction du modèle...")
        self.model = pulp.LpProblem("MPVRP_CC", pulp.LpMinimize)
        
        # === VARIABLES ===
        self.x = {(i, j, k, p, t): pulp.LpVariable(f"x_{i}_{j}_{k}_{p}_{t}", cat=pulp.LpBinary)
                  for i in self.V for j in self.V if i != j for k in self.K for p in self.P for t in self.T}
        
        self.Load = {(d, k, t, p): pulp.LpVariable(f"Load_{d}_{k}_{t}_{p}", cat=pulp.LpBinary)
                     for d in self.D for k in self.K for t in self.T for p in self.P}
        
        self.Deliv = {(s, p, k, t): pulp.LpVariable(f"Deliv_{s}_{p}_{k}_{t}", lowBound=0)
                      for s in self.S for p in self.P for k in self.K for t in self.T}
        
        self.QLoad = {(d, k, t, p): pulp.LpVariable(f"QLoad_{d}_{k}_{t}_{p}", lowBound=0)
                      for d in self.D for k in self.K for t in self.T for p in self.P}
        
        self.q = {(i, k, p, t): pulp.LpVariable(f"q_{i}_{k}_{p}_{t}", lowBound=0)
                  for i in self.V for k in self.K for p in self.P for t in self.T}
        
        self.Switch = {(k, t, p1, p2): pulp.LpVariable(f"Switch_{k}_{t}_{p1}_{p2}", cat=pulp.LpBinary)
                       for k in self.K for t in self.T for p1 in self.P for p2 in self.P if p1 != p2}
        
        self.Start = {(self.g_k[k], d, k): pulp.LpVariable(f"Start_{self.g_k[k]}_{d}_{k}", cat=pulp.LpBinary)
                      for k in self.K for d in self.D}
        
        self.Fin = {(s, self.g_k[k], k, p, t): pulp.LpVariable(f"Fin_{s}_{self.g_k[k]}_{k}_{p}_{t}", cat=pulp.LpBinary)
                    for k in self.K for s in self.S for p in self.P for t in self.T}
        
        self.Used = {(k, t): pulp.LpVariable(f"Used_{k}_{t}", cat=pulp.LpBinary)
                     for k in self.K for t in self.T}
        
        self.Prod = {(k, t, p): pulp.LpVariable(f"Prod_{k}_{t}_{p}", cat=pulp.LpBinary)
                     for k in self.K for t in self.T for p in self.P}

        # Segment terminé sur un dépôt (évite les dépôts de passage)
        self.EndDepot = {(d, k, p, t): pulp.LpVariable(f"EndDepot_{d}_{k}_{p}_{t}", cat=pulp.LpBinary)
                 for d in self.D for k in self.K for p in self.P for t in self.T}
        
        # === FONCTION OBJECTIF ===
        routing_cost = pulp.lpSum(self._get_distance(i, j) * self.x[i, j, k, p, t]
                                  for i in self.V for j in self.V if i != j for k in self.K for p in self.P for t in self.T)
        switch_cost = pulp.lpSum(self.change_cost.get((p1, p2), 0) * self.Switch[k, t, p1, p2]
                                 for k in self.K for t in self.T for p1 in self.P for p2 in self.P if p1 != p2)
        start_cost = pulp.lpSum(self._get_distance(self.g_k[k], d) * self.Start[self.g_k[k], d, k]
                                for k in self.K for d in self.D)
        end_cost = pulp.lpSum(self._get_distance(s, self.g_k[k]) * self.Fin[s, self.g_k[k], k, p, t]
                              for k in self.K for s in self.S for p in self.P for t in self.T)

        # Petit terme de bris de symétrie : minimise le nombre de positions utilisées
        used_penalty = 1e-4 * pulp.lpSum(self.Used[k, t] for k in self.K for t in self.T)
        
        self.model += routing_cost + switch_cost + start_cost + end_cost + used_penalty, "Total_Cost"
        
        # === CONTRAINTES (formulation par segments, issue de solver3) ===

        # 1) Satisfaction de la demande
        for s in self.S:
            for p in self.P:
                self.model += (
                    pulp.lpSum(self.Deliv[s, p, k, t] for k in self.K for t in self.T) == self.demand.get((s, p), 0)
                ), f"Demand_{s}_{p}"

        # 2) Interdire les visites (station,produit) sans demande
        for s in self.S:
            for p in self.P:
                if self.demand.get((s, p), 0) == 0:
                    for k in self.K:
                        for t in self.T:
                            self.model += (
                                pulp.lpSum(self.x[i, s, k, p, t] for i in self.V if i != s) == 0
                            ), f"NoVisit_{s}_{p}_{k}_{t}"

        # 3) Interdire l'utilisation de produits dont la demande totale est nulle
        for p in self.P:
            total_demand_p = sum(self.demand.get((s, p), 0) for s in self.S)
            if total_demand_p == 0:
                for k in self.K:
                    for t in self.T:
                        self.model += self.Prod[k, t, p] == 0, f"NoZeroDemandProd_{k}_{t}_{p}"

        # 4) Début de tournée
        for k in self.K:
            g = self.g_k[k]
            self.model += pulp.lpSum(self.Start[g, d, k] for d in self.D) == self.Used[k, 1], f"Start_{k}"

        # 5) Lien Start et chargement initial (t=1)
        for k in self.K:
            g = self.g_k[k]
            for d in self.D:
                self.model += self.Start[g, d, k] == pulp.lpSum(self.Load[d, k, 1, p] for p in self.P), f"StartLoad_{k}_{d}"

        # 6) Fin de tournée (un seul retour garage si véhicule utilisé)
        for k in self.K:
            g = self.g_k[k]
            self.model += (
                pulp.lpSum(self.Fin[s, g, k, p, t] for s in self.S for p in self.P for t in self.T) == self.Used[k, 1]
            ), f"End_{k}"

        # 7) Ordonnancement des segments (pas de trous)
        for k in self.K:
            for t in self.T[:-1]:
                self.model += self.Used[k, t] >= self.Used[k, t + 1], f"UsedOrder_{k}_{t}"

        # 8) Un seul (dépôt,produit) chargé par segment utilisé
        for k in self.K:
            for t in self.T:
                self.model += (
                    pulp.lpSum(self.Load[d, k, t, p] for d in self.D for p in self.P) == self.Used[k, t]
                ), f"OneLoad_{k}_{t}"

        # 9) Produit actif identifié par le chargement
        for k in self.K:
            for t in self.T:
                for p in self.P:
                    self.model += self.Prod[k, t, p] == pulp.lpSum(self.Load[d, k, t, p] for d in self.D), f"ProdFromLoad_{k}_{t}_{p}"

        # 10) Capacité du véhicule par segment
        for k in self.K:
            for t in self.T:
                self.model += (
                    pulp.lpSum(self.QLoad[d, k, t, p] for d in self.D for p in self.P) <= self.C[k] * self.Used[k, t]
                ), f"Cap_{k}_{t}"

        # 11) Stock des dépôts
        for d in self.D:
            for p in self.P:
                self.model += (
                    pulp.lpSum(self.QLoad[d, k, t, p] for k in self.K for t in self.T) <= self.stock.get((d, p), 0)
                ), f"Stock_{d}_{p}"

        # 12) Lien QLoad et Load + chargement minimal (epsilon=1)
        eps_load = 1.0
        for d in self.D:
            for k in self.K:
                for t in self.T:
                    for p in self.P:
                        self.model += self.QLoad[d, k, t, p] <= self.M * self.Load[d, k, t, p], f"QLoadAct_{d}_{k}_{t}_{p}"
                        self.model += self.QLoad[d, k, t, p] >= eps_load * self.Load[d, k, t, p], f"QLoadMin_{d}_{k}_{t}_{p}"

        # 13) Conservation (segment pur): chargé = livré (par produit, par segment)
        for k in self.K:
            for t in self.T:
                for p in self.P:
                    self.model += (
                        pulp.lpSum(self.Deliv[s, p, k, t] for s in self.S) == pulp.lpSum(self.QLoad[d, k, t, p] for d in self.D)
                    ), f"LoadEqualsDeliv_{k}_{t}_{p}"

        # 14) Lien livraison et visite
        for s in self.S:
            for k in self.K:
                for p in self.P:
                    for t in self.T:
                        inflow = pulp.lpSum(self.x[i, s, k, p, t] for i in self.V if i != s)
                        self.model += self.Deliv[s, p, k, t] <= self.M * inflow, f"DelivIfVisit_{s}_{k}_{p}_{t}"

        # 15) Visiter une station implique livrer (>0) sur le produit du segment
        positive_demands = [d for d in self.demand.values() if d > 0]
        eps_deliv = min(1.0, min(positive_demands)) if positive_demands else 1.0
        for s in self.S:
            for k in self.K:
                for p in self.P:
                    if self.demand.get((s, p), 0) > 0:
                        for t in self.T:
                            inflow = pulp.lpSum(self.x[i, s, k, p, t] for i in self.V if i != s)
                            fin_term = self.Fin[s, self.g_k[k], k, p, t]
                            self.model += (
                                self.Deliv[s, p, k, t] >= eps_deliv * (inflow + fin_term)
                            ), f"VisitImpliesDeliv_{s}_{k}_{p}_{t}"

        # 16) Conservation du flot aux stations (par produit, par segment)
        for s in self.S:
            for k in self.K:
                for p in self.P:
                    for t in self.T:
                        inflow = pulp.lpSum(self.x[i, s, k, p, t] for i in self.V if i != s)
                        outflow = pulp.lpSum(self.x[s, j, k, p, t] for j in self.V if j != s)
                        self.model += inflow == outflow + self.Fin[s, self.g_k[k], k, p, t], f"FlowS_{s}_{k}_{p}_{t}"

        # 17) Dépôts: pas de dépôt de passage (chaque visite de dépôt coupe le segment)
        # - Départ: un segment part exactement du dépôt chargé
        # - Arrivée: si un segment arrive à un dépôt, il se termine sur ce dépôt
        for d in self.D:
            for k in self.K:
                for p in self.P:
                    for t in self.T:
                        inflow = pulp.lpSum(self.x[i, d, k, p, t] for i in self.V if i != d)
                        outflow = pulp.lpSum(self.x[d, j, k, p, t] for j in self.V if j != d)
                        self.model += outflow == self.Load[d, k, t, p], f"DepotDepart_{d}_{k}_{p}_{t}"
                        self.model += inflow == self.EndDepot[d, k, p, t], f"DepotArriveEnd_{d}_{k}_{p}_{t}"

        # 18) Un segment utilisé doit se terminer exactement une fois (dépôt ou station->garage)
        for k in self.K:
            for t in self.T:
                for p in self.P:
                    self.model += (
                        pulp.lpSum(self.EndDepot[d, k, p, t] for d in self.D)
                        + pulp.lpSum(self.Fin[s, self.g_k[k], k, p, t] for s in self.S)
                        == self.Prod[k, t, p]
                    ), f"OneEnd_{k}_{t}_{p}"

        # 19) Continuité des segments: si on termine sur un dépôt à t, on charge sur ce même dépôt à t+1
        for k in self.K:
            for t in self.T[:-1]:
                self.model += (
                    self.Used[k, t + 1] == pulp.lpSum(self.EndDepot[d, k, p, t] for d in self.D for p in self.P)
                ), f"NextUsed_{k}_{t}"

                for d in self.D:
                    self.model += (
                        pulp.lpSum(self.Load[d, k, t + 1, p] for p in self.P)
                        == pulp.lpSum(self.EndDepot[d, k, p, t] for p in self.P)
                    ), f"NextDepot_{k}_{t}_{d}"

        # 20) Lier arcs et produit actif (évite arcs sur p inactif)
        num_arcs = len(self.V) * (len(self.V) - 1)
        for k in self.K:
            for t in self.T:
                for p in self.P:
                    self.model += (
                        pulp.lpSum(self.x[i, j, k, p, t] for i in self.V for j in self.V if i != j) <= num_arcs * self.Prod[k, t, p]
                    ), f"XProd_{k}_{t}_{p}"

        # Fin uniquement si produit actif
        for k in self.K:
            g = self.g_k[k]
            for t in self.T:
                for p in self.P:
                    for s in self.S:
                        self.model += self.Fin[s, g, k, p, t] <= self.Prod[k, t, p], f"FinProd_{s}_{k}_{t}_{p}"

        # Forcer un minimum d'arcs si le segment est utilisé
        for k in self.K:
            for t in self.T:
                self.model += (
                    self.Used[k, t] <= pulp.lpSum(self.x[i, j, k, p, t] for i in self.V for j in self.V if i != j for p in self.P)
                ), f"UsedArcs_{k}_{t}"

        # 21) Détection changement de produit (entre segments)
        for k in self.K:
            for t in self.T:
                for p1 in self.P:
                    for p2 in self.P:
                        if p1 == p2:
                            continue
                        if t == 1:
                            prod_prev = 1 if p1 == self.P_initial[k] else 0
                            self.model += (
                                self.Switch[k, t, p1, p2] >= prod_prev + self.Prod[k, t, p2] - 1
                            ), f"Switch_{k}_{t}_{p1}_{p2}"
                        else:
                            self.model += (
                                self.Switch[k, t, p1, p2] >= self.Prod[k, t-1, p1] + self.Prod[k, t, p2] - 1
                            ), f"Switch_{k}_{t}_{p1}_{p2}"

        # 22) MTZ / charge restante: initialisation au dépôt
        for d in self.D:
            for k in self.K:
                for t in self.T:
                    for p in self.P:
                        self.model += self.q[d, k, p, t] == self.QLoad[d, k, t, p], f"MTZInit_{d}_{k}_{t}_{p}"

        # 23) MTZ / charge restante: décroissance le long des arcs
        for i in self.V:
            for j in self.S:
                if i == j:
                    continue
                for k in self.K:
                    for t in self.T:
                        for p in self.P:
                            self.model += (
                                self.q[j, k, p, t]
                                <= self.q[i, k, p, t] - self.Deliv[j, p, k, t] + self.M * (1 - self.x[i, j, k, p, t])
                            ), f"MTZDec_{i}_{j}_{k}_{t}_{p}"

        # 24) MTZ / capacité
        for i in self.V:
            for k in self.K:
                for t in self.T:
                    for p in self.P:
                        outflow = pulp.lpSum(self.x[i, j, k, p, t] for j in self.V if j != i)
                        self.model += self.q[i, k, p, t] <= self.C[k] * outflow, f"MTZCap_{i}_{k}_{t}_{p}"

        print(f"Modèle construit: {len(self.model.variables())} variables, {len(self.model.constraints)} contraintes")
    
    def solve(self, time_limit: int = 3600, gap: float = 0.01) -> Dict:
        """
        Résout le modèle directement avec les contraintes MTZ intégrées pour éviter les sous-tournées.
        
        Args:
            time_limit (int): Temps limite de résolution en secondes (défaut: 3600).
            gap (float): Écart d'optimalité relatif accepté (défaut: 1%).
            
        Returns:
            Dict: Dictionnaire contenant la solution complète ou None si échec.
        """
        if self.model is None:
            self.build_model()
        
        print(f"\nRésolution (time_limit={time_limit}s, gap={gap})...")
        solver = pulp.PULP_CBC_CMD(msg=1, timeLimit=time_limit, gapRel=gap)
        
        start_time = time.time()
        status = self.model.solve(solver)
        
        if status != pulp.LpStatusOptimal:
            print(f"Statut: {pulp.LpStatus[status]}")
            return None
        
        solve_time = time.time() - start_time
        print(f"Solution optimale trouvée en {solve_time:.3f}s!")
        
        return self.extract_solution(solve_time)
    
    def extract_solution(self, solve_time: float = 0.0) -> Dict:
        """
        Extrait la solution complète à partir des variables du modèle résolu.
        
        Args:
            solve_time (float): Temps de calcul en secondes.
            
        Returns:
            Dict: Structure de données contenant :
                - objective: Valeur de la fonction objectif.
                - solve_time: Temps de résolution.
                - status: Statut de la solution.
                - routes: Dictionnaire des routes par véhicule.
                - summary: Résumé des livraisons, chargements et changements.
                - variables: Variables actives du modèle (optionnel).
        """
        if self.model.status != pulp.LpStatusOptimal:
            return None
        
        solution = {
            'objective': pulp.value(self.model.objective),
            'solve_time': solve_time,
            'status': 'optimal',
            'routes': {},
            'summary': {
                'num_vehicles_used': 0,
                'num_switches': 0,
                'total_switch_cost': 0.0,
                'total_distance': 0.0,
                'deliveries': {},
                'loads': {},
                'switches': []
            }
        }
        
        # Construire les routes pour chaque véhicule
        for k in self.K:
            route_data = self._build_vehicle_route(k)
            if route_data['is_used']:
                solution['routes'][k] = route_data
        
        # Calculer les statistiques globales
        solution['summary']['num_vehicles_used'] = len(solution['routes'])
        
        for k, route in solution['routes'].items():
            # Compter les switches
            for sw in route.get('switches', []):
                solution['summary']['num_switches'] += 1
                solution['summary']['total_switch_cost'] += sw['cost']
                solution['summary']['switches'].append({
                    'vehicle': k,
                    'position': sw['position'],
                    'from_product': sw['from'],
                    'to_product': sw['to'],
                    'cost': sw['cost']
                })
            
            # Enregistrer les livraisons
            for station, products in route.get('deliveries', {}).items():
                for product, qty in products.items():
                    key = f"{station}_{product}_{k}"
                    solution['summary']['deliveries'][key] = qty
            
            # Enregistrer les chargements
            for depot, load_list in route.get('loads', {}).items():
                for load_info in load_list:
                    key = f"{depot}_{k}_{load_info['position']}_{load_info['product']}"
                    solution['summary']['loads'][key] = load_info['quantity']
        
        # Remaining capacity per vehicle
        solution['summary']['remaining_capacity'] = {}
        for k, route in solution['routes'].items():
            total_loaded = sum(
                load_info['quantity']
                for load_list in route.get('loads', {}).values()
                for load_info in load_list
            )
            solution['summary']['remaining_capacity'][k] = self.C[k] - total_loaded
        
        solution['summary']['total_distance'] = solution['objective'] - solution['summary']['total_switch_cost']
        
        return solution
    
    def get_absolute_node_id(self, node_type: str, relative_id: int) -> int:
        """Retourne l'ID numérique tel qu'il apparaît dans l'instance (sans accumulation).

        Historique: une ancienne convention utilisait des IDs "absolus" via offsets (garages puis dépôts puis stations).
        Cette implémentation n'utilise plus d'accumulation: l'ID numérique retourné est l'ID *relatif* de l'entité
        (même plage que dans l'instance).
        """
        return int(relative_id)

    def print_solution(self, solution: Dict):
        """Affiche la solution dans le terminal"""
        if not solution:
            print("Pas de solution.")
            return
        
        print("\n" + "="*60)
        print("SOLUTION OPTIMALE")
        print("="*60)
        print(f"Coût total: {solution['objective']:.2f}")
        print(f"Temps de résolution: {solution.get('solve_time', 0):.3f}s")
        
        print("\n--- Routes des véhicules ---")
        for k, route in solution['routes'].items():
            print(f"\nVéhicule {k}:")
            if route.get('is_used', False):
                path_str = " -> ".join(route['path'])
                print(f"  Chemin: {path_str}")
                
                if route.get('loads'):
                    print("  Chargements:")
                    for depot, loads_list in route['loads'].items():
                        for load_info in loads_list:
                            print(f"    {depot}: {load_info['quantity']:.1f} de produit {load_info['product']}")
                
                if route.get('deliveries'):
                    print("  Livraisons:")
                    for station, products in route['deliveries'].items():
                        for product, qty in products.items():
                            print(f"    {station}: {qty:.1f} de produit {product}")
                
                if route.get('switches'):
                    print("  Changements de produit:")
                    for sw in route['switches']:
                        print(f"    Position {sw['position']}: {sw['from']} -> {sw['to']} (coût: {sw['cost']:.1f})")
            else:
                print("  Non utilisé")
        
        # Statistiques globales - utiliser le résumé pré-calculé
        summary = solution.get('summary', {})
        total_vehicles = summary.get('num_vehicles_used', len(solution['routes']))
        total_switches = summary.get('num_switches', 0)
        total_switch_cost = summary.get('total_switch_cost', 0.0)
        total_distance = summary.get('total_distance', solution['objective'])
        
        print(f"\n--- Statistiques ---")
        print(f"Véhicules utilisés: {total_vehicles}")
        print(f"Changements de produit: {total_switches}")
        print(f"Coût des changements: {total_switch_cost:.2f}")
        print(f"Distance totale: {total_distance:.2f}")

    def export_solution_dat(self, solution: Dict, filepath: str):
        """
        Exporte la solution au format .dat standardisé à partir du dictionnaire solution.
        
        Le format de sortie est :
        - Pour chaque véhicule :
            Ligne 1: ID: Nœud [Charge] - Nœud (Livraison) - ...
            Ligne 2: ID: Produit(Coût) - Produit(Coût) - ...
        - Métriques globales (nombre de véhicules, switchs, coûts, temps, etc.)
        
        Args:
            solution (Dict): La solution à exporter (retournée par extract_solution).
            filepath (str): Chemin du fichier de sortie.
        """
        if not solution or 'routes' not in solution:
            print("Pas de solution à exporter.")
            return

        with open(filepath, 'w', encoding='utf-8') as f:
            # Écrire les routes de chaque véhicule (ID: <route> / ID: <products>)
            for k in sorted(solution['routes'].keys()):
                route = solution['routes'][k]

                # Format ligne 1: "ID: route"
                path_str = self._format_route_path(route)
                f.write(f"{k}: {path_str}\n")

                # Format ligne 2: "ID: produit(coût) - ..."
                products_str = self._format_products_costs(route, k)
                f.write(f"{k}: {products_str}\n")

                # Séparateur
                f.write("\n")

            # Métriques finales - utiliser le résumé pré-calculé
            summary = solution.get('summary', {})
            num_vehicles_used = summary.get('num_vehicles_used', len(solution['routes']))
            num_switches = summary.get('num_switches', 0)
            total_switch_cost = summary.get('total_switch_cost', 0.0)
            total_distance = summary.get('total_distance', solution['objective'])

            f.write(f"{num_vehicles_used}\n")
            f.write(f"{num_switches}\n")
            f.write(f"{total_switch_cost:.1f}\n")
            f.write(f"{total_distance:.2f}\n")

            # Informations système
            f.write(f"{platform.processor()}\n")
            f.write(f"{solution.get('solve_time', 0):.3f}\n")
        
        print(f"\nSolution exportée: {filepath}")

    def _build_vehicle_route(self, k: int) -> Dict:
        route = {
            'is_used': False,
            'path': [],
            'loads': {},
            'deliveries': {},
            'products': [],
            'switches': [],
            't_to_path_index': {}
        }
        
        if not pulp.value(self.Used[k, 1]) or pulp.value(self.Used[k, 1]) < 0.5:
            return route
        
        route['is_used'] = True
        g = self.g_k[k]
        
        # 1. Trouver le Start
        start_depot = None
        for d in self.D:
            if pulp.value(self.Start[g, d, k]) and pulp.value(self.Start[g, d, k]) > 0.5:
                start_depot = d
                break
        
        if not start_depot:
            return route
        
        # 2. Construire la séquence de positions
        positions_info = {}
        for t in self.T:
            for p in self.P:
                if (k, t, p) in self.Prod and pulp.value(self.Prod[k, t, p]) and pulp.value(self.Prod[k, t, p]) > 0.5:
                    for d in self.D:
                        if (d, k, t, p) in self.QLoad:
                            qty = pulp.value(self.QLoad[d, k, t, p])
                            if qty and qty > 0.01:
                                positions_info[t] = {'depot': d, 'product': p, 'quantity': qty}
                                break
                    break
        
        # 3. Extraire les livraisons
        for s in self.S:
            for p in self.P:
                total_qty = sum(pulp.value(self.Deliv[s, p, k, t]) for t in self.T if (s, p, k, t) in self.Deliv)
                if total_qty and total_qty > 0.01:
                    if s not in route['deliveries']:
                        route['deliveries'][s] = {}
                    route['deliveries'][s][p] = total_qty
        
        # 4. Extraire les switches
        route['switches'] = []
        for t in self.T:
            for p1 in self.P:
                for p2 in self.P:
                    if p1 != p2 and (k, t, p1, p2) in self.Switch:
                        if pulp.value(self.Switch[k, t, p1, p2]) and pulp.value(self.Switch[k, t, p1, p2]) > 0.5:
                            route['switches'].append({
                                'position': t,
                                'from': p1,
                                'to': p2,
                                'cost': self.change_cost.get((p1, p2), 0)
                            })
        
        # 5. Construire le chemin
        route['path'].append(g)
        route['path'].append(start_depot)
        
        # Pour chaque position t, suivre les arcs
        sorted_positions = sorted(positions_info.keys())
        current_product = self.P_initial[k]
        
        for t in sorted_positions:
            pos_info = positions_info[t]
            depot = pos_info['depot']
            product = pos_info['product']
            quantity = pos_info['quantity']
            
            # Enregistrer le chargement
            if depot not in route['loads']:
                route['loads'][depot] = []
            route['loads'][depot].append({
                'product': product,
                'quantity': quantity,
                'position': t
            })
            
            # Mapper t à l'index dans le chemin
            route['t_to_path_index'][t] = len(route['path']) - 1
            
            # Suivre les arcs pour ce produit et cette position
            arcs_for_product_t = []
            for i in self.V:
                for j in self.V:
                    if i != j and (i, j, k, product, t) in self.x:
                        if pulp.value(self.x[i, j, k, product, t]) and pulp.value(self.x[i, j, k, product, t]) > 0.5:
                            arcs_for_product_t.append((i, j))
            
            # Parcourir les arcs depuis le dépôt actuel
            current = depot
            visited = set()
            while arcs_for_product_t:
                found = False
                for arc in arcs_for_product_t:
                    if arc[0] == current and arc not in visited:
                        if arc[1] not in route['path']:
                            route['path'].append(arc[1])
                        current = arc[1]
                        visited.add(arc)
                        arcs_for_product_t.remove(arc)
                        found = True
                        break
                if not found:
                    break
            
            route['products'].append(product)
        
        # 7. Gérer la fin de tournée
        for s in self.S:
            for p in self.P:
                for t in self.T:
                    if (s, self.g_k[k], k, p, t) in self.Fin and pulp.value(self.Fin[s, self.g_k[k], k, p, t]) > 0.5:
                        # Suivre les arcs pour ce t et p depuis le dernier current jusqu'à s
                        arcs_fin = []
                        for i in self.V:
                            for j in self.V:
                                if i != j and (i, j, k, p, t) in self.x:
                                    if pulp.value(self.x[i, j, k, p, t]) > 0.5:
                                        arcs_fin.append((i, j))
                        
                        # Trier les arcs pour former un chemin depuis current
                        current = route['path'][-1] if route['path'] else self.g_k[k]
                        visited = set()
                        while arcs_fin:
                            found = False
                            for arc in arcs_fin:
                                if arc[0] == current and arc not in visited:
                                    if arc[1] not in route['path']:
                                        route['path'].append(arc[1])
                                    current = arc[1]
                                    visited.add(arc)
                                    arcs_fin.remove(arc)
                                    found = True
                                    break
                            if not found:
                                break
                        
                        # Ajouter la fin au garage
                        if s not in route['path']:
                            route['path'].append(s)
                        route['path'].append(self.g_k[k])
                        break
        
        return route
    
    def _format_route_path(self, route: Dict) -> str:
        """Formate le chemin avec quantités chargées [] et livrées ().

        Convention d'export (sans accumulation, sans préfixe):
        - Garage: "<id>"
        - Dépôt:  "<id> [qte]"
        - Station:"<id> (qte)"
        """
        path_parts = []
        path = route['path']
        loads = route.get('loads', {})
        deliveries = route.get('deliveries', {})
        
        # Calculer les totaux par nœud
        depot_totals = {}
        for depot, load_list in loads.items():
            depot_totals[depot] = sum(load['quantity'] for load in load_list)
        
        station_totals = {}
        for station, products in deliveries.items():
            station_totals[station] = sum(products.values())
        
        for node in path:
            # Export sans préfixe: on écrit seulement l'ID numérique de l'entité.
            node_id = int(str(node)[1:]) if isinstance(node, str) and len(node) > 1 else node

            if isinstance(node, str) and node.startswith('D') and node in depot_totals:
                total = depot_totals[node]
                path_parts.append(f"{node_id} [{int(round(total))}]")
            elif isinstance(node, str) and node.startswith('S') and node in station_totals:
                total = station_totals[node]
                path_parts.append(f"{node_id} ({int(round(total))})")
            else:
                path_parts.append(str(node_id))
        
        return " - ".join(path_parts)
    
    def _format_products_costs(self, route: Dict, vehicle_id: int) -> str:
        """Formate la ligne produit(coût_cumulé)"""
        if not route.get('is_used', False):
            return ""
        
        path = route['path']
        switches = route.get('switches', [])
        t_map = route.get('t_to_path_index', {})
        
        # Organiser les switches par index dans le chemin
        switch_by_path_index = {}
        for sw in switches:
            t = sw['position']
            if t in t_map:
                path_idx = t_map[t]
                switch_by_path_index[path_idx] = sw
        
        # Construire la séquence
        current_product = self.P_initial[vehicle_id]
        cumulative_cost = 0.0
        products_parts = []
        
        for i in range(len(path)):
            # Appliquer le changement avant le nœud courant
            if i in switch_by_path_index:
                sw = switch_by_path_index[i]
                cumulative_cost += sw['cost']
                current_product = sw['to']
            
            products_parts.append(f"{current_product}({cumulative_cost:.1f})")
        
        return " - ".join(products_parts)
    
def main():
    import os
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    data_dir = os.path.join(project_root, "data", "instances")
    solutions_dir = os.path.join(project_root, "data", "solutions")
    
    if not os.path.exists(data_dir):
        print(f"Erreur: Le dossier '{data_dir}' n'existe pas.")
        return
    
    available_files = [f for f in os.listdir(data_dir) if f.endswith('.dat')]
    if available_files:
        print("Fichiers d'instance disponibles dans data/:")
        for f in available_files:
            print(f"  - {f}")
        print()
    
    instance_name = input("Entrez le nom du fichier instance (ex: MPVRP_3_s3_d1_p2.dat): ").strip()
    instance_file = os.path.join(data_dir, instance_name)
    
    if not os.path.exists(instance_file):
        print(f"Erreur: Le fichier '{instance_file}' n'existe pas.")
        return
    
    # Nom du fichier de sortie selon la nomenclature
    base_name = os.path.splitext(instance_name)[0]
    output_file = os.path.join(solutions_dir, f"Sol_{base_name}.dat")
    
    print(f"\nLecture de l'instance: {instance_file}")
    instance = parse_instance(instance_file)
    
    print(f"\nInstance: {instance.num_vehicles} véhicules, {instance.num_garages} garages, "
          f"{instance.num_products} produits, {instance.num_stations} stations, {instance.num_depots} dépôts")
    
    solver = MPVRPSolver(instance, max_positions=5)
    solver.build_model()
    
    import time
    start_time = time.time()
    solution = solver.solve(time_limit=300)
    
    if solution:
        solution['solve_time'] = time.time() - start_time
        solver.print_solution(solution)
        solver.export_solution_dat(solution, output_file)
        print(f"\nSolution exportée vers: {output_file}")

if __name__ == "__main__":
    main()