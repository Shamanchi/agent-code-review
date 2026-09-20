"""API-тесты без сети: TestClient."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_review_and_feedback_flow(client: TestClient) -> None:
    code = "def f():\n    print(1)\n"
    resp = client.post("/api/v1/reviews", json={"code": code})
    assert resp.status_code == 200
    rules = {f["rule"] for f in resp.json()["findings"]}
    assert {"print-call", "missing-docstring"} <= rules

    fb = client.post("/api/v1/feedback", json={"rule": "print-call", "accepted": False})
    assert fb.status_code == 200
    assert fb.json()["weight"] == 0.8

    weights = client.get("/api/v1/rules").json()["weights"]
    assert weights["print-call"] == 0.8


def test_review_rejects_non_python(client: TestClient) -> None:
    resp = client.post("/api/v1/reviews", json={"code": "x=1", "language": "go"})
    assert resp.status_code == 422


@pytest.mark.integration()
def test_review_empty_function_shape(client: TestClient) -> None:
    """Интеграционный по маркеру: та же форма ответа, без сети."""
    resp = client.post("/api/v1/reviews", json={"code": 'def ok():\n    """Fine."""\n    return 1\n'})
    assert resp.status_code == 200
    assert resp.json()["summary"]["total"] == 0
