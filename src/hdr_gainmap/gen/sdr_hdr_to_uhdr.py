import os
from hdr_gainmap.preset import Preset
from hdr_gainmap.image import image_tools
from hdr_gainmap.image.image_settings import IMAGE_SETTINGS
from hdr_gainmap.hdrgm.hdrgm import create_hdrgm


class SdrHdrToUhdr:
    def __init__(
        self,
        sdr_path: str,
        hdr_path: str,
        hdrgm_path: str | None = None,
        preset: str = Preset.default,
        tag: bool = False,
        keep_temp_files: bool = False,
    ) -> None:
        self.sdr_path = sdr_path
        self.hdr_path = hdr_path
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
        hdr_np_image, hdr_rgb_profile = image_tools.open_hdr_avif_image(self.hdr_path)

        # check sizes consistency
        if sdr_np_image.shape[:2] != hdr_np_image.shape[:2]:
            raise ("Sdr and Hdr image sizes are not identical")

        # crop to respect ratio if needed
        if self.settings.min_ratio_w_h or self.settings.max_ratio_w_h:
            sdr_np_image = image_tools.crop_to_ratio(
                img=sdr_np_image,
                min_ratio=self.settings.min_ratio_w_h,
                max_ratio=self.settings.max_ratio_w_h,
            )
            hdr_np_image = image_tools.crop_to_ratio(
                img=hdr_np_image,
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
            hdr_np_image = image_tools.resize_to_max(
                img=hdr_np_image,
                width_max=self.settings.width_max,
                height_max=self.settings.height_max,
            )
            self.sdr_changed = True

        # get rgb linear values
        sdr_np_image_linear = image_tools.get_linear_image(
            image=sdr_np_image,
            rgb_profile=sdr_rgb_profile,
        )
        hdr_np_image_linear = image_tools.get_linear_image(
            image=hdr_np_image,
            rgb_profile=hdr_rgb_profile,
            is_hdr=True,
        )

        # convert hdr values to the sdr primaries
        hdr_np_image_linear = image_tools.get_adapted_rgb_primaries(
            image=hdr_np_image_linear,
            origin_rgb_profile=hdr_rgb_profile,
            new_rgb_profile=sdr_rgb_profile,
            is_hdr=True,
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
        if not os.path.isfile(self.hdr_path):
            raise FileNotFoundError(f"Hdr image file not found: {self.hdr_path}")


def process_folder(
    input_directory: str,
    overwrite_existing: bool = False,
    keep_temp_files: bool = False,
) -> None:
    """
    Processes all JPG images in the specified directory to generate UHDR images.
    For each JPG file, if a corresponding AVIF file exists, generates a UHDR image.
    Skips processing if the UHDR output already exists and `overwrite_existing` is False.

    Args:
        input_directory: Path to the directory containing JPG and AVIF files.
        overwrite_existing: If True, overwrites existing UHDR files. Defaults to False.
        keep_temporary_files: If True, retains temporary files after processing. Defaults to False.

    Raises:
        FileNotFoundError: If "input_directory" does not exist or is not a directory.
        ValueError: If no valid JPG/AVIF pairs are found in the directory.
    """
    if not os.path.isdir(input_directory):
        raise FileNotFoundError(f"Directory does not exist: {input_directory}")

    file_list = os.listdir(input_directory)

    for filename in file_list:
        base_name, file_extension = os.path.splitext(filename)

        uhdr_output_filepath = os.path.join(input_directory, f"{base_name}_uhdr.jpg")
        if not overwrite_existing and os.path.isfile(uhdr_output_filepath):
            continue

        if file_extension.lower() == ".jpg":
            corresponding_avif_filepath = os.path.join(
                input_directory, f"{base_name}.avif"
            )

            if os.path.isfile(corresponding_avif_filepath):
                print(f"Processing file: {filename}")
                process = SdrHdrToUhdr(
                    sdr_path=os.path.join(input_directory, filename),
                    hdr_path=corresponding_avif_filepath,
                    keep_temp_files=keep_temp_files,
                )
                process.validate()
                process.run()
