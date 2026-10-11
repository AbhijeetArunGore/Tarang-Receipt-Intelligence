"""Configuration and environment management for Tarang Receipt Intelligence Platform.

Centralizes all filesystem paths, policy parameters, OCR configurations,
and discovery of input files regardless of UUID prefixes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


# Project Root Directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_file_by_pattern(pattern: str, root_dir: Path = PROJECT_ROOT) -> Optional[Path]:
    """Find the first file matching a given glob pattern in the root directory."""
    matches = list(root_dir.glob(pattern))
    if matches:
        return matches[0]
    return None


# Input Files Discovery (Gracefully handles UUID prefixes if present)
CLAIMS_TRAIN_PATH = (
    find_file_by_pattern("*claims_train.csv") or PROJECT_ROOT / "claims_train.csv"
)
CLAIMS_TEST_PATH = (
    find_file_by_pattern("*claims_test.csv") or PROJECT_ROOT / "claims_test.csv"
)
EMPLOYEES_PATH = (
    find_file_by_pattern("*employees.csv") or PROJECT_ROOT / "employees.csv"
)
SAMPLE_SUBMISSION_PATH = (
    find_file_by_pattern("*sample_submission.csv")
    or PROJECT_ROOT / "sample_submission.csv"
)
EXPENSE_POLICY_PATH = (
    find_file_by_pattern("*expense-policy.pdf") or PROJECT_ROOT / "expense-policy.pdf"
)
EMAIL_THREAD_PATH = (
    find_file_by_pattern("*email-thread.txt") or PROJECT_ROOT / "email-thread.txt"
)
IMAGES_DIR = PROJECT_ROOT / "images"

# Output Locations
PREDICTIONS_PATH = PROJECT_ROOT / "predictions.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORTS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)


# Tesseract Executable Discovery
def find_tesseract_cmd() -> Optional[str]:
    """Discover Tesseract binary location across environment and standard Windows paths."""
    env_cmd = os.getenv("TESSERACT_CMD")
    if env_cmd and os.path.isfile(env_cmd):
        return env_cmd

    candidate_paths = [
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for path in candidate_paths:
        if os.path.isfile(path):
            return path

    import shutil
    shutil_path = shutil.which("tesseract")
    if shutil_path:
        return shutil_path

    return None


TESSERACT_CMD = find_tesseract_cmd()

# OCR Provider Settings
OCR_PROVIDER = os.getenv("OCR_PROVIDER", "tesseract" if TESSERACT_CMD else "none")
VISION_API_KEY = os.getenv("VISION_API_KEY", "")
VISION_API_ENDPOINT = os.getenv("VISION_API_ENDPOINT", "https://api.openai.com/v1/chat/completions")
VISION_MODEL_ID = os.getenv("VISION_MODEL_ID", "gpt-4o-mini")
VISION_REQUEST_TIMEOUT = int(os.getenv("VISION_REQUEST_TIMEOUT", "15"))
VISION_MAX_RETRIES = int(os.getenv("VISION_MAX_RETRIES", "2"))

# Financial Policy Parameters (Tarang v3.2 & Nilesh brief)
AMOUNT_AUTO_APPROVE_MAX = float(os.getenv("AMOUNT_AUTO_APPROVE_MAX", "2000.0"))
AMOUNT_TOLERANCE_ABSOLUTE = float(os.getenv("AMOUNT_TOLERANCE_ABSOLUTE", "10.0"))  # Policy allows rounding to nearest Rs 10
DATE_TOLERANCE_DAYS = int(os.getenv("DATE_TOLERANCE_DAYS", "3"))

FOOD_LIMIT_WITHOUT_APPROVAL = 2500.0
LODGING_LIMIT_M1_M2 = 3000.0
LODGING_LIMIT_M3 = 4500.0

# Operations Baseline (Tarang Pharma context)
TOTAL_MONTHLY_CLAIMS = 2400
NAGPUR_MONTHLY_CLAIMS = 240
TOTAL_REPS = 160
NAGPUR_REPS = 16
CLERK_COUNT = 2
CLERK_MONTHLY_SALARY = 38000.0
MINUTES_PER_CLAIM_MANUAL = 3.5
COST_PER_QUERY = 45.0

# Server settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
UI_PORT = int(os.getenv("UI_PORT", "8501"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
