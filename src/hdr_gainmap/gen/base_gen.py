import os
from abc import ABC, abstractmethod
from hdr_gainmap.preset import Preset
from hdr_gainmap.image import image_tools
from hdr_gainmap.image.image_settings import IMAGE_SETTINGS
from hdr_gainmap.hdrgm.hdrgm import create_hdrgm


class BaseGen(ABC):
    """Abstract base class for hdr gainmap gen"""

    def __init__(
        self,
        sdr_path: str,
        hdrgm_path: str | None = None,
        preset: str = Preset.default,
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
        """Main execution pipeline."""
        # Load input images
        self._load_images()

        # Preprocessing
        self._apply_crop_and_resize()

        # Get linear images and process
        self._process_images()

        # Add HDR tag if requested
        self._apply_hdr_tag()

        # Define output path
        self._set_output_path()

        # Generate gainmap
        self._create_gainmap()

        # Save temporary files if requested
        self._save_temp_files()

    @abstractmethod
    def _load_images(self) -> None:
        """Load input images. Each subclass implements its own loading logic."""
        pass

    @abstractmethod
    def _process_images(self) -> None:
        """Process images to generate linear HDR. Each subclass implements specific logic."""
        pass

    def _apply_crop_and_resize(self) -> None:
        """Apply cropping and resizing based on settings."""
        # This will be overridden by subclasses that need custom logic
        # Default implementation for single SDR image
        if not hasattr(self, 'sdr_np_image'):
            return

        if self.settings.min_ratio_w_h or self.settings.max_ratio_w_h:
            self.sdr_np_image = image_tools.crop_to_ratio(
                img=self.sdr_np_image,
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
            self.sdr_changed = True

    def _apply_hdr_tag(self) -> None:
        """Apply HDR tag if requested."""
        if self.tag:
            image_tools.add_hdr_tag(
                sdr_np_image_linear=self.sdr_np_image_linear,
                hdr_np_image_linear=self.hdr_np_image_linear,
            )
            self.sdr_changed = True

    def _set_output_path(self) -> None:
        """Set output path for gainmap if not provided."""
        if not self.hdrgm_path:
            base_path, _ = os.path.splitext(self.sdr_path)
            self.hdrgm_path = f"{base_path}_hdrgm.jpg"

    def _create_gainmap(self) -> None:
        """Create the HDRGM image."""
        create_hdrgm(
            sdr_np_image_linear=self.sdr_np_image_linear,
            hdr_np_image_linear=self.hdr_np_image_linear,
            sdr_rgb_profile=self.sdr_rgb_profile,
            sdr_icc_bytes=self.sdr_icc_bytes,
            output_path=self.hdrgm_path,
            preset=self.preset,
            keep_temp_files=self.keep_temp_files,
        )

    def _save_temp_files(self) -> None:
        """Save temporary SDR file if requested."""
        if self.sdr_changed and self.keep_temp_files:
            base_path, _ = os.path.splitext(self.sdr_path)
            sdr_path = f"{base_path}_temp.jpg"
            image_tools.save_sdr_image(
                sdr_np_image_linear=self.sdr_np_image_linear,
                rgb_profile=self.sdr_rgb_profile,
                sdr_path=sdr_path,
                exif_bytes=self.sdr_exif_bytes,
                icc_bytes=self.sdr_icc_bytes,
            )

    @abstractmethod
    def validate(self) -> None:
        """Validate input files. Each subclass implements its own validation."""
        pass
