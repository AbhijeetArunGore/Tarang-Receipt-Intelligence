"""Automated API tests for FastAPI endpoints using TestClient."""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api import app


client = TestClient(app)


def test_api_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ocr_provider" in data
    assert data["version"] == "1.0.0"


def test_api_predict_endpoint_valid():
    # Create synthetic test receipt image
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("test_receipt.jpg", buf, "image/jpeg")}
    data = {
        "claim_id": "CLM-99901",
        "emp_id": "TPD-0412",
        "category": "Food",
        "amount_claimed": "350.00",
        "expense_date": "2026-07-20",
    }

    response = client.post("/predict", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["claim_id"] == "CLM-99901"
    assert res_data["decision"] in ("approve", "review")
    assert "extracted_fields" in res_data
    assert "processing_time_ms" in res_data


def test_api_predict_empty_file():
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    data = {
        "claim_id": "CLM-99902",
        "emp_id": "TPD-0412",
        "category": "Food",
        "amount_claimed": "100.00",
    }
    response = client.post("/predict", files=files, data=data)
    assert response.status_code == 400
