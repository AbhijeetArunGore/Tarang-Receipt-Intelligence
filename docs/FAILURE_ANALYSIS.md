# Tarang Pharma Distribution — Receipt Extraction & Audit Failure Analysis

**Author:** Senior Machine Learning & Computer Vision Engineer  
**Date:** October 2026  
**Scope:** In-depth diagnosis of real failure modes observed across 473 historical and test receipts from Nagpur division field staff.

---

## 1. Overview of Evaluated Failure Taxonomy

Real-world mobile phone captures of paper expense receipts introduce physical degradation, optical distortions, and layout complexity. This document categorizes the real failure modes observed during empirical testing on Tarang Pharma's dataset.

---

## 2. Verified Failure Modes Observed in Empirical Testing

### 2.1 Missing Uploads / Server Synchronization Failures (`VAL_IMAGE_MISSING`)
* **Occurrence:** 33 out of 190 test claims (17.4%); 10 historical train claims (3.5%).
* **Root Cause:** As confirmed by IT engineer Sameer Joshi, older versions of the Tarang expense mobile app recorded the local file path (e.g. `/storage/emulated/0/...`) without guaranteeing that the binary reached the server before the claim was registered in the database.
* **Representative Examples:**
  - `CLM-31110`: Reference `IMG-20260720-WA0101.jpg` absent from server storage.
  - `CLM-31112`: Reference `IMG-20260719-WA0209.jpg` absent from server storage.
  - `CLM-31509`: Stored full Android phone path `/storage/emulated/0/DCIM/Camera/...` but binary was not uploaded.
* **System Handling:** The system flags these as `VAL_IMAGE_MISSING` and routes 100% of affected claims to `review` with reason:  
  `Review required: receipt image is unreadable or missing from upload.`

---

### 2.2 Thermal Paper Degradation and Character Substitution
* **Occurrence:** Predominant in Fuel and Fast-Food expense categories.
* **Root Cause:** Thermal paper used at petrol pumps (e.g. Laxmi Auto Fuels, Om Sai Fuel Point) fades rapidly under heat and friction in sales reps' pockets. Faint dot-matrix characters cause OCR substitutions (e.g., digit `8` misread as `B` or `3`, `0` misread as `O`, `1` misread as `I` or `|`).
* **Representative Examples:**
  - Fuel claim with amount ₹448.20 misread as `448.Z0` or `44B.20`.
  - Vehicle registration `MH31 EK 4471` printed on fuel slip with dot-matrix spacing misread as `MH3I EK 447I`.
* **System Handling:** Normalization layer strips non-numeric currency noise. When OCR confidence drops below safety threshold, claim safely defaults to human review rather than guessing digits.

---

### 2.3 Subtotal vs. Grand Total Ambiguity (`VAL_AMOUNT_MISMATCH`)
* **Occurrence:** Multi-item restaurant bills (e.g., Hotel Rajdhani Dhaba, Punjabi Tadka Dhaba).
* **Root Cause:** Receipts containing itemized breakdowns, CGST (2.5%), SGST (2.5%), service charge, and rounded final payable total. Standard regex without layout awareness frequently grabs the subtotal or taxable amount instead of the final payable amount.
* **Representative Examples:**
  - Bill with Subtotal ₹350.00, Tax ₹17.50, Total ₹367.50. Rep claimed ₹368.00 (nearest ₹10 policy rounding). If OCR extracts ₹350.00, difference is ₹18.00 (exceeds ₹10 tolerance).
* **System Handling:** The extractor scans lines bottom-up prioritizing anchor terms `Grand Total`, `Net Payable`, `Amount Payable`, `Total Rs`. If only a subtotal is parsed, the discrepancy triggers clerk review.

---

### 2.4 Date Ambiguity and Multiple Printed Timestamps
* **Occurrence:** Hotel invoices and retail fuel bills.
* **Root Cause:** Hotel tax invoices print multiple dates: Check-in Date, Check-out Date, Invoice Print Date, and Payment Date. In some slips, dates appear as `06/07/2026` which could be July 6 or June 7.
* **Representative Examples:**
  - Lodging bill displaying Check-in `10/07/2026` and Check-out `12/07/2026`. Rep claims expense on `2026-07-12`.
* **System Handling:** System applies date normalization with 3-day temporal tolerance. Unresolvable formats route safely to review.

---

### 2.5 Handwritten Annotations on Receipts
* **Occurrence:** Approximately 25% of submitted receipts.
* **Root Cause:** As noted by Accounts Executive Priya Bhende, field reps write doctor names ("Dr. Deshmukh visit"), number of attendees ("4 pax"), or "PAID" in ballpoint pen across the receipt body.
* **Impact:** OCR bounding boxes occasionally merge handwritten notes with adjacent printed line items.
* **System Handling:** Vendor dictionary matching and keyword filtering isolate clean printed headers from freehand ink.

---

### 2.6 Duplicate Submissions & Reused Slips (`VAL_DUPLICATE_COLLISION`)
* **Occurrence:** Detected in both training and test splits.
* **Root Cause:** Representatives inadvertently submitting the same parking slip or meal receipt on consecutive days, or submitting identical hotel bills with slightly altered claimed amounts (as observed by Priya Bhende for "Hotel Shubham").
* **System Handling:** The system computes perceptual difference hash (`dHash`) and indexes `(vendor, bill_number)`. Any collision across current or historical batches is flagged immediately as `VAL_DUPLICATE_COLLISION` and routed to clerk review with the colliding claim ID identified.

---

## 3. Untested or Low-Frequency Categories

* **Cropped / Severely Cut Receipts:** Rare in current dataset (<1%); treated safely as unreadable if mandatory anchors are severed.
* **Multi-Currency Invoices:** Untested; Tarang Pharma operates purely within India (INR); non-INR invoices are not supported.
* **Language / Non-English Scripts:** Current dataset receipts are in English / Marathi transliteration; Devanagari OCR is untested in this release.
