from dataclasses import dataclass
from hdr_gainmap.preset import Preset


@dataclass
class ImageSettings:
    min_ratio_w_h: float | None = None
    max_ratio_w_h: float | None = None
    width_max: int | None = None
    height_max: int | None = None
    quality: int = 95
    output_rgb_profile: str | None = None


IMAGE_SETTINGS = {
    Preset.default: ImageSettings(),
    Preset.best: ImageSettings(
        quality=100,
    ),
    Preset.light: ImageSettings(
        quality=80,
    ),
    Preset.insta: ImageSettings(
        min_ratio_w_h=0.8,
        max_ratio_w_h=1.91,
        width_max=1080,
        height_max=1350,
        quality=100,
        output_rgb_profile="Display P3",
    ),
}
