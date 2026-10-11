"""Unit tests for image loading, validation, and CV preprocessing."""

import io
import pytest
from PIL import Image
import numpy as np

from src.image_processing import (
    ImageProcessor,
    ImageProcessingError,
    ALLOWED_EXTENSIONS,
)


def test_validate_file_extensions():
    assert ImageProcessor.validate_file("receipt.jpg")[0] is False  # not exists
    # bytes input
    img_bytes = io.BytesIO()
    Image.new("RGB", (100, 100), color="white").save(img_bytes, format="JPEG")
    valid, _ = ImageProcessor.validate_file(img_bytes.getvalue())
    assert valid is True


def test_load_valid_image():
    # Create synthetic test image
    img = Image.new("RGB", (200, 200), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    loaded = ImageProcessor.load_image(buf)
    assert isinstance(loaded, Image.Image)
    assert loaded.size == (200, 200)


def test_corrupt_image_rejection():
    corrupt_bytes = b"NOT_A_REAL_IMAGE_DATA_12345"
    with pytest.raises(ImageProcessingError):
        ImageProcessor.load_image(corrupt_bytes)


def test_generate_ocr_variants():
    # Synthetic image with pattern
    arr = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(arr)

    variants = ImageProcessor.generate_ocr_variants(img)
    assert "standard" in variants
    assert "grayscale" in variants
    assert "enhanced" in variants
    assert "threshold" in variants

    assert variants["standard"].size == (100, 100)
    assert variants["grayscale"].mode == "L"


def test_detect_blank_image():
    # Solid white image has variance 0
    blank = Image.new("RGB", (100, 100), color="white")
    is_blank, reason = ImageProcessor.is_blank_or_degraded(blank)
    assert is_blank is True

    # Real textured image
    arr = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    textured = Image.fromarray(arr)
    is_blank, _ = ImageProcessor.is_blank_or_degraded(textured)
    assert is_blank is False


def test_load_pil_image_and_uploaded_file():
    # Direct PIL image
    pil_img = Image.new("RGB", (150, 150), color="blue")
    loaded = ImageProcessor.load_image(pil_img)
    assert isinstance(loaded, Image.Image)
    assert loaded.size == (150, 150)

    # Simulated Streamlit UploadedFile
    class MockUploaded:
        def __init__(self, data):
            self.data = data
        def getvalue(self):
            return self.data

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG")
    mock_file = MockUploaded(buf.getvalue())
    loaded_mock = ImageProcessor.load_image(mock_file)
    assert isinstance(loaded_mock, Image.Image)
    assert loaded_mock.size == (150, 150)

