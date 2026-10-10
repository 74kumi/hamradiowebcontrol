from types import SimpleNamespace

from chaoscomms.bluetooth import discover_devices


def test_discovery_parses_devices_without_pairing(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[-2:] == ["scan", "on"]:
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        return SimpleNamespace(
            stdout="Device aa:bb:cc:dd:ee:ff VR-N7500\nDevice 11:22:33:44:55:66 Other\n",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr("chaoscomms.bluetooth.subprocess.run", fake_run)

    result = discover_devices()

    assert result["status"] == "ok"
    assert result["devices"] == [
        {"address": "AA:BB:CC:DD:EE:FF", "name": "VR-N7500"},
        {"address": "11:22:33:44:55:66", "name": "Other"},
    ]
    assert all("pair" not in command for command in calls)
    assert all("connect" not in command for command in calls)


def test_discovery_handles_missing_bluetoothctl(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("chaoscomms.bluetooth.subprocess.run", missing)

    result = discover_devices()

    assert result["status"] == "unavailable"
    assert result["devices"] == []
