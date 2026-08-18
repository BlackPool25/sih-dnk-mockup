"""Report builder — populates bilingual prompt templates from DB flags.

``build_report(report)`` walks every ErrorEntry and MissingEntry, looks up
the per-field prompt template in the config_flags table (with a generic
fallback), formats it, and returns the enriched ValidationReport.
"""

from __future__ import annotations

from app.services.db_tools import get_config_flag
from app.services.graded import ValidationReport

# Hardcoded fallback templates — used only when the DB flag chain
# (specific → generic) yields nothing.
_FALLBACK_ERROR_HI = "कृपया {field} को सही करें: {message}"
_FALLBACK_ERROR_EN = "Please correct {field}: {message}"
_FALLBACK_MISSING_HI = "कृपया {label} ({field_key}) प्रदान करें"
_FALLBACK_MISSING_EN = "Please provide {label} ({field_key})"


def _resolve_error_template(field: str, lang: str) -> str:
    """Resolve prompt.error.{field}.{lang} → prompt.error.generic.{lang} → hardcoded."""
    try:
        flag = get_config_flag(f"prompt.error.{field}.{lang}")
        return str(flag["flag_value"])
    except KeyError:
        pass
    try:
        flag = get_config_flag(f"prompt.error.generic.{lang}")
        return str(flag["flag_value"])
    except KeyError:
        pass
    return _FALLBACK_ERROR_EN if lang == "en" else _FALLBACK_ERROR_HI


def _resolve_missing_template(field_key: str, lang: str) -> str:
    """Resolve prompt.missing.{field_key}.{lang} → prompt.missing.generic.{lang} → hardcoded."""
    try:
        flag = get_config_flag(f"prompt.missing.{field_key}.{lang}")
        return str(flag["flag_value"])
    except KeyError:
        pass
    try:
        flag = get_config_flag(f"prompt.missing.generic.{lang}")
        return str(flag["flag_value"])
    except KeyError:
        pass
    return _FALLBACK_MISSING_EN if lang == "en" else _FALLBACK_MISSING_HI


def build_report(report: ValidationReport) -> ValidationReport:
    """Populate prompt_template_hi/en on every entry from DB config flags.

    Resolution chain (per error):
      1. prompt.error.{field}.hi/en  →  specific to that field
      2. prompt.error.generic.hi/en  →  cross-field fallback
      3. hardcoded English/Hindi      →  last resort

    Resolution chain (per missing):
      1. prompt.missing.{field_key}.hi/en  →  specific to that field
      2. prompt.missing.generic.hi/en      →  cross-field fallback
      3. hardcoded English/Hindi           →  last resort
    """
    for entry in report.errors:
        template_hi = _resolve_error_template(entry.field, "hi")
        template_en = _resolve_error_template(entry.field, "en")
        entry.prompt_template_hi = template_hi.format(field=entry.field, message=entry.message)
        entry.prompt_template_en = template_en.format(field=entry.field, message=entry.message)

    for entry in report.missing:
        template_hi = _resolve_missing_template(entry.field_key, "hi")
        template_en = _resolve_missing_template(entry.field_key, "en")
        entry.prompt_template_hi = template_hi.format(
            field_key=entry.field_key,
            label=entry.label or entry.field_key,
            example=entry.example,
        )
        entry.prompt_template_en = template_en.format(
            field_key=entry.field_key,
            label=entry.label or entry.field_key,
            example=entry.example,
        )

    return report


__all__ = ["build_report"]
