from chaoscomms.api import create_app

app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("chaoscomms.main:app", host="0.0.0.0", port=8080, reload=False)
