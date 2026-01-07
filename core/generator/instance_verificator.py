import numpy as np
import os
import sys
import re

class InstanceVerificator:
    def __init__(self, filepath):
        self.filepath = filepath
        self.errors = []
        self.warnings = []
        self.data = {}
        
    def verify(self):
        """Effectue toutes les vérifications"""
        print(f"Vérification de l'instance : {os.path.basename(self.filepath)}\n")
        
        # 1. Vérifications structurelles
        if not self.check_file_exists():
            return False
        
        if not self.load_data():
            return False
        
        # 2. Vérifications minimales
        self.check_minimum_elements()
        
        # 3. Vérifications des IDs uniques
        self.check_unique_ids()
        
        # 4. Vérifications de validité
        self.check_validity()
        
        # 5. Vérification Demande ≤ Capacité max
        self.check_capacity_demand()
        
        # 6. Vérification chevauchement géographique
        self.check_geographic_overlap()
        
        # 7. Vérification inégalité triangulaire (matrice de transition)
        self.check_triangle_inequality()
        
        # 8. Vérifications de faisabilité
        self.check_feasibility()
        
        # 9. Vérifications géométriques
        self.check_geometry()
        
        # Afficher le rapport
        self.print_report()
        
        return len(self.errors) == 0
    
    def check_file_exists(self):
        """Vérifie que le fichier existe"""
        if not os.path.exists(self.filepath):
            self.errors.append(f"❌ Fichier non trouvé : {self.filepath}")
            return False
        return True
    
    def load_data(self):
        """Charge les données du fichier .dat"""
        try:
            with open(self.filepath, 'r') as f:
                all_lines = [line.strip() for line in f.readlines()]
            
            # Extraire l'UUID si présent (première ligne commençant par #)
            self.data['uuid'] = None
            uuid_pattern = re.compile(r'^#\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$', re.IGNORECASE)
            for line in all_lines:
                if line.startswith('#'):
                    match = uuid_pattern.match(line)
                    if match:
                        self.data['uuid'] = match.group(1)
                        break
            
            # Filtrer les commentaires et lignes vides
            lines = [line for line in all_lines if line and not line.startswith('#')]
            
            if len(lines) < 6:
                self.errors.append("❌ Fichier mal formaté : pas assez de sections")
                return False
            
            # Lire les paramètres pour calculer le nombre exact de lignes attendues
            first_line_params = [int(x) for x in lines[0].split()]
            if len(first_line_params) != 5:
                self.errors.append(f"❌ Ligne 1 : attendu 5 paramètres, trouvé {len(first_line_params)}")
                return False
            
            nb_p_temp, nb_d_temp, nb_g_temp, nb_s_temp, nb_v_temp = first_line_params
            expected_lines = 1 + nb_p_temp + nb_v_temp + nb_d_temp + nb_g_temp + nb_s_temp
            
            if len(lines) != expected_lines:
                self.errors.append(f"❌ Nombre de lignes incorrect : attendu {expected_lines}, trouvé {len(lines)}")
                self.errors.append(f"   Détail attendu : 1 (params) + {nb_p_temp} (matrice) + {nb_v_temp} (véhicules) + {nb_d_temp} (dépôts) + {nb_g_temp} (garages) + {nb_s_temp} (stations)")
                return False
            
            # Parsing - Ordre: nb_p, nb_d, nb_g, nb_s, nb_v
            params = np.array([int(x) for x in lines[0].split()])
            nb_p, nb_d, nb_g, nb_s, nb_v = params
            
            self.data['params'] = params
            self.data['nb_p'] = nb_p
            self.data['nb_d'] = nb_d
            self.data['nb_g'] = nb_g
            self.data['nb_s'] = nb_s
            self.data['nb_v'] = nb_v
            
            idx = 1
            
            # Matrice de transition
            transition_costs = []
            for i in range(nb_p):
                transition_costs.append([float(x) for x in lines[idx].split()])
                idx += 1
            self.data['transition_costs'] = np.array(transition_costs)
            
            # Véhicules
            vehicles = []
            for i in range(nb_v):
                vehicles.append([float(x) for x in lines[idx].split()])
                idx += 1
            self.data['vehicles'] = np.array(vehicles)
            
            # Dépôts
            depots = []
            for i in range(nb_d):
                depots.append([float(x) for x in lines[idx].split()])
                idx += 1
            self.data['depots'] = np.array(depots)
            
            # Garages
            garages = []
            for i in range(nb_g):
                garages.append([float(x) for x in lines[idx].split()])
                idx += 1
            self.data['garages'] = np.array(garages)
            
            # Stations
            stations = []
            for i in range(nb_s):
                stations.append([float(x) for x in lines[idx].split()])
                idx += 1
            self.data['stations'] = np.array(stations)
            
            return True
        except Exception as e:
            self.errors.append(f"Erreur lors du chargement : {str(e)}")
            return False
    
    def check_minimum_elements(self):
        """Vérifie les éléments minimums"""
        checks = [
            ('nb_v', 1, "Véhicules"),
            ('nb_d', 1, "Dépôts"),
            ('nb_g', 1, "Garages"),
            ('nb_s', 1, "Stations"),
            ('nb_p', 1, "Produits"),
        ]
        
        for key, min_val, name in checks:
            if self.data[key] < min_val:
                self.errors.append(f"Au moins 1 {name} requis, trouvé : {self.data[key]}")
            else:
                print(f"✓ {name} : {self.data[key]}")
    
    def check_unique_ids(self):
        """Vérifie que les IDs sont uniques ET contigus [1, n] pour chaque type d'entité"""
        print("\n🔢 Vérifications des IDs (unicité et contiguïté) :")
        
        entities = [
            ('vehicles', 'Véhicules', self.data['nb_v']),
            ('depots', 'Dépôts', self.data['nb_d']),
            ('garages', 'Garages', self.data['nb_g']),
            ('stations', 'Stations', self.data['nb_s'])
        ]
        
        for key, name, expected_count in entities:
            ids = [int(row[0]) for row in self.data[key]]
            unique_ids = set(ids)
            expected_ids = set(range(1, expected_count + 1))
            
            # Vérifier unicité
            if len(ids) != len(unique_ids):
                duplicates = [id for id in ids if ids.count(id) > 1]
                self.errors.append(f"❌ IDs dupliqués pour {name} : {set(duplicates)}")
            # Vérifier contiguïté [1, n]
            elif unique_ids != expected_ids:
                missing = expected_ids - unique_ids
                extra = unique_ids - expected_ids
                if missing:
                    self.errors.append(f"❌ IDs manquants pour {name}: {sorted(missing)}")
                if extra:
                    self.errors.append(f"❌ IDs hors plage pour {name}: {sorted(extra)} (attendu: 1-{expected_count})")
            else:
                print(f"✓ IDs {name} valides [1-{expected_count}]")
    
    def check_validity(self):
        """Vérifie la validité des données"""
        print("\n✅ Vérifications de validité :")
        
        # Garages utilisés existent
        vehicles = self.data['vehicles']
        garage_ids = set(int(v[2]) for v in vehicles)
        valid_garage_ids = set(int(g[0]) for g in self.data['garages'])
        
        for gid in garage_ids:
            if gid not in valid_garage_ids:
                self.errors.append(f"❌ Garage {gid} utilisé par véhicule mais n'existe pas")
        
        # Produits initiaux valides
        product_ids = set(range(1, self.data['nb_p'] + 1))
        for v in vehicles:
            if int(v[3]) not in product_ids:
                self.errors.append(f"❌ Produit initial {int(v[3])} invalide pour véhicule {int(v[0])}")
        
        # Matrice de transition carrée
        if self.data['transition_costs'].shape != (self.data['nb_p'], self.data['nb_p']):
            self.errors.append(f"❌ Matrice de transition mal dimensionnée : {self.data['transition_costs'].shape} au lieu de ({self.data['nb_p']}, {self.data['nb_p']})")
        else:
            print("✓ Matrice de transition cohérente")
        
        # Diagonale de la matrice de transition doit être 0
        diag = np.diag(self.data['transition_costs'])
        if not np.allclose(diag, 0):
            non_zero_diag = [(i+1, diag[i]) for i in range(len(diag)) if diag[i] != 0]
            self.errors.append(f"❌ Diagonale de la matrice de transition non nulle : {non_zero_diag}")
        else:
            print("✓ Diagonale de la matrice de transition = 0")
        
        # Demandes > 0 pour au moins une station
        stations = self.data['stations']
        total_demand_exists = False
        for s in stations:
            demands = s[3:]
            if np.sum(demands) > 0:
                total_demand_exists = True
                break
        
        if not total_demand_exists:
            self.warnings.append(" Aucune demande dans les stations")
        else:
            print("✓ Au moins une station avec demande")
        
        # Stocks >= 0
        depots = self.data['depots']
        if np.all(depots[:, 2:] >= 0):
            print("✓ Stocks non-négatifs")
        else:
            self.errors.append("❌ Stocks négatifs détectés")
    
    def check_capacity_demand(self):
        """Vérifie que chaque demande <= capacité totale flotte (Split Delivery)
        
        Contrainte de Split Delivery:
        - Un camion ne peut desservir une station qu'une fois pour un produit
        - Plusieurs camions peuvent desservir la même station pour le même produit
        - Donc : demande(s, p) <= SUM(capacités de tous les camions)
        """
        print("\n🚗 Vérification capacité (Split Delivery) :")
        
        vehicles = self.data['vehicles']
        stations = self.data['stations']
        total_capacity = np.sum(vehicles[:, 1])
        
        violations = []
        for s in stations:
            station_id = int(s[0])
            for p_idx, demand in enumerate(s[3:]):
                if demand < 0:
                    violations.append(f"Station {station_id}, Produit {p_idx+1}: Demande négative ({demand:.0f})")
                elif demand > total_capacity:
                    violations.append(f"Station {station_id}, Produit {p_idx+1}: {demand:.0f} > {total_capacity:.0f} (capacité totale)")
        
        if violations:
            self.errors.append(f"❌ {len(violations)} demande(s) dépassent la capacité totale flotte ({total_capacity:.0f}):")
            for v in violations[:5]:
                self.errors.append(f"   - {v}")
            if len(violations) > 5:
                self.errors.append(f"   ... et {len(violations) - 5} autre(s)")
        else:
            print(f"✓ Toutes les demandes ≤ Capacité totale flotte ({total_capacity:.0f})")
    
    def check_geographic_overlap(self):
        """Vérifie qu'il n'y a pas de chevauchement géographique"""
        print("\n📍 Vérification chevauchement géographique :")
        
        min_distance = 0.1  # Distance minimale entre deux points
        all_points = []
        
        for d in self.data['depots']:
            all_points.append(('Dépôt', int(d[0]), d[1], d[2]))
        for g in self.data['garages']:
            all_points.append(('Garage', int(g[0]), g[1], g[2]))
        for s in self.data['stations']:
            all_points.append(('Station', int(s[0]), s[1], s[2]))
        
        overlaps = []
        for i in range(len(all_points)):
            for j in range(i + 1, len(all_points)):
                p1, p2 = all_points[i], all_points[j]
                dist = np.sqrt((p1[2] - p2[2])**2 + (p1[3] - p2[3])**2)
                if dist < min_distance:
                    overlaps.append(f"{p1[0]} {p1[1]} et {p2[0]} {p2[1]} (dist={dist:.3f})")
        
        if overlaps:
            self.warnings.append(f"⚠️ {len(overlaps)} chevauchement(s) détecté(s):")
            for o in overlaps:
                self.warnings.append(f"   - {o}")
        else:
            print("✓ Pas de chevauchement géographique")
    
    def check_triangle_inequality(self):
        """
        Vérifie l'inégalité triangulaire sur la matrice des coûts de transition.
        
        Pour tout triplet de produits (i, j, k):
        Cost(i → k) ≤ Cost(i → j) + Cost(j → k)
        
        Si non respectée, c'est un WARNING (pas une erreur) car :
        - C'est réaliste physiquement (certains nettoyages sont plus complexes)
        - Le solveur pourrait exploiter des "changements intermédiaires"
        """
        print("\n🔺 Vérification inégalité triangulaire (matrice de transition) :")
        
        transition = self.data['transition_costs']
        nb_p = self.data['nb_p']
        
        if nb_p < 3:
            print("✓ Moins de 3 produits : vérification non applicable")
            return
        
        violations = []
        
        for i in range(nb_p):
            for k in range(nb_p):
                if i == k:
                    continue
                direct_cost = transition[i, k]
                
                for j in range(nb_p):
                    if j == i or j == k:
                        continue
                    indirect_cost = transition[i, j] + transition[j, k]
                    
                    if direct_cost > indirect_cost:
                        violations.append({
                            'from': i + 1,
                            'to': k + 1,
                            'via': j + 1,
                            'direct': direct_cost,
                            'indirect': indirect_cost,
                            'savings': direct_cost - indirect_cost
                        })
        
        if violations:
            # Trier par économie décroissante
            violations.sort(key=lambda x: x['savings'], reverse=True)
            
            self.warnings.append(f"⚠️ Inégalité triangulaire non respectée ({len(violations)} cas) :")
            self.warnings.append(f"   → Le solveur pourrait utiliser des changements intermédiaires")
            
            # Afficher les 5 cas les plus significatifs
            for v in violations[:5]:
                self.warnings.append(
                    f"   - P{v['from']}→P{v['to']} : direct={v['direct']:.1f} > "
                    f"via P{v['via']} ({v['indirect']:.1f}) | Économie: {v['savings']:.1f}"
                )
            
            if len(violations) > 5:
                self.warnings.append(f"   ... et {len(violations) - 5} autre(s) cas")
        else:
            print("✓ Inégalité triangulaire respectée (matrice métrique)")
    
    def check_feasibility(self):
        """Vérifie la faisabilité"""
        print("\n📦 Vérifications de faisabilité :")
        
        depots = self.data['depots']
        stations = self.data['stations']
        nb_p = self.data['nb_p']
        
        # Demande totale par produit
        total_demand = np.zeros(nb_p)
        for s in stations:
            total_demand += s[3:]
        
        # Stock total par produit
        total_stock = np.zeros(nb_p)
        for d in depots:
            total_stock += d[3:]
        
        feasible = True
        for p in range(nb_p):
            if total_stock[p] >= total_demand[p]:
                print(f"✓ Produit {p+1} : Stock {total_stock[p]:.0f} ≥ Demande {total_demand[p]:.0f}")
            else:
                self.errors.append(f"❌ Produit {p+1} : Stock {total_stock[p]:.0f} < Demande {total_demand[p]:.0f}")
                feasible = False
        
        self.data['feasible'] = feasible
    
    def check_geometry(self):
        """Vérifie les coordonnées géométriques"""
        print("\n🗺 Vérifications géométriques :")
        
        # Vérifier NaN/Inf
        all_data = [self.data['depots'], self.data['garages'], self.data['stations']]
        for dataset in all_data:
            if np.any(np.isnan(dataset)) or np.any(np.isinf(dataset)):
                self.errors.append("❌ NaN ou Inf détectés dans les coordonnées")
                return
        
        print("✓ Pas de NaN ou Inf")
        
        # Vérifier valeurs négatives dans les bonnes colonnes
        depots = self.data['depots']
        garages = self.data['garages']
        stations = self.data['stations']
        
        # Coordonnées >= 0
        if np.all(depots[:, 1:3] >= 0) and np.all(garages[:, 1:3] >= 0) and np.all(stations[:, 1:3] >= 0):
            print("Coordonnées non-négatives")
        else:
            self.warnings.append("Coordonnées négatives détectées")
        
        # Capacités > 0
        vehicles = self.data['vehicles']
        if np.all(vehicles[:, 1] > 0):
            print("✓ Capacités positives")
        else:
            self.errors.append("❌ Capacités non-positives détectées")
    
    def print_report(self):
        """Affiche le rapport final"""
        print("\n" + "="*50)
        print("📊 RAPPORT DE VÉRIFICATION")
        print("="*50)
        
        # Afficher l'UUID si présent
        instance_uuid = self.data.get('uuid')
        if instance_uuid:
            print(f"\n🔑 UUID : {instance_uuid}")
        else:
            print("\n⚠️ UUID : Non trouvé (instance ancienne ou manuelle)")
        
        if self.errors:
            print(f"\n❌ {len(self.errors)} erreur(s) :")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("\n✅ Aucune erreur critique !")
        
        if self.warnings:
            print(f"\n⚠️ {len(self.warnings)} avertissement(s) :")
            for warning in self.warnings:
                print(f"  {warning}")
        
        feasible_status = "✅ FAISABLE" if self.data.get('feasible', False) else "⚠️ À vérifier"
        status = "✅ VALIDE" if len(self.errors) == 0 else "❌ INVALIDE"
        
        print(f"\nStatut : {status}")
        print(f"Faisabilité : {feasible_status}")
        print("="*50 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python instance_verificator.py <filepath>")
        print("Exemple: python instance_verificator.py instances/MPVRP_3_s3_d1_p2.dat")
        return
    
    filepath = sys.argv[1]
    verificator = InstanceVerificator(filepath)
    is_valid = verificator.verify()
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
