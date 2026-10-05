from fastapi import FastAPI

from chaoscomms.radio import HamlibRadio, Radio

SERVICE_VERSION = "0.1.0"


def create_app(radio: Radio | None = None) -> FastAPI:
    app = FastAPI(title="ChaosComms", version=SERVICE_VERSION)
    app.state.radio = radio or HamlibRadio()

    @app.get("/")
    def root() -> dict[str, str]:
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
