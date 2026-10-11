"""Streamlit interactive web screen for Tarang Receipt Intelligence Platform.

Provides receipt image upload, field comparison, policy audit findings,
real-time OCR extraction, and approve/review decision display.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from PIL import Image

from src.config import OCR_PROVIDER
from src.data import load_employees
from src.decisions import DecisionEngine
from src.duplicate_detection import DuplicateDetector
from src.extraction import ReceiptExtractor
from src.image_processing import ImageProcessingError, ImageProcessor
from src.normalization import normalize_amount
from src.observability import StopWatch
from src.ocr import get_ocr_provider
from src.policy import ExpensePolicyEngine
from src.validation import ClaimValidator


st.set_page_config(
    page_title="Tarang Pharma — Receipt Intelligence",
    page_icon="🧾",
    layout="wide",
)

# Custom header
st.title("🧾 Tarang Pharma Distribution — Receipt Intelligence & Audit")
st.caption("Nagpur Division Expense Audit Platform | Automated 5-Field Extraction & Policy Gate")

# Sidebar: System status and configuration
st.sidebar.header("⚙️ Engine Status & Config")
ocr_provider = get_ocr_provider()
is_ocr_ready = ocr_provider.is_available()

if is_ocr_ready:
    st.sidebar.success(f"OCR Active: {ocr_provider.__class__.__name__}")
else:
    st.sidebar.warning("OCR Engine: Unavailable")
    st.sidebar.info("To configure local OCR, ensure Tesseract is installed and TESSERACT_CMD is set in .env")

st.sidebar.markdown("---")
st.sidebar.subheader("Policy Baseline (Tarang v3.2)")
st.sidebar.markdown("""
- **Sub-₹2,000 Rule:** Gated auto-approval (clean bills only)
- **High-Value Cap:** Claims ≥ ₹2,000 routed to Finance clerk
- **Food Cap:** ₹2,500 without prior manager approval
- **Lodging:** Must be GST tax invoice (mandatory GSTIN)
- **Rounding:** Up to ±₹10 accepted per policy
""")

# Load employee roster for dropdown
try:
    emp_df = load_employees()
    emp_list = emp_df["emp_id"].tolist()
except Exception:
    emp_df = None
    emp_list = ["TPD-0412", "TPD-0418", "TPD-0422", "TPD-0430"]

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Claim Details & Receipt Upload")

    c1, c2 = st.columns(2)
    with c1:
        claim_id_input = st.text_input("Claim ID", value="CLM-31086")
        emp_id_input = st.selectbox("Representative Employee ID", options=emp_list, index=0)
        category_input = st.selectbox(
            "Expense Category",
            options=["Fuel", "Food", "Lodging", "Local travel", "Courier", "Parking"],
            index=1,
        )

    with c2:
        amount_input = st.text_input("Amount Claimed (₹)", value="350.00")
        date_input = st.text_input("Expense Date", value="2026-07-20")
        vendor_typed = st.text_input("Vendor (Typed by Rep)", value="Hotel Rajdhani Dhaba")

    rep_comment = st.text_input("Representative Comment", value="Lunch meeting with stockist")

    uploaded_file = st.file_uploader(
        "Upload Receipt Photograph (JPEG, PNG, WebP)",
        type=["jpg", "jpeg", "png", "webp"],
    )

    image_to_process = None
    if uploaded_file is not None:
        try:
            image_to_process = Image.open(uploaded_file)
            st.image(image_to_process, caption="Receipt Preview", use_container_width=True)
        except Exception as e:
            st.error(f"Failed to display image: {e}")

    process_btn = st.button("🚀 Audit & Verify Receipt", type="primary", use_container_width=True)

with col_right:
    st.subheader("2. Audit Results & Extraction Inspection")

    if process_btn:
        if not image_to_process:
            st.error("Please upload a receipt photograph before processing.")
        elif not is_ocr_ready:
            st.error("OCR Provider is not available. Please install Tesseract or configure an API key.")
        else:
            with st.spinner("Extracting bill fields and running policy audit..."):
                with StopWatch() as timer:
                    # 1. Image preprocessing
                    pil_img = ImageProcessor.load_image(image_to_process)

                    # 2. OCR extraction
                    ocr_res = ocr_provider.extract_text(pil_img)
                    extractor = ReceiptExtractor()
                    extracted = extractor.extract(ocr_res)

                    # 3. Duplicate check
                    detector = DuplicateDetector()
                    dup_res = detector.check_duplicate(
                        current_claim_id=claim_id_input,
                        image=pil_img,
                        vendor_name=extracted.fields.vendor_name,
                        bill_number=extracted.fields.bill_number,
                    )

                    # 4. Validation
                    validator = ClaimValidator(employees_df=emp_df)
                    claim_dict = {
                        "claim_id": claim_id_input,
                        "emp_id": emp_id_input,
                        "category": category_input,
                        "amount_claimed": amount_input,
                        "amount_claimed_num": normalize_amount(amount_input),
                        "expense_date": date_input,
                        "vendor": vendor_typed,
                    }
                    val_res = validator.validate(claim_dict, extracted, duplicate_check=dup_res, image_resolved=True)

                    # 5. Policy check
                    emp_info = validator.employee_index.get(emp_id_input)
                    policy_engine = ExpensePolicyEngine()
                    pol_res = policy_engine.evaluate(claim_dict, extracted, employee_info=emp_info)

                    # 6. Decision
                    decision_engine = DecisionEngine(validator=validator, policy_engine=policy_engine)
                    decision = decision_engine.decide(claim_dict, extracted, val_res, pol_res, image_resolved=True)

            # Display Decision Banner
            st.markdown("---")
            if decision.decision == "approve":
                st.success(f"### Decision: ✅ APPROVE (Straight-Through Automated)")
            else:
                st.warning(f"### Decision: 🔍 REVIEW (Route to Finance Clerk)")

            st.info(f"**Audit Rationale:** {decision.reason}")

            # Extracted Fields Table
            st.markdown("#### 📋 Extracted Bill Fields")
            fields_data = [
                {"Field": "Vendor Name", "Extracted Value": extracted.fields.vendor_name or "—", "Claimed Value": vendor_typed},
                {"Field": "Bill Date", "Extracted Value": extracted.fields.bill_date or "—", "Claimed Value": date_input},
                {"Field": "Bill Number", "Extracted Value": extracted.fields.bill_number or "—", "Claimed Value": "—"},
                {"Field": "GSTIN", "Extracted Value": extracted.fields.gstin or "—", "Claimed Value": "—"},
                {"Field": "Total Amount (₹)", "Extracted Value": f"₹{extracted.fields.bill_amount:.2f}" if extracted.fields.bill_amount is not None else "—", "Claimed Value": f"₹{normalize_amount(amount_input):.2f}" if normalize_amount(amount_input) else amount_input},
            ]
            st.dataframe(pd.DataFrame(fields_data), use_container_width=True)

            # Validation & Policy Findings
            st.markdown("#### 🛡️ Compliance & Validation Findings")
            if val_res.findings:
                for f in val_res.findings:
                    if f.severity.value == "ERROR":
                        st.error(f"❌ **{f.rule_id}:** {f.message}")
                    else:
                        st.warning(f"⚠️ **{f.rule_id}:** {f.message}")
            else:
                st.success("✅ All claim-to-receipt reconciliation checks passed.")

            if pol_res.evaluations:
                for ev in pol_res.evaluations:
                    if not ev.passed:
                        st.warning(f"📌 **{ev.rule_name}:** {ev.reason}")

            st.caption(f"⏱️ Processing Latency: {timer.elapsed_ms:.1f} ms | Provider: {ocr_provider.__class__.__name__}")

    else:
        st.info("Upload a receipt and click **Audit & Verify Receipt** to view extraction and policy reconciliation.")
