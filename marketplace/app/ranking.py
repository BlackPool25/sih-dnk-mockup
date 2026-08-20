"""Marketplace ranking — weighted score stub.

Weights (locked for demo):
  trust 0.55 / freshness 0.25 / sales_velocity 0.15 / manual_boost 0.05

All scores normalized to [0, 1] before weighting.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RankingInput:
    trust_score: float
    freshness_score: float
    sales_velocity: float
    manual_boost: float = 0.0


@dataclass(frozen=True, slots=True)
class RankingOutput:
    final_score: float
    breakdown: dict[str, float]


# Locked weights for demo — must sum to 1.0
WEIGHT_TRUST: float = 0.55
WEIGHT_FRESHNESS: float = 0.25
WEIGHT_VELOCITY: float = 0.15
WEIGHT_BOOST: float = 0.05


def compute_score(inp: RankingInput) -> RankingOutput:
    """Compute weighted ranking score from normalized inputs.

    Stub: clamps inputs to [0,1] then applies fixed weights.
    Future: incorporate Meilisearch relevance, seller trust level.
    """
    t = max(0.0, min(1.0, inp.trust_score))
    f = max(0.0, min(1.0, inp.freshness_score))
    v = max(0.0, min(1.0, inp.sales_velocity))
    b = max(0.0, min(1.0, inp.manual_boost))
    breakdown: dict[str, float] = {
        "trust": round(t * WEIGHT_TRUST, 4),
        "freshness": round(f * WEIGHT_FRESHNESS, 4),
        "velocity": round(v * WEIGHT_VELOCITY, 4),
        "boost": round(b * WEIGHT_BOOST, 4),
    }
    final_score = round(sum(breakdown.values()), 4)
    return RankingOutput(final_score=final_score, breakdown=breakdown)
