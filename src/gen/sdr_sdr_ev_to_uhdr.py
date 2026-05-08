import os
from uhdr.uhdr import UltraHdr
from preset import Preset
from image import image_tools
from image.image_settings import PRESETS

class SdrSdrEvToUhdr:

    def __init__(
        self,
        sdr_path: str,
        sdr_ev_path: str,
        ev: float = 2.0,
        uhdr_path: str | None = None,
        preset: str = Preset.default,
        tag: bool = False,
        keep_temp_files: bool = False,
    ) -> None:
        self.sdr_path = sdr_path
        self.sdr_ev_path = sdr_ev_path
        self.ev = ev
        self.uhdr_path = uhdr_path
        self.settings = PRESETS[preset]
        self.tag = tag
        self.keep_temp_files = keep_temp_files
        self.sdr_changed = False

    def run(self) -> None:
        # load images
        sdr_np_image, sdr_rgb_profile, sdr_exif = image_tools.open_sdr_image(self.sdr_path)
        sdr_ev_np_image, sdr_ev_rgb_profile, _ = image_tools.open_sdr_image(self.sdr_ev_path)

        # check sizes consistency
        if sdr_np_image.shape[:2] != sdr_ev_np_image.shape[:2]:
            raise("Sdr and Hdr image sizes are not identical")

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

        # Add Hdr tag if asked
        if self.tag:
            image_tools.add_hdr_tag(
                sdr_np_image_linear=sdr_np_image_linear,
                hdr_np_image_linear=hdr_np_image_linear,
            )
            self.sdr_changed = True

        # save new sdr if needed
        sdr_path = self.sdr_path
        if self.sdr_changed:
            base_path, _ = os.path.splitext(self.sdr_path)
            sdr_path = f"{base_path}_temp.jpg"
            image_tools.save_sdr_image(
                sdr_np_image_linear=sdr_np_image_linear,
                rgb_profile=sdr_rgb_profile,
                sdr_path=sdr_path,
                exif=sdr_exif,
            )

        # create uhdr image
        if not self.uhdr_path:
            base_path, _ = os.path.splitext(self.sdr_path)
            self.uhdr_path = f"{base_path}_uhdr.jpg"
        ultra_hdr = UltraHdr(
            linear_sdr_image=sdr_np_image_linear,
            linear_hdr_image=hdr_np_image_linear,
            input_sdr_path=sdr_path,
            output_uhdr_path=self.uhdr_path,
            settings=self.settings.uhdr_settings,
            keep_temp_files=self.keep_temp_files,
        )
        ultra_hdr.run()

        # delete temp file if needed
        if self.tag and not self.keep_temp_files:
            os.remove(sdr_path)

    def validate(self) -> None:
        if not os.path.isfile(self.sdr_path):
            raise FileNotFoundError(f"Sdr image not found: {self.sdr_path}")
        if not os.path.isfile(self.sdr_ev_path):
            raise FileNotFoundError(f"Sdr ev image not found: {self.sdr_ev_path}")
        if not (-5.01 < self.ev < 5.01):
            raise ValueError(f"EV value must be in [-5,5]")
