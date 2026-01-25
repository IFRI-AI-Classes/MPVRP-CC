import time

import pulp

from .schemas import Instance

SOLVER_NAME = "PULP_CBC_CMD"
TIME_LIMIT = 100
EXPORT_TOURS = True


class Solver:
    def __init__(self, instance: Instance, max_positions: int = None):
        """Initialise le solveur pour une instance donnée du MPVRP-CC."""
        self.instance = instance
        self.model = pulp.LpProblem("MPVRP-CC", pulp.LpMinimize)
        self.solution = None

        self.K = [k for k in instance.camions.keys()]
        self.D = [d for d in instance.depots.keys()]
        self.G = [g for g in instance.garages.keys()]
        self.S = [s for s in instance.stations.keys()]
        self.P = list(range(1, instance.num_products + 1))

        self.V = self.D + self.S  # V = D ∪ S
        self.N = self.D + self.G + self.S  # N = D ∪ G ∪ S

        if max_positions is None:
            max_positions = len(self.P) * len(self.S)
        self.T = list(range(1, max_positions + 1))

        self.C = {c.id : c.capacity for c in instance.camions.values()}
        self.g_k = {c.id : c.garage_id for c in instance.camions.values()}
        self.p_initial = {c.id : c.initial_product for c in instance.camions.values()}

        self.demand = {(s.id, p): s.demand.get(p, 0) for s in instance.stations.values() for p in self.P}
        self.stock = {(d.id, p): d.stocks.get(p, 0) for d in instance.depots.values() for p in self.P}
        self.costs = instance.costs
        self.distances = instance.distances

        self.M = 1e6  # Grande constante pour les contraintes Big-M

    def build_model(self):
        """MIP model construction."""

        ##### Variables de décision ######

        # x[i, j, k, p, t1 si le véhicule k va de i ∈ V à j ∈ V avec le produit p à la position t, 0 sinon.
        self.x = pulp.LpVariable.dicts("x", ((i, j, k, p, t) for i in self.V for j in self.V for k in self.K for p in self.P for t in self.T), cat=pulp.LpBinary)
        # load[d, k, p, t] : 1 si le véhicule k charge le produit p au dépôt d ∈ D à la position t ∈ T pour une mini-tournée, 0 sinon.
        self.load = pulp.LpVariable.dicts("load", ((d, k, p, t) for d in self.D for k in self.K for p in self.P for t in self.T), cat=pulp.LpBinary)
        # deliv[s, p, k, t] : Quantité du produit p livrée à la station s par le véhicule k à la position t.
        self.deliv = pulp.LpVariable.dicts("deliv", ((s, p, k, t) for s in self.S for p in self.P for k in self.K for t in self.T), lowBound=0, cat=pulp.LpContinuous)
        # q_load[d, k, p, t]: Quantité du produit p chargée par le véhicule k au dépôt d à la position t.
        self.q_load = pulp.LpVariable.dicts("q_load", ((d, k, p, t) for d in self.D for k in self.K for p in self.P for t in self.T), lowBound=0, cat=pulp.LpContinuous)
        # q[i, k, p, t]: Quantité de produit p restant dans le véhicule k au nœud i à la position t.
        self.q = pulp.LpVariable.dicts("q", ((i, k, p, t) for i in self.V for k in self.K for p in self.P for t in self.T), lowBound=0, cat=pulp.LpContinuous)
        # switch[k, t, p1, p2]: 1 si le véhicule k effectue un changement de produit de p′ à p à la position t ∈ T (p′ != p).
        self.switch = pulp.LpVariable.dicts("switch", ((k, t, p1, p2) for k in self.K for t in self.T for p1 in self.P for p2 in self.P if p1 != p2), cat=pulp.LpBinary)
        # start[g, d, k]: 1 si le véhicule k commence sa tournée au garage gk et se dirige vers le dépôt d ∈ D, 0 sinon.
        self.start = pulp.LpVariable.dicts("start", ((self.g_k[k], d, k) for d in self.D for k in self.K), cat=pulp.LpBinary)
        # fin[s, g_k, k, p, t]: 1 si le véhicule k termine sa tournée complète au garage gk depuis s à la fin de la mini-tournée t.
        self.fin = pulp.LpVariable.dicts("fin", ((s, self.g_k[k], k, p, t) for s in self.S for k in self.K for p in self.P for t in self.T), cat=pulp.LpBinary)
        # used[k, t]: 1 si la position t ∈ T est utilisée pour une mini-tournée du véhicule k.
        self.used = pulp.LpVariable.dicts("used", ((k, t) for k in self.K for t in self.T), cat=pulp.LpBinary)
        # prod[k, t, p]: 1 si le véhicule k transporte le produit p à la position t ∈ T.
        self.prod = pulp.LpVariable.dicts("prod", ((k, t, p) for k in self.K for t in self.T for p in self.P), cat=pulp.LpBinary)
        # endDepot[d, k, p, t]: 1 si le véhicule k termine sa mini-tournée au dépôt d ∈ D avec le produit p à la position t ∈ T.
        self.endDepot = pulp.LpVariable.dicts("endDepot", ((d, k, p, t) for d in self.D for k in self.K for p in self.P for t in self.T), cat=pulp.LpBinary)

        ###### Fonction objectif ######

        routing_cost = pulp.lpSum(
            self.distances.get((i, j), 0.0) * self.x[i, j, k, p, t]
            for i in self.V for j in self.V for k in self.K for p in self.P for t in self.T if i != j
        )

        switch_cost = pulp.lpSum(
            self.costs.get((p1, p2), 0.0) * self.switch[k, t, p1, p2]
            for k in self.K for t in self.T for p1 in self.P for p2 in self.P if p1 != p2
        )

        start_cost = pulp.lpSum(
            self.distances.get((f"G{self.g_k[k]}", d), 0.0) * self.start[self.g_k[k], d, k]
            for d in self.D for k in self.K
        )

        end_cost = pulp.lpSum(
            self.distances.get((s, f"G{self.g_k[k]}"), 0.0) * self.fin[s, self.g_k[k], k, p, t]
            for s in self.S for k in self.K for p in self.P for t in self.T
        )

        self.model += routing_cost + switch_cost + start_cost + end_cost, "Total_Cost"

        ###### Contraintes ######

        # 1. La demande totale d’une station pour un produit est satisfaite par la somme des
        # livraisons de ce produit effectuées sur toutes les mini-tournées t de tous les véhicules.
        for s in self.S:
            for p in self.P:
                self.model += pulp.lpSum(
                    self.deliv[s, p, k, t]
                    for k in self.K for t in self.T
                ) >= self.demand.get((s, p), 0), f"Demand_Satisfaction_{s}_{p}"

        # 2. Chaque véhicule doit obligatoirement démarrer sa tournée depuis son garage attitré
        # gk vers un dépôt d’approvisionnement s’il est utilisé (U sedk1 = 1). L’égalité à 1 garantit qu’un et
        # un seul dépôt est choisi comme première destination.
        for k in self.K:
            self.model += pulp.lpSum(
                self.start[self.g_k[k], d, k]
                for d in self.D
            ) == self.used[k, 1], f"Start_From_Garage_{k}"

        # 3. Justification : Le départ du garage vers un dépôt n’est pas un arc du graphe (les arcs x ne
        # relient que les nœuds de service V ). Cette contrainte lie donc explicitement le dépôt choisi au
        # départ (Start) au dépôt effectivement chargé au premier segment (Load à t = 1), garantissant la
        # cohérence de la solution et du coût cgk d
        for k in self.K:
            for d in self.D:
                self.model += self.start[self.g_k[k], d, k] == pulp.lpSum(
                    self.load[d, k, 1, p] 
                    for p in self.P
                    ), f"StartLoad_{k}_{d}"

        # 4. Chaque véhicule utilisé doit terminer sa tournée complète en revenant à son garage
        # gk depuis une station s ∈ S. Le véhicule ne peut pas terminer directement depuis un dépôt, ce qui
        # force la livraison effective avant le retour au garage.
        for k in self.K:
            self.model += ( pulp.lpSum(
                self.fin[s, self.g_k[k], k, p, t]
                for s in self.S for p in self.P for t in self.T
            ) == self.used[k, 1]
            ), f"End_At_Garage_{k}"

        # 5. Le flot doit s’équilibrer à chaque station pour chaque mini-tournée t. Le véhicule
        # peut soit repartir vers une autre station/dépôt, soit rentrer au garage (F in).
        for k in self.K:
            for s in self.S:
                for t in self.T:
                    for p in self.P:
                        self.model += pulp.lpSum(
                            self.x[i, s, k, p, t]
                            for i in self.V if i != s
                        ) == pulp.lpSum(
                            self.x[s, j, k, p, t]
                            for j in self.V if j != s
                        ) + self.fin[s, self.g_k[k], k, p, t], f"Flow_Balance_Station_{s}_Vehicle_{k}_Tour_{t}_Product_{p}"

        # 6. À la position t (un segment), le véhicule ne peut pas utiliser un dépôt comme
        # simple nœud de transit. La contrainte (C5a) impose qu’on part d’un dépôt d si et seulement si on
        # a chargé ce dépôt pour ce segment (Loaddktp = 1). La contrainte (C5b) impose qu’on arrive sur
        # un dépôt uniquement pour terminer le segment (EndDepotdkpt = 1).
        for k in self.K:
            for d in self.D:
                for t in self.T:
                    for p in self.P:
                        self.model += pulp.lpSum(
                            self.x[d, j, k, p, t]
                            for j in self.V if j != d
                        ) == self.load[d, k, p, t], f"Depart_From_Depot_{d}_Vehicle_{k}_Tour_{t}_Product_{p}"
                        self.model += pulp.lpSum(
                            self.x[i, d, k, p, t]
                            for i in self.V if i != d
                        ) == self.endDepot[d, k, p, t], f"Arrive_At_Depot_{d}_Vehicle_{k}_Tour_{t}_Product_{p}"

        # 7. Si le produit p est actif sur le segment t (P rodktp = 1), alors ce segment doit se
        # terminer exactement une fois : soit en revenant à un dépôt (variable EndDepot), soit en revenant
        # au garage depuis une station (variable F in).
        for k in self.K:
            for t in self.T:
                for p in self.P:
                    self.model += pulp.lpSum(
                        self.endDepot[d, k, p, t]
                        for d in self.D
                    ) + pulp.lpSum(
                        self.fin[s, self.g_k[k], k, p, t]
                        for s in self.S
                    ) == self.prod[k, t, p], f"Product_Active_Ending_{k}_Tour_{t}_Product_{p}"

        # 8. Un nouveau segment t + 1 ne peut démarrer que si le segment t s’est terminé sur
        # un dépôt. Le second lien impose que le dépôt de chargement du segment t + 1 est exactement le
        # dépôt où le segment t s’est terminé (rechargement au même dépôt).
        for k in self.K:
            for t in self.T[:-1]:
                self.model += self.used[k, t + 1] == pulp.lpSum(
                    self.endDepot[d, k, p, t]
                    for d in self.D for p in self.P
                ), f"Next_Tour_Starts_After_Ending_{k}_Tour_{t}"

                for d in self.D:
                    for p in self.P:
                        self.model += pulp.lpSum(
                            self.load[d, k, p, t + 1] 
                            for p in self.P
                        ) == pulp.lpSum(
                            self.endDepot[d, k, p, t] 
                            for p in self.P
                        ), f"NextDepot_{k}_{t}_{d}_Product_{p}"

        # 9. Un véhicule ne peut visiter une même station qu’une seule fois pour un produit
        # donné, sur toutes les positions.
        for k in self.K:
            for s in self.S:
                for p in self.P:
                    self.model += pulp.lpSum(
                        self.x[i, s, k, p, t]
                        for i in self.V if i != s for t in self.T
                    ) <= 1, f"Single_Visit_Station_{s}_Vehicle_{k}_Product_{p}"

        # 10.Une livraison ne peut avoir lieu que si le véhicule arrive effectivement à la station
        # avec le produit concerné (inflow). Le terme M (Big-M) permet de désactiver la contrainte lorsque
        # la visite a lieu, autorisant ainsi une livraison jusqu’à concurrence de la demande.
        for k in self.K:
            for s in self.S:
                for p in self.P:
                    for t in self.T:
                        self.model += self.deliv[s, p, k, t] <= pulp.lpSum(
                            self.x[i, s, k, p, t]
                            for i in self.V if i != s
                        ) * self.M, f"Delivery_Only_If_Arrival_Station_{s}_Vehicle_{k}_Tour_{t}_Product_{p}"

        # 11. On ne peut pas modéliser strictement "> 0" en PLNEM. On impose donc un
        # plancher ϵdeliv > 0 dès qu’une station est visitée (inflow) ou qu’on termine la tournée depuis cette
        # station (F in). Dans l’implémentation, on prend ϵ^[deliv] = min{1, min(dsp : dsp > 0)} pour rester
        # faisable si certaines demandes sont fractionnaires.
        for k in self.K:
            for s in self.S:
                for p in self.P:
                    for t in self.T:
                        epsilon_deliv = min(1, min(v for (st, pr), v in self.demand.items() if st == s and pr == p and v > 0)) if any(v > 0 for (st, pr), v in self.demand.items() if st == s and pr == p) else 0
                        self.model += self.deliv[s, p, k, t] >= epsilon_deliv * pulp.lpSum(
                            self.x[i, s, k, p, t]
                            for i in self.V if i != s
                        ), f"Min_Delivery_If_Arrival_Station_{s}_Vehicle_{k}_Tour_{t}_Product_{p}"
                        self.model += self.deliv[s, p, k, t] >= epsilon_deliv * pulp.lpSum(
                            self.fin[s, self.g_k[k], k, p, t]
                        ), f"Min_Delivery_If_Ending_Station_{s}_Vehicle_{k}_Tour_{t}_Product_{p}"

        # 12. Par conservation de la matière, tout ou presque ce qui est chargé à un dépôt pour une mini-
        # tournée doit être livré lors de cette mini-tournée.
        for k in self.K:
            for t in self.T:
                for p in self.P:
                    self.model += pulp.lpSum(
                        self.q_load[d, k, p, t]
                        for d in self.D
                    ) == pulp.lpSum(
                        self.deliv[s, p, k, t]
                        for s in self.S
                    ), f"Mass_Conservation_Vehicle_{k}_Tour_{t}_Product_{p}"

        # 13. La variable continue QLoad (quantité chargée) est conditionnée par la variable
        # binaire Load (décision de chargement). Lorsque Loaddktp = 0, la quantité QLoaddktp est forcée à
        # zéro ; sinon, elle est bornée par le Big-M.
        for d in self.D:
            for k in self.K:
                for p in self.P:
                    for t in self.T:
                        self.model += self.q_load[d, k, p, t] <= self.M * self.load[d, k, p, t], f"QLoad_BigM_Depot_{d}_Vehicle_{k}_Tour_{t}_Product_{p}"

        # 14. Cette contrainte évite les segments "vides" (Load = 1 mais quantité chargée
        # nulle). Dans l’implémentation, on fixe ϵ^[load] = 1.
        for d in self.D:
            for k in self.K:
                for p in self.P:
                    for t in self.T:
                        self.model += self.q_load[d, k, p, t] >= 1 * self.load[d, k, p, t], f"Min_QLoad_If_Load_Depot_{d}_Vehicle_{k}_Tour_{t}_Product_{p}"

        # 15. Les dépôts disposent d’un stock limité Sdp pour chaque produit. La somme de tous
        # les prélèvements effectués par l’ensemble des véhicules ne peut excéder cette capacité de stockage.
        for d in self.D:
            for p in self.P:
                self.model += pulp.lpSum(
                    self.q_load[d, k, p, t]
                    for k in self.K for t in self.T
                ) <= self.stock.get((d, p), 0), f"Depot_Stock_Limit_{d}_Product_{p}"

        # 16. Chaque véhicule k possède une capacité physique maximale Ck qui ne peut être
        # dépassée lors d’un chargement. La variable U sedkt active ou désactive cette borne selon que la
        # position t est utilisée ou non.
        for k in self.K:
            for t in self.T:
                self.model += pulp.lpSum(
                    self.q_load[d, k, p, t]
                    for d in self.D for p in self.P
                ) <= self.C[k] * self.used[k, t], f"Vehicle_Capacity_{k}_Tour_{t}"

        # 17. Si le véhicule va de i vers j (x = 1), la charge en arrivant à j doit être égale
        # à la charge en i moins ce qui a été livré en j. Comme Deliv > 0 pour au moins une station du
        # cycle, cela interdit mathématiquement de boucler sur un ensemble de stations sans repasser par
        # un dépôt.
        for k in self.K:
                for t in self.T:
                    for p in self.P:
                        self.model += (self.q[d, k, p, t] == self.q_load[d, k, p, t] 
                        ), f"Init_Load_Balance_Depot_{d}_Vehicle_{k}_Tour_{t}_Product_{p}"

        for i in self.V:
            for j in self.S:
                if i == j:
                    continue
                for k in self.K:
                    for t in self.T:
                        for p in self.P:
                            self.model += (
                                self.q[j, k, p, t]
                                <= self.q[i, k, p, t] - self.deliv[j, p, k, t] + self.M * (1 - self.x[i, j, k, p, t])
                            ), f"Decrease_Balance_From_{i}_To_{j}_Vehicle_{k}_Tour_{t}_Product_{p}"

        # 18. Respect de la capacité
        for i in self.V:
            for k in self.K:
                for t in self.T:
                    for p in self.P:
                        self.model += self.q[i, k, p, t] <= self.C[k] * pulp.lpSum(
                            self.x[i, j, k, p, t] 
                            for j in self.V if j != i
                        ), f"Capacity_Respect_Node_{i}_Vehicle_{k}_Tour_{t}_Product_{p}"

        # 19. Si la position t est active (U sedkt = 1), exactement un produit doit être chargé
        # à un dépôt pour cette mini-tournée. Cela modélise le fait qu’une citerne ne transporte qu’un seul
        # type de produit par voyage.
        for k in self.K:
            for t in self.T:
                self.model += pulp.lpSum(
                    self.prod[k, t, p]
                    for p in self.P
                ) == self.used[k, t], f"Single_Product_Per_Tour_Vehicle_{k}_Tour_{t}"

        # 20. Produit actif identifié par le chargement
        for k in self.K:
            for t in self.T:
                for p in self.P:
                    self.model += self.prod[k, t, p] == pulp.lpSum(
                        self.load[d, k, p, t]
                        for d in self.D
                    ), f"Prod_{p}_From_Load_{k}_{t}"

        # 21. Pour éliminer les symétries et simplifier le modèle, les positions doivent être
        # utilisées de manière consécutive (1, 2, 3, ...). Une position t + 1 ne peut être active que si la
        # position t l’est également, évitant ainsi les "trous" dans la séquence.
        for k in self.K:
            for t in self.T[:-1]:
                self.model += self.used[k, t + 1] <= self.used[k, t], f"Consecutive_Tours_Vehicle_{k}_Tour_{t}"

        # 22. Détection du changement de produit
        for k in self.K:
            for t in self.T:
                for p1 in self.P:
                    for p2 in self.P:
                        if p1 == p2:
                            continue
                        if t == 1:
                            prod_prev = 1 if p1 == self.p_initial[k] else 0
                            self.model += (
                                self.switch[k, t, p1, p2] >= prod_prev + self.prod[k, t, p2] - 1
                            ), f"Product_Change_Detection_Vehicle_{k}_Tour_{t}_Products_{p1}_{p2}"
                        else:
                            self.model += (
                                self.switch[k, t, p1, p2] >= self.prod[k, t-1, p1] + self.prod[k, t, p2] - 1
                            ), f"Product_Change_Detection_Vehicle_{k}_Tour_{t}_Products_{p1}_{p2}"

    def solve(self):
        self.build_model()
        solver = pulp.getSolver(SOLVER_NAME, timeLimit=TIME_LIMIT)
        start_time = time.time()
        self.model.solve(solver)
        end_time = time.time()

        self.solution = {
            "status": pulp.LpStatus[self.model.status],
            "objective_value": pulp.value(self.model.objective),
            "time_taken": end_time - start_time,
        }

        if EXPORT_TOURS:
            tours = self.extract_tours()
            print(tours)

    def extract_tours(self):
        """Extract tours from the solved model."""
        tours = {}
        for k in self.K:
            tours[k] = []
            for t in self.T:
                tour = []
                for i in self.V:
                    for j in self.V:
                        for p in self.P:
                            if i != j and pulp.value(self.x[i, j, k, p, t]) > 0.5:
                                tour.append((i, j, p))
                if tour:
                    tours[k].append({
                        "tour_number": t,
                        "segments": tour
                    })
        return tours


if __name__ == "__main__":
    from .utils import parse_instance

    instance = parse_instance("data/instances/MPVRP_01_s5_d2_p2.dat")
    solver = Solver(instance)
    solver.solve()
    print(solver.solution)