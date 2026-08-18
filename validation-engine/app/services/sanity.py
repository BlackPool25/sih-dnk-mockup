"""Post-hoc sanity bounds for extracted values (Wave 1, T1).

Decision 6: proper FORMAT is already enforced by ``response_schema`` +
reprompt in ``GeminiDraftExtractor`` — this module is the post-hoc
PLAUSIBILITY gate.  A value can be schema-valid yet implausible (quantity=2000
for a small-woodware order, weight_grams=1e9).  Sanity bounds reject such
values so the chat re-asks (business-error-wins) instead of booking a nonsense
shipment.  Deterministic-only, no LLM, no DB.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.shipment import CATEGORY_SLUGS, ShipmentDraft

# Default (min, max) windows per numeric draft field, inclusive.  Sentinels
# (-1 / "unknown" / None) mean "unstated" and are always accepted.
_DEFAULT_BOUNDS: dict[str, tuple[int, int]] = {
    "quantity": (1, 1_000),
    "weight_grams": (1, 30_000),  # EMS cap
    "value_minor": (1, 50_000_000),  # ₹5,00,000
}

# Optional per-category overrides narrowing a default window, keyed by the
# exact seeded slugs so a typo can never silently widen a bound.
_CATEGORY_OVERRIDES: dict[str, dict[str, tuple[int, int]]] = {
    slug: {} for slug in CATEGORY_SLUGS
}

_SENTINEL_VALUES: frozenset[object] = frozenset({-1, "unknown", None})


class TurnError(BaseModel):
    """One business-rule violation — shared by the turn validation + sanity gate."""

    field: str
    message: str


def _bounds_for(category: str | None, field: str) -> tuple[int, int] | None:
    if category is not None:
        override = _CATEGORY_OVERRIDES.get(category, {}).get(field)
        if override is not None:
            return override
    return _DEFAULT_BOUNDS.get(field)


def sanity_ok(value: object, field: str, category: str | None) -> bool:
    """True iff *value* is plausible for *field* under *category*.

    Non-numeric fields have no bound (True); sentinels are never implausible.
    """
    bounds = _bounds_for(category, field)
    if bounds is None or value in _SENTINEL_VALUES:
        return True
    low, high = bounds
    return isinstance(value, int) and low <= value <= high


def sanity_violations(draft: ShipmentDraft, category: str | None) -> list[TurnError]:
    """The numeric draft fields outside their sanity window, as TurnErrors.

    Sentinels are skipped — an unstated field is the caller's question, never
    an error.
    """
    errors: list[TurnError] = []
    for field in _DEFAULT_BOUNDS:
        value = getattr(draft, field, None)
        if value in _SENTINEL_VALUES or not isinstance(value, int):
            continue
        bounds = _bounds_for(category, field)
        if bounds is None:
            continue
        low, high = bounds
        if not (low <= value <= high):
            errors.append(
                TurnError(
                    field=field,
                    message=(
                        f"{field} {value} outside plausible range {low}..{high} "
                        f"for {category or 'any category'}"
                    ),
                )
            )
    return errors


__all__ = ["TurnError", "sanity_ok", "sanity_violations"]
