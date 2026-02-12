from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class InstanceGenerationRequest(BaseModel):
    """Parameters for generating an MPVRP-CC instance"""
    id_instance: str = Field(..., description="Instance identifier (e.g., '01')")
    nb_vehicules: int = Field(..., ge=1, description="Number of vehicles")
    nb_depots: int = Field(..., ge=1, description="Number of depots")
    nb_garages: int = Field(..., ge=1, description="Number of garages")
    nb_stations: int = Field(..., ge=1, description="Number of stations")
    nb_produits: int = Field(..., ge=1, description="Number of products")
    max_coord: float = Field(default=100.0, description="Grid size")
    min_capacite: int = Field(default=10000, description="Minimum vehicle capacity")
    max_capacite: int = Field(default=25000, description="Maximum vehicle capacity")
    min_transition_cost: float = Field(default=10.0, description="Minimum product changeover cost")
    max_transition_cost: float = Field(default=80.0, description="Maximum product changeover cost")
    min_demand: int = Field(default=500, description="Minimum demand per station/product")
    max_demand: int = Field(default=5000, description="Maximum demand per station/product")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class InstanceGenerationResponse(BaseModel):
    """Réponse de génération d'instance avec le contenu du fichier"""
    filename: str
    content: str


class SolutionVerificationResponse(BaseModel):
    """Réponse de vérification de solution"""
    feasible: bool
    errors: list[str]
    metrics: dict

class UserBase(BaseModel):
    team_name: str
    email: EmailStr

class UserCreate(UserBase):
    """Schema pour la création d'équipe."""
    password: str

class UserResponse(UserBase):
    """Retourner les infos de l'utilisateur sans le password."""
    id: int
    class Config:
        from_attributes = True


#SCHÉMAS SCORING & RESULTS
class InstanceDetail(BaseModel):
    """Details d'une unique instance soumise."""
    instance: str
    category: str
    feasible: bool
    distance: float
    transition_cost: float
    errors: list[str]

class SubmissionResultResponse(BaseModel):
    """Détails complets des 150 instances d'une soumission."""
    submission_id: int
    submitted_at: datetime
    total_score: float
    is_fully_feasible: bool
    instances_details: list[InstanceDetail]

    class Config:
        from_attributes = True


# SCHÉMAS HISTORIQUE & LEADERBOARD
class HistoryEntry(BaseModel):
    """Résumé des soumissions passées"""
    submission_id: int
    submitted_at: datetime
    score: float
    valid_instances: str
    is_fully_feasible: bool

class TeamHistoryResponse(BaseModel):
    """Réponse de l'API pour l'historique complet d'une équipe."""
    team_name: str
    total_submissions: int
    history: list[HistoryEntry]

class LeaderboardEntry(BaseModel):
    """Entrée pour le leaderboard."""
    rank: int
    team: str
    score: float
    instances_validated: str


#SCHÉMAS JWT(Json Web Token)
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None