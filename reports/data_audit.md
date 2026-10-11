# Tarang Pharma Distribution — Receipt Intelligence & Data Audit Report

**Date of Audit:** October 2026  
**Auditor:** Senior ML / CV Engineer & Financial Automation Consultant  
**Location:** Nagpur, Maharashtra, India  

---

## 1. Executive Summary

A comprehensive data audit was conducted on Tarang Pharma Distribution's field expense dataset, encompassing historical training claims, unverified test claims, employee records, physical receipt photographs, expense policy rules (v3.2), and internal correspondence.

Key operational findings:
1. **Total Claims Audited:** 283 historical claims (`claims_train.csv`) and 190 pending claims (`claims_test.csv`).
2. **Employee Roster Join Coverage:** **100.0%** across both train and test splits (all 16 Nagpur division field representatives matched).
3. **Physical Receipt Photography Coverage:**
   - Train split: **273/283** (96.5%) images successfully resolved; **10** missing on server due to mobile upload failures.
   - Test split: **159/190** (83.7%) images resolved; **31** missing on server due to mobile upload failures.
4. **Sub-₹2,000 Volume Proportion:** **91.2%** of train claims and **92.6%** of test claims fall under ₹2,000, confirming Nilesh Agrawal's stated ~90% proportion.
5. **Data Quality Anomalies Identified:** Mobile file path leaks, extension mismatches (`.jpeg` vs `.jpg`), Windows download duplicate naming (`(1)` suffix), unreadable thermal slips, and duplicate bill submissions.

---

## 2. Dataset Quality & Schema Inventory

| Dataset Name | File Reference | Row Count | Column Count | Unique IDs | Null Rates by Key Columns | Known Data Anomalies | Recommended Handling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Claims Train** | `claims_train.csv` | 283 | 16 | 283 unique claims | `rep_comment` (12%), `clerk_note` (28%), `clerk_gstin` (62%) | Mobile upload failures; informal rep comments | Deterministic image resolution; audit clerk entries as noisy reference |
| **Claims Test** | `claims_test.csv` | 190 | 9 | 190 unique claims | `rep_comment` (14%) | Missing photos for 31 claims; varying date/amount typing | Deterministic image resolution; missing photo claims routed to `review` |
| **Employee Roster** | `employees.csv` | 16 | 7 | 16 unique emp_id | 0.0% nulls | None; complete roster for Nagpur | Authoritative master directory for vehicle & grade checks |
| **Sample Submission** | `sample_submission.csv` | 190 | 8 | 190 rows | Template targets | Strict schema: 8 required columns | Strict output conformity in `predictions.csv` |
| **Receipt Images** | `images/` directory | 453 files | N/A | 453 physical files | 0 corrupt files | UUID file prefixes; ` (1)` browser rename artifacts | Multi-strategy indexed image resolver |

---

## 3. Expense Amount Distributions & Category Breakdown

### 3.1 Amount Claimed Statistics (INR)

| Metric | Historical Train Split (₹) | Test Split (₹) |
| :--- | :--- | :--- |
| **Mean Amount** | ₹691.02 | ₹595.71 |
| **Median Amount (50%)** | ₹340.00 | ₹353.50 |
| **Standard Deviation** | ₹934.82 | ₹743.71 |
| **Minimum Claim** | ₹20.00 | ₹20.00 |
| **Maximum Claim** | ₹6272.00 | ₹4700.00 |
| **Proportion < ₹2,000** | **91.2%** | **92.6%** |

### 3.2 Category Frequency

| Expense Category | Train Count (Share) | Test Count (Share) | Policy Compliance Requirement |
| :--- | :--- | :--- | :--- |
| **Courier** | 30 (10.6%) | 18 (9.5%) | Actuals with receipt |
| **Food** | 103 (36.4%) | 74 (38.9%) | Actuals; <= ₹2,500 without prior approval |
| **Fuel** | 77 (27.2%) | 54 (28.4%) | Actuals; vehicle no on bill |
| **Local travel** | 34 (12.0%) | 16 (8.4%) | Actuals with receipt |
| **Lodging** | 18 (6.4%) | 11 (5.8%) | Outstation only; <= ₹3,000 (M1/M2) or ₹4,500 (M3); GST tax invoice |
| **Parking** | 21 (7.4%) | 17 (8.9%) | Actuals; daily city parking expected |

---

## 4. Physical Receipt Image Inspection

- **Total Physical Files:** 453
- **Image Decodability:** 100% of images are valid, non-corrupted image binaries.
- **Image Formats:** {'JPEG': 453}
- **Average Dimensions:** 766 × 638 pixels
- **Average File Size:** 40.4 KB
- **Image Quality Observations:**
  1. *Orientation:* Multiple receipts captured in portrait, landscape, or inverted 90/180/270 degree rotation. Requires EXIF orientation correction.
  2. *Lighting & Contrast:* Real-world mobile captures with uneven shadows, flash reflections, and wrinkled paper.
  3. *Thermal Paper Degradation:* Fuel and retail receipts exhibit faint thermal printing, faded headers, and missing leading digits.
  4. *Handwritten Markings:* As noted by Priya Bhende in email thread, field reps frequently annotate receipts with pen ("paid", doctor names, visit counters). The OCR extraction parser must separate handwritten notes from printed merchant totals.

---

## 5. Duplicate and Misconduct Analysis

- **Train Duplicate Image References:** 0 rows share an image file name.
- **Test Duplicate Image References:** 0 rows share an image file name.
- **Cross-Split Duplicate Image References:** 0 image filenames appear across train and test.
- **Policy Section 8 (Misconduct):** Claiming a bill twice or altering a bill constitutes disciplinary misconduct.
- **Operational Strategy:** The system incorporates perceptual image hashing and invoice/vendor fingerprinting to detect repeated submissions and route them immediately to `review`.

---

## 6. Historical Decision Analysis (Train Split)

| Status | Count | Percentage |
| :--- | :--- | :--- |
| **approved** | 275 | 97.2% |
| **queried** | 6 | 2.1% |
| **rejected** | 2 | 0.7% |

Clerk notes reveal:
- Approved claims: marked "ok", "approved", or blank.
- Queried claims: "bill not readable", "amount mismatch", "vehicle number missing", "hotel bill not GST invoice".
- Rejected claims: duplicate bills, personal expenses, or non-compliant category claims.

---

## 7. Submission Schema Requirements

The required submission output `predictions.csv` must strictly match `sample_submission.csv`:
- Columns: `claim_id,vendor,receipt_date,receipt_number,gstin,total_amount,decision,reason`
- Exactly 190 rows corresponding to `claims_test.csv`.
- Allowed decision values: strictly `approve` or `review`.
- Formatted values: `receipt_date` formatted as `YYYY-MM-DD`, `total_amount` formatted as float/numeric, `gstin` valid 15-char alphanumeric or blank.

---

## 8. Data Audit Sign-Off

The dataset has been completely audited, verified, and mapped. All data anomalies and edge cases are documented with defensive engineering mitigations implemented in the processing pipeline.
