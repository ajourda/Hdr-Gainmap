from hdr_gainmap.gen.base_gen import BaseGen
from hdr_gainmap.image import image_tools
import os


class SdrHdrToHdrgm(BaseGen):
    def __init__(
        self,
        sdr_path: str,
        hdr_path: str,
        hdrgm_path: str | None = None,
        preset: str = "default",
        tag: bool = False,
        keep_temp_files: bool = False,
    ) -> None:
        super().__init__(sdr_path, hdrgm_path, preset, tag, keep_temp_files)
        self.hdr_path = hdr_path

    def _load_images(self) -> None:
        """Load SDR and HDR images."""
        self.sdr_np_image, self.sdr_rgb_profile, self.sdr_exif_bytes, self.sdr_icc_bytes = (
            image_tools.open_sdr_image(self.sdr_path)
        )
        self.hdr_np_image, self.hdr_rgb_profile = image_tools.open_hdr_avif_image(self.hdr_path)

        # check sizes consistency
        if self.sdr_np_image.shape[:2] != self.hdr_np_image.shape[:2]:
            raise ValueError("Sdr and Hdr image sizes are not identical")

    def _apply_crop_and_resize(self) -> None:
        """Apply cropping and resizing to both SDR and HDR images."""
        if self.settings.min_ratio_w_h or self.settings.max_ratio_w_h:
            self.sdr_np_image = image_tools.crop_to_ratio(
                img=self.sdr_np_image,
                min_ratio=self.settings.min_ratio_w_h,
                max_ratio=self.settings.max_ratio_w_h,
            )
            self.sdr_changed = True
            self.hdr_np_image = image_tools.crop_to_ratio(
                img=self.hdr_np_image,
                min_ratio=self.settings.min_ratio_w_h,
                max_ratio=self.settings.max_ratio_w_h,
            )

        if self.settings.width_max or self.settings.height_max:
            self.sdr_np_image = image_tools.resize_to_max(
                img=self.sdr_np_image,
                width_max=self.settings.width_max,
                height_max=self.settings.height_max,
            )
            self.sdr_changed = True
            self.hdr_np_image = image_tools.resize_to_max(
                img=self.hdr_np_image,
                width_max=self.settings.width_max,
                height_max=self.settings.height_max,
            )

    def _process_images(self) -> None:
        """Get linear images and convert HDR to SDR primaries."""
        self.sdr_np_image_linear = image_tools.get_linear_image(
            image=self.sdr_np_image,
            rgb_profile=self.sdr_rgb_profile,
        )
        self.hdr_np_image_linear = image_tools.get_linear_image(
            image=self.hdr_np_image,
            rgb_profile=self.hdr_rgb_profile,
            is_hdr=True,
        )

        # convert hdr values to the sdr primaries
        self.hdr_np_image_linear = image_tools.get_adapted_rgb_primaries(
            image=self.hdr_np_image_linear,
            origin_rgb_profile=self.hdr_rgb_profile,
            new_rgb_profile=self.sdr_rgb_profile,
            is_hdr=True,
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
                process = SdrHdrToHdrgm(
                    sdr_path=os.path.join(input_directory, filename),
                    hdr_path=corresponding_avif_filepath,
                    keep_temp_files=keep_temp_files,
                )
                process.validate()
                process.run()
