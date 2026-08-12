import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes import generator, model, scoring, scoreboard

load_dotenv()

FRONTEND_DEV_URL = os.getenv("FRONTEND_DEV_URL", "")
FRONTEND_PROD_URL = os.getenv("FRONTEND_PROD_URL", "")
FRONTEND_PROD_URL_2 = os.getenv("FRONTEND_PROD_URL_2", "")
CORS_ALLOW_LOCALHOST = os.getenv("CORS_ALLOW_LOCALHOST", "true").lower() in {"1", "true", "yes"}

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


ALLOWED_ORIGINS = [origin for origin in (FRONTEND_PROD_URL, FRONTEND_PROD_URL_2, FRONTEND_DEV_URL) if origin]
CORS_ORIGIN_REGEX = r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?" if CORS_ALLOW_LOCALHOST else None
logger.info("CORS allow-list configured with %s origin(s)", len(ALLOWED_ORIGINS))


app = FastAPI(
    title="MPVRP-CC API",
    description="API for generating instances and verifying solutions to the MPVRP-CC problem (Multi-Product Vehicle Routing Problem with Changeover Cost)",
    version="1.0.0",
)

# Allow configured frontends and, by default, local static servers used in development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Inclure les routes
app.include_router(generator.router)
app.include_router(model.router)
app.include_router(scoring.router)
app.include_router(scoreboard.router)

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


@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"], include_in_schema=False)
async def health_check():
    """Vérifie l'état de santé de l'API"""
    return {"status": "healthy"}
