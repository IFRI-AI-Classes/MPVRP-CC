import uuid
import shutil
import os
import json
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from backup.database.db import get_db
from backup.database import models_db as models
from backup.core.scoring.score_evaluation import process_full_submission
from backup.core.auth.auth_logic import get_current_user
from backup.app.schemas import SubmissionResultResponse, TeamHistoryResponse

router = APIRouter(prefix="/scoring", tags=["Scoring"])

@router.post("/submit/{user_id}")
async def submit_solutions_endpoint(
    user_id: int, 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """
    Endpoint pour soumettre l'archive ZIP des 150 solutions.
    
    1. Vérifie si l'utilisateur existe.
    2. Sauvegarde le fichier ZIP temporairement sur le serveur.
    3. Crée une entrée 'Submission' en base de données.
    4. Lance le calcul lourd en tâche de fond (BackgroundTasks).
    """
    
    # Vérifier que l'utilisateur existe
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur/Équipe non trouvé.e")

    # Valider le format de fichier
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .zip sont acceptés")

    # On utilise un UUID pour éviter que deux uploads simultanés ne se chevauchent et on sauvegarde le fichier
    unique_filename = f"upload_{uuid.uuid4()}.zip"
    temp_path = os.path.join("temp", unique_filename)
    
    # Créer le dossier temp s'il n'existe pas
    os.makedirs("temp", exist_ok=True)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer) #Ecriture par morceaux (chunks) pour ne pas surcharger la mémoire
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde : {str(e)}")

    # Enregistrement de soumission
    # Le score est initialisé à 0.0 et sera mis à jour par la tâche de fond
    new_submission = models.Submission(
        user_id=user_id, 
        total_weighted_score=0.0,
        is_fully_feasible=False
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    # Processus de traitement asynchrone
    # Le serveur travaille sur les 150 instances en arrière-plan et l'user peut faire autre chose
    background_tasks.add_task(process_full_submission, new_submission.id, temp_path, db)

    return {
        "status": "Accepted",
        "submission_id": new_submission.id,
        "team": user.team_name,
        "message": "Le calcul de votre score a débuté. Les résultats seront bientôt disponibles sur le leaderboard."
    }

#Recupération des details du traitement de la soumission
@router.get("/result/{submission_id}", response_model=SubmissionResultResponse)
async def get_submission_result(
    submission_id: int, 
    db: Session = Depends(get_db)
):
    """
    Récupère le résultat détaillé d'une soumission :
    - Score global
    - Statut de faisabilité
    - Détail par instance (avec les logs d'erreurs)
    """
    
    # On cherche la soumission
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")

    # On récupère toutes les instances liées à cette soumission
    results = db.query(models.InstanceResult).filter(
        models.InstanceResult.submission_id == submission_id
    ).all()

    # On prépare une réponse structurée (JSON -> Python Object) qu'on va return
    detailed_results = []
    for r in results:
        detailed_results.append({
            "instance": r.instance_name,
            "category": r.category,
            "feasible": r.is_feasible,
            "distance": r.calculated_distance,
            "transition_cost": r.calculated_transition_cost,
            "errors": json.loads(r.errors_log) if r.errors_log else []
        })

    return {
        "submission_id": submission.id,
        "submitted_at": submission.submitted_at,
        "total_score": submission.total_weighted_score,
        "is_fully_feasible": submission.is_fully_feasible,
        'total_valid_instances': f'{submission.total_feasible_count}/150',
        'total_valid_instances_per_category': submission.category_stats,
        "instances_details": detailed_results
    }

@router.get("/history/{user_id}", response_model=TeamHistoryResponse)
async def get_user_submission_history(
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Retrieves the complete submission history for a specific user/team.

    Returns a list of all past submissions with their global scores, 
    feasibility status, and the number of validated instances.
    """
    
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Récupérer toutes les soumissions de cet utilisateur, de la plus récente à la plus ancienne
    submissions = (
        db.query(models.Submission)
        .filter(models.Submission.user_id == current_user.id)
        .order_by(models.Submission.submitted_at.desc())
        .all()
    )

    history = []
    for sub in submissions:
        history.append({
            "submission_id": sub.id,
            "submitted_at": sub.submitted_at,
            "score": round(sub.total_weighted_score, 2),
            "valid_instances": f"{sub.total_feasible_count}/150",
            "is_fully_feasible": sub.is_fully_feasible
        })

    return {
        "team_name": user.team_name,
        "total_submissions": len(history),
        "history": history
    }