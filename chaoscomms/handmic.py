"""Safe simulated Bluetooth hand-mic input boundary."""

from __future__ import annotations

from dataclasses import dataclass, field

SAFE_ACTIONS = {"none", "select_active_radio", "receive_audio_toggle", "volume_up", "volume_down"}
BUTTONS = ("button_1", "button_2", "button_3", "ptt")


@dataclass
class HandMic:
    """Simulator for a future HID/BLE/HFP hand-mic adapter."""

    mapping: dict[str, str] = field(default_factory=lambda: {button: "none" for button in BUTTONS})
    last_event: str | None = None

    def set_mapping(self, button: str, action: str) -> None:
        if button not in BUTTONS:
            raise KeyError(button)
        if action not in SAFE_ACTIONS:
            raise ValueError("unsupported or transmit-capable action")
        self.mapping[button] = action

    def event(self, button: str) -> dict[str, object]:
        if button not in BUTTONS:
            raise KeyError(button)
        self.last_event = button
        action = "blocked_ptt" if button == "ptt" else self.mapping[button]
        return {"button": button, "action": action, "ptt": False, "transmit_enabled": False}

    def status(self) -> dict[str, object]:
        return {
            "status": "simulator",
            "paired": False,
            "connected": False,
            "buttons": list(BUTTONS),
            "mapping": dict(self.mapping),
            "last_event": self.last_event,
            "ptt": False,
            "transmit_enabled": False,
        }

    def restore(self, state: dict[str, object]) -> None:
        mapping = state.get("mapping")
        if isinstance(mapping, dict):
            for button, action in mapping.items():
                if (
                    isinstance(button, str)
                    and isinstance(action, str)
                    and button in BUTTONS
                    and action in SAFE_ACTIONS
                ):
                    self.mapping[button] = action

    def persistent_state(self) -> dict[str, object]:
        return {"mapping": dict(self.mapping)}
