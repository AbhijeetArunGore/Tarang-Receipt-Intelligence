"""Unit tests for observability, audit records, and telemetry."""

import json
import time
import pytest

from src.observability import StopWatch, ProcessingAuditRecord, setup_logger


def test_stopwatch():
    with StopWatch() as timer:
        time.sleep(0.01)
    assert timer.elapsed_ms > 5.0


def test_processing_audit_record_serialization():
    rec = ProcessingAuditRecord(
        claim_id="CLM-7001",
        provider_name="tesseract",
        processing_time_ms=750.2,
        status="success",
        decision="approve",
        reason="Checks passed",
        estimated_cost_inr=0.0,
    )
    raw_json = rec.to_json()
    parsed = json.loads(raw_json)
    assert parsed["claim_id"] == "CLM-7001"
    assert parsed["decision"] == "approve"
    assert "timestamp" in parsed


def test_setup_logger():
    log = setup_logger("test_tarang_log")
    assert log.name == "test_tarang_log"
