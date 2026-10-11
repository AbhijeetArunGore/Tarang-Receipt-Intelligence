# Tarang Pharma Distribution — Financial Cost Model & Operational ROI Analysis

**Prepared For:** Nilesh Agrawal, Finance Controller  
**Author:** Senior Machine Learning & Financial Automation Consultant  
**Date:** October 2026  
**Location:** Nagpur, Maharashtra, India  

---

## 1. Baseline Financial and Operational Parameters

The financial model is grounded directly in the figures stated in Tarang Pharma's Field Expense Policy (v3.2) and operational brief:

* **Monthly Volume Across Company:** 2,400 photo claims / month
* **Annual Claim Volume:** 28,800 claims / year
* **Nagpur Division Volume:** ~240 claims / month (~16 field representatives)
* **Finance Staffing:** 2 Finance Clerks (Priya Bhende and colleague)
* **Loaded Salary Cost per Clerk:** ₹38,000 / month (Total: ₹76,000 / month)
* **Effective Working Hours:** 160 hours / month per clerk (Loaded hourly rate = ₹237.50 / hour)
* **Current Manual Handling Time:** 3.5 minutes / claim (manual transcription + policy verification)
* **Current Total Manual Burden:** 2,400 claims × 3.5 min = 8,400 minutes = **140.0 hours / month**
* **Cost of Queried Claim:** ₹45.00 in clerk and rep coordination time (plus 1-week payment delay)

---

## 2. Platform Architecture & Inference Cost Structure

The platform implements an efficient local OCR pipeline utilizing Tesseract OCR 5.4, supplemented by optional cloud Vision APIs when configured.

| Component | Local Tesseract Engine | Cloud Multimodal Vision (Optional) |
| :--- | :--- | :--- |
| **API Calls per Claim** | 0 external calls | 1 call / claim |
| **Provider Cost per Claim** | **₹0.00** | ~₹0.02 – ₹0.05 / claim |
| **Monthly Inference Cost (2,400 claims)** | **₹0.00** | ~₹48.00 – ₹120.00 / month |
| **Infrastructure Hosting** | ~₹2,500 / month (Standard CPU VM) | ~₹2,500 / month |
| **Monthly Software Operating Cost** | **₹2,500 / month** | **₹2,600 / month** |

*Note: Nilesh Agrawal's requirement ("I'm not paying more per photo than a clerk costs me") is satisfied: the local software cost per photo is **₹1.04** (all-inclusive VM hosting), compared to the clerk cost of **₹31.67** per photo.*

---

## 3. Calculation Methodology & Explicit Formulas

### 3.1 Formulas
1. **Annual Claims:**  
   $$\text{Annual Claims} = 2,400 \times 12 = 28,800$$
2. **Monthly Manual Hours Saved:**  
   $$\text{Monthly Hours Saved} = \frac{2,400 \times \text{Average Minutes Eliminated per Claim}}{60}$$
3. **Monthly Gross Labour Savings:**  
   $$\text{Monthly Gross Labour Savings} = \text{Monthly Hours Saved} \times \text{Loaded Hourly Rate (₹237.50)}$$
4. **Monthly Net Financial Benefit:**  
   $$\text{Monthly Net Benefit} = \text{Gross Labour Savings} + \text{Avoidable Losses} - \text{Inference Costs} - \text{Infrastructure Costs} - \text{Maintenance Allocation}$$
5. **Monthly Inference Cost:**  
   $$\text{Monthly Inference Cost} = 2,400 \times \text{Average Cost per Claim}$$

---

## 4. Scenario Analysis: Conservative, Base, and Optimistic

The system delivers two distinct operational benefits:
1. **Straight-Through Processing (STP):** Eliminates 100% of human touch time (3.5 minutes saved) on clean routine claims.
2. **Assisted Review (Copilot):** For claims routed to review, all 5 bill fields and validation findings are pre-populated, reducing clerk review time from 3.5 minutes down to 1.0 minute (saving 2.5 minutes per claim).

| Operational Parameter | Conservative Scenario | Base Scenario | Optimistic Scenario |
| :--- | :--- | :--- | :--- |
| **STP Auto-Approval Rate** | 12.0% (288 claims) | 22.0% (528 claims) | 35.0% (840 claims) |
| **Human Review Rate** | 88.0% (2,112 claims) | 78.0% (1,872 claims) | 65.0% (1,560 claims) |
| **Time per Auto-Approved Claim** | 0.0 min (100% automated) | 0.0 min (100% automated) | 0.0 min (100% automated) |
| **Time per Human-Reviewed Claim** | 1.2 minutes (pre-filled) | 1.0 minute (pre-filled) | 0.8 minutes (pre-filled) |
| **Total Monthly Clerk Hours Needed** | 42.2 hours | 31.2 hours | 20.8 hours |
| **Monthly Clerk Hours Saved** | **97.8 hours** | **108.8 hours** | **119.2 hours** |
| **Gross Monthly Capacity Value (₹)** | **₹23,227** | **₹25,840** | **₹28,310** |
| **Infrastructure & Hosting (₹)** | (₹2,500) | (₹2,500) | (₹2,500) |
| **Monthly Inference Cost (₹)** | ₹0.00 | ₹0.00 | ₹0.00 |
| **Maintenance Allocation (₹)** | (₹3,000) | (₹3,000) | (₹3,000) |
| **Monthly Net Economic Benefit (₹)** | **₹17,727** | **₹20,340** | **₹22,810** |
| **Annualized Net Benefit (₹)** | **₹2,12,724 / yr** | **₹2,44,080 / yr** | **₹2,73,720 / yr** |
| **Clerk Capacity Released** | **61.1% of 1 Clerk** | **68.0% of 1 Clerk** | **74.5% of 1 Clerk** |

---

## 5. Staff Redeployment vs. Direct Headcount Reduction

**Critical Financial Governance Note:**  
The hours saved represent released staff capacity. Tarang Finance can choose between:
1. **Cash Savings:** Eliminating overtime or reducing clerk headcount over time.
2. **Redeployment Value:** Allowing Priya Bhende and her colleague to redirect ~109 hours per month toward:
   - Investigating quarterly salary recovery discrepancies.
   - Performing vendor GST reconciliation to capture input tax credit (ITC).
   - Speeding up payment reimbursement cycles to improve field sales morale (addressing Area Sales Manager Amol Kathane's concern).
