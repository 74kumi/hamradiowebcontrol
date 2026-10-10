"""Bounded, discovery-only Bluetooth operations."""

from __future__ import annotations

import re
import subprocess
from typing import Any

_DEVICE_RE = re.compile(r"^Device\s+([0-9A-Fa-f:]{17})\s+(.+?)\s*$")


def discover_devices(timeout_seconds: int = 8) -> dict[str, Any]:
    """Scan for nearby Bluetooth devices without pairing or connecting."""
    try:
        subprocess.run(
            ["bluetoothctl", "--timeout", str(timeout_seconds), "scan", "on"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 4,
        )
        listed = subprocess.run(
            ["bluetoothctl", "devices"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError:
        return {
            "status": "unavailable",
            "devices": [],
            "message": "bluetoothctl is not installed",
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "devices": [],
            "message": "Bluetooth discovery timed out",
        }

    devices = []
    for line in listed.stdout.splitlines():
        match = _DEVICE_RE.match(line.strip())
        if match:
            devices.append({"address": match.group(1).upper(), "name": match.group(2)})
    return {
        "status": "ok",
        "devices": devices,
        "message": f"Discovered {len(devices)} Bluetooth device(s)",
    }
