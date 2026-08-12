import io

import httpx
import pytest

from backend.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_scoring_rejects_non_zip():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/scoring/submit",
            data={"email": "team@example.com"},
            files={"file": ("solutions.txt", io.BytesIO(b"invalid"), "text/plain")},
        )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_scoring_formats_service_result(monkeypatch):
    import backend.app.routes.scoring as route

    monkeypatch.setattr(route, "DATA_SOURCE_ID", None)
    monkeypatch.setattr(route, "process_full_submission", lambda _: {
        "ok": True,
        "total_weighted_score": 12.25,
        "is_fully_feasible": False,
        "total_feasible_count": 1,
        "category_stats": {"with_changeover_costs": 1},
        "processor_info": "ok",
        "instance_results": [{
            "instance": "Sol_MPVRP_001.dat", "category": "with_changeover_costs",
            "feasible": True, "distance": 10, "transition_cost": 2.25, "errors": [],
        }],
    })
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/scoring/submit",
            data={"email": "team@example.com", "name": "Team"},
            files={"file": ("solutions.zip", io.BytesIO(b"placeholder"), "application/zip")},
        )
    assert response.status_code == 200
    assert response.json()["total_valid_instances"] == "1/150"
