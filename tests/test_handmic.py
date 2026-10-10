from chaoscomms.handmic import HandMic


def test_handmic_blocks_ptt_and_allows_safe_mapping():
    mic = HandMic()

    mic.set_mapping("button_1", "select_active_radio")

    assert mic.event("button_1")["action"] == "select_active_radio"
    assert mic.event("ptt")["action"] == "blocked_ptt"
    assert mic.status()["ptt"] is False
    assert mic.status()["transmit_enabled"] is False


def test_handmic_rejects_transmit_capable_mapping():
    mic = HandMic()

    try:
        mic.set_mapping("button_1", "ptt")
    except ValueError as error:
        assert "transmit" in str(error)
    else:
        raise AssertionError("transmit mapping was accepted")


def test_handmic_restores_only_known_safe_actions():
    mic = HandMic()
    mic.restore({"mapping": {"button_1": "volume_up", "ptt": "ptt", "unknown": "none"}})

    assert mic.mapping["button_1"] == "volume_up"
    assert mic.mapping["ptt"] == "none"
