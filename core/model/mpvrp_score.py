"""
Système de notation pour MPVRP-CRP (Multi-Product Vehicle Routing Problem with Compartments)

Ce module effectue deux tâches principales :
1. Vérifie la validité d'une solution via le module mpvrp_verify
2. Calcule un score de qualité sur 100 points basé sur trois critères :
   - Optimisation des ressources (flotte et remplissage) : 40 points
   - Qualité du routage (efficacité des trajets) : 40 points
   - Gestion des produits (pureté des tournées) : 20 points
"""

import os
import math
import json
try:
    from core.model import mpvrp_verify as verifier
except ImportError:
    import core.model.mpvrp_verify as verifier

class MPVRPScorer:
    """
    Classe responsable du calcul du score de qualité d'une solution.
    """
    def __init__(self, instance, solution, reconstruction_result):
        self.instance = instance
        self.solution = solution
        self.reconstruction_result = reconstruction_result
        
        # Données analysées
        self.used_vehicles_ids = set() # IDs des véhicules utilisés
        self.num_used = 0  # Nombre de véhicules utilisés
        self.total_demand = 0 # Demande totale servie
        self.products_with_demand = set() # Produits demandés
        self.total_capacity_deployed = 0 # Capacité totale des véhicules utilisés
        self.max_vehicle_capacity = 0 # Capacité maximale parmi tous les véhicules
        self.total_cost = 0 # Coût total de la solution

    def compute(self):
        """
        Exécute l'analyse et le calcul des scores.
        Returns:
            tuple: (score_final, détails)
        """
        if not self._analyze_basic_data():
            return 0, {"error": "Aucun véhicule utilisé"}

        score_resources, details_resources = self._calculate_resource_score()
        score_routing, details_routing = self._calculate_routing_score()
        score_products, details_products = self._calculate_product_score()

        final_score = score_resources + score_routing + score_products

        # Synthèse des détails
        details = {
            **details_resources,
            **details_routing,
            **details_products,
            "scores": {
                "resources": round(score_resources, 2),
                "routing": round(score_routing, 2),
                "products": round(score_products, 2),
                "total": round(final_score, 2)
            }
        }

        return final_score, details

    def _analyze_basic_data(self):
        """Analyse les données de base de la solution et de l'instance."""
        # Identification des véhicules utilisés via la reconstruction du module de vérification
        self.used_vehicles_ids = set()
        for vid, data in self.reconstruction_result.items():
             # Un véhicule est utilisé si son chemin contient plus que le garage (départ + retour)
             if len(data.get('path', [])) > 1:
                 self.used_vehicles_ids.add(vid)
        
        self.num_used = len(self.used_vehicles_ids)
        if self.num_used == 0:
            return False

        # Demande totale et produits
        for s in self.instance.stations:
            for p, q in s.demands.items():  # p = produit, q = quantité demandée
                if q > 0:
                    self.total_demand += q
                    self.products_with_demand.add(p)  # on ne compte que les produits réellement demandés

        # Capacité déployée et capacité maximale
        for v in self.instance.vehicles:
            self.max_vehicle_capacity = max(self.max_vehicle_capacity, v.capacity) # on détermine dynamiquement la capacité maximale parmi tous les véhicules
            if v.id in self.used_vehicles_ids:
                self.total_capacity_deployed += v.capacity

        # Coût total
        if 'metrics' in self.solution and 'total_distance' in self.solution['metrics']:
             self.total_cost = self.solution['metrics']['total_distance'] + self.solution['metrics'].get('switch_cost', 0)
        else:
             self.total_cost = self.solution.get('objective', 0)
        return True

    def _calculate_resource_score(self):
        """Calcule le score d'optimisation des ressources (40 points)."""
        # Estimation du nombre optimal de camions à utiliser
        has_change_costs = any(c > 0 for c in self.instance.change_costs.values()) # variable binaire qui vérifie si des coûts de changement sont définis
         # Calcul du nombre minimum de camions nécessaires basé sur la demande totale et la capacité maximale
        min_trucks_volume = math.ceil(self.total_demand / self.max_vehicle_capacity) if self.max_vehicle_capacity > 0 else self.num_used
        
        if has_change_costs:
            #Si des coûts de changement existent, le nombre optimal de camions est le plus grand entre: (1) le minimum nécessaire pour transporter tout le volume, et (2) le nombre de produits distincts (limité par la flotte disponible).
            target_trucks = max(min_trucks_volume, min(len(self.products_with_demand), len(self.instance.vehicles)))
        else:
            target_trucks = min_trucks_volume

        # Score d'utilisation de flotte (20 points)
        if self.num_used <= target_trucks:
            score_fleet = 20.0
        else:
            ratio = target_trucks / self.num_used
            score_fleet = 20.0 * ratio

        # Score remplissage (20 points)
        fill_rate = self.total_demand / self.total_capacity_deployed if self.total_capacity_deployed > 0 else 0
        if self.num_used <= target_trucks:
            score_fill = 10.0 + (10.0 * fill_rate)
        else:
            score_fill = 20.0 * fill_rate

        return score_fleet + score_fill, {
            "total_demand": self.total_demand,
            "total_capacity_deployed": self.total_capacity_deployed,
            "num_trucks_used": self.num_used,
            "target_trucks": target_trucks
        }

    def _calculate_routing_score(self):
        """Calcule le score de qualité du routage (40 points)."""
        baseline_cost = 0 # Coût de référence basé sur l'aller-retour simple vers chaque station
        avg_depot_x = sum(d.x for d in self.instance.depots) / len(self.instance.depots) # Coordonnée X moyenne des dépôts
        avg_depot_y = sum(d.y for d in self.instance.depots) / len(self.instance.depots) # Coordonnée Y moyenne des dépôts
        
        for s in self.instance.stations:
            dist = math.sqrt((s.x - avg_depot_x)**2 + (s.y - avg_depot_y)**2) # Distance euclidienne entre la station et le dépôt moyen
            baseline_cost += dist * 2
        
        baseline_cost += (self.num_used * 20) # Coût fixe par véhicule utilisé
        
        if baseline_cost > 0:
            ratio_routing = baseline_cost / self.total_cost if self.total_cost > 0 else 0
            score_routing = 40.0 * min(1.0, ratio_routing ) # Le score est plafonné à 40 points 
        else:
            score_routing = 0

        return score_routing, {
            "cost_actual": self.total_cost,
            "cost_baseline": baseline_cost
        }

    def _calculate_product_score(self):
        """Calcule le score de gestion des produits (20 points)."""
        purity_scores = []
        for vid in self.used_vehicles_ids:
            v_deliveries = {}
            total_v_qty = 0
            rec = self.reconstruction_result.get(vid, {})
            for (s, p), q in rec.get('deliveries', {}).items():
                v_deliveries[p] = v_deliveries.get(p, 0) + q # total livré par produit
                total_v_qty += q
                
            if total_v_qty > 0:
                max_p_qty = max(v_deliveries.values())
                purity = max_p_qty / total_v_qty # pureté = proportion du produit majoritaire sur le total livré (la pureté est calculée par véhicule)
                purity_scores.append(purity)
            else:
                purity_scores.append(0)
                
        avg_purity = sum(purity_scores) / len(purity_scores) if purity_scores else 0
        score_products = 20.0 * avg_purity
        
        return score_products, {
            "avg_purity": avg_purity
        }


class MPVRPScoreCLI:
    """
    Interface en ligne de commande pour l'évaluation.
    """
    def __init__(self):
        """Initialise les chemins des dossiers."""
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        # Remonter de core/model vers la racine pour trouver data
        # core/model -> core -> MPVRP-CC
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(self.script_dir)))
        self.data_dir = os.path.join(self.project_root, "data", "instances")
        self.solutions_dir = os.path.join(self.project_root, "data", "solutions")

        if not os.path.exists(self.data_dir):
            # Repli: exécution depuis un autre dossier (ex: lancement direct du script).
            self.project_root = os.getcwd()
            self.data_dir = os.path.join(self.project_root, "data", "instances")
            self.solutions_dir = os.path.join(self.project_root, "data", "solutions")

    def run(self):
        if not self._check_directories():
            return

        instance_name = self._select_instance()
        if not instance_name:
            return

        instance, solution = self._load_data(instance_name)
        if not instance or not solution:
            return

        # Vérification
        if not self._verify_solution(instance, solution):
            return

        print("Solution Valide. Calcul du score...")
        
        # La reconstruction est déjà dans solution['routes']
        reconstruction_results = solution['routes']
        
        scorer = MPVRPScorer(instance, solution, reconstruction_results)
        score, details = scorer.compute()
        
        self._print_report(details)

    def _check_directories(self):
        if not os.path.exists(self.data_dir):
            print(f"Dossier data/ introuvable: {self.data_dir}")
            return False
        return True

    def _select_instance(self):
        available_files = [f for f in os.listdir(self.data_dir) if f.endswith('.dat')]
        if not available_files:
            print("Aucun fichier .dat dans data/")
            return None

        print("Fichiers disponibles :")
        for f in available_files:
            print(f"  - {f}")
        
        return input("\nInstance à évaluer (ex: MPVRP_3_s3_d1_p2.dat) : ").strip()

    def _load_data(self, instance_name):
        instance_path = os.path.join(self.data_dir, instance_name)
        base_name = os.path.splitext(instance_name)[0]
        solution_name = f"Sol_{base_name}.dat"
        solution_path = os.path.join(self.solutions_dir, solution_name)
        
        if not os.path.exists(instance_path):
            print(f"Fichier instance introuvable: {instance_path}")
            return None, None
        if not os.path.exists(solution_path):
            print(f"Fichier solution introuvable: {solution_path}")
            return None, None

        print(f"Chargement de {instance_name}...")
        instance = verifier.parse_instance(instance_path)
        print(f"Chargement de {solution_name}...")
        solution = verifier.parse_solution_dat(solution_path, instance)
        
        return instance, solution

    def _verify_solution(self, instance, solution):
        print("Vérification de la validité...")
        all_errors = []
        
        # Vérification continuité
        for vid, route in solution['routes'].items():
            errs = verifier.verify_route_continuity(route, vid, instance)
            all_errors.extend(errs)
                
        all_errors.extend(verifier.verify_demands(solution, instance))
        all_errors.extend(verifier.verify_stocks(solution, instance))
        all_errors.extend(verifier.verify_capacity(solution, instance))
        
        costs = verifier.calculate_total_cost(solution, instance)
        
        # Vérification coût rapporté vs calculé
        if 'metrics' in solution and 'total_distance' in solution['metrics']:
            reported_dist = solution['metrics']['total_distance']
            reported_switch = solution['metrics'].get('switch_cost', 0)
            reported_total = reported_dist + reported_switch
            
            if abs(costs['total'] - reported_total) > 0.1:
                all_errors.append(f"Écart de coût significatif: Calc={costs['total']:.1f} vs Rep={reported_total:.1f}")

        if all_errors:
            print(f"\nSOLUTION INVALIDE ({len(all_errors)} erreurs)")
            print("Score: 0/100")
            for e in all_errors[:5]:
                print(f"  - {e}")
            if len(all_errors) > 5: 
                print("  ...")
            return False
            
        return True

    def _print_report(self, details):
        s = details['scores']
        print(f"\n{'='*40}")
        print(f"       RAPPORT DE PERFORMANCE")
        print(f"{'='*40}")
        print(f"SCORE GLOBAL : {s['total']}/100")
        print(f"{'='*40}")
        
        print(f"\n1. Optimisation Ressources : {s['resources']}/40")
        print(f"   - Camions utilisés : {details.get('stats_trucks_used', 'N/A')}")
        print(f"   - Cible (Vol/Prod) : {details.get('stats_trucks_target', 'N/A')}")
        print(f"   - Taux Remplissage : {details.get('stats_fill_rate', 'N/A')}%")
        
        print(f"\n2. Qualité Routage : {s['routing']}/40")
        print(f"   - Efficacité Distance : {details.get('stats_efficiency', 'N/A')}%")
        print(f"   - Coût par unité : {details.get('stats_cost_per_unit', 'N/A')}")
        
        print(f"\n3. Gestion Produits : {s['products']}/20")
        print(f"   - Changements produits : {details.get('stats_total_switches', 'N/A')}")

if __name__ == "__main__":
    cli = MPVRPScoreCLI()
    cli.run()
