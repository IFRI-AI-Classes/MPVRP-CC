import numpy as np
import os
import sys

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
        
        # 3. Vérifications de validité
        self.check_validity()
        
        # 4. Vérifications de faisabilité
        self.check_feasibility()
        
        # 5. Vérifications géométriques
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
                lines = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')]
            
            if len(lines) < 6:
                self.errors.append("❌ Fichier mal formaté : pas assez de sections")
                return False
            
            # Parsing
            params = np.array([int(x) for x in lines[0].split()])
            nb_v, nb_d, nb_g, nb_s, nb_p = params
            
            self.data['params'] = params
            self.data['nb_v'] = nb_v
            self.data['nb_d'] = nb_d
            self.data['nb_g'] = nb_g
            self.data['nb_s'] = nb_s
            self.data['nb_p'] = nb_p
            
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
    
    def check_validity(self):
        """Vérifie la validité des données"""
        print("\n Vérifications de validité :")
        
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
        
        if self.errors:
            print(f"\n❌ {len(self.errors)} erreur(s) :")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("\n✅ Aucune erreur critique !")
        
        if self.warnings:
            print(f"\n️ {len(self.warnings)} avertissement(s) :")
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
