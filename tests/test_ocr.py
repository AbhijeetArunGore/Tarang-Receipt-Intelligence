"""Unit tests for OCR provider interfaces, fallbacks, and mock engines."""

import pytest
from PIL import Image

from src.ocr import (
    BaseOCRProvider,
    MockOCRProvider,
    TesseractOCRProvider,
    UnavailableOCRProvider,
    VisionAPIProvider,
    get_ocr_provider,
)


def test_unavailable_provider():
    provider = UnavailableOCRProvider("Test unavailable reason")
    assert provider.is_available() is False

    dummy_img = Image.new("RGB", (100, 100), color="white")
    res = provider.extract_text(dummy_img)
    assert res.status == "unavailable"
    assert res.text == ""
    assert res.confidence == 0.0
    assert "Test unavailable" in res.error_message


def test_mock_provider():
    mock_text = "PETROL PUMP NAGPUR\nBill: 1234\nAmount: Rs 500"
    provider = MockOCRProvider(mock_text=mock_text)
    assert provider.is_available() is True

    dummy_img = Image.new("RGB", (100, 100), color="white")
    res = provider.extract_text(dummy_img)
    assert res.status == "success"
    assert res.text == mock_text
    assert len(res.lines) == 3
    assert res.confidence == 0.95
    assert res.estimated_cost_inr == 0.0


def test_vision_api_provider_without_key():
    provider = VisionAPIProvider(api_key="")
    assert provider.is_available() is False

    dummy_img = Image.new("RGB", (100, 100), color="white")
    res = provider.extract_text(dummy_img)
    assert res.status == "unavailable"
    assert "VISION_API_KEY is not configured" in res.error_message


def test_get_ocr_provider_factory():
    p_mock = get_ocr_provider("mock")
    assert isinstance(p_mock, MockOCRProvider)

    p_none = get_ocr_provider("unknown_provider")
    assert isinstance(p_none, UnavailableOCRProvider)


def test_tesseract_provider_initialization():
    provider = TesseractOCRProvider()
    assert isinstance(provider, BaseOCRProvider)
    # Check that is_available returns a boolean without throwing an unhandled exception
    available = provider.is_available()
    assert isinstance(available, bool)
