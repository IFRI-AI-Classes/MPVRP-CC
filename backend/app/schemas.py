from typing import Optional

from pydantic import BaseModel, Field


class InstanceGenerationRequest(BaseModel):
    """Parameters accepted by the current structured instance generator."""
    instance_code: str = Field(..., min_length=1, description="Public instance identifier")
    nb_vehicules: int = Field(..., ge=1, description="Number of vehicles")
    nb_depots: int = Field(..., ge=1, description="Number of depots")
    nb_garages: int = Field(..., ge=1, description="Number of garages")
    nb_stations: int = Field(..., ge=1, description="Number of stations")
    nb_produits: int = Field(..., ge=1, description="Number of products")
    max_coord: int = Field(default=100, ge=1, description="Integer grid size")
    changeover_cost_level: str = Field(default="normal", pattern="^(low|normal|high|mixed)$")
    capacity_level: str = Field(default="medium", pattern="^(low|medium|large|mixed)$")
    demand_level: str = Field(default="medium", pattern="^(low|medium|high|mixed)$")
    stock_level: str = Field(default="medium", pattern="^(low|medium|high|mixed)$")
    demand_probability: float = Field(default=0.45, gt=0, le=1)
    coordinate_strategy: str = Field(default="clustered", pattern="^(uniform|clustered|corridor)$")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class InstanceGenerationResponse(BaseModel):
    filename: str
    content: str


class SolutionVerificationResponse(BaseModel):
    feasible: bool
    errors: list[str]
    metrics: dict



#SCORING & RESULTS
class InstanceDetail(BaseModel):
    instance: str
    category: str = "with_changeover_costs"
    feasible: bool
    distance: float
    transition_cost: float
    errors: list[str]

class SubmissionResultResponse(BaseModel):
    submission_id: int
    submitted_at: str
    total_score: float
    is_fully_feasible: bool
    total_valid_instances: str
    total_valid_instances_per_category: Optional[str] = None
    is_ready: bool
    processor_info: Optional[str] = None
    instances_details: list[InstanceDetail]

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    rank: int
    team: str
    score: float
    instances_validated: str
    last_submission: Optional[str] = None
