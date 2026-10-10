"""Receive-only APRS packet boundary."""

from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True)
class APRSPacket:
    source: str
    destination: str
    path: list[str]
    information: str
    position: dict[str, float] | None
    transport: str
    transmit_enabled: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class APRSTransport(Protocol):
    def packets(self) -> list[APRSPacket]: ...


class SimulatedAPRS:
    """Deterministic receive-only APRS source for VM and UI testing."""

    def packets(self) -> list[APRSPacket]:
        return [
            APRSPacket(
                source="N0CALL",
                destination="APRS",
                path=["WIDE1-1"],
                information="!4903.50N/07201.75W-Test station",
                position={"latitude": 49.0583, "longitude": -72.0292},
                transport="simulator",
            )
        ]


class APRSManager:
    def __init__(self, transport: APRSTransport) -> None:
        self.transport = transport

    def recent_packets(self) -> list[dict[str, object]]:
        return [packet.as_dict() for packet in self.transport.packets()]
