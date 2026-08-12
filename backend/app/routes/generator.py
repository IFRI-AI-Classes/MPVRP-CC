import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.core.generation.config import GenerationConfig
from backend.core.generation.instance_generator import generate
from backend.app.schemas import InstanceGenerationRequest

router = APIRouter(prefix="/generator", tags=["Generator"])


@router.post("/generate")
async def generate_instance(request: InstanceGenerationRequest):
    """
    Generates an MPVRP-CC instance file with the specified parameters.

    The required parameters are:

    - id_instance: Instance identifier
    - nb_vehicules: Number of vehicles
    - nb_depots: Number of depots
    - nb_garages: Number of garages
    - nb_stations: Number of stations
    - nb_produits: Number of products

    Returns the instance file directly for download.
    """
    try:
        # Créer un dossier temporaire pour la génération
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GenerationConfig(
                instance_code=request.instance_code,
                vehicles=request.nb_vehicules,
                depots=request.nb_depots,
                garages=request.nb_garages,
                stations=request.nb_stations,
                products=request.nb_produits,
                output_dir=Path(temp_dir),
                grid_size=request.max_coord,
                changeover_cost_level=request.changeover_cost_level,
                capacity_level=request.capacity_level,
                demand_level=request.demand_level,
                stock_level=request.stock_level,
                demand_probability=request.demand_probability,
                coordinate_strategy=request.coordinate_strategy,
                seed=request.seed,
                force=True,
            )
            filepath = generate(config)

            if filepath is None:
                raise HTTPException(
                    status_code=400,
                    detail="Instances parameters are invalid or generation failed."
                )

            filename = os.path.basename(filepath)

            # Lire le contenu du fichier généré
            with open(filepath, 'rb') as f:
                content = f.read()

        # Retourner le fichier en téléchargement
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during generation : {str(e)}")
