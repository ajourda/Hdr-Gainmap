from dataclasses import dataclass
from preset import Preset


@dataclass
class HdrgmSettings:
    min_gain_ev: float = -1.0
    max_gain_ev: float = 5.6  # PQ limit: log2(10000/203)
    sdr_quality: int = 95
    gain_map_quality: int = 90
    gain_map_size_factor: int = 1
    is_multichannel: bool = False
    forced_max_hdr_capacity: float | None = None


HDRGM_SETTINGS = {
    Preset.default: HdrgmSettings(),
    Preset.best: HdrgmSettings(
        min_gain_ev = -3.0,
        gain_map_quality = 100,
        is_multichannel = True,
    ),
    Preset.light: HdrgmSettings(
        gain_map_quality = 80,
        gain_map_size_factor = 2,
    ),
    Preset.insta: HdrgmSettings(
        min_gain_ev = 0.0,
        max_gain_ev = 4.0,
    ),
}
