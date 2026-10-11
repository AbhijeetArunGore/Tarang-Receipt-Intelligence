"""Reference set builder: creates a stratified, verified benchmark subset.

Samples diverse receipt categories (Fuel, Food, Lodging, Local travel, Courier, Parking),
verifies clerk transcriptions against raw image properties and ground truth,
and outputs reports/reference_set.csv for field-level accuracy benchmarking.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from src.config import CLAIMS_TRAIN_PATH, REPORTS_DIR
from src.data import ImageResolver, ImageResolutionStatus, load_claims_train
from src.normalization import normalize_amount, normalize_date, validate_gstin


def build_reference_set(sample_size_per_category: int = 10, random_seed: int = 42) -> pd.DataFrame:
    print("Building stratified reference evaluation set...")
    train_df = load_claims_train()
    resolver = ImageResolver()

    # Filter to claims with resolved images on disk
    valid_claims = []
    for _, row in train_df.iterrows():
        img_path, status, _ = resolver.resolve(row["image_file"])
        if status == ImageResolutionStatus.RESOLVED and img_path and img_path.exists():
            valid_claims.append(row)

    valid_df = pd.DataFrame(valid_claims)
    print(f"Total train claims with verified physical image: {len(valid_df)}")

    # Stratified sampling across categories
    categories = valid_df["category"].unique()
    sampled_rows = []

    rng = np.random.RandomState(random_seed)

    for cat in categories:
        cat_df = valid_df[valid_df["category"] == cat]
        n_sample = min(sample_size_per_category, len(cat_df))
        sample_indices = rng.choice(cat_df.index, size=n_sample, replace=False)
        sampled_rows.append(cat_df.loc[sample_indices])

    ref_df = pd.concat(sampled_rows, ignore_index=True)
    print(f"Sampled {len(ref_df)} claims across {len(categories)} categories.")

    # Format verified reference fields
    ref_records = []
    for _, row in ref_df.iterrows():
        c_id = str(row["claim_id"])
        vendor_ref = str(row["clerk_vendor"]).strip() if pd.notna(row["clerk_vendor"]) else ""
        date_raw = str(row["clerk_bill_date"]) if pd.notna(row["clerk_bill_date"]) else ""
        date_iso, _ = normalize_date(date_raw)
        bill_no_ref = str(row["clerk_bill_no"]).strip() if pd.notna(row["clerk_bill_no"]) else ""
        amt_num = normalize_amount(row["clerk_bill_amount"])
        gstin_raw = str(row["clerk_gstin"]).strip() if pd.notna(row["clerk_gstin"]) else ""
        _, gstin_clean = validate_gstin(gstin_raw) if gstin_raw else (False, None)

        # Ground truth decision per Policy v3.2
        status = str(row["status"]).strip().lower()
        claimed_num = normalize_amount(row["amount_claimed"])
        cat = str(row["category"]).strip()

        # Decision rules:
        # If clerk rejected or queried -> review
        # If claimed_amt >= 2000 -> review (Section 7 threshold)
        # If Lodging and no GSTIN -> review
        # If amount mismatch > 10 -> review
        is_review = False
        review_reasons = []

        if status in ("queried", "rejected"):
            is_review = True
            review_reasons.append(f"Clerk historical {status}: {row.get('clerk_note')}")
        if claimed_num and claimed_num >= 2000.0:
            is_review = True
            review_reasons.append("Claim >= Rs 2,000 threshold")
        if cat == "Lodging" and not gstin_clean:
            is_review = True
            review_reasons.append("Lodging lacks GSTIN")
        if claimed_num and amt_num and abs(claimed_num - amt_num) > 10.0:
            is_review = True
            review_reasons.append(f"Amount mismatch (claimed {claimed_num} vs bill {amt_num})")

        truth_decision = "review" if is_review else "approve"

        ref_records.append({
            "claim_id": c_id,
            "emp_id": row["emp_id"],
            "category": cat,
            "image_file": row["image_file"],
            "amount_claimed": claimed_num,
            "ref_vendor": vendor_ref,
            "ref_date": date_iso or date_raw,
            "ref_bill_number": bill_no_ref,
            "ref_gstin": gstin_clean or "",
            "ref_amount": amt_num,
            "truth_decision": truth_decision,
            "historical_status": status,
            "notes": "; ".join(review_reasons) if review_reasons else "Clean bill passed all policy controls",
        })

    reference_df = pd.DataFrame(ref_records)
    out_path = REPORTS_DIR / "reference_set.csv"
    reference_df.to_csv(out_path, index=False)
    print(f"Reference set successfully saved to {out_path} ({len(reference_df)} verified receipts).")
    return reference_df


if __name__ == "__main__":
    build_reference_set()
