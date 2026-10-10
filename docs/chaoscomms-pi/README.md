# ChaosComms Raspberry Pi ARM64 deployment

This deployment rebuilds ChaosComms on a clean 64-bit Raspberry Pi OS/Debian host. Do not copy the x86 VM disk to the Pi.

## Prerequisites

- 64-bit Raspberry Pi OS/Debian
- Python 3.11 or newer
- Network access to the configured package indexes
- A reviewed checkout of this repository
- Hardware-specific radio/audio permissions configured separately

The installer does not copy credentials, SSH keys, radio secrets, or VM state.

## Check prerequisites

From the repository root on the Pi:

```sh
sudo env CHAOSCOMMS_MODE=simulator ./deploy/bootstrap-pi.sh --check
```

The check refuses non-ARM64 hosts by default. For a non-ARM64 staging machine only:

```sh
sudo env CHAOSCOMMS_ALLOW_NON_ARM64=1 CHAOSCOMMS_MODE=simulator \
  ./deploy/bootstrap-pi.sh --check
```

## Install simulator mode

Use this first before connecting hardware:

```sh
sudo env CHAOSCOMMS_MODE=simulator ./deploy/bootstrap-pi.sh
```

The script creates the `chaoscomms` service account, installs a virtual environment under `/opt/chaoscomms`, installs the current source, writes `/etc/chaoscomms.env`, and enables the systemd service.

## Install live mode

Only after the radio device mapping and permissions have been reviewed:

```sh
sudo env CHAOSCOMMS_MODE=live ./deploy/bootstrap-pi.sh
```

Live mode still reports receive-only capabilities. It does not enable PTT or transmission.

## Verification

```sh
systemctl is-active chaoscomms.service
curl http://127.0.0.1:8080/api/v1/health
curl http://127.0.0.1:8080/api/v1/radios
curl http://127.0.0.1:8080/api/v1/resources
curl http://127.0.0.1:8080/api/v1/access
```

Expected safety state:

```json
{"receive_only": true, "transmit_enabled": false}
```

## Hardware follow-up

The bootstrap does not guess serial paths, Bluetooth identities, audio devices, or udev permissions. Those must be inventoried on the actual Pi and added as a separate reviewed configuration before physical-radio validation.
