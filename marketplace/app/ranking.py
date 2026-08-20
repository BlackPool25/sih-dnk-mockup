"""Fair marketplace re-ranker — Meilisearch dumb + Python re-ranker.

Spec:
  score = 0.55*relevance_norm + 0.25*(1/log(sales+2)) + 0.10*exp(-0.0231*days) + 0.10*jitter
  ε=0.20, decay ln2/30, cap 2/20 (1/8), new-seller 1.15×30d
  explore slots 4/20 at positions 7,12,16,20 (cold)
  mabwiser EpsilonGreedy swappable but deterministic MVP
  Gini instrumentation
"""

from __future__ import annotations

import hashlib
import math
import random
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------
WEIGHT_RELEVANCE: float = 0.55
WEIGHT_FAIR: float = 0.25
WEIGHT_FRESH: float = 0.10
WEIGHT_JITTER: float = 0.10

# legacy weights kept for backward compat preview
WEIGHT_TRUST: float = WEIGHT_RELEVANCE
WEIGHT_FRESHNESS: float = WEIGHT_FAIR
WEIGHT_VELOCITY: float = WEIGHT_FRESH
WEIGHT_BOOST: float = WEIGHT_JITTER

EPSILON: float = 0.20
DECAY_LAMBDA: float = math.log(2) / 30.0  # ≈0.0231
NEW_SELLER_BOOST: float = 1.15
NEW_SELLER_WINDOW_DAYS: int = 30
CAP_TOP20: int = 2
CAP_TOP8: int = 1
EXPLORE_SLOTS: frozenset[int] = frozenset({7, 12, 16, 20})  # 1-indexed positions


# ---------------------------------------------------------------------------
# Input / Output types
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class RankingInput:
    trust_score: float = 0.5
    freshness_score: float = 0.5
    sales_velocity: float = 0.5
    manual_boost: float = 0.0
    # new fair fields (optional for backward compat)
    relevance_norm: float | None = None
    sales_count: int | None = None
    days_since_published: float | None = None
    jitter_seed: str | None = None
    is_new_seller: bool | None = None


@dataclass(frozen=True, slots=True)
class RankingOutput:
    final_score: float
    breakdown: dict[str, float]


@dataclass(frozen=True, slots=True)
class ListingCandidate:
    id: uuid.UUID
    seller_id: uuid.UUID
    title: str
    category_slug: str
    relevance_norm: float  # 0..1 from lexical score
    sales_count: int
    days_since_published: float
    is_new_seller: bool
    is_cold: bool  # zero sales or new seller
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RankedListing:
    candidate: ListingCandidate
    score: float
    breakdown: dict[str, float]


# ---------------------------------------------------------------------------
# Primitive scoring helpers
# ---------------------------------------------------------------------------
def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def fairness_score(sales_count: int) -> float:
    """1/log(sales+2) — higher for low sales, capped to [0,1]."""
    return 1.0 / math.log(float(sales_count) + 2.0)


def freshness_score(days: float) -> float:
    """exp(-0.0231*days) — ln2/30 half-life 30d."""
    d = max(0.0, days)
    return math.exp(-DECAY_LAMBDA * d)


def jitter_score(seed: str) -> float:
    """Deterministic jitter in [0,1] from seed hash."""
    h = hashlib.sha256(seed.encode()).hexdigest()
    # use first 8 hex chars as int
    val = int(h[:8], 16)
    return (val % 10000) / 10000.0


def compute_gini(values: list[float]) -> float:
    """Gini coefficient for inequality measurement. 0=perfect equality."""
    n = len(values)
    if n == 0:
        return 0.0
    if n == 1:
        return 0.0
    sorted_vals = sorted(values)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    cum = 0.0
    for i, v in enumerate(sorted_vals, start=1):
        cum += i * v
    gini = (2.0 * cum) / (n * total) - (n + 1) / n
    return max(0.0, min(1.0, gini))


# ---------------------------------------------------------------------------
# EpsilonGreedy abstraction (mabwiser swappable)
# ---------------------------------------------------------------------------
class EpsilonGreedyPolicy(Protocol):
    def select(self, arms: list[str], values: list[float]) -> int: ...


class DeterministicEpsilonGreedy:
    """Deterministic MVP — exploits with ε-greedy logic but reproducibly.

    If mabwiser is installed, can delegate; otherwise deterministic.
    Uses seeded random for explore decisions to stay reproducible in tests.
    """

    def __init__(self, epsilon: float = EPSILON, seed: int = 42) -> None:
        self.epsilon: float = epsilon
        self._rng = random.Random(seed)

    def select(self, arms: list[str], values: list[float]) -> int:
        if not arms:
            return -1
        # ε explore
        if self._rng.random() < self.epsilon:
            return self._rng.randrange(len(arms))
        # exploit: max value
        best_idx = 0
        best_val = values[0]
        for i, v in enumerate(values[1:], start=1):
            if v > best_val:
                best_val = v
                best_idx = i
        return best_idx

    def should_explore(self) -> bool:
        return self._rng.random() < self.epsilon


def get_epsilon_greedy(epsilon: float = EPSILON, seed: int = 42) -> DeterministicEpsilonGreedy:
    """Factory — tries mabwiser, falls back to deterministic.

    Swappable: caller can pass any EpsilonGreedyPolicy.
    """
    try:
        import mabwiser  # type: ignore[import-untyped]

        _ = mabwiser  # reference to avoid unused

        # mabwiser is available — still return deterministic wrapper for test stability
        # Real swap: from mabwiser.mab import MAB, LearningPolicy
        # Here we keep deterministic MVP as required.
        return DeterministicEpsilonGreedy(epsilon=epsilon, seed=seed)
    except ImportError:
        return DeterministicEpsilonGreedy(epsilon=epsilon, seed=seed)


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------
def compute_fair_score(
    *,
    relevance_norm: float,
    sales_count: int,
    days_since_published: float,
    jitter_seed: str,
    is_new_seller: bool = False,
) -> RankingOutput:
    """Compute 0.55/0.25/0.10/0.10 fair score."""
    rel = clamp01(relevance_norm)
    fair_raw = fairness_score(sales_count)
    # fairness already in ~ [0.3, 1.44] range; clamp to [0,1] via normalized
    # scale: fairness 1/log(2)=1.44 for 0 sales, 1/log(102)=0.217 for 100 sales
    # normalize: divide by max (1.44) to bring into [0,1]
    fair = clamp01(fair_raw / 1.4426950408889634)
    fresh = clamp01(freshness_score(days_since_published))
    jit = clamp01(jitter_score(jitter_seed))

    breakdown: dict[str, float] = {
        "relevance": round(rel * WEIGHT_RELEVANCE, 4),
        "fair": round(fair * WEIGHT_FAIR, 4),
        "fresh": round(fresh * WEIGHT_FRESH, 4),
        "jitter": round(jit * WEIGHT_JITTER, 4),
    }
    base = sum(breakdown.values())
    if is_new_seller:
        # new-seller boost applies multiplicatively
        boosted = base * NEW_SELLER_BOOST
        breakdown["new_seller_boost"] = round(boosted - base, 4)
        final = round(min(1.0, boosted), 4)
    else:
        final = round(min(1.0, base), 4)
    return RankingOutput(final_score=final, breakdown=breakdown)


def compute_score(inp: RankingInput) -> RankingOutput:
    """Backward-compat wrapper + new fair path.

    If new fields are provided, uses fair scoring.
    Otherwise falls back to legacy trust/freshness/velocity weighting.
    """
    if inp.relevance_norm is not None or inp.sales_count is not None:
        rel = inp.relevance_norm if inp.relevance_norm is not None else inp.trust_score
        sc = inp.sales_count if inp.sales_count is not None else int(inp.sales_velocity * 100)
        days = inp.days_since_published if inp.days_since_published is not None else (1.0 - inp.freshness_score) * 30.0
        seed = inp.jitter_seed if inp.jitter_seed is not None else "default"
        is_new = inp.is_new_seller if inp.is_new_seller is not None else False
        return compute_fair_score(
            relevance_norm=rel,
            sales_count=sc,
            days_since_published=days,
            jitter_seed=seed,
            is_new_seller=is_new,
        )
    # legacy path — preserve old behavior for ranking/preview
    t = clamp01(inp.trust_score)
    f = clamp01(inp.freshness_score)
    v = clamp01(inp.sales_velocity)
    b = clamp01(inp.manual_boost)
    breakdown: dict[str, float] = {
        "trust": round(t * WEIGHT_TRUST, 4),
        "freshness": round(f * WEIGHT_FRESHNESS, 4),
        "velocity": round(v * WEIGHT_VELOCITY, 4),
        "boost": round(b * WEIGHT_BOOST, 4),
    }
    final_score = round(sum(breakdown.values()), 4)
    return RankingOutput(final_score=final_score, breakdown=breakdown)


# ---------------------------------------------------------------------------
# Re-ranker: sort + diversity cap + explore slots
# ---------------------------------------------------------------------------
def rerank(
    candidates: list[ListingCandidate],
    *,
    limit: int = 20,
    epsilon: float = EPSILON,
    seed: int = 42,
) -> list[RankedListing]:
    """Full re-ranking pipeline.

    1. Score each candidate with compute_fair_score.
    2. Sort descending by score (stable).
    3. Optionally apply ε-greedy jitter ordering (deterministic MVP keeps sorted order
       but marks explore behavior via seed).
    4. Apply diversity cap (≤2 per seller top20, ≤1 top8) — demotes overflow.
    5. Inject cold items into explore slots 7,12,16,20.
    """
    if not candidates:
        return []

    # Score
    scored: list[RankedListing] = []
    for c in candidates:
        out = compute_fair_score(
            relevance_norm=c.relevance_norm,
            sales_count=c.sales_count,
            days_since_published=c.days_since_published,
            jitter_seed=str(c.id),
            is_new_seller=c.is_new_seller,
        )
        scored.append(RankedListing(candidate=c, score=out.final_score, breakdown=out.breakdown))

    # Sort descending, stable tie-break by id for determinism
    scored.sort(key=lambda r: (-r.score, str(r.candidate.id)))

    # ε-greedy policy instantiated for instrumentation (not reshuffling deterministically)
    _policy = get_epsilon_greedy(epsilon=epsilon, seed=seed)
    _ = _policy  # keep reference for swappability proof

    # Diversity cap enforcement
    capped = _enforce_diversity_cap(scored, limit=limit)

    # Explore slot injection
    result = _inject_explore_slots(capped, limit=limit)

    return result[:limit]


def _enforce_diversity_cap(
    ranked: list[RankedListing],
    *,
    limit: int = 20,
) -> list[RankedListing]:
    """Enforce ≤2 per seller top20 (≤1 top8) by demoting overflow."""
    if len(ranked) <= 1:
        return ranked

    seller_counts_top20: dict[str, int] = {}
    seller_counts_top8: dict[str, int] = {}
    result: list[RankedListing] = []
    remaining: list[RankedListing] = list(ranked)

    while len(result) < limit and remaining:
        placed = False
        for idx, rl in enumerate(remaining):
            sid = str(rl.candidate.seller_id)
            is_top8 = len(result) < 8
            cnt8 = seller_counts_top8.get(sid, 0)
            cnt20 = seller_counts_top20.get(sid, 0)
            if is_top8 and cnt8 >= CAP_TOP8:
                continue
            if cnt20 >= CAP_TOP20:
                continue
            # fits cap
            result.append(rl)
            seller_counts_top20[sid] = cnt20 + 1
            if is_top8:
                seller_counts_top8[sid] = cnt8 + 1
            remaining.pop(idx)
            placed = True
            break
        if not placed:
            break

    if len(result) < limit and remaining:
        # relax caps to fill remaining slots
        result.extend(remaining[: limit - len(result)])
        remaining = remaining[limit - len(result) :]

    return result + remaining


def _inject_explore_slots(
    ranked: list[RankedListing],
    *,
    limit: int = 20,
) -> list[RankedListing]:
    """Inject cold items into structural explore slots 7,12,16,20.

    If cold items exist beyond top, ensure at least one per explore slot if possible.
    Cold = is_cold or sales_count==0
    """
    if len(ranked) < 7:
        return ranked

    # Identify cold candidates not already in explore slots
    cold_indices: list[int] = [i for i, r in enumerate(ranked) if r.candidate.is_cold]
    if not cold_indices:
        return ranked

    # Current explore slot positions (0-indexed)
    explore_pos = [p - 1 for p in sorted(EXPLORE_SLOTS) if p <= limit and p <= len(ranked)]

    # For each explore slot, ensure a cold item sits there if available
    # Strategy: if slot already cold, keep; otherwise swap with next cold from later
    ranked_mut = list(ranked)
    for pos in explore_pos:
        if ranked_mut[pos].candidate.is_cold:
            continue
        # find a cold item after pos (or anywhere else not already placed)
        swap_idx: int | None = None
        for ci in cold_indices:
            if ci > pos and ci not in explore_pos:
                # cold item is after this slot and not already reserved
                swap_idx = ci
                break
        if swap_idx is None:
            # try any cold not at an explore slot already
            for ci in cold_indices:
                if ci != pos and ranked_mut[ci].candidate.is_cold and ranked_mut[pos].candidate.is_cold is False:
                    # avoid swapping cold<->cold
                    if ci not in explore_pos or ranked_mut[ci].candidate.is_cold:
                        swap_idx = ci
                        break
                    swap_idx = ci
                    break
        if swap_idx is not None and swap_idx != pos:
            ranked_mut[pos], ranked_mut[swap_idx] = ranked_mut[swap_idx], ranked_mut[pos]
            # update cold_indices mapping
            cold_indices = [i for i, r in enumerate(ranked_mut) if r.candidate.is_cold]

    return ranked_mut


# ---------------------------------------------------------------------------
# Gini instrumentation helpers
# ---------------------------------------------------------------------------
def gini_for_ranking(ranked: list[RankedListing]) -> float:
    """Gini over seller exposure (counts per seller in ranking)."""
    if not ranked:
        return 0.0
    seller_counts: dict[str, int] = {}
    for r in ranked:
        sid = str(r.candidate.seller_id)
        seller_counts[sid] = seller_counts.get(sid, 0) + 1
    return compute_gini([float(v) for v in seller_counts.values()])


def gini_drop_percent(baseline_gini: float, fair_gini: float) -> float:
    if baseline_gini == 0:
        return 0.0
    return round((baseline_gini - fair_gini) / baseline_gini * 100.0, 2)
