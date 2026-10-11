# Tarang Receipt Intelligence — REST API Specification

**Base URL:** `http://localhost:8000`  
**Interactive Swagger Docs:** `http://localhost:8000/docs`  
**OpenAPI Specification:** `http://localhost:8000/openapi.json`  

---

## 1. Endpoints

### 1.1 Health Check: `GET /health`

Returns service health, version, and active OCR engine availability.

#### Response `200 OK`
```json
{
  "status": "healthy",
  "ocr_provider": "TesseractOCRProvider",
  "ocr_available": true,
  "version": "1.0.0"
}
```

---

### 1.2 Predict Claim: `POST /predict`

Accepts multipart receipt photo upload along with rep claim metadata. Performs image preprocessing, OCR, duplicate checking, validation against employee roster, policy evaluation, and issues an `approve` or `review` decision.

#### Request Parameters (Multipart Form-Data)
| Parameter | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `file` | File Binary | Yes | Photographed receipt (JPEG, PNG, WebP) | `receipt.jpg` |
| `claim_id` | String | Yes | Unique claim identifier | `CLM-31086` |
| `emp_id` | String | Yes | Claimant Employee ID | `TPD-0412` |
| `category` | String | Yes | Fuel, Food, Lodging, Local travel, Courier, Parking | `Food` |
| `amount_claimed` | String | Yes | Claimed amount in INR | `350.00` |
| `expense_date` | String | No | Date of expense (YYYY-MM-DD) | `2026-07-20` |
| `rep_comment` | String | No | Freehand rep comment | `Lunch with stockist` |

#### Example cURL
```bash
curl -X POST http://localhost:8000/predict \
  -F "file=@sample_receipt.jpg" \
  -F "claim_id=CLM-31086" \
  -F "emp_id=TPD-0412" \
  -F "category=Food" \
  -F "amount_claimed=350.00" \
  -F "expense_date=2026-07-20"
```

#### Example Python Client
```python
import requests

url = "http://localhost:8000/predict"
files = {"file": open("receipt.jpg", "rb")}
data = {
    "claim_id": "CLM-31086",
    "emp_id": "TPD-0412",
    "category": "Food",
    "amount_claimed": "350.00",
    "expense_date": "2026-07-20",
}
resp = requests.post(url, files=files, data=data)
print(resp.json())
```

#### Response `200 OK` (Approved)
```json
{
  "claim_id": "CLM-31086",
  "decision": "approve",
  "reason": "Receipt amount matches the submitted claim; mandatory fields and applicable policy checks passed.",
  "extracted_fields": {
    "vendor_name": "Hotel Rajdhani Dhaba",
    "bill_date": "2026-07-20",
    "bill_number": "RD-8891",
    "gstin": "27AABCR1234F1Z9",
    "bill_amount": 350.0
  },
  "validation_status": "PASSED",
  "validation_errors": [],
  "policy_checks_passed": true,
  "policy_review_reasons": [],
  "ocr_provider": "TesseractOCRProvider",
  "processing_time_ms": 782.4,
  "warnings": []
}
```

#### Response `200 OK` (Routed to Review)
```json
{
  "claim_id": "CLM-31087",
  "decision": "review",
  "reason": "Review required: receipt amount differs from the submitted claim (Receipt amount (₹350.00) differs from claimed amount (₹500.00) beyond policy tolerance (±₹10)).",
  "extracted_fields": {
    "vendor_name": "Hotel Rajdhani Dhaba",
    "bill_date": "2026-07-20",
    "bill_number": "RD-8891",
    "gstin": "27AABCR1234F1Z9",
    "bill_amount": 350.0
  },
  "validation_status": "FAILED",
  "validation_errors": [
    "Receipt amount (₹350.00) differs from claimed amount (₹500.00) beyond policy tolerance (±₹10)"
  ],
  "policy_checks_passed": true,
  "policy_review_reasons": [],
  "ocr_provider": "TesseractOCRProvider",
  "processing_time_ms": 745.1,
  "warnings": []
}
```
