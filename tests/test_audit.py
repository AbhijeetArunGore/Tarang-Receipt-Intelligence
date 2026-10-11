"""Unit tests for dataset audit logic and integrity verifications."""

import pytest
import pandas as pd
from scripts.audit_data import run_data_audit
from src.config import REPORTS_DIR


def test_audit_data_execution():
    report_text = run_data_audit()
    assert isinstance(report_text, str)
    assert "Tarang Pharma Distribution" in report_text
    assert "Executive Summary" in report_text
    assert (REPORTS_DIR / "data_audit.md").exists()
