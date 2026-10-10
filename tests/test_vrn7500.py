from chaoscomms.radio import RadioStatus, VRN7500Radio


class FakeVRTransport:
    def status(self) -> RadioStatus:
        return RadioStatus(True, "VR-N7500", 146_520_000, "FM", False, None)


def test_vrn7500_adapter_uses_injected_transport_read_only() -> None:
    status = VRN7500Radio(transport=FakeVRTransport()).status()

    assert status.connected is True
    assert status.model == "VR-N7500"
    assert status.frequency_hz == 146_520_000
    assert status.mode == "FM"
    assert status.ptt_enabled is False


def test_vrn7500_adapter_without_transport_is_disconnected() -> None:
    status = VRN7500Radio().status()

    assert status.connected is False
    assert status.ptt_enabled is False
    assert "BLE" in (status.error or "")
