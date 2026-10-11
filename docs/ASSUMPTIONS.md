# Tarang Pharma Distribution — Engineering Assumptions & Policy Reconciliations

**Document Version:** 1.0.0  
**Status:** Defensible Engineering Baseline  
**Project:** Receipt Intelligence & Expense Audit Platform  

---

## 1. Context & Business Intent

Tarang Pharma Distribution employs approximately 160 medical representatives across Maharashtra, processing roughly 2,400 expense claims per month. Currently, two finance clerks manually re-type 5 bill fields per receipt and review each claim. Finance Controller Nilesh Agrawal requested an automated OCR system with automatic approval for claims under ₹2,000 to eliminate clerk backlog and save operational expenditure.

---

## 2. Policy Reconciliations & Contradiction Resolution

### 2.1 Nilesh's Brief vs. Policy v3.2 Controls (Sub-₹2,000 Claims)

* **Documented Conflict:**  
  In the email thread, Nilesh states: *"Anything under Rs 2,000 gets approved off the photo, clerks look at the big ones only."*  
  Conversely, Expense Policy v3.2 Section 3 mandates: *"A claim without a readable bill photo is queried back to the rep."* Section 8 explicitly classifies duplicate submissions or altered receipts as disciplinary misconduct. Furthermore, clerk Priya Bhende noted in correspondence that duplicate bills have slipped through because amounts were slightly different.
* **Engineering Assumption & Resolution:**  
  Unconditional auto-approval for claims under ₹2,000 would create severe financial leakage by paying unreadable uploads, blank receipts, mismatched amounts, and duplicate invoices. Therefore, the system implements **Gated Automatic Approval**:
  - Auto-approval applies **only** if:
    1. The receipt photograph is successfully resolved and decoded.
    2. Required fields (total amount and bill date) are extracted with high confidence.
    3. The extracted bill amount reconciles with the claimed amount within policy tolerance (±₹10).
    4. No duplicate receipt image hash or invoice number collision is detected.
    5. Category-specific policy rules pass (e.g., fuel claims verified against registered vehicle number).
  - Any claim failing these verification gates is routed to `review`, regardless of whether the claim amount is under ₹2,000.

---

### 2.2 Missing Physical Receipts (Mobile Upload Failures)

* **Data Observation:**  
  IT lead Sameer Joshi confirmed that the older mobile application version had upload failures where photos never reached the server. In `claims_test.csv`, 33 out of 190 claims lack an image on disk.
* **Engineering Assumption:**  
  Per Policy Section 3, a claim without a readable receipt cannot be reimbursed. Any claim with missing or unresolvable images is routed to `review` with reason:  
  `Review required: receipt image is unreadable or missing from upload.` Extracted fields are left blank (null) in accordance with schema rules.

---

### 2.3 Amount Comparison & Rounding Tolerance

* **Policy Provision (Section 3):**  
  *"The claim amount is the amount on the bill. Rounding to the nearest Rs 10 is accepted."*
* **Engineering Assumption:**  
  An absolute tolerance of `₹10.00` is enforced. For example, if a fuel bill is ₹448.20 and the representative claims ₹450.00, this is treated as compliant with policy tolerance. If the difference exceeds ₹10.00, it is flagged for clerk review.

---

### 2.4 Date Representation & Temporal Tolerance

* **Data Observation:**  
  Field representatives input dates in varied formats (`YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`), and receipts display dates in multiple Indian conventions.
* **Engineering Assumption:**  
  All dates are normalized internally to ISO `YYYY-MM-DD`. Expense claims submitted within `±3 days` of the printed bill date are accepted to accommodate field representatives traveling outstation or submitting claims on weekends. Discrepancies exceeding 3 days are flagged for human review.

---

### 2.5 Mandatory GSTIN Requirements by Category

* **Policy Provision (Section 2):**  
  Hotel / lodging bills *must* be GST tax invoices. Other categories (daily parking slips, auto-rickshaw fares, small tea stalls) frequently do not have GST registration.
* **Engineering Assumption:**  
  GSTIN is mandatory **only** for `Lodging` claims. For `Fuel`, `Food`, `Local travel`, `Courier`, and `Parking`, missing GSTIN on the receipt is acceptable and does not trigger review, provided the amount and date reconcile.

---

### 2.6 Fuel Claims & Vehicle Number Verification

* **Policy Provision (Section 2):**  
  *"Fuel. Actuals for field days, own two-wheeler (Area Sales Managers: own car). The bill must show the vehicle number."*
* **Engineering Assumption:**  
  The system matches the employee ID against `employees.csv` to retrieve their registered vehicle registration (e.g., `MH31 EK 4471`). If the OCR text contains a vehicle registration that contradicts the employee's registered vehicle, the claim is routed to `review`.

---

### 2.7 Historical Clerk Labels as Noisy Ground Truth

* **Observation:**  
  Clerk notes and email remarks reveal human transcription errors, inconsistent spacing, and operational fatigue (e.g., Priya Bhende admitting: *"Rohan, Pooja and Harshal put in a parking slip almost every day... I've stopped opening those"*).
* **Engineering Assumption:**  
  Historical clerk entries in `claims_train.csv` are treated as noisy reference labels. For rigorous model evaluation, an independently verified stratified reference subset is established to benchmark true OCR accuracy.
