from chaoscomms.api import create_app

app = create_app(web_auth_required=True)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "chaoscomms.main:app",
        host="0.0.0.0",
        port=8443,
        reload=False,
        ssl_keyfile="/etc/chaoscomms/tls/chaoscomms.key",
        ssl_certfile="/etc/chaoscomms/tls/chaoscomms.crt",
    )


if __name__ == "__main__":
    main()
