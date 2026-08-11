"""Shared globals for the seed package — project paths and the corpus
snapshot provenance (SNAPSHOT_DATE / VERIFIED_AT) every imported config row
carries.  Nothing else lives here: each domain module keeps its own spec
constants next to the code that consumes them.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"

VERIFIED_AT = datetime(2026, 8, 8, tzinfo=UTC)  # corpus snapshot date
SNAPSHOT_DATE = date(2026, 8, 8)
