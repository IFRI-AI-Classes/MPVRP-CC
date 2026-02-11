import os
import zipfile
import shutil
import json
from sqlalchemy.orm import Session
from backup.database import models_db as models
from backup.core.model.feasibility import verify_solution
from backup.core.model.utils import parse_instance, parse_solution

# Coefficients & penalty
COEFFS = {"small": 1.0, "medium": 0.5, "large": 0.2}
BIG_M = 100000.0  # Penalty for unfeasible instances 
NUMBER_OF_INSTANCES_PER_CATEGORY = 50

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 2. On définit le chemin vers les instances en suivant ta nouvelle arborescence
# Racine -> data -> instances -> category
INSTANCES_ROOT = os.path.join(BASE_DIR, "data", "instances")

def process_full_submission(submission_id: int, zip_path: str, db: Session):
    """
    Traite un fichier ZIP de 150 instances :
    1. Dézippe les solutions de l'utilisateur.
    2. Mappe les noms simplifiés (Sol_M_001) vers les fichiers instances réels du serveur.
    3. Calcule la faisabilité et les coûts (Distance + Change-over).
    4. Applique la pondération et enregistre tout en base de données.
    """
    extract_path = f"temp_extract_{submission_id}"
    
    try:
        #1/ On accède au fichier zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        total_weighted_sum = 0
        fully_feasible = True

        for category, weight in COEFFS.items():
            category_score = 0
            instance_dir = os.path.join(INSTANCES_ROOT, category)
            
            # 2/ Création d'un dictionnaire de mapping pour le serveur :
            # On lie le numéro '001' au nom complexe du fichier de l'instance  'MPVRP_L_001_...'
            instance_mapping = {}
            if os.path.exists(instance_dir):
                for f in os.listdir(instance_dir):
                    if f.startswith("MPVRP_") and (f.endswith(".txt") or f.endswith(".dat")):
                        parts = f.split('_')
                        if len(parts) >= 3:
                            instance_number = parts[2]  # ex: '001' car on aura ["MPVRP", "L","001", etc]
                            instance_mapping[instance_number] = f

            # 3/ Boucle sur les instances de la catégorie (50 dans notre cas)
            for i in range(1, NUMBER_OF_INSTANCES_PER_CATEGORY+1):
                num_str = f"{i:03d}"  # Formatage '001', '002', etc.
                prefix = category[0].upper()   # 'S', 'M', 'L'
                
                # Nom attendu dans le ZIP de l'utilisateur; ex: 'Sol_M_003.dat'
                sol_name = f"Sol_{prefix}_{num_str}.dat"
                
                #Régler les problèmes de casse Small == small
                solutions_dir = os.path.join(extract_path, "Solutions")
                dirs = os.listdir(solutions_dir)
                category_dir = next((d for d in dirs if d.lower() == category.lower()), category)
                
                sol_path = os.path.join(solutions_dir, category_dir, sol_name)

                # Récupération du fichier d'instance correspondant sur le serveur
                inst_filename = instance_mapping.get(num_str)
                inst_path = os.path.join(instance_dir, inst_filename) if inst_filename else None

                # 4/ Vérification de faisabilité 
                errors = []
                metrics = {}
                feasible = False

                if inst_path and os.path.exists(sol_path):
                    try:
                        instance_obj = parse_instance(inst_path)
                        solution_obj = parse_solution(sol_path)
                        
                        # On lance la vérification avec la fonction verify_solution
                        errors, metrics = verify_solution(instance_obj, solution_obj)
                        feasible = (len(errors) == 0)
                    except Exception as e:
                        errors = [f"Erreur technique lors du parsing: {str(e)}"]
                else:
                    # Gestion des fichiers manquants
                    if not inst_filename:
                        errors = [f"Instance officielle {num_str} introuvable sur le serveur."]
                    else:
                        errors = [f"Fichier {sol_name} absent du dossier Solutions/{category}/"]

                # Calcul du score de l'instance 
                if not feasible:
                    instance_score = BIG_M
                    fully_feasible = False
                else:
                    # Somme Distance + Switch Cost (Métriques recalculées par le serveur)
                    instance_score = metrics.get("distance_total", 0) + metrics.get("total_switch_cost", 0)
                
                category_score += instance_score

                # Archivage des résultats détaillés 
                res_detail = models.InstanceResult(
                    submission_id=submission_id,
                    category=category,
                    instance_name=sol_name,
                    is_feasible=feasible,
                    calculated_distance=metrics.get("distance_total", 0),
                    calculated_transition_cost=metrics.get("total_switch_cost", 0),
                    errors_log=json.dumps(errors) # Sérialisation JSON pour le frontend
                )
                db.add(res_detail)

            # Application de la pondération de catégorie
            total_weighted_sum += (category_score * weight)

        # Mise à jour finale de la soumission
        sub = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if sub:
            sub.total_weighted_score = total_weighted_sum / 3  # Score moyen final
            sub.is_fully_feasible = fully_feasible
            db.commit()

    except Exception as fatal_e:
        print(f"CRITICAL ERROR in scoring logic: {str(fatal_e)}")
    
    finally:
        #  Nettoyage (Scalabilité & Espace disque) 
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        if os.path.exists(zip_path):
            os.remove(zip_path)