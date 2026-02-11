from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backup.database.db import get_db
from backup.database import models_db as models

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register_test")
async def register_test_team(team_name: str, email: str, db: Session = Depends(get_db)):
    """
    Crée une équipe de test rapidement
    """
    # Vérifier si l'équipe existe déjà
    existing_user = db.query(models.User).filter(models.User.team_name == team_name).first()
    if existing_user:
        return {"message": "Équipe déjà existante", "user_id": existing_user.id}

    # Création du nouvel utilisateur
    new_user = models.User(
        team_name=team_name,
        email=email,
        password_hash="test_password"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "Équipe créée avec succès !",
        "user_id": new_user.id,
        "team_name": new_user.team_name
    }