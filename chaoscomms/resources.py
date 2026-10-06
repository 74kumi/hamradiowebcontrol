"""Exclusive radio/audio ownership and receive-only safety policy."""

from dataclasses import dataclass
from threading import Lock


class ResourceBusy(RuntimeError):
    """Raised when a resource is already owned by another integration."""


@dataclass(frozen=True)
class ResourceLease:
    resource: str
    owner: str
    transmit_enabled: bool = False


@dataclass(frozen=True)
class SafetyPolicy:
    receive_only: bool = True

    def require_transmit(self, owner: str) -> None:
        if self.receive_only:
            raise PermissionError(f"transmit disabled for receive-only policy ({owner})")


class ResourceManager:
    def __init__(self, policy: SafetyPolicy | None = None) -> None:
        self.policy = policy or SafetyPolicy()
        self._leases: dict[str, ResourceLease] = {}
        self._lock = Lock()

    def acquire(self, resource: str, owner: str) -> ResourceLease:
        with self._lock:
            existing = self._leases.get(resource)
            if existing is not None:
                raise ResourceBusy(
                    f"resource {resource} is owned by {existing.owner}"
                )
            lease = ResourceLease(resource, owner, transmit_enabled=False)
            self._leases[resource] = lease
            return lease

    def release(self, lease: ResourceLease) -> None:
        with self._lock:
            current = self._leases.get(lease.resource)
            if current == lease:
                del self._leases[lease.resource]

    def snapshot(self) -> dict[str, dict[str, object]]:
        with self._lock:
            return {
                resource: {
                    "owner": lease.owner,
                    "transmit_enabled": lease.transmit_enabled,
                }
                for resource, lease in self._leases.items()
            }
