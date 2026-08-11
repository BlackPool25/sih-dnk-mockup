"""Markdown pipe-table parsing helpers for the corpus research files.

The corpus `.md` files are the raw data source for the config tables.
These helpers turn the markdown pipe tables into plain Python structures:

- header + row cells, with bold `**...**` markers stripped
- integer coercion that tolerates currency symbols (₹), thousand
  separators, and em-dashes / empty cells (→ ``None``)

Non-table lines (prose, headings, trailing notes) are ignored, so a table
that ends mid-file can never absorb following paragraphs as rows.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_SEPARATOR_CELL = re.compile(r":?-{3,}:?")
_EMPTY_CELLS = {"", "—", "–", "-", "n/a", "N/A", "NA", "null", "None", "?"}


def strip_markdown(cell: str) -> str:
    """Strip `**bold**` markers and surrounding whitespace from a cell."""
    return _BOLD.sub(r"\1", cell.strip()).strip()


def parse_table(lines: Iterable[str]) -> list[dict[str, str]]:
    """Parse all pipe tables from markdown lines into a list of row dicts.

    The first non-separator ``|``-line of each table is its header; header
    cells become the dict keys.  Separator lines (``|---|---|``) are
    skipped.  Blank lines do NOT terminate a table (corpus tables are
    contiguous pipe blocks), so all rows in a file merge into one list —
    callers pick the rows whose keys they expect.
    """
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue  # prose/headings — never table content
        cells = [strip_markdown(c) for c in stripped.strip("|").split("|")]
        if not cells or all(_SEPARATOR_CELL.fullmatch(c) for c in cells):
            continue  # separator row, or degenerate line
        if header is None:
            header = cells
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def parse_int(value: str | None) -> int | None:
    """Parse an integer cell; ``None`` for empty / em-dash / unavailable."""
    if value is None:
        return None
    cleaned = (
        value.strip().replace("₹", "").replace(",", "").replace("\u2009", "")
    )
    if cleaned in _EMPTY_CELLS:
        return None
    return int(cleaned)


def parse_minor(value: str | None) -> int | None:
    """Parse a rupee cell into integer paise (₹ × 100); ``None`` if empty."""
    rupees = parse_int(value)
    return None if rupees is None else rupees * 100
