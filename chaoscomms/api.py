from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from chaoscomms.aprs import APRSManager, SimulatedAPRS
from chaoscomms.config import build_runtime
from chaoscomms.js8call import JS8CallManager, SimulatedJS8Call
from chaoscomms.radio import HamlibRadio, Radio, RadioManager, SimulatedRadio

SERVICE_VERSION = "0.1.0"
STATIC_DIR = Path(__file__).parent / "static"


def default_manager() -> RadioManager:
    return RadioManager([
        SimulatedRadio("ft891", "Yaesu FT-891", "transceiver"),
        SimulatedRadio("ft2980r", "Yaesu FT-2980R", "transceiver"),
        SimulatedRadio("vrn7500", "VR-N7500", "transceiver"),
    ])


def create_app(
    radio: Radio | None = None,
    manager: RadioManager | None = None,
    aprs: APRSManager | None = None,
    js8call: JS8CallManager | None = None,
) -> FastAPI:
    app = FastAPI(title="ChaosComms", version=SERVICE_VERSION)
    if radio is None and manager is None:
        radio, manager = build_runtime()
    app.state.radio = radio or HamlibRadio()
    app.state.manager = manager or default_manager()
    app.state.aprs = aprs or APRSManager(SimulatedAPRS())
    app.state.js8call = js8call or JS8CallManager(SimulatedJS8Call())
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/v1/about")
    def about() -> dict[str, str]:
        return {"service": "ChaosComms", "version": SERVICE_VERSION}

    @app.get("/api/v1/radios")
    def radios() -> dict[str, object]:
        return {"radios": app.state.manager.statuses()}

    @app.get("/api/v1/aprs")
    def aprs_packets() -> dict[str, object]:
        return {"packets": app.state.aprs.recent_packets(), "transmit_enabled": False}

    @app.get("/api/v1/js8call")
    def js8call_events() -> dict[str, object]:
        return {"events": app.state.js8call.recent_events(), "transmit_enabled": False}

    @app.get("/api/v1/health")
    def health() -> dict[str, object]:
        status = app.state.radio.status()
        return {
            "status": "ok" if status.connected else "degraded",
            "radio": status.as_dict(),
            "capabilities": {"receive_only": True, "ptt": False},
        }

    return app
