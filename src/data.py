"""Dataset loading, schema validation, and deterministic receipt image resolution.

Provides deterministic mapping between claim records and physical image files,
handling UUID prefixes, path variations, and extension mismatches.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    from src.config import (
        CLAIMS_TEST_PATH,
        CLAIMS_TRAIN_PATH,
        EMPLOYEES_PATH,
        IMAGES_DIR,
        SAMPLE_SUBMISSION_PATH,
    )
    from src.observability import logger
except (ImportError, ModuleNotFoundError):
    from config import (  # type: ignore
        CLAIMS_TEST_PATH,
        CLAIMS_TRAIN_PATH,
        EMPLOYEES_PATH,
        IMAGES_DIR,
        SAMPLE_SUBMISSION_PATH,
    )
    from observability import logger  # type: ignore


class ImageResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    MISSING_UPLOAD = "missing_upload"
    AMBIGUOUS = "ambiguous"
    NOT_FOUND = "not_found"


class ImageResolver:
    """Deterministically resolves claim image_file references to disk paths."""

    def __init__(self, images_dir: Path = IMAGES_DIR) -> None:
        self.images_dir = images_dir
        self.image_index: Dict[str, Path] = {}
        self.stem_index: Dict[str, List[Path]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Indexes all images in the images folder."""
        if not self.images_dir.exists():
            logger.warning(f"Images directory does not exist: {self.images_dir}")
            return

        for p in self.images_dir.iterdir():
            if not p.is_file():
                continue

            full_name = p.name
            # Handle uuid-filename prefix: e.g. 00d24a9f-...-IMG-...jpg
            parts = full_name.split("-", 5)
            stripped_name = parts[5] if len(parts) >= 6 else full_name

            # Map direct names and stripped names
            self.image_index[full_name.lower()] = p
            self.image_index[stripped_name.lower()] = p

            # Map stem (without extension)
            stem = Path(stripped_name).stem.lower()
            if stem not in self.stem_index:
                self.stem_index[stem] = []
            self.stem_index[stem].append(p)

    def resolve(self, image_ref: Optional[str]) -> Tuple[Optional[Path], ImageResolutionStatus, str]:
        """Resolve an image reference string from claim data to an actual path on disk."""
        if not image_ref or pd.isna(image_ref) or str(image_ref).strip() == "":
            return None, ImageResolutionStatus.MISSING_UPLOAD, "Claim does not have an image filename recorded"

        # Extract pure filename from possible mobile directory paths
        ref_str = str(image_ref).replace("\\", "/").strip()
        filename = ref_str.split("/")[-1]
        filename_lower = filename.lower()

        # 1. Exact match in index
        if filename_lower in self.image_index:
            return self.image_index[filename_lower], ImageResolutionStatus.RESOLVED, "Exact match"

        # 2. Extension swap (.jpeg <-> .jpg)
        p_obj = Path(filename_lower)
        alt_ext = ".jpg" if p_obj.suffix in [".jpeg", ".jpe"] else (".jpeg" if p_obj.suffix == ".jpg" else None)
        if alt_ext:
            alt_name = (p_obj.stem + alt_ext).lower()
            if alt_name in self.image_index:
                return self.image_index[alt_name], ImageResolutionStatus.RESOLVED, f"Extension resolved: {alt_name}"

        # 3. Stem match (ignoring (1) duplicate markers or extension changes)
        stem_clean = p_obj.stem.replace(" (1)", "").replace("(1)", "").strip()
        if stem_clean in self.stem_index:
            candidates = self.stem_index[stem_clean]
            if len(candidates) == 1:
                return candidates[0], ImageResolutionStatus.RESOLVED, f"Stem matched: {candidates[0].name}"
            # Prefer candidate matching non-(1) if possible
            non_duplicate = [c for c in candidates if " (1)" not in c.name]
            if len(non_duplicate) == 1:
                return non_duplicate[0], ImageResolutionStatus.RESOLVED, f"Stem resolved to primary copy: {non_duplicate[0].name}"
            return candidates[0], ImageResolutionStatus.RESOLVED, f"Candidate chosen deterministically: {candidates[0].name}"

        return None, ImageResolutionStatus.NOT_FOUND, f"File {filename} was not found in images directory (upload failed)"


def load_claims_train(filepath: Path = CLAIMS_TRAIN_PATH) -> pd.DataFrame:
    """Load and validate training claims data."""
    if not filepath.exists():
        raise FileNotFoundError(f"Claims train file not found at {filepath}")
    df = pd.read_csv(filepath)
    return df


def load_claims_test(filepath: Path = CLAIMS_TEST_PATH) -> pd.DataFrame:
    """Load and validate testing claims data."""
    if not filepath.exists():
        raise FileNotFoundError(f"Claims test file not found at {filepath}")
    df = pd.read_csv(filepath)
    return df


def load_employees(filepath: Path = EMPLOYEES_PATH) -> pd.DataFrame:
    """Load employee roster data."""
    if not filepath.exists():
        raise FileNotFoundError(f"Employees file not found at {filepath}")
    df = pd.read_csv(filepath)
    return df


def load_sample_submission(filepath: Path = SAMPLE_SUBMISSION_PATH) -> pd.DataFrame:
    """Load sample submission template."""
    if not filepath.exists():
        raise FileNotFoundError(f"Sample submission file not found at {filepath}")
    df = pd.read_csv(filepath)
    return df
