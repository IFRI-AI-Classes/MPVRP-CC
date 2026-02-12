from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backup.database.db import get_db
from backup.database import models_db as models
from backup.app.schemas import LeaderboardEntry

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/", response_model=list[LeaderboardEntry])
async def get_global_leaderboard(db: Session = Depends(get_db)):
    """
    Returns the official leaderboard and displays the best attempt for each team.
    """
    # Sous-requête pour identifier le score minimal par utilisateur
    subquery = (
        db.query(
            models.Submission.user_id,
            func.min(models.Submission.total_weighted_score).label("min_score")
        )
        .group_by(models.Submission.user_id)
        .subquery()
    )

    # On récupère les infos complètes de la meilleure soumission (équipe, le score et le compteur d'instances validées)
    # par jointure de tables
    query = (
        db.query(
            models.User.team_name,
            models.Submission.total_weighted_score,
            models.Submission.total_feasible_count,
            models.Submission.submitted_at
        )
        .join(subquery, (models.Submission.user_id == subquery.c.user_id) & 
                        (models.Submission.total_weighted_score == subquery.c.min_score))
        .join(models.User, models.User.id == models.Submission.user_id)
        .order_by(models.Submission.total_weighted_score.asc())
        .all()
    )

    #Formatage de la réponse
    leaderboard = []
    for i, row in enumerate(query):
        leaderboard.append({
            "rank": i + 1,
            "team": row.team_name,
            "score": round(row.total_weighted_score, 2),
            "instances_validated": f"{row.total_feasible_count}/150",
            "last_submission": row.submitted_at
        })

    return leaderboard