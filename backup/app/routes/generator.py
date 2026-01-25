import os
import tempfile
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backup.core.generator.instance_provider import generer_instance
from backup.app.schemas import InstanceGenerationRequest

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
            filepath = generer_instance(
                id_inst=request.id_instance,
                nb_v=request.nb_vehicules,
                nb_d=request.nb_depots,
                nb_g=request.nb_garages,
                nb_s=request.nb_stations,
                nb_p=request.nb_produits,
                max_coord=request.max_coord,
                min_capacite=request.min_capacite,
                max_capacite=request.max_capacite,
                min_transition_cost=request.min_transition_cost,
                max_transition_cost=request.max_transition_cost,
                min_demand=request.min_demand,
                max_demand=request.max_demand,
                seed=request.seed,
                force_overwrite=True,  # Toujours écraser dans le dossier temp
                output_dir=temp_dir,
                silent=True  # Mode silencieux pour l'API
            )

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
        return StreamingResponse(
            BytesIO(content),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during generation : {str(e)}")
