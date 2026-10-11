# Tarang Pharma Distribution — Submission Form

---

## Question 1: GitHub Repository URL

**Repository URL:**  
`https://github.com/AbhijeetArunGore/Tarang-Receipt-Intelligence`

*Repository is public, clean, and includes all source modules, tests, configuration scripts, reports, documentation, and the final predictions artifact (`predictions.csv`).*

---

## Question 2: What did you build, what decision does it support, and what are the numbers?

### What Was Built
We built an end-to-end receipt intelligence and expense audit platform tailored specifically for Tarang Pharma Distribution's field operations in Nagpur, Maharashtra. The system ingests photographed expense bills, extracts five key fields (`vendor`, `receipt_date`, `receipt_number`, `gstin`, `total_amount`), executes multi-point validation against representative claims and employee records, evaluates Tarang Field Expense Policy v3.2, and issues an authoritative recommendation: **`approve`** (eligible for straight-through reimbursement) or **`review`** (requires human clerk inspection).

### What Decision It Supports
The platform supports weekly reimbursement processing for 160 medical representatives across Maharashtra. It automates routine, clean, compliant expenses under ₹2,000, while routing high-value claims, unreadable photos, amount mismatches, and suspected duplicate invoices to Finance Controller Nilesh Agrawal's team with clear evidence-backed explanations.

### The Measured Numbers
1. **Total Test Claims Processed:** **190 claims** (`claims_test.csv`).
2. **Automated Approvals (Straight-Through Processing):** **22 claims (11.6%)** automatically approved with zero human touch.
3. **Routed to Human Review:** **168 claims (88.4%)** routed to finance clerks for verification (including 33 claims with missing server uploads, high-value claims ≥ ₹2,000, and unreadable thermal slips).
4. **Field Extraction Benchmark Accuracy (on 60 verified receipts):**
   - Vendor Name (Normalized): **50.0%**
   - GSTIN (Normalized): **58.3%**
   - Bill Date (Normalized): **35.0%**
   - Bill Amount (Normalized): **23.3%**
   - Bill Number (Normalized): **21.7%**
5. **False Approval Rate (Financial Risk):** **0.0% (0 claims)** across all evaluated reference receipts. Zero invalid claims were paid out.
6. **Financial Exposure from Erroneous Approvals:** **₹0.00**.
7. **Monthly Staff Capacity Released:** **~109 hours / month** across 2,400 monthly claims (saving 2.5 minutes on assisted pre-filled reviews and 3.5 minutes on auto-approvals).
8. **Monthly & Annual Financial Benefit:** **₹20,340 net benefit / month** (**₹2.44 Lakhs annually**) after infrastructure costs, operating at **₹0.00 marginal inference cost**.

---

## Question 3: Expected Hidden-Test Score

Based on empirical performance observed across our verified 60-receipt benchmark and the distribution of the 190 test claims, here is the realistic expected performance on an unseen hidden test set:

| Field / Output | Expected Normalized Match Accuracy Range | Evaluation Basis & Distribution Context |
| :--- | :--- | :--- |
| **Vendor Name** | **45.0% – 55.0%** | Backed by Nagpur regional merchant dictionary and header layout anchors; limited by severe thermal paper fading. |
| **Bill Date** | **30.0% – 40.0%** | Normalized to ISO `YYYY-MM-DD` within ±3-day tolerance; constrained by ambiguous date stamps and faint print. |
| **Bill Number** | **20.0% – 28.0%** | Anchored on `Invoice`, `Bill No`, `Ticket` keywords; affected by non-standard receipt layouts and missing numbers on local transit. |
| **GSTIN** | **52.0% – 62.0%** | Exact 15-character checksum and regex validation. High accuracy because small vendors have no GSTIN (correctly left null), while printed GSTINs are detected. |
| **Bill Amount** | **22.0% – 30.0%** | Enforces strict ±₹10 tolerance. Constrained by thermal receipts and multi-item subtotal vs grand total ambiguity. |
| **Approve / Review Decision** | **85.0% – 92.0% Agreement** | High agreement with conservative policy ground truth because the decision engine reliably defaults to human review whenever extraction is uncertain. |

*Distribution Shift Note:* In `claims_test.csv`, **17.4% (33 claims)** completely lack physical images on the server due to mobile sync failures. On these claims, field accuracy will be 0.0% (serialized as blank per schema), but decision accuracy will be 100% correct because all 33 are appropriately routed to `review`.

---

## Question 4: How Do You Know It Works?

We verified system correctness through empirical, reproducible testing rather than theoretical assumptions:
1. **Stratified Reference Set (`reports/reference_set.csv`):** Sampled 60 real receipts across all 6 expense categories (Fuel, Food, Lodging, Local travel, Courier, Parking) from historical training data. Transcriptions were independently cross-checked against actual image properties.
2. **Empirical Evaluation Pipeline (`scripts/evaluate.py`):** Tested the full OCR and policy pipeline on the reference set, generating `reports/metrics.json` and `reports/evaluation.md`.
3. **Automated Test Suite (29 passing pytest tests):**
   - Data loading & deterministic image mapping (`tests/test_data.py`)
   - Normalizers for currency, multi-format dates, GSTINs, and strings (`tests/test_normalization.py`)
   - Safe CV loading, orientation fix, and corrupt file rejection (`tests/test_image_processing.py`)
   - OCR abstraction, mock providers, and graceful degradation (`tests/test_ocr.py`)
   - Perceptual image hashing (dHash) and invoice collision detection (`tests/test_duplicate_detection.py`)
   - Policy threshold rules and grade caps (`tests/test_policy.py`)
   - Decision routing and explanation synthesis (`tests/test_decisions.py`)
   - Full FastAPI REST endpoints (`tests/test_api.py`)
   - Strict 190-row submission template conformity (`tests/test_submission.py`)
4. **End-to-End Prediction Verification:** Generated `predictions.csv` for all 190 test claims, verifying row count, column order, valid decision vocabulary, and null serialization.

---

## Question 5: What Did You Change or Challenge in Nilesh's Request?

### What We Challenged
In his initial email, Finance Controller Nilesh Agrawal requested:
> *"Anything under Rs 2,000 gets approved off the photo, clerks look at the big ones only."*

We **strongly challenged** unconditional sub-₹2,000 automatic approval based on the real data:
1. **89.5% of all Tarang claims fall under ₹2,000.** Unconditional approval would effectively blindfold Finance to 9 out of 10 expenses.
2. **Missing Receipts:** 17.4% of test claims have no receipt image on the server. Unconditional approval would auto-pay unverified claims.
3. **Duplicate Exploitation:** As Accounts Executive Priya Bhende reported, duplicate bills (such as Hotel Shubham) are submitted with slight amount differences.
4. **Policy v3.2 Non-Compliance:** Unconditional approval would bypass vehicle number checks on fuel bills and mandatory GSTINs on lodging stays.

### What We Implemented Instead: Gated Automatic Approval
We restricted automatic approval under ₹2,000 so that it triggers **only** when all defensive controls pass:
- Physical receipt image is present, decoded, and legible.
- Bill amount extracted with high confidence and matches claimed amount within policy tolerance (±₹10).
- Bill date aligns within 3 days.
- No duplicate image hash or invoice collision detected.
- Mandatory category rules pass (e.g., fuel vehicle number matches employee's registered vehicle).
Any failure safely routes to human review.

---

## Question 6: What is Wrong with Your Implementation or the Supplied Data?

### Data Issues Identified in Supplied Pack
1. **Server Image Upload Sync Failure:** 33 out of 190 claims in `claims_test.csv` (17.4%) and 10 claims in `claims_train.csv` (3.5%) do not exist in `images/`. The mobile app stored local device paths (`/storage/emulated/0/...`) before upload confirmation.
2. **Free-Hand String Contamination:** Field reps typed amounts as `"Rs 2352"`, `"3,539.00"`, `"Rs. 30"`, rather than numeric floats, requiring custom parsing.
3. **Noisy Historical Clerk Labels:** Historical clerk transcriptions in `claims_train.csv` contain human errors, typos (e.g. `"Krisnha Hotel Comforts"`), and admitted fatigue (clerk ignoring daily parking slips).
4. **Thermal Paper Degradation:** Receipts from local fuel stations in Nagpur exhibit heavy fading, faint print, and severed dot-matrix digits.

### Implementation Limitations
1. **Local OCR Character Substitution on Faded Receipts:** Tesseract 5.4 struggles with low-contrast, faded thermal slips, leading to a conservative straight-through processing rate (11.6% auto-approved; remainder routed to review).
2. **Vendor Name Formatting Variance:** While known merchants are mapped via dictionary, unindexed small dhabas are captured from top lines and may include noise like "Cash Memo".
3. **Devanagari / Regional Script Support:** Slips containing purely Marathi/Hindi printed script are unsupported by the English OCR model.

---

## Question 7: Cost Per Claim and Monthly Cost

### Measured Pricing & Architecture Arithmetic
* **OCR Provider:** Local Tesseract OCR v5.4.0 (Open-source on host CPU).
* **External API Calls per Claim:** **0**
* **Inference Cost per Claim:** **₹0.00**
* **Monthly Inference Cost (2,400 claims):** **₹0.00**

### Operating Costs
* **Cloud VM / Hosting Allocation:** ~**₹2,500 / month** (standard 4-core CPU instance).
* **Total Monthly Software Cost:** **₹2,500 / month**
* **Cost per Claim:** $\frac{₹2,500}{2,400} = \mathbf{₹1.04\text{ per claim}}$  
  *(Drastically lower than the clerk cost of ₹31.67 per claim, fulfilling Nilesh's requirement).*

### Monthly Financial Net Benefit
* **Monthly Volume:** 2,400 claims
* **Manual Time Eliminated:** Assisted review pre-fills 5 fields, saving 2.5 minutes on reviewed claims; STP saves 3.5 minutes on auto-approved claims.
* **Monthly Clerk Hours Released:** **~109 hours / month**
* **Gross Labour Value:** $109\text{ hrs} \times ₹237.50/\text{hr} = \mathbf{₹25,840 / \text{month}}$
* **Net Monthly Benefit:** $₹25,840 - ₹2,500\text{ (Hosting)} - ₹3,000\text{ (Maintenance)} = \mathbf{₹20,340 / \text{month}}$ (**₹2.44 Lakhs annually**).

---

## Question 8: What Did You Deliberately Leave Out?

1. **No Black-Box "Fraud Score" ML Model:** Discarded training an XGBoost or Random Forest fraud classifier. Historical clerk notes reflect workload triage rather than verified fraud ground truth. Deterministic rule-based checks (duplicate hashing, amount mismatch, vehicle verification) provide auditable, defensible controls without false-positive black-box risk.
2. **No Complex Multi-Agent Framework (LangGraph / AutoGen):** Discarded. Multi-agent negotiation adds latency, stochastic variance, and unnecessary complexity to what is fundamentally an OCR parsing and deterministic validation pipeline.
3. **No Vector Database (RAG):** Tarang's policy is a concise 8-clause document. Encoding rules directly in Python functions guarantees 100% precision, zero retrieval latency, and testability.
4. **No Unattended High-Risk Approvals:** We deliberately omitted auto-approving claims ≥ ₹2,000 or claims with ambiguous amounts. Human review remains mandatory for material financial decisions.

---

## Question 9: AI Usage and Screen Recording

### AI Tools Used
* **AI Coding Assistant:** Antigravity IDE Assistant powered by Google DeepMind Gemini models for code generation, unit testing, and markdown documentation.
* **OCR / Vision Engines:** Local Tesseract OCR v5.4.0 (`tesseract.exe`) via `pytesseract`.
* **Multimodal API Interface:** Structured adapter for OpenAI/Gemini Vision API (configured behind `.env.example`).
* **Paid Calls Made:** **None ($0.00 / ₹0.00 spent).** All processing ran locally.
* **Where AI Helped:** Data audit parsing, regex anchor structuring, and test parametrization.
* **Where AI Misled:** Attempting naive numeric comparisons on string amount fields and assuming all sub-₹2,000 claims should be approved unconditionally.

### Screen Recording
* **Script:** Completed in `docs/RECORDING_SCRIPT.md` (3-minute timed script).
* **Recording Status:** [Verified Demonstration Video Pending Upload by User / Placeholder]
* **Demo URL:** `https://youtu.be/tarang-receipt-intelligence-demo` *(Placeholder: record and attach final YouTube/Loom URL as instructed in submission guidelines)*

---

## Question 10: Three Things a Person Needs on Monday

If a new engineer or finance operator takes over this repository on Monday morning, here are the three essential things they must know:

1. **How to Run the Entire System Cleanly:**
   ```bash
   pip install -r requirements.txt
   # Verify Tesseract OCR is installed at C:\Users\abhis\AppData\Local\Programs\Tesseract-OCR\tesseract.exe
   python scripts/predict_batch.py    # Generates predictions.csv
   pytest -v                          # Runs all 29 automated tests
   streamlit run app/ui.py            # Launches web testing dashboard
   uvicorn app.api:app --reload       # Launches FastAPI service on port 8000
   ```
2. **How Decisions Are Made (The Safety Invariant):**  
   The system will **never** auto-approve a claim unless: (a) receipt image is resolved, (b) amount matches within ₹10, (c) date is within 3 days, (d) no duplicate invoice exists, and (e) policy limits pass. If any check fails, it safely defaults to `review`.
3. **The Urgent Fix Required for Field IT (Sameer Joshi):**  
   17.4% of claims fail because the mobile app saves the local file path before the photo finishes uploading to the server. Issue a patch to the Android app ensuring upload confirmation before claim database submission.
