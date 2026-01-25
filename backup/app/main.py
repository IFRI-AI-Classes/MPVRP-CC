from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backup.app.routes import generator, model

app = FastAPI(
    title="MPVRP-CC API",
    description="API for generating instances and verifying solutions to the MPVRP-CC problem (Multi-Product Vehicle Routing Problem with Changeover Cost)",
    version="1.0.0"
)

# Configuration CORS pour permettre les appels depuis n'importe quelle origine
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes
app.include_router(generator.router)
app.include_router(model.router)


@app.api_route("/", methods=["GET", "HEAD"], tags=["Root"])
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "Bienvenue sur l'API MPVRP-CC",
        "documentation": "/docs",
        "endpoints": {
            "generator": "/generator/generate - POST: Génère une instance MPVRP-CC",
            "model": "/model/verify - POST: Vérifie une solution pour une instance"
        }
    }


@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
async def health_check():
    """Vérifie l'état de santé de l'API"""
    return {"status": "healthy"}

