import os
from preset import Preset
from image import image_tools
from image.image_settings import IMAGE_SETTINGS
from hdrgm.hdrgm import create_hdrgm


class SdrSdrEvToUhdr:

    def __init__(
        self,
        sdr_path: str,
        sdr_ev_path: str,
        ev: float = 2.0,
        hdrgm_path: str | None = None,
        preset: str = Preset.default,
        tag: bool = False,
        keep_temp_files: bool = False,
    ) -> None:
        self.sdr_path = sdr_path
        self.sdr_ev_path = sdr_ev_path
        self.ev = ev
        self.hdrgm_path = hdrgm_path
        self.preset = preset
        self.settings = IMAGE_SETTINGS[preset]
        self.tag = tag
        self.keep_temp_files = keep_temp_files
        self.sdr_changed = False

    def run(self) -> None:
        # load images
        sdr_np_image, sdr_rgb_profile, sdr_exif_bytes, sdr_icc_bytes = (
            image_tools.open_sdr_image(self.sdr_path)
        )
        sdr_ev_np_image, sdr_ev_rgb_profile, _, _ = image_tools.open_sdr_image(
            self.sdr_ev_path
        )

        # check sizes consistency
        if sdr_np_image.shape[:2] != sdr_ev_np_image.shape[:2]:
            raise ("Sdr and SdrEv image sizes are not identical")

        # crop to respect ratio if needed
        if self.settings.min_ratio_w_h or self.settings.max_ratio_w_h:
            sdr_np_image = image_tools.crop_to_ratio(
                img=sdr_np_image,
                min_ratio=self.settings.min_ratio_w_h,
                max_ratio=self.settings.max_ratio_w_h,
            )
            sdr_ev_np_image = image_tools.crop_to_ratio(
                img=sdr_ev_np_image,
                min_ratio=self.settings.min_ratio_w_h,
                max_ratio=self.settings.max_ratio_w_h,
            )
            self.sdr_changed = True

        # resize to respect max size if needed
        if self.settings.width_max or self.settings.height_max:
            sdr_np_image = image_tools.resize_to_max(
                img=sdr_np_image,
                width_max=self.settings.width_max,
                height_max=self.settings.height_max,
            )
            sdr_ev_np_image = image_tools.resize_to_max(
                img=sdr_ev_np_image,
                width_max=self.settings.width_max,
                height_max=self.settings.height_max,
            )
            self.sdr_changed = True

        # get rgb linear values
        sdr_np_image_linear = image_tools.get_linear_image(
            image=sdr_np_image,
            rgb_profile=sdr_rgb_profile,
        )
        sdr_ev_np_image_linear = image_tools.get_linear_image(
            image=sdr_ev_np_image,
            rgb_profile=sdr_ev_rgb_profile,
        )

        # get hdr image
        hdr_np_image_linear = image_tools.get_hdr_from_sdr_stacking(
            sdr_np_linear=sdr_np_image_linear,
            sdr_rgb_profile=sdr_rgb_profile,
            sdr_ev_np_linear=sdr_ev_np_image_linear,
            sdr_ev_rgb_profile=self.sdr_ev_rgb_profile,
            ev=self.ev,
        )

        # add hdr tag if asked
        if self.tag:
            image_tools.add_hdr_tag(
                sdr_np_image_linear=sdr_np_image_linear,
                hdr_np_image_linear=hdr_np_image_linear,
            )
            self.sdr_changed = True

        # output path definition
        if not self.hdrgm_path:
            base_path, _ = os.path.splitext(self.sdr_path)
            self.hdrgm_path = f"{base_path}_hdrgm.jpg"

        # create hdr gainmap
        create_hdrgm(
            sdr_np_image_linear=sdr_np_image_linear,
            hdr_np_image_linear=hdr_np_image_linear,
            sdr_rgb_profile=sdr_rgb_profile,
            sdr_icc_bytes=sdr_icc_bytes,
            output_path=self.hdrgm_path,
            preset=self.preset,
            keep_temp_files=self.keep_temp_files,
        )

        # create temp file if asked
        if self.sdr_changed and self.keep_temp_files:
            base_path, _ = os.path.splitext(self.sdr_path)
            sdr_path = f"{base_path}_temp.jpg"
            image_tools.save_sdr_image(
                sdr_np_image_linear=sdr_np_image_linear,
                rgb_profile=sdr_rgb_profile,
                sdr_path=sdr_path,
                exif_bytes=sdr_exif_bytes,
                icc_bytes=sdr_icc_bytes,
            )

    def validate(self) -> None:
        if not os.path.isfile(self.sdr_path):
            raise FileNotFoundError(f"Sdr image not found: {self.sdr_path}")
        if not os.path.isfile(self.sdr_ev_path):
            raise FileNotFoundError(f"Sdr ev image not found: {self.sdr_ev_path}")
        if not (-5 <= self.ev <= 5):
            raise ValueError(f"EV value must be in [-5,5]")
