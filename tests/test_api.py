import io

import httpx
import pytest
from pydantic import ValidationError

from backend.app.main import app
from backend.app.schemas import InstanceGenerationRequest


pytestmark = [pytest.mark.api, pytest.mark.integration]


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def api_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def test_generation_schema_matches_current_generator():
    request = InstanceGenerationRequest(
        instance_code="DEMO", nb_vehicules=3, nb_depots=2, nb_garages=1,
        nb_stations=5, nb_produits=2, changeover_cost_level="mixed",
    )
    assert request.capacity_level == "medium"
    assert request.changeover_cost_level == "mixed"
    with pytest.raises(ValidationError):
        InstanceGenerationRequest(
            instance_code="DEMO", nb_vehicules=0, nb_depots=1, nb_garages=1,
            nb_stations=1, nb_produits=1,
        )


@pytest.mark.anyio
async def test_root_health_and_openapi(api_client):
    assert (await api_client.get("/")).status_code == 200
    assert (await api_client.get("/health")).json() == {"status": "healthy"}
    schema = (await api_client.get("/openapi.json")).json()
    assert "/generator/generate" in schema["paths"]
    assert "/model/verify" in schema["paths"]


@pytest.mark.anyio
async def test_generator_returns_download(api_client):
    response = await api_client.post("/generator/generate", json={
        "instance_code": "API", "nb_vehicules": 3, "nb_depots": 2,
        "nb_garages": 1, "nb_stations": 5, "nb_produits": 2, "seed": 42,
    })
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"# ")


@pytest.mark.anyio
async def test_generator_rejects_old_or_invalid_payload(api_client):
    response = await api_client.post("/generator/generate", json={"id_instance": "OLD"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_verifier_requires_both_files(api_client):
    assert (await api_client.post("/model/verify")).status_code == 422


def test_app_configuration():
    assert app.title == "MPVRP-CC API"
    assert app.version == "1.0.0"
    assert app.user_middleware


def test_extract_notion_date():
    from backend.database.notion import _extract_value
    assert _extract_value({"type": "date", "date": {"start": "2026-01-01"}}) == "2026-01-01"


@pytest.mark.anyio
async def test_scoreboard_normalizes_notion_payload(api_client, monkeypatch):
    import backend.app.routes.scoreboard as route
    monkeypatch.setattr(route, "DATA_SOURCE_ID", "test")
    monkeypatch.setattr(route, "get_all_entries", lambda _: [{"properties": {
        "Rank": {"type": "number", "number": 1},
        "Name": {"type": "title", "title": [{"plain_text": "Team"}]},
        "Score": {"type": "number", "number": 42},
        "Feasible solutions": {"type": "number", "number": 150},
        "Submission date": {"type": "date", "date": {"start": "2026-01-01"}},
    }}])
    response = await api_client.get("/scoreboard")
    assert response.status_code == 200
    assert response.json()[0]["team"] == "Team"
