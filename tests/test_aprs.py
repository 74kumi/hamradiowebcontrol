from chaoscomms.aprs import APRSManager, SimulatedAPRS


def test_simulated_aprs_packet_has_safe_receive_only_metadata() -> None:
    packet = SimulatedAPRS().packets()[0]

    assert packet.source == "N0CALL"
    assert packet.destination == "APRS"
    assert packet.position == {"latitude": 49.0583, "longitude": -72.0292}
    assert packet.transmit_enabled is False


def test_aprs_manager_returns_packets() -> None:
    manager = APRSManager(SimulatedAPRS())

    payload = manager.recent_packets()

    assert len(payload) == 1
    assert payload[0]["source"] == "N0CALL"
    assert payload[0]["transport"] == "simulator"
    assert payload[0]["transmit_enabled"] is False
