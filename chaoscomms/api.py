from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from chaoscomms.radio import HamlibRadio, Radio

SERVICE_VERSION = "0.1.0"
STATIC_DIR = Path(__file__).parent / "static"


def create_app(radio: Radio | None = None) -> FastAPI:
    app = FastAPI(title="ChaosComms", version=SERVICE_VERSION)
    app.state.radio = radio or HamlibRadio()
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/v1/about")
    def about() -> dict[str, str]:
        return {"service": "ChaosComms", "version": SERVICE_VERSION}

    @app.get("/api/v1/health")
    def health() -> dict[str, object]:
        status = app.state.radio.status()
        return {
            "status": "ok" if status.connected else "degraded",
            "radio": status.as_dict(),
            "capabilities": {"receive_only": True, "ptt": False},
        }

    return app
