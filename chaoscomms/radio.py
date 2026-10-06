"""Radio integration boundaries and safe simulated adapters."""

import socket
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class RadioStatus:
    connected: bool
    model: str
    frequency_hz: int | None
    mode: str | None
    ptt_enabled: bool
    error: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class Radio(Protocol):
    def status(self) -> RadioStatus: ...


class ManagedRadio(Radio, Protocol):
    radio_id: str
    kind: str
    source: str
    def status_dict(self) -> dict[str, object]: ...


class SimulatedRadio:
    """A deterministic, receive-only adapter used for VM and UI testing."""

    source = "simulator"

    def __init__(self, radio_id: str, model: str, kind: str) -> None:
        self.radio_id = radio_id
        self.model = model
        self.kind = kind

    def status(self) -> RadioStatus:
        return RadioStatus(
            connected=True,
            model=self.model,
            frequency_hz=14_074_000,
            mode="USB",
            ptt_enabled=False,
            error=None,
        )

    def status_dict(self) -> dict[str, object]:
        return {
            "id": self.radio_id,
            "model": self.model,
            "kind": self.kind,
            "source": self.source,
            "status": self.status().as_dict(),
            "capabilities": {
                "frequency_read": True,
                "mode_read": True,
                "audio_receive": True,
                "ptt": False,
            },
        }


class HamlibRadio:
    """Read-only Hamlib adapter boundary for the FT-891."""

    radio_id = "ft891"
    kind = "transceiver"
    source = "hamlib"

    def __init__(
        self,
        radio_id: str = "ft891",
        model: str = "FT-891",
        host: str = "127.0.0.1",
        port: int = 4532,
    ) -> None:
        self.radio_id = radio_id
        self.model = model
        self.host = host
        self.port = port

    def _command(self, file: Any, command: str) -> list[str]:
        file.write(f"{command}\n".encode())
        file.flush()
        lines: list[str] = []
        while True:
            line = file.readline().decode().strip()
            if line.startswith("RPRT "):
                if line != "RPRT 0":
                    raise RuntimeError(line)
                return lines
            lines.append(line)

    def status(self) -> RadioStatus:
        try:
            with socket.create_connection((self.host, self.port), timeout=1.5) as connection:
                file = connection.makefile("rwb")
                frequency = int(self._command(file, "f")[0])
                mode = self._command(file, "m")[0]
            return RadioStatus(True, self.model, frequency, mode, False, None)
        except (OSError, ValueError, RuntimeError, IndexError) as error:
            return RadioStatus(
                False,
                self.model,
                None,
                None,
                False,
                f"rigctld unavailable at {self.host}:{self.port}: {error}",
            )

    def status_dict(self) -> dict[str, object]:
        return {
            "id": self.radio_id,
            "model": self.model,
            "kind": self.kind,
            "source": self.source,
            "status": self.status().as_dict(),
            "capabilities": {
                "frequency_read": True,
                "mode_read": True,
                "audio_receive": True,
                "ptt": False,
            },
        }


class VRN7500Transport(Protocol):
    def status(self) -> RadioStatus: ...


class VRN7500Radio:
    """Receive-only boundary for the VR-N7500 BLE/RFCOMM transport."""

    radio_id = "vrn7500"
    kind = "transceiver"
    source = "benlink"

    def __init__(self, transport: VRN7500Transport | None = None) -> None:
        self.transport = transport

    def status(self) -> RadioStatus:
        if self.transport is None:
            return RadioStatus(
                False,
                "VR-N7500",
                None,
                None,
                False,
                "VR-N7500 BLE/RFCOMM transport not configured",
            )
        try:
            return self.transport.status()
        except (OSError, RuntimeError, TimeoutError) as error:
            return RadioStatus(False, "VR-N7500", None, None, False, str(error))

    def status_dict(self) -> dict[str, object]:
        return {
            "id": self.radio_id,
            "model": "VR-N7500",
            "kind": self.kind,
            "source": self.source,
            "status": self.status().as_dict(),
            "capabilities": {
                "frequency_read": True,
                "mode_read": True,
                "audio_receive": False,
                "ptt": False,
            },
        }


class RadioManager:
    def __init__(self, radios: Sequence[ManagedRadio]) -> None:
        self.radios = list(radios)

    def statuses(self) -> list[dict[str, object]]:
        return [radio.status_dict() for radio in self.radios]
