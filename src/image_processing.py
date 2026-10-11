"""Image validation, orientation correction, and computer vision preprocessing.

Provides safe loading, EXIF orientation correction, variant generation
(original, contrast-enhanced, adaptive-thresholded) without destroying small characters.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageOps

from src.observability import logger

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit
MAX_IMAGE_DIMENSION = 3000  # Resize dimension limit to prevent OOM
MIN_IMAGE_DIMENSION = 50  # Below this, image is severely degraded


class ImageProcessingError(Exception):
    """Custom exception for image validation and processing failures."""
    pass


class ImageProcessor:
    """Handles image validation, decoding, orientation fix, and OCR preprocessing variants."""

    @staticmethod
    def validate_file(
        image_input: Union[Path, str, bytes, io.BytesIO, Image.Image, Any],
        max_size: int = MAX_FILE_SIZE_BYTES,
    ) -> Tuple[bool, str]:
        """Validate input type, extension, and file size."""
        if isinstance(image_input, Image.Image):
            return True, "Valid"
        elif isinstance(image_input, (str, Path)):
            p = Path(image_input)
            if not p.exists():
                return False, f"Image file not found: {p}"
            if p.suffix.lower() not in ALLOWED_EXTENSIONS:
                return False, f"Unsupported file extension: {p.suffix}"
            if p.stat().st_size > max_size:
                return False, f"File size ({p.stat().st_size} bytes) exceeds {max_size} bytes limit"
        elif isinstance(image_input, (bytes, io.BytesIO)):
            size = len(image_input) if isinstance(image_input, bytes) else len(image_input.getvalue())
            if size > max_size:
                return False, f"Upload size exceeds {max_size} bytes limit"
        elif hasattr(image_input, "getvalue"):
            val = image_input.getvalue()
            if len(val) > max_size:
                return False, f"Upload size exceeds {max_size} bytes limit"
        elif hasattr(image_input, "read"):
            return True, "Valid"
        else:
            return False, f"Unsupported image input type: {type(image_input)}"

        return True, "Valid"

    @classmethod
    def load_image(
        cls, image_input: Union[Path, str, bytes, io.BytesIO, Image.Image, Any]
    ) -> Image.Image:
        """Safely load image, validate decodability, and correct EXIF orientation."""
        valid, msg = cls.validate_file(image_input)
        if not valid:
            raise ImageProcessingError(msg)

        try:
            if isinstance(image_input, Image.Image):
                img = image_input.copy()
            elif isinstance(image_input, (str, Path)):
                img = Image.open(image_input)
            elif isinstance(image_input, bytes):
                img = Image.open(io.BytesIO(image_input))
            elif hasattr(image_input, "getvalue"):
                img = Image.open(io.BytesIO(image_input.getvalue()))
            elif hasattr(image_input, "read"):
                img = Image.open(image_input)
            else:
                img = Image.open(image_input)

            # Force load into memory to catch truncated/corrupted files
            img.load()
        except Exception as e:
            raise ImageProcessingError(f"Failed to decode image: {str(e)}")

        # Check dimensions
        w, h = img.size
        if w < MIN_IMAGE_DIMENSION or h < MIN_IMAGE_DIMENSION:
            raise ImageProcessingError(f"Image too small/degraded: {w}x{h} px")

        # Correct EXIF orientation if present
        try:
            img = ImageOps.exif_transpose(img)
        except Exception as e:
            logger.debug(f"EXIF orientation correction skipped: {e}")

        # Convert palette/RGBA to RGB
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Resize if oversized
        if max(w, h) > MAX_IMAGE_DIMENSION:
            scale = MAX_IMAGE_DIMENSION / max(w, h)
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"Resized image from {w}x{h} to {new_size}")

        return img

    @classmethod
    def generate_ocr_variants(cls, pil_img: Image.Image) -> Dict[str, Image.Image]:
        """Generate preprocessing variants for OCR benchmarking:
        1. 'standard': Original RGB image
        2. 'grayscale': Grayscale conversion preserving subtle ink
        3. 'enhanced': Contrast-limited adaptive histogram equalization (CLAHE)
        4. 'threshold': Mild Otsu/Bilateral binarization
        """
        variants = {"standard": pil_img}

        rgb_np = np.array(pil_img)
        if len(rgb_np.shape) == 3 and rgb_np.shape[2] == 3:
            gray_np = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2GRAY)
        else:
            gray_np = rgb_np

        variants["grayscale"] = Image.fromarray(gray_np)

        # 3. Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_np = clahe.apply(gray_np)
        variants["enhanced"] = Image.fromarray(enhanced_np)

        # 4. Bilateral filter + Otsu thresholding
        denoised = cv2.bilateralFilter(gray_np, 5, 50, 50)
        _, thresh_np = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants["threshold"] = Image.fromarray(thresh_np)

        return variants

    @staticmethod
    def is_blank_or_degraded(pil_img: Image.Image) -> Tuple[bool, str]:
        """Detect whether an image is completely blank, solid color, or severely degraded."""
        gray = np.array(pil_img.convert("L"))
        variance = float(np.var(gray))
        if variance < 20.0:
            return True, f"Image lacks contrast/content (variance: {variance:.1f})"
        return False, "Normal"
