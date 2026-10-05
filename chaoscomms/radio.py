"""Radio integration boundary."""

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


class HamlibRadio:
    """Read-only Hamlib adapter boundary.

    The first release deliberately does not expose set-frequency or PTT methods.
    A later implementation can use rigctld after the safety gates are complete.
    """

    def __init__(self, model: str = "FT-891", host: str = "127.0.0.1", port: int = 4532) -> None:
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
