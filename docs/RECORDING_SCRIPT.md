# Tarang Pharma Distribution — Screen Recording Demonstration Script

**Target Duration:** Exactly 3 minutes (180 seconds)  
**Presenter:** Abhijeet Arun Gore  
**Project:** Receipt Intelligence & Expense Audit Platform  

---

### [0:00 – 0:20] Segment 1: Executive Context & Architecture
* **Visual:** Display GitHub repository root and architecture diagram.
* **Spoken Narration:**  
  *"Hello! This is the Receipt Intelligence and Expense Audit Platform built for Tarang Pharma Distribution in Nagpur, Maharashtra. Tarang processes 2,400 monthly photo claims from 160 medical reps, consuming 140 clerk hours each month. Finance Controller Nilesh Agrawal requested an automated system to extract 5 bill fields and approve claims under ₹2,000. We built a modular, production-grade system using local Tesseract OCR, deterministic policy controls, perceptual duplicate detection, FastAPI, and Streamlit—running at ₹0.00 marginal inference cost."*

---

### [0:20 – 1:00] Segment 2: Interactive Web Screen & Clean Approval
* **Visual:** Switch to Streamlit UI (`localhost:8501`).
* **Actions:**
  1. Show sidebar showing "OCR Active: TesseractOCRProvider".
  2. Input claim details: `CLM-31086`, Rep `TPD-0412`, Category `Food`, Amount `₹350.00`, Date `2026-07-20`.
  3. Upload sample receipt image (`IMG_20260718_111930.jpg`).
  4. Click "Audit & Verify Receipt".
* **Spoken Narration:**  
  *"Here is our Streamlit dashboard. In the left panel, we enter representative details and upload a genuine receipt photograph. When we click 'Audit & Verify Receipt', the system performs image orientation correction, runs OCR, extracts all 5 bill fields—Vendor Name, Bill Date, Bill Number, GSTIN, and Bill Amount—and reconciles them against the claim and policy v3.2. As you see here, the amount matches, mandatory fields pass, and the system issues an immediate green decision: APPROVE with straight-through processing."*

---

### [1:00 – 1:35] Segment 3: Real Review Condition & Governance Controls
* **Visual:** Remain on Streamlit UI.
* **Actions:**
  1. Change claimed amount to `₹500.00` (creating intentional discrepancy against ₹350 receipt).
  2. Click "Audit & Verify Receipt".
  3. Show the amber `REVIEW` banner and specific validation error (`VAL_AMOUNT_MISMATCH`).
* **Spoken Narration:**  
  *"Now let's demonstrate our conservative governance controls. If the rep claims ₹500 for a ₹350 bill, the system instantly flags `VAL_AMOUNT_MISMATCH` and routes the claim to REVIEW. Similarly, if a lodging bill lacks a mandatory GSTIN, or if an image hash collides with a previously submitted invoice, the system blocks automatic approval. This directly addresses Nilesh's requirement: claims under ₹2,000 are not unconditionally rubber-stamped, preventing financial fraud."*

---

### [1:35 – 2:00] Segment 4: FastAPI REST Service & Health Check
* **Visual:** Switch browser tab to FastAPI Swagger docs (`localhost:8000/docs`).
* **Actions:**
  1. Execute `GET /health` showing `"status": "healthy"`, `"ocr_available": true`.
  2. Show `POST /predict` schema supporting multipart image uploads and structured Pydantic response.
* **Spoken Narration:**  
  *"Behind the UI is a high-performance FastAPI service. The GET /health endpoint verifies OCR engine status and system availability. The POST /predict endpoint accepts direct multipart image uploads and claim metadata, returning structured JSON with extracted fields, validation findings, latency, and audit reasons in under 800 milliseconds."*

---

### [2:00 – 2:30] Segment 5: Empirical Evaluation & Financial Cost Model
* **Visual:** Open `reports/evaluation.md` and `docs/COST_MODEL.md`.
* **Spoken Narration:**  
  *"To verify performance, we benchmarked the system against a verified reference set of 60 representative receipts across all 6 categories. Critical finding: False approvals were exactly 0.0%, meaning zero bad claims were auto-approved. In our financial model for 2,400 monthly claims, assisted review releases ~109 hours of clerk time each month—a net economic value of ₹2.44 Lakhs annually at zero marginal inference cost."*

---

### [2:30 – 3:00] Segment 6: Predictions.csv, Automated Tests & Wrap-Up
* **Visual:** Switch to terminal in VS Code.
* **Actions:**
  1. Display `predictions.csv` (190 rows matching `sample_submission.csv` schema).
  2. Run `pytest -v` showing all test suites passing.
* **Spoken Narration:**  
  *"Finally, here is `predictions.csv`, matching the test template across all 190 rows with compliant decision vocabulary. Our automated test suite covers data loading, normalizers, policy rules, decisions, API endpoints, and submission conformity. The platform is completely reproducible, documented, and ready for deployment. Thank you!"*
