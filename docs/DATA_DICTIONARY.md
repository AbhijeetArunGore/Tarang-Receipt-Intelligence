# Tarang Pharma Distribution — Schema & Data Dictionary

---

## 1. Claims Datasets (`claims_train.csv` & `claims_test.csv`)

| Column Name | Data Type | Nullable | Source | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `claim_id` | String | No | System | Unique claim reference number | `CLM-31086` |
| `emp_id` | String | No | Rep App | Claimant employee identifier | `TPD-0412` |
| `submitted_on` | Date (ISO) | No | System | Timestamp when claim was submitted in mobile app | `2026-06-09` |
| `expense_date` | String | No | Rep App | Expense date as entered by the representative | `18-07-2026` |
| `category` | String | No | Rep App | Expense category: Fuel, Food, Lodging, Local travel, Courier, Parking | `Fuel` |
| `vendor` | String | No | Rep App | Vendor / Merchant name as entered by representative | `Laxmi Auto Fuels` |
| `amount_claimed` | String | No | Rep App | Claimed reimbursement amount (freehand string) | `Rs. 450.00` |
| `rep_comment` | String | Yes | Rep App | Representative's memo / doctor visit note | `Field visit Wardha` |
| `image_file` | String | Yes | Rep App | Receipt photo filename recorded at upload | `IMG_20260718_111930.jpg` |
| `clerk_vendor` | String | Yes | Clerk (Train only) | Vendor name as transcribed by clerk from bill photo | `Laxmi Auto Fuels` |
| `clerk_bill_date` | String | Yes | Clerk (Train only) | Bill date transcribed by clerk (DD-MM-YYYY) | `18-07-2026` |
| `clerk_bill_no` | String | Yes | Clerk (Train only) | Invoice / Bill number transcribed by clerk | `INV-4029` |
| `clerk_bill_amount` | String | Yes | Clerk (Train only) | Total bill amount transcribed by clerk | `448.20` |
| `clerk_gstin` | String | Yes | Clerk (Train only) | GSTIN transcribed by clerk (blank if none) | `27AAAAA0000A1Z5` |
| `status` | String | No | Clerk (Train only) | Historical outcome: `approved`, `queried`, `rejected` | `approved` |
| `clerk_note` | String | Yes | Clerk (Train only) | Internal clerk audit note | `ok` |

---

## 2. Employee Roster (`employees.csv`)

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `emp_id` | String | Unique employee identifier | `TPD-0412` |
| `name` | String | Representative full name | `Rohan Wankhede` |
| `designation` | String | Corporate designation (MR, Sr MR, ASM) | `Medical Representative` |
| `headquarter` | String | Territory headquarters | `Nagpur` |
| `manager_id` | String | Reporting manager employee ID | `TPD-0301` |
| `vehicle_no` | String | Registered vehicle registration number | `MH31 EK 4471` |
| `grade` | String | Employment grade (M1, M2, M3) determining hotel allowance | `M1` |

---

## 3. Submission Predictions (`predictions.csv`)

| Column Name | Data Type | Allowed Values / Format | Description |
| :--- | :--- | :--- | :--- |
| `claim_id` | String | From `claims_test.csv` | Unique claim identifier |
| `vendor` | String | Free text / blank | Merchant name printed on bill |
| `receipt_date` | String | `YYYY-MM-DD` / blank | Bill date in ISO format |
| `receipt_number` | String | Free text / blank | Invoice / Bill / Ticket number |
| `gstin` | String | 15-char alphanumeric / blank | GSTIN if printed |
| `total_amount` | String / Float | Numeric / blank | Total payable bill amount (Rs) |
| `decision` | String | Strictly `approve` or `review` | Automated audit recommendation |
| `reason` | String | Concise text | Evidence-backed reason |
