"""Pytest bootstrap: put the project root on sys.path so `import app` works."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
