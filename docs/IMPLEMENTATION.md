# ChaosComms 0.1 implementation

This is the first receive-only vertical slice for the ChaosComms Raspberry Pi controller.

## Current behavior

- FastAPI service on port `8080`
- `GET /` returns service metadata
- `GET /api/v1/health` reports radio status and capabilities
- Hamlib integration is an explicit read-only boundary
- PTT is hard-disabled and reported as `false`
- No radio commands are sent in this release

## Local development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/pytest
.venv/bin/uvicorn chaoscomms.main:app --reload --port 8080
curl http://127.0.0.1:8080/api/v1/health
```

## Deployment shape

`deploy/chaoscomms.service` is the target systemd unit for Raspberry Pi OS Lite or Ubuntu ARM64. The service intentionally runs as an unprivileged account and does not grant serial, USB, GPIO, or PTT permissions yet.

## Next slices

1. Add a real `rigctld` status query with timeouts and no write commands.
2. Add stable udev names for the DigiRig and audio devices.
3. Add a mobile dashboard and WebSocket status stream.
4. Add SQLite event/audit storage.
5. Do not implement PTT until every safety rule in the root README has executable tests.
