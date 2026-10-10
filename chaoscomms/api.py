import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from chaoscomms.aprs import APRSManager, SimulatedAPRS
from chaoscomms.audio import AudioCapture
from chaoscomms.auth import control_authentication_configured, require_control_token
from chaoscomms.config import build_runtime
from chaoscomms.js8call import JS8CallManager, SimulatedJS8Call
from chaoscomms.radio import Radio, RadioManager, SimulatedRadio
from chaoscomms.resources import ResourceManager

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
    resources: ResourceManager | None = None,
) -> FastAPI:
    app = FastAPI(title="ChaosComms", version=SERVICE_VERSION)
    if radio is None and manager is None:
        radio, manager = build_runtime()
    app.state.manager = manager or default_manager()
    app.state.radio = radio or app.state.manager.active_radio()
    app.state.aprs = aprs or APRSManager(SimulatedAPRS())
    app.state.js8call = js8call or JS8CallManager(SimulatedJS8Call())
    app.state.resources = resources or ResourceManager()
    app.state.audio = AudioCapture()
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/settings")
    def settings_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "settings.html")

    @app.get("/api/v1/about")
    def about() -> dict[str, str]:
        return {"service": "ChaosComms", "version": SERVICE_VERSION}

    @app.get("/api/v1/access")
    def access() -> dict[str, object]:
        return {
            "control_authentication": "bearer",
            "control_authentication_configured": control_authentication_configured(),
            "control_enabled": False,
            "receive_only": True,
        }

    @app.get(
        "/api/v1/control/capabilities",
        dependencies=[Depends(require_control_token)],
    )
    def control_capabilities() -> dict[str, object]:
        return {"control_enabled": False, "ptt": False}

    @app.get("/api/v1/radios")
    def radios() -> dict[str, object]:
        return {"radios": app.state.manager.statuses()}

    @app.get("/api/v1/settings")
    def settings() -> dict[str, object]:
        return {
            "runtime_mode": os.getenv("CHAOSCOMMS_MODE", "live").strip().lower(),
            "receive_only": True,
            "ptt": False,
            "radios": app.state.manager.statuses(),
            "audio": app.state.audio.status(),
        }

    @app.post("/api/v1/radios/{radio_id}/select")
    def select_radio(radio_id: str) -> dict[str, object]:
        try:
            app.state.manager.select(radio_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="radio not found") from error
        app.state.radio = app.state.manager.active_radio()
        return {"active_radio_id": app.state.manager.active_radio_id}

    @app.get("/api/v1/aprs")
    def aprs_packets() -> dict[str, object]:
        return {"packets": app.state.aprs.recent_packets(), "transmit_enabled": False}

    @app.get("/api/v1/resources")
    def resources_status() -> dict[str, object]:
        return {
            "resources": app.state.resources.snapshot(),
            "receive_only": app.state.resources.policy.receive_only,
            "transmit_enabled": False,
        }

    @app.get("/api/v1/audio")
    def audio_status() -> dict[str, object]:
        return app.state.audio.status()

    @app.websocket("/api/v1/audio/stream")
    async def audio_stream(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            async for chunk in app.state.audio.chunks():
                await websocket.send_bytes(chunk)
        except WebSocketDisconnect:
            pass
        finally:
            try:
                await websocket.close()
            except RuntimeError:
                pass

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
