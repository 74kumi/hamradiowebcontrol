import pytest

from chaoscomms.resources import ResourceBusy, ResourceManager, SafetyPolicy


def test_radio_resource_is_exclusive() -> None:
    manager = ResourceManager()

    lease = manager.acquire("radio:ft891", "aprs")

    assert lease.resource == "radio:ft891"
    assert lease.owner == "aprs"
    with pytest.raises(ResourceBusy):
        manager.acquire("radio:ft891", "js8call")

    manager.release(lease)
    replacement = manager.acquire("radio:ft891", "js8call")
    assert replacement.owner == "js8call"


def test_audio_resource_is_exclusive() -> None:
    manager = ResourceManager()

    manager.acquire("audio:primary", "aprs")

    with pytest.raises(ResourceBusy):
        manager.acquire("audio:primary", "js8call")


def test_transmit_is_hard_denied_by_receive_only_policy() -> None:
    policy = SafetyPolicy(receive_only=True)

    with pytest.raises(PermissionError, match="transmit disabled"):
        policy.require_transmit("aprs")


def test_resource_snapshot_is_safe_to_publish() -> None:
    manager = ResourceManager()
    lease = manager.acquire("radio:ft891", "aprs")

    assert manager.snapshot() == {
        "radio:ft891": {"owner": "aprs", "transmit_enabled": False}
    }

    manager.release(lease)
    assert manager.snapshot() == {}
