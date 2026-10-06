from fastapi.testclient import TestClient

from chaoscomms.api import create_app
from chaoscomms.config import build_runtime
from chaoscomms.radio import RadioManager, RadioStatus, SimulatedRadio


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


def test_radio_manager_reports_all_three_simulated_radios() -> None:
    manager = RadioManager([
        SimulatedRadio("ft891", "Yaesu FT-891", "transceiver"),
        SimulatedRadio("ft2980r", "Yaesu FT-2980R", "transceiver"),
        SimulatedRadio("vrn7500", "VR-N7500", "transceiver"),
    ])

    payload = manager.statuses()

    assert [radio["id"] for radio in payload] == ["ft891", "ft2980r", "vrn7500"]
    assert all(radio["source"] == "simulator" for radio in payload)
    assert all(radio["capabilities"]["ptt"] is False for radio in payload)

def test_radios_endpoint_exposes_multi_radio_status() -> None:
    manager = RadioManager([
        SimulatedRadio("ft891", "Yaesu FT-891", "transceiver"),
        SimulatedRadio("ft2980r", "Yaesu FT-2980R", "transceiver"),
        SimulatedRadio("vrn7500", "VR-N7500", "transceiver"),
    ])
    client = TestClient(create_app(manager=manager))

    response = client.get("/api/v1/radios")

    assert response.status_code == 200
    assert len(response.json()["radios"]) == 3
    assert response.json()["radios"][2]["model"] == "VR-N7500"


def test_simulator_runtime_uses_simulated_primary_and_fleet() -> None:
    radio, manager = build_runtime("simulator")

    assert isinstance(radio, SimulatedRadio)
    assert [entry["source"] for entry in manager.statuses()] == ["simulator"] * 3


def test_unknown_runtime_mode_is_rejected() -> None:
    try:
        build_runtime("transmit")
    except ValueError as error:
        assert "simulator" in str(error)
        assert "live" in str(error)
    else:
        raise AssertionError("unknown runtime mode was accepted")
