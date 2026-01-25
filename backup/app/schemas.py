from pydantic import BaseModel, Field
from typing import Optional


class InstanceGenerationRequest(BaseModel):
    """Paramètres pour générer une instance MPVRP-CC"""
    id_instance: str = Field(..., description="Identifiant de l'instance (ex: '01')")
    nb_vehicules: int = Field(..., ge=1, description="Nombre de véhicules")
    nb_depots: int = Field(..., ge=1, description="Nombre de dépôts")
    nb_garages: int = Field(..., ge=1, description="Nombre de garages")
    nb_stations: int = Field(..., ge=1, description="Nombre de stations")
    nb_produits: int = Field(..., ge=1, description="Nombre de produits")
    max_coord: float = Field(default=100.0, description="Taille de la grille")
    min_capacite: int = Field(default=10000, description="Capacité minimale des véhicules")
    max_capacite: int = Field(default=25000, description="Capacité maximale des véhicules")
    min_transition_cost: float = Field(default=10.0, description="Coût min changement produit")
    max_transition_cost: float = Field(default=80.0, description="Coût max changement produit")
    min_demand: int = Field(default=500, description="Demande minimale par station/produit")
    max_demand: int = Field(default=5000, description="Demande maximale par station/produit")
    seed: Optional[int] = Field(default=None, description="Graine aléatoire pour reproductibilité")


class InstanceGenerationResponse(BaseModel):
    """Réponse de génération d'instance avec le contenu du fichier"""
    filename: str
    content: str


class SolutionVerificationResponse(BaseModel):
    """Réponse de vérification de solution"""
    feasible: bool
    errors: list[str]
    metrics: dict

