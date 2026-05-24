from hdr_gainmap.gen.base_gen import BaseGen
from hdr_gainmap.image import image_tools
import os


class SdrSdrEvToHdrgm(BaseGen):
    def __init__(
        self,
        sdr_path: str,
        sdr_ev_path: str,
        ev: float = 2.0,
        hdrgm_path: str | None = None,
        preset: str = "default",
        tag: bool = False,
        keep_temp_files: bool = False,
    ) -> None:
        super().__init__(sdr_path, hdrgm_path, preset, tag, keep_temp_files)
        self.sdr_ev_path = sdr_ev_path
        self.ev = ev

    def _load_images(self) -> None:
        """Load SDR and SDR EV images."""
        self.sdr_np_image, self.sdr_rgb_profile, self.sdr_exif_bytes, self.sdr_icc_bytes = (
            image_tools.open_sdr_image(self.sdr_path)
        )
        self.sdr_ev_np_image, self.sdr_ev_rgb_profile, _, _ = image_tools.open_sdr_image(
            self.sdr_ev_path
        )

        # check sizes consistency
        if self.sdr_np_image.shape[:2] != self.sdr_ev_np_image.shape[:2]:
            raise ValueError("Sdr and SdrEv image sizes are not identical")

    def _apply_crop_and_resize(self) -> None:
        """Apply cropping and resizing to both SDR images."""
        if self.settings.min_ratio_w_h or self.settings.max_ratio_w_h:
            self.sdr_np_image = image_tools.crop_to_ratio(
                img=self.sdr_np_image,
                min_ratio=self.settings.min_ratio_w_h,
                max_ratio=self.settings.max_ratio_w_h,
            )
            self.sdr_ev_np_image = image_tools.crop_to_ratio(
                img=self.sdr_ev_np_image,
                min_ratio=self.settings.min_ratio_w_h,
                max_ratio=self.settings.max_ratio_w_h,
            )
            self.sdr_changed = True

        if self.settings.width_max or self.settings.height_max:
            self.sdr_np_image = image_tools.resize_to_max(
                img=self.sdr_np_image,
                width_max=self.settings.width_max,
                height_max=self.settings.height_max,
            )
            self.sdr_ev_np_image = image_tools.resize_to_max(
                img=self.sdr_ev_np_image,
                width_max=self.settings.width_max,
                height_max=self.settings.height_max,
            )
            self.sdr_changed = True

    def _process_images(self) -> None:
        """Get linear images and create HDR from SDR stacking."""
        self.sdr_np_image_linear = image_tools.get_linear_image(
            image=self.sdr_np_image,
            rgb_profile=self.sdr_rgb_profile,
        )
        sdr_ev_np_image_linear = image_tools.get_linear_image(
            image=self.sdr_ev_np_image,
            rgb_profile=self.sdr_ev_rgb_profile,
        )

        # get hdr image
        self.hdr_np_image_linear = image_tools.get_hdr_from_sdr_stacking(
            sdr_np_linear=self.sdr_np_image_linear,
            sdr_rgb_profile=self.sdr_rgb_profile,
            sdr_ev_np_linear=sdr_ev_np_image_linear,
            sdr_ev_rgb_profile=self.sdr_ev_rgb_profile,
            ev=self.ev,
        )

    def validate(self) -> None:
        if not os.path.isfile(self.sdr_path):
            raise FileNotFoundError(f"Sdr image not found: {self.sdr_path}")
        if not os.path.isfile(self.sdr_ev_path):
            raise FileNotFoundError(f"Sdr ev image not found: {self.sdr_ev_path}")
        if not (-5 <= self.ev <= 5):
            raise ValueError("EV value must be in [-5,5]")
