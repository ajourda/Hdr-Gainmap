from pathlib import Path

from hdr_gainmap.preset import Preset
from hdr_gainmap.image import image_tools
from hdr_gainmap.image.image_settings import IMAGE_SETTINGS, ImageSettings
from hdr_gainmap.hdrgm.hdrgm import create_hdrgm


class SdrTmToHdrgm:
    _sdr_path: Path
    _hdrgm_path: Path
    _preset: Preset
    _settings: ImageSettings
    _tag: bool
    _keep_temp_files: bool
    _sdr_changed: bool

    def __init__(
        self,
        sdr_path: Path,
        hdrgm_path: Path | None = None,
        preset: Preset = Preset.default,
        tag: bool = False,
        keep_temp_files: bool = False,
    ) -> None:
        self._sdr_path = sdr_path
        self._hdrgm_path = (
            self._sdr_path.with_stem(self._sdr_path.stem + "_hdrgm")
            if hdrgm_path is None
            else hdrgm_path
        )
        self._preset = preset
        self._settings = IMAGE_SETTINGS[preset]
        self._tag = tag
        self._keep_temp_files = keep_temp_files
        self._sdr_changed = False

    def run(self) -> None:
        # load image
        sdr_np_image, sdr_rgb_profile, sdr_exif_bytes, sdr_icc_bytes = (
            image_tools.open_sdr_image(self._sdr_path)
        )

        # crop to respect ratio if needed
        if self._settings.min_ratio_w_h or self._settings.max_ratio_w_h:
            sdr_np_image = image_tools.crop_to_ratio(
                img=sdr_np_image,
                min_ratio=self._settings.min_ratio_w_h,
                max_ratio=self._settings.max_ratio_w_h,
            )
            self._sdr_changed = True

        # resize to respect max size if needed
        if self._settings.width_max or self._settings.height_max:
            sdr_np_image = image_tools.resize_to_max(
                img=sdr_np_image,
                width_max=self._settings.width_max,
                height_max=self._settings.height_max,
            )
            self._sdr_changed = True

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
        if self._tag:
            image_tools.add_hdr_tag(
                sdr_np_image_linear=sdr_np_image_linear,
                hdr_np_image_linear=hdr_np_image_linear,
            )
            self._sdr_changed = True

        # create hdr gainmap
        create_hdrgm(
            sdr_np_image_linear=sdr_np_image_linear,
            hdr_np_image_linear=hdr_np_image_linear,
            sdr_rgb_profile=sdr_rgb_profile,
            sdr_icc_bytes=sdr_icc_bytes,
            output_path=self._hdrgm_path,
            preset=self._preset,
            keep_temp_files=self._keep_temp_files,
        )

        # create temp file if asked
        if self._sdr_changed and self._keep_temp_files:
            sdr_path = self._sdr_path.with_stem(self._sdr_path.stem + "_temp")
            image_tools.save_sdr_image(
                sdr_np_image_linear=sdr_np_image_linear,
                rgb_profile=sdr_rgb_profile,
                sdr_path=sdr_path,
                exif_bytes=sdr_exif_bytes,
                icc_bytes=sdr_icc_bytes,
            )

    def validate(self) -> None:
        if not self._sdr_path.is_file():
            raise FileNotFoundError(f"Sdr image not found: {self._sdr_path}")
