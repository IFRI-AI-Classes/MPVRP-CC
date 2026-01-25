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
    Génère un fichier d'instance MPVRP-CC avec les paramètres spécifiés.

    Les paramètres obligatoires sont:
    - id_instance: Identifiant de l'instance
    - nb_vehicules: Nombre de véhicules
    - nb_depots: Nombre de dépôts
    - nb_garages: Nombre de garages
    - nb_stations: Nombre de stations
    - nb_produits: Nombre de produits

    Retourne directement le fichier d'instance en téléchargement.
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
                    detail="Échec de la génération de l'instance. Vérifiez les paramètres fournis."
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
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")
