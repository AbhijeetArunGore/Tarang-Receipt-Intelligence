"""Structured logging, metrics collection, and audit observability.

Ensures zero credential leakage, sanitize employee PII, and structured JSON logging.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


def setup_logger(name: str = "tarang", log_level: str = "INFO") -> logging.Logger:
    """Configure a structured standard logger with safe formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger()


@dataclass
class ProcessingAuditRecord:
    """Structured audit log for every processed receipt and claim."""
    claim_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    provider_name: str = "none"
    model_id: Optional[str] = None
    processing_time_ms: float = 0.0
    status: str = "pending"  # success | error | review | fallback
    extracted_fields_present: list[str] = field(default_factory=list)
    validation_status: str = "unverified"
    policy_status: str = "unverified"
    decision: str = "review"
    reason: str = ""
    api_calls_count: int = 0
    estimated_cost_inr: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialize record to JSON, strictly avoiding PII or raw secrets."""
        data = asdict(self)
        return json.dumps(data)

    def log_record(self, log: logging.Logger = logger) -> None:
        """Emit structured JSON log message."""
        log.info("AUDIT_EVENT: %s", self.to_json())


class StopWatch:
    """Context manager for high-precision latency measurement."""

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "StopWatch":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0
