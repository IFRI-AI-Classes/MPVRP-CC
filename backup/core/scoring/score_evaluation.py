import os
import zipfile
import shutil
import json

from sqlalchemy.orm import Session

from backup.database import models_db as models
from backup.core.model.feasibility import verify_solution
from backup.core.model.utils import parse_instance, parse_solution

COEFFS = {"small": 1.0, "medium": 0.5, "large": 0.2}
BIG_M  = 100000.0
NUMBER_OF_INSTANCES_PER_CATEGORY = 50

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
INSTANCES_ROOT = os.path.join(BASE_DIR, "data", "instances")

# Nouvelles fonctions pour gérer les erreurs
def _mark_submission_failed(submission_id: int, reason: str, db: Session):
    """
    Erreur fatale (ZIP illisible, dossier Solutions/ absent...) :
    score pénalisé pour que is_ready devienne True côté frontend
    et que l'équipe voie un message d'erreur plutôt qu'un spinner infini.
    """
    try:
        sub = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if sub:
            sub.total_weighted_score = BIG_M * 150
            sub.is_fully_feasible    = False
            sub.total_feasible_count = 0
            sub.category_stats       = json.dumps({"small": 0, "medium": 0, "large": 0})
            sub.processor_info       = reason
            db.commit()
    except Exception as e:
        print(f"[WORKER {submission_id}] Impossible de marquer l'échec : {e}")


def _validate_zip_structure(solutions_root: str) -> dict:
    """
    Pré-check de la structure du ZIP après extraction.
    Retourne un rapport avec :
      - ok        : bool — True si tout est conforme
      - warnings  : list[str] — anomalies non bloquantes
      - errors    : list[str] — anomalies bloquantes par catégorie
      - by_category : dict — état détaillé par catégorie
    """
    report = {
        "ok": True,
        "warnings": [],
        "errors": [],
        "by_category": {}
    }

    prefix_map = {"small": "S", "medium": "M", "large": "L"}

    for category, prefix in prefix_map.items():
        cat_report = {"present": False, "dat_count": 0, "missing": [], "unexpected": []}

        # Résolution insensible à la casse
        dirs     = os.listdir(solutions_root)
        cat_dir  = next((d for d in dirs if d.lower() == category.lower()), None)

        if cat_dir is None:
            cat_report["present"] = False
            report["errors"].append(
                f"Dossier Solutions/{category.capitalize()}/ absent — "
                f"les 50 instances {category} recevront la pénalité maximale."
            )
            report["ok"] = False
        else:
            cat_report["present"] = True
            cat_path = os.path.join(solutions_root, cat_dir)
            dat_files = [f for f in os.listdir(cat_path) if f.endswith(".dat")]
            cat_report["dat_count"] = len(dat_files)

            # Fichiers attendus : Sol_S_001.dat … Sol_S_050.dat
            expected = {f"Sol_{prefix}_{i:03d}.dat" for i in range(1, NUMBER_OF_INSTANCES_PER_CATEGORY + 1)}
            found    = set(dat_files)

            missing    = sorted(expected - found)
            unexpected = sorted(found - expected)

            cat_report["missing"]    = missing
            cat_report["unexpected"] = unexpected

            if len(dat_files) != NUMBER_OF_INSTANCES_PER_CATEGORY:
                msg = (
                    f"Solutions/{category.capitalize()}/ : "
                    f"{len(dat_files)} fichier(s) .dat trouvé(s) sur {NUMBER_OF_INSTANCES_PER_CATEGORY} attendus."
                )
                if missing:
                    msg += f" Manquants : {', '.join(missing[:5])}"
                    if len(missing) > 5:
                        msg += f" … (+{len(missing) - 5})"
                report["warnings"].append(msg)
                # Avertissement non bloquant

        report["by_category"][category] = cat_report

    return report


def _format_processor_info(report: dict) -> str:
    """Sérialise le rapport de structure en string lisible pour processor_info."""
    lines = ["=== Rapport de structure du ZIP ==="]

    if report["ok"] and not report["warnings"]:
        lines.append("Structure conforme — 3 catégories présentes, 50 fichiers chacune.")
        return "\n".join(lines)

    if report["errors"]:
        lines.append("\n⛔ ERREURS BLOQUANTES :")
        for e in report["errors"]:
            lines.append(f"  • {e}")

    if report["warnings"]:
        lines.append("\n⚠️  AVERTISSEMENTS :")
        for w in report["warnings"]:
            lines.append(f"  • {w}")

    lines.append("\n--- Détail par catégorie ---")
    for cat, info in report["by_category"].items():
        status = "✅" if info["present"] and info["dat_count"] == NUMBER_OF_INSTANCES_PER_CATEGORY else "❌"
        lines.append(f"  {status} {cat.capitalize()} : {info['dat_count']}/{NUMBER_OF_INSTANCES_PER_CATEGORY} fichiers")

    return "\n".join(lines)


def process_full_submission(submission_id: int, zip_path: str, db: Session):
    extract_path = f"temp_extract_{submission_id}"
    total_valid_instances = 0
    results_per_category  = {"small": 0, "medium": 0, "large": 0}

    try:
        # Vérification existence du ZIP 
        if not os.path.exists(zip_path):
            _mark_submission_failed(submission_id, f"Fichier ZIP introuvable : {zip_path}", db)
            return

        # Extraction
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        except zipfile.BadZipFile:
            _mark_submission_failed(submission_id, "Le fichier soumis n'est pas un ZIP valide.", db)
            return
        except Exception as e:
            _mark_submission_failed(submission_id, f"Erreur lors de l'extraction : {e}", db)
            return

        #Vérification dossier Solutions/ 
        solutions_root = os.path.join(extract_path, "Solutions")
        if not os.path.exists(solutions_root):
            _mark_submission_failed(
                submission_id,
                "Structure invalide : le dossier 'Solutions/' est absent du ZIP.\n"
                "Structure attendue : Solutions/Small/, Solutions/Medium/, Solutions/Large/",
                db
            )
            return

        # Pré-check structure détaillé
        structure_report = _validate_zip_structure(solutions_root)
        processor_info   = _format_processor_info(structure_report)

        # On met à jour processor_info dès maintenant (avant la boucle)
        sub = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if sub:
            sub.processor_info = processor_info
            db.commit()

        # Boucle d'évaluation 
        total_weighted_sum = 0
        fully_feasible     = True

        for category, weight in COEFFS.items():
            category_score = 0
            instance_dir   = os.path.join(INSTANCES_ROOT, category)
            cat_info       = structure_report["by_category"].get(category, {})

            instance_mapping = {}
            if os.path.exists(instance_dir):
                for f in os.listdir(instance_dir):
                    if f.startswith("MPVRP_") and (f.endswith(".txt") or f.endswith(".dat")):
                        parts = f.split('_')
                        if len(parts) >= 3:
                            instance_mapping[parts[2]] = f

            dirs         = os.listdir(solutions_root)
            category_dir = next((d for d in dirs if d.lower() == category.lower()), None)

            for i in range(1, NUMBER_OF_INSTANCES_PER_CATEGORY + 1):
                num_str   = f"{i:03d}"
                prefix    = category[0].upper()
                sol_name  = f"Sol_{prefix}_{num_str}.dat"
                errors    = []
                metrics   = {}
                feasible  = False

                if not cat_info.get("present", False):
                    # Erreur déjà signalée dans processor_info
                    errors = [f"Catégorie {category} absente du ZIP (voir rapport de structure)."]

                else:
                    sol_path      = os.path.join(solutions_root, category_dir, sol_name)
                    inst_filename = instance_mapping.get(num_str)
                    inst_path     = os.path.join(instance_dir, inst_filename) if inst_filename else None

                    if not inst_filename:
                        errors = [f"Instance officielle {num_str} introuvable sur le serveur."]
                    elif not os.path.exists(sol_path):
                        errors = [f"Fichier {sol_name} absent de Solutions/{category}/."]
                    else:
                        try:
                            instance_obj = parse_instance(inst_path)
                            solution_obj = parse_solution(sol_path)
                            errors, metrics = verify_solution(instance_obj, solution_obj)
                            feasible = (len(errors) == 0)
                            if feasible:
                                total_valid_instances += 1
                                results_per_category[category] += 1
                        except Exception as e:
                            errors = [f"Erreur technique lors du parsing : {e}"]

                instance_score = (
                    metrics.get("distance_total", 0) + metrics.get("total_switch_cost", 0)
                    if feasible else BIG_M
                )
                if not feasible:
                    fully_feasible = False

                category_score += instance_score

                db.add(models.InstanceResult(
                    submission_id              = submission_id,
                    category                   = category,
                    instance_name              = sol_name,
                    is_feasible                = feasible,
                    calculated_distance        = metrics.get("distance_total", 0),
                    calculated_transition_cost = metrics.get("total_switch_cost", 0),
                    errors_log                 = json.dumps(errors)
                ))

            total_weighted_sum += category_score * weight

        #Mise à jour finale
        sub = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if sub:
            sub.total_weighted_score = total_weighted_sum / 3
            sub.is_fully_feasible    = fully_feasible
            sub.total_feasible_count = total_valid_instances
            sub.category_stats       = json.dumps(results_per_category)
            db.commit()

    except Exception as fatal_e:
        _mark_submission_failed(submission_id, f"Erreur inattendue : {fatal_e}", db)

    finally:
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        if os.path.exists(zip_path):
            os.remove(zip_path)