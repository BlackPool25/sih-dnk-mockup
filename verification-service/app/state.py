"""Verification state machine stub — mocked transitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VerificationLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    LIVENESS = "liveness"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class TransitionResult:
    level: VerificationLevel
    status: VerificationStatus
    mocked: bool = True
    next_level: VerificationLevel | None = None


_LEVEL_ORDER: list[VerificationLevel] = [
    VerificationLevel.L0,
    VerificationLevel.L1,
    VerificationLevel.L2,
]

_NEXT: dict[VerificationLevel, VerificationLevel | None] = {
    VerificationLevel.L0: VerificationLevel.L1,
    VerificationLevel.L1: VerificationLevel.L2,
    VerificationLevel.L2: None,
    VerificationLevel.LIVENESS: None,
}


def next_required_level(current: VerificationLevel | None) -> VerificationLevel | None:
    if current is None:
        return VerificationLevel.L0
    return _NEXT.get(current)


def mock_verify(level: VerificationLevel) -> TransitionResult:
    """Mocked verification — always succeeds for demo."""
    return TransitionResult(
        level=level,
        status=VerificationStatus.SUCCESS,
        mocked=True,
        next_level=_NEXT.get(level),
    )
