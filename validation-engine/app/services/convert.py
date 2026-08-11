"""Thin facade over the seed package (``app/services/seed/``).

All seeding logic moved to ``app.services.seed.*`` (decomposed 2026-08-09):
one module per config domain (lanes/categories/states/flags/pbe/rules) +
``__init__`` with the orchestration (CONFIG_TABLES, _config_truncate,
import_configs) and the CLI (main).  This module exists so
``python -m app.services.convert`` and every existing
``from app.services.convert import ...`` statement keep working unchanged.
"""

import sys

from app.services.seed import import_configs, import_lanes, main

__all__ = ["import_configs", "import_lanes", "main"]

if __name__ == "__main__":
    sys.exit(main())
