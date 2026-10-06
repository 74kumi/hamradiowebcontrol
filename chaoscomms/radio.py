"""Radio integration boundaries and safe simulated adapters."""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Protocol


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

    def status(self) -> RadioStatus:
        return RadioStatus(
            connected=False,
            model=self.model,
            frequency_hz=None,
            mode=None,
            ptt_enabled=False,
            error=f"rigctld unavailable at {self.host}:{self.port}",
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


class RadioManager:
    def __init__(self, radios: Sequence[ManagedRadio]) -> None:
        self.radios = list(radios)

    def statuses(self) -> list[dict[str, object]]:
        return [radio.status_dict() for radio in self.radios]
