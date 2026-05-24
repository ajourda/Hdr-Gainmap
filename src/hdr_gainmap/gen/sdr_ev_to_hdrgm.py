from hdr_gainmap.gen.base_gen import BaseGen
from hdr_gainmap.image import image_tools
import os


class SdrToHdrgm(BaseGen):
    def __init__(
        self,
        sdr_path: str,
        ev: float = 2.0,
        hdrgm_path: str | None = None,
        preset: str = "default",
        tag: bool = False,
        keep_temp_files: bool = False,
    ) -> None:
        super().__init__(sdr_path, hdrgm_path, preset, tag, keep_temp_files)
        self.ev = ev

    def _load_images(self) -> None:
        """Load SDR image."""
        self.sdr_np_image, self.sdr_rgb_profile, self.sdr_exif_bytes, self.sdr_icc_bytes = (
            image_tools.open_sdr_image(self.sdr_path)
        )

    def _process_images(self) -> None:
        """Get linear SDR image and apply EV to create HDR."""
        self.sdr_np_image_linear = image_tools.get_linear_image(
            image=self.sdr_np_image,
            rgb_profile=self.sdr_rgb_profile,
        )

        self.hdr_np_image_linear = self.sdr_np_image_linear * pow(2, self.ev)

    def validate(self) -> None:
        if not os.path.isfile(self.sdr_path):
            raise FileNotFoundError(f"Sdr image not found: {self.sdr_path}")
        if not (-5 <= self.ev <= 5):
            raise ValueError("EV value must be in [-5,5]")
