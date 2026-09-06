import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_current(client):
    r = client.get("/api/current")
    assert r.status_code == 200
    body = r.json()
    assert "solar_kw" in body
    assert "battery_soc_pct" in body


def test_history_respects_hours_param(client):
    r = client.get("/api/history", params={"hours": 24})
    assert r.status_code == 200
    assert len(r.json()["readings"]) == 24


def test_forecast(client):
    r = client.get("/api/forecast", params={"horizon": 6})
    assert r.status_code == 200
    body = r.json()
    assert len(body["timestamps"]) == 6


def test_recommendation(client):
    r = client.get("/api/recommendation")
    assert r.status_code == 200
    body = r.json()
    assert body["action"] in {"CHARGE", "DISCHARGE", "CURTAIL", "EXPORT", "HOLD"}
