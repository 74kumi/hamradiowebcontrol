# HamRadioWebControl

**ChaosComms** is a mobile-first web control plane for a portable amateur-radio rack.

## Hardware target

- Raspberry Pi
- Yaesu FT-891
- Yaesu FT-2980R
- DigiRig for FT-2980 audio/PTT
- PreSonus AudioBox for evaluation with FT-891 and digital modes
- N7DDC-style ATU-100 clone
- SDRplay receiver
- HackRF
- Android phone or tablet as the primary interface

## Core goals

- No RDP, VNC, or desktop dependency
- Responsive browser interface and installable PWA
- FT-891 control through Hamlib
- FT-2980 audio/PTT through DigiRig
- Browser audio using WebRTC
- JS8Call integration without rebuilding its decoder
- SDR waterfall with tap-to-tune
- Safe ATU integration after the exact board and firmware are identified
- Fully local operation with no cloud dependency
- Automatic **Field Mode** hotspot when no known Wi-Fi or Ethernet is available

## Version 0.1 target

1. Raspberry Pi OS Lite deployment
2. Hardware discovery and stable device mapping
3. FT-891 read-only CAT status
4. Mobile dashboard
5. Field Mode network status and fallback design
6. PTT disabled by default

## Safety rules

Transmission features are not enabled until all of the following exist:

- maximum transmit timeout;
- automatic PTT release on browser or network disconnect;
- automatic release on exceptions;
- single-radio transmit lock;
- visible transmit state;
- local emergency inhibit;
- command audit log.

The first milestone is receive/control-only. We are building a radio controller, not an unattended 80-watt mystery beacon.

## Planned stack

- Python 3
- FastAPI
- Hamlib / `rigctld`
- WebSockets
- WebRTC
- NetworkManager
- SQLite initially
- Progressive Web App frontend
- systemd deployment

See `docs/ATTACK-PLAN.md` and `CODEX.md` before making changes.
