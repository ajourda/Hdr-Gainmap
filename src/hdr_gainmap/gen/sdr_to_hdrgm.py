from pathlib import Path

from hdr_gainmap.preset import Preset
from hdr_gainmap.image import image_tools
from hdr_gainmap.image.image_settings import IMAGE_SETTINGS
from hdr_gainmap.hdrgm.hdrgm import create_hdrgm


class SdrTmToHdrgm:
    def __init__(
        self,
        sdr_path: Path,
        hdrgm_path: Path | None = None,
        preset: Preset = Preset.default,
        tag: bool = False,
        keep_temp_files: bool = False,
    ) -> None:
        self.sdr_path = sdr_path
        self.hdrgm_path = hdrgm_path
        self.preset = preset
        self.settings = IMAGE_SETTINGS[preset]
        self.tag = tag
        self.keep_temp_files = keep_temp_files
        self.sdr_changed = False

    def run(self) -> None:
        # load image
        sdr_np_image, sdr_rgb_profile, sdr_exif_bytes, sdr_icc_bytes = (
            image_tools.open_sdr_image(self.sdr_path)
        )

        # crop to respect ratio if needed
        if self.settings.min_ratio_w_h or self.settings.max_ratio_w_h:
            sdr_np_image = image_tools.crop_to_ratio(
                img=sdr_np_image,
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
            self.sdr_changed = True

        # get rgb linear values
        sdr_np_image_linear = image_tools.get_linear_image(
            image=sdr_np_image,
            rgb_profile=sdr_rgb_profile,
        )

        # compute hdr with tone mapped sdr
        hdr_np_image_linear = image_tools.tonemap_sdr_to_hdr(
            sdr_np_image_linear=sdr_np_image_linear,
            sdr_rgb_profile=sdr_rgb_profile,
        )

        # add Hdr tag if asked
        if self.tag:
            image_tools.add_hdr_tag(
                sdr_np_image_linear=sdr_np_image_linear,
                hdr_np_image_linear=hdr_np_image_linear,
            )
            self.sdr_changed = True

        # output path definition
        if not self.hdrgm_path:
            self.hdrgm_path = self.sdr_path.with_stem(self.sdr_path.stem + "_hdrgm")

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
            sdr_path = self.sdr_path.with_stem(self.sdr_path.stem + "_temp")
            image_tools.save_sdr_image(
                sdr_np_image_linear=sdr_np_image_linear,
                rgb_profile=sdr_rgb_profile,
                sdr_path=sdr_path,
                exif_bytes=sdr_exif_bytes,
                icc_bytes=sdr_icc_bytes,
            )

    def validate(self) -> None:
        if not self.sdr_path.is_file():
            raise FileNotFoundError(f"Sdr image not found: {self.sdr_path}")
