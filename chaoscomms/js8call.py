"""Receive-only JS8Call local API boundary."""

from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True)
class JS8Event:
    event_type: str
    source: str | None
    destination: str | None
    text: str
    dial_frequency_hz: int | None
    audio_offset_hz: int | None
    snr_db: int | None
    transport: str
    transmit_enabled: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class JS8CallTransport(Protocol):
    def events(self) -> list[JS8Event]: ...


class SimulatedJS8Call:
    """Deterministic receive-only JS8Call source for VM testing."""

    def events(self) -> list[JS8Event]:
        return [
            JS8Event(
                event_type="RX.DIRECTED",
                source="N0CALL",
                destination="CHAOS",
                text="ChaosComms test message",
                dial_frequency_hz=14_078_000,
                audio_offset_hz=1_500,
                snr_db=-12,
                transport="simulator",
            )
        ]


class JS8CallManager:
    def __init__(self, transport: JS8CallTransport) -> None:
        self.transport = transport

    def recent_events(self) -> list[dict[str, object]]:
        return [event.as_dict() for event in self.transport.events()]
