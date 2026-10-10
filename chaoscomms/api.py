import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from chaoscomms.aprs import APRSManager, SimulatedAPRS
from chaoscomms.audio import AudioCapture
from chaoscomms.auth import control_authentication_configured, require_control_token
from chaoscomms.config import build_runtime
from chaoscomms.devices import inventory, is_safe_mapping_path
from chaoscomms.js8call import JS8CallManager, SimulatedJS8Call
from chaoscomms.radio import Radio, RadioManager, SimulatedRadio
from chaoscomms.resources import ResourceManager
from chaoscomms.state import load_state, save_state
from chaoscomms.web_auth import verify_password, web_password_configured, web_username

SERVICE_VERSION = "0.1.0"
STATIC_DIR = Path(__file__).parent / "static"
WEB_PUBLIC_PATHS = {"/login", "/api/v1/login"}


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
    web_auth_required: bool = False,
    state_path: Path | None = None,
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
    app.state.runtime_mode = os.getenv("CHAOSCOMMS_MODE", "live").strip().lower()
    app.state.state_path = state_path or (
        Path(os.environ.get("CHAOSCOMMS_STATE_FILE", "/var/lib/chaoscomms/settings.json"))
        if web_auth_required
        else None
    )
    if app.state.state_path is not None:
        persisted = load_state(app.state.state_path)
        if app.state.runtime_mode != "simulator":
            persisted = {**persisted, "simulator_radios": []}
        app.state.manager.restore(persisted)
    app.state.web_auth_required = web_auth_required

    @app.middleware("http")
    async def web_authentication(request: Request, call_next):
        if not app.state.web_auth_required or request.url.path.startswith("/static/"):
            return await call_next(request)
        if request.url.path in WEB_PUBLIC_PATHS:
            return await call_next(request)
        if request.session.get("authenticated") is not True:
            if request.url.path.startswith("/api/"):
                return JSONResponse({"detail": "login required"}, status_code=401)
            return RedirectResponse("/login")
        return await call_next(request)

    app.add_middleware(
        SessionMiddleware,
        secret_key=os.environ.get("CHAOSCOMMS_SESSION_SECRET", "test-only-session-secret"),
        https_only=web_auth_required,
        same_site="strict",
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    def persist_settings() -> None:
        if app.state.state_path is not None:
            save_state(app.state.state_path, app.state.manager.persistent_state())

    @app.get("/login")
    def login_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "login.html")

    @app.post("/api/v1/login")
    async def login(request: Request) -> JSONResponse:
        payload = await request.json()
        if (
            web_password_configured()
            and payload.get("username") == web_username()
            and verify_password(
                str(payload.get("password", "")),
                os.environ.get("CHAOSCOMMS_WEB_PASSWORD_HASH"),
            )
        ):
            request.session["authenticated"] = True
            return JSONResponse({"authenticated": True})
        return JSONResponse({"detail": "invalid credentials"}, status_code=401)

    @app.post("/api/v1/logout")
    async def logout(request: Request) -> JSONResponse:
        request.session.clear()
        return JSONResponse({"authenticated": False})

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

    @app.get("/api/v1/devices")
    def devices() -> dict[str, object]:
        return inventory()

    @app.post("/api/v1/radios")
    def add_radio(payload: dict[str, object]) -> dict[str, object]:
        if app.state.runtime_mode != "simulator":
            raise HTTPException(status_code=409, detail="radio changes require simulator mode")
        radio_id = str(payload.get("id", "")).strip()
        model = str(payload.get("model", "")).strip()
        if not radio_id or not model or "/" in radio_id:
            raise HTTPException(status_code=400, detail="id and model are required")
        try:
            app.state.manager.add_simulator(radio_id, model)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        persist_settings()
        return {"radios": app.state.manager.statuses(), "receive_only": True, "ptt": False}

    @app.delete("/api/v1/radios/{radio_id}")
    def remove_radio(radio_id: str) -> dict[str, object]:
        if app.state.runtime_mode != "simulator":
            raise HTTPException(status_code=409, detail="radio changes require simulator mode")
        try:
            app.state.manager.remove(radio_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="radio not found") from error
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        app.state.radio = app.state.manager.active_radio()
        persist_settings()
        return {"radios": app.state.manager.statuses(), "receive_only": True, "ptt": False}

    @app.post("/api/v1/radios/{radio_id}/mapping")
    def map_radio(radio_id: str, payload: dict[str, str]) -> dict[str, object]:
        if app.state.runtime_mode != "simulator":
            raise HTTPException(status_code=409, detail="mapping changes require simulator mode")
        device = str(payload.get("device", "")).strip()
        if not device or not is_safe_mapping_path(device):
            raise HTTPException(
                status_code=400,
                detail="device path is not an allowed discovered device",
            )
        try:
            app.state.manager.set_mapping(radio_id, {"device": device})
        except KeyError as error:
            raise HTTPException(status_code=404, detail="radio not found") from error
        persist_settings()
        return {
            "radio_id": radio_id,
            "mapping": {"device": device},
            "receive_only": True,
            "ptt": False,
        }

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
        persist_settings()
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

    @app.post("/api/v1/bluetooth/scan")
    def bluetooth_scan() -> dict[str, object]:
        return {
            "status": "disabled",
            "devices": [],
            "message": "Bluetooth scanning is disabled while CHAOSCOMMS_MODE=simulator",
            "receive_only": True,
            "ptt": False,
        }

    @app.post("/api/v1/bluetooth/pair")
    def bluetooth_pair() -> dict[str, object]:
        return {
            "status": "disabled",
            "message": "Bluetooth pairing requires an explicitly enabled hardware mode",
            "receive_only": True,
            "ptt": False,
        }

    @app.get("/api/v1/audio")
    def audio_status() -> dict[str, object]:
        return app.state.audio.status()

    @app.websocket("/api/v1/audio/stream")
    async def audio_stream(websocket: WebSocket) -> None:
        if (
            app.state.web_auth_required
            and websocket.scope.get("session", {}).get("authenticated") is not True
        ):
            await websocket.close(code=1008)
            return
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
