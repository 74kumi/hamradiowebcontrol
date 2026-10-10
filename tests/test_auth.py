import pytest
from fastapi.testclient import TestClient

from chaoscomms.api import create_app
from chaoscomms.radio import RadioStatus


class FakeRadio:
    def status(self) -> RadioStatus:
        return RadioStatus(False, "FT-891", None, None, False, "unavailable")


def test_control_endpoint_requires_configured_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOSCOMMS_API_TOKEN", "test-token")
    client = TestClient(create_app(radio=FakeRadio()))

    response = client.get("/api/v1/control/capabilities")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_control_endpoint_accepts_matching_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOSCOMMS_API_TOKEN", "test-token")
    client = TestClient(create_app(radio=FakeRadio()))

    response = client.get(
        "/api/v1/control/capabilities",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"control_enabled": False, "ptt": False}


def test_control_endpoint_fails_closed_when_token_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CHAOSCOMMS_API_TOKEN", raising=False)
    client = TestClient(create_app(radio=FakeRadio()))

    response = client.get(
        "/api/v1/control/capabilities",
        headers={"Authorization": "Bearer anything"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "control authentication is not configured"


def test_access_endpoint_does_not_disclose_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOSCOMMS_API_TOKEN", "test-token")
    client = TestClient(create_app(radio=FakeRadio()))

    response = client.get("/api/v1/access")

    assert response.status_code == 200
    assert response.json() == {
        "control_authentication": "bearer",
        "control_authentication_configured": True,
        "control_enabled": False,
        "receive_only": True,
    }
    assert "test-token" not in response.text


def test_settings_mutation_fails_closed_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOSCOMMS_MODE", "simulator")
    monkeypatch.delenv("CHAOSCOMMS_API_TOKEN", raising=False)
    client = TestClient(create_app(radio=FakeRadio(), web_auth_required=True))

    response = client.post("/api/v1/radios", json={"id": "new", "model": "New radio"})

    assert response.status_code == 401
    assert response.json()["detail"] == "login required"
