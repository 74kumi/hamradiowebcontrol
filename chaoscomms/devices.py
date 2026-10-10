"""Read-only connected-device inventory for settings and mapping UI."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def serial_devices() -> list[dict[str, str]]:
    devices: list[dict[str, str]] = []
    for link in sorted(Path("/dev/serial/by-id").glob("*")):
        devices.append({"id": link.name, "path": str(link), "kind": "serial"})
    if not devices:
        for path in sorted(Path("/dev").glob("ttyUSB*")):
            devices.append({"id": path.name, "path": str(path), "kind": "serial"})
    return devices


def audio_devices() -> list[dict[str, str]]:
    try:
        result = subprocess.run(
            ["arecord", "-l"], capture_output=True, text=True, timeout=3, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    devices: list[dict[str, str]] = []
    pattern = re.compile(r"^card (\d+): ([^[]+) \[([^]]+)\]")
    for line in result.stdout.splitlines():
        match = pattern.match(line.strip())
        if match:
            card, identifier, name = match.groups()
            devices.append({
                "id": identifier.strip(),
                "name": name,
                "path": f"plughw:CARD={identifier.strip()},DEV=0",
                "kind": "audio_capture",
                "card": card,
            })
    return devices


def inventory() -> dict[str, object]:
    return {
        "serial": serial_devices(),
        "audio": audio_devices(),
        "receive_only": True,
        "ptt": False,
    }
