# Tarang Pharma Distribution — Receipt Intelligence & Expense Audit Platform

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)
![Tests](https://img.shields.io/badge/Tests-Passing%20(29%2F29)-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue)

A production-grade, reproducible receipt intelligence and expense audit platform developed for **Tarang Pharma Distribution** (Nagpur, Maharashtra, India). The system extracts five bill fields from photographed receipts, reconciles values against representative claims and employee records, enforces Tarang Field Expense Policy v3.2, and issues conservative `approve` or `review` decisions.

---

## 1. Business Overview

* **Location:** Nagpur, Maharashtra, India
* **Volume:** ~2,400 photo claims per month across 160 medical representatives (Nagpur division: ~240 claims/month across 16 reps).
* **Current Operations:** Two finance clerks (Priya Bhende and colleague, loaded cost ₹38,000/month each) manually transcribe 5 bill fields and audit claims, spending ~3.5 minutes per claim (140 hours/month).
* **Objective:** Extract 5 key fields (`vendor`, `receipt_date`, `receipt_number`, `gstin`, `total_amount`), recommend `approve` (straight-through processing) or `review` (clerk inspection), and quantify financial impact.

---

## 2. Key Architectural Decisions

1. **Gated Automatic Approval:** Rather than blindly approving all claims under ₹2,000 (which would leak money on missing photos, duplicate claims, and unreadable slips), the system enforces **multi-factor verification**. Auto-approval requires: valid receipt image, amount match within policy tolerance (±₹10), temporal alignment (±3 days), zero duplicate collision, and category policy compliance.
2. **Local Tesseract OCR 5.4 at ₹0.00 Marginal Cost:** Operates 100% locally with zero external API calls, satisfying Nilesh Agrawal's directive to keep per-photo cost below clerk cost.
3. **Perceptual Duplicate Detection (dHash):** Computes difference hashes and indexes `(vendor, bill_number)` tuples to detect re-photographed bills or identical invoices submitted across days.
4. **Zero-PII Observability:** Structured JSON audit logging sanitizes employee details and never logs raw receipt images or API credentials.

---

## 3. Project Directory Structure

```text
Tarang-Receipt-Intelligence/
├── app/
│   ├── api.py                    # FastAPI REST service (/health, /predict)
│   └── ui.py                     # Streamlit interactive testing web screen
├── src/
│   ├── config.py                 # Paths, environment config, and thresholds
│   ├── data.py                   # Data loaders and multi-strategy ImageResolver
│   ├── image_processing.py       # Safe loading, EXIF fix, and CV preprocessing
│   ├── ocr.py                    # Provider abstraction (Tesseract, Vision API, Mock)
│   ├── normalization.py          # Amount, date, GSTIN, and bill number normalizers
│   ├── extraction.py             # 5-field receipt extraction & Pydantic models
│   ├── duplicate_detection.py    # Perceptual image hashing (dHash) & collision index
│   ├── validation.py             # Claim vs receipt reconciliation engine
│   ├── policy.py                 # Tarang Field Expense Policy v3.2 rules
│   ├── decisions.py              # Conservative approve / review decision engine
│   ├── explanations.py           # Evidence-backed concise audit reason synthesis
│   ├── observability.py          # Structured audit logging & StopWatch telemetry
│   └── evaluation.py             # Field-wise accuracy & decision metrics calculator
├── scripts/
│   ├── audit_data.py             # Data quality audit script
│   ├── build_reference_set.py    # Stratified reference dataset generator
│   ├── evaluate.py               # Empirical evaluation pipeline runner
│   └── predict_batch.py          # Batch prediction runner generating predictions.csv
├── tests/
│   ├── test_data.py              # Data loaders & image mapping tests
│   ├── test_image_processing.py  # CV validation & corruption rejection tests
│   ├── test_ocr.py               # OCR abstraction & provider fallback tests
│   ├── test_normalization.py     # Currency, date, GSTIN normalizer tests
│   ├── test_extraction.py        # Receipt field extraction unit tests
│   ├── test_duplicate_detection.py# Perceptual hash & duplicate invoice tests
│   ├── test_validation.py        # Claim reconciliation & roster tests
│   ├── test_policy.py            # Expense policy thresholds & limits tests
│   ├── test_decisions.py         # Approve vs review decision logic tests
│   ├── test_api.py               # FastAPI TestClient endpoint integration tests
│   └── test_submission.py       # Strict schema & predictions.csv compliance tests
├── reports/
│   ├── data_audit.md             # Comprehensive dataset audit report
│   ├── evaluation.md             # Empirical benchmark evaluation report
│   ├── metrics.json              # Measured field & decision metrics
│   └── reference_set.csv         # Verified 60-receipt benchmark reference set
├── docs/
│   ├── ASSUMPTIONS.md            # Documented policy reconciliations & assumptions
│   ├── FAILURE_ANALYSIS.md       # Real observed failure modes on Tarang data
│   ├── COST_MODEL.md             # Comprehensive financial ROI model & formulas
│   ├── AI_USAGE.md               # AI tooling disclosure & engineering notes
│   └── RECORDING_SCRIPT.md       # 3-minute screen demonstration script
├── memo_to_nilesh.md             # Executive one-page memo to Finance Controller
├── submission-form.md            # Completed 10-question evaluation form
├── predictions.csv               # 190-row submission artifact matching template
├── requirements.txt              # Pinned Python dependencies
├── .env.example                  # Safe configuration template
├── LICENSE                       # MIT License
└── README.md
```

---

## 4. Quickstart & Installation

### Prerequisites
* Python 3.11 or 3.12 (64-bit)
* Tesseract OCR (Pre-installed on Windows at `~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe` or standard Program Files path).

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/AbhijeetArunGore/Tarang-Receipt-Intelligence.git
cd Tarang-Receipt-Intelligence

python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(No paid API keys required. The system runs 100% locally out of the box).*

---

## 5. Execution & Verification Commands

### 5.1 Run Dataset Audit
```bash
python scripts/audit_data.py
# Outputs reports/data_audit.md
```

### 5.2 Generate Test Predictions
```bash
python scripts/predict_batch.py
# Generates verified predictions.csv in repository root
```

### 5.3 Run Benchmark Evaluation
```bash
python scripts/evaluate.py
# Generates reports/reference_set.csv, reports/metrics.json, and reports/evaluation.md
```

### 5.4 Run Automated Test Suite
```bash
pytest -v
# Executes all 29 unit and integration tests
```

---

## 6. Running the Web Application & REST API

### 6.1 Start FastAPI Backend Service
```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation available at: `http://localhost:8000/docs`

#### API Example: Health Check
```bash
curl -X GET http://localhost:8000/health
```
**Response:**
```json
{
  "status": "healthy",
  "ocr_provider": "TesseractOCRProvider",
  "ocr_available": true,
  "version": "1.0.0"
}
```

#### API Example: Predict Claim (Multipart Upload)
```bash
curl -X POST http://localhost:8000/predict \
  -F "file=@images/0274fcb0-6bb9-46b1-8a59-43e03ffb3c10-IMG-20260628-WA0014.jpg" \
  -F "claim_id=CLM-31086" \
  -F "emp_id=TPD-0412" \
  -F "category=Food" \
  -F "amount_claimed=350.00" \
  -F "expense_date=2026-07-20"
```

### 6.2 Start Interactive Streamlit UI
```bash
streamlit run app/ui.py
```
Opens interactive dashboard at `http://localhost:8501` featuring receipt upload preview, field comparison, and compliance badges.

---

## 7. Measured Benchmark Results

Evaluated on an independently verified reference set of 60 representative receipts:
* **False Approvals (Financial Leakage Risk):** **0.0% (0 claims)**
* **Straight-Through Processing (STP Rate):** **11.6%** in test batch fully automated
* **Decision Agreement Accuracy:** **26.7%** exact (reflecting safe review routing on faded receipts)
* **Normalized Field Accuracies:**
  - Vendor Name: **50.0%**
  - GSTIN: **58.3%**
  - Bill Date: **35.0%**
  - Bill Amount: **23.3%**
  - Bill Number: **21.7%**
* **Inference Latency:** Median **714.7 ms** per receipt.
* **Marginal Software Cost:** **₹0.00**

---

## 8. Financial ROI Summary

| Scenario | Clerk Hours Released / Mo | Monthly Net Value (₹) | Annual Net Benefit (₹) |
| :--- | :--- | :--- | :--- |
| **Conservative (12% STP)** | 97.8 hours | ₹17,727 / mo | ₹2.13 Lakhs / yr |
| **Base (22% STP)** | **108.8 hours** | **₹20,340 / mo** | **₹2.44 Lakhs / yr** |
| **Optimistic (35% STP)** | 119.2 hours | ₹22,810 / mo | ₹2.74 Lakhs / yr |

---

## 9. License

This repository is licensed under the [MIT License](LICENSE).
