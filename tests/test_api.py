from fastapi.testclient import TestClient

from chaoscomms.api import create_app
from chaoscomms.radio import RadioStatus


class FakeRadio:
    def status(self) -> RadioStatus:
        return RadioStatus(
            connected=False,
            model="FT-891",
            frequency_hz=None,
            mode=None,
            ptt_enabled=False,
            error="rigctld unavailable",
        )


def test_health_reports_receive_only_capabilities() -> None:
    client = TestClient(create_app(radio=FakeRadio()))

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "radio": {
            "connected": False,
            "model": "FT-891",
            "frequency_hz": None,
            "mode": None,
            "ptt_enabled": False,
            "error": "rigctld unavailable",
        },
        "capabilities": {"receive_only": True, "ptt": False},
    }


def test_root_serves_mobile_dashboard() -> None:
    client = TestClient(create_app(radio=FakeRadio()))

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "ChaosComms" in response.text
    assert "PTT disabled" in response.text


def test_api_metadata_is_available() -> None:
    client = TestClient(create_app(radio=FakeRadio()))

    response = client.get("/api/v1/about")

    assert response.status_code == 200
    assert response.json() == {"service": "ChaosComms", "version": "0.1.0"}
