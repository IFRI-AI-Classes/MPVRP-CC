from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import os
import zipfile
import io

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INSTANCES_DIR = os.path.join(BASE_DIR, "data", "instances")

@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/problem")
def problem(request: Request):
    return templates.TemplateResponse("problem.html", {"request": request})

@router.get("/specifications")
def specifications(request: Request):
    return templates.TemplateResponse("specifications.html", {"request": request})

@router.get("/instances")
def instances(request: Request):
    instances_data = []
    if os.path.exists(INSTANCES_DIR):
        files = [f for f in os.listdir(INSTANCES_DIR) if f.endswith('.dat')]
        files.sort()
        for f in files:
            file_path = os.path.join(INSTANCES_DIR, f)
            size_bytes = os.path.getsize(file_path)
            size_str = f"{size_bytes / 1024:.2f} KB" if size_bytes < 1024 * 1024 else f"{size_bytes / (1024 * 1024):.2f} MB"
            instances_data.append({"name": f, "size": size_str})

    return templates.TemplateResponse("instances.html", {
        "request": request,
        "instances": instances_data
    })

@router.get("/download/{filename}")
def download_instance(filename: str):
    file_path = os.path.join(INSTANCES_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

@router.get("/download-all")
def download_all_instances():
    """Télécharger toutes les instances sous format ZIP"""
    if not os.path.exists(INSTANCES_DIR):
        raise HTTPException(status_code=404, detail="Instances directory not found")

    files = [f for f in os.listdir(INSTANCES_DIR) if f.endswith('.dat')]
    if not files:
        raise HTTPException(status_code=404, detail="No instances available")

    # Créer un fichier ZIP en mémoire
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in files:
            file_path = os.path.join(INSTANCES_DIR, filename)
            zip_file.write(file_path, arcname=filename)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=MPVRP-CC_instances.zip"
        }
    )

