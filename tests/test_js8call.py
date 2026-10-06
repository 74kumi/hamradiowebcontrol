from chaoscomms.js8call import JS8CallManager, SimulatedJS8Call


def test_simulated_js8call_event_is_receive_only() -> None:
    event = SimulatedJS8Call().events()[0]

    assert event.event_type == "RX.DIRECTED"
    assert event.source == "N0CALL"
    assert event.text == "ChaosComms test message"
    assert event.transmit_enabled is False


def test_js8call_manager_returns_events() -> None:
    manager = JS8CallManager(SimulatedJS8Call())

    payload = manager.recent_events()

    assert len(payload) == 1
    assert payload[0]["transport"] == "simulator"
    assert payload[0]["transmit_enabled"] is False
