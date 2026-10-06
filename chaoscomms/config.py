import os

from chaoscomms.radio import HamlibRadio, Radio, RadioManager, SimulatedRadio, VRN7500Radio


def build_runtime(mode: str | None = None) -> tuple[Radio, RadioManager]:
    selected = (mode or os.getenv("CHAOSCOMMS_MODE", "live")).strip().lower()
    if selected == "simulator":
        radios = [
            SimulatedRadio("ft891", "Yaesu FT-891", "transceiver"),
            SimulatedRadio("ft2980r", "Yaesu FT-2980R", "transceiver"),
            SimulatedRadio("vrn7500", "VR-N7500", "transceiver"),
        ]
        return radios[0], RadioManager(radios)
    if selected == "live":
        ft891 = HamlibRadio("ft891", "Yaesu FT-891")
        ft2980r = HamlibRadio("ft2980r", "Yaesu FT-2980R")
        vrn7500 = VRN7500Radio()
        return ft891, RadioManager([ft891, ft2980r, vrn7500])
    raise ValueError("CHAOSCOMMS_MODE must be simulator or live")
