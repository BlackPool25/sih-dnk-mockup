from decimal import Decimal

import pytest

from app.preferential import (
    PreferentialRateError,
    calculate_preferential_rate,
)


def test_ineligible_uses_standard_rate():

    result = calculate_preferential_rate(
        eligible=False,
        standard_rate_percent=Decimal("10"),
        preferential_rate_percent=None,
        reason="Origin requirement not satisfied",
    )

    assert result["eligible"] is False

    assert (
        result["effective_rate_percent"]
        == Decimal("10")
    )

    assert result["rate_type"] == "STANDARD"


def test_eligible_uses_preferential_rate():

    result = calculate_preferential_rate(
        eligible=True,
        standard_rate_percent=Decimal("10"),
        preferential_rate_percent=Decimal("5"),
        agreement="TEST-AGREEMENT",
    )

    assert result["eligible"] is True

    assert (
        result["effective_rate_percent"]
        == Decimal("5")
    )

    assert result["rate_type"] == "PREFERENTIAL"

    assert (
        result["agreement"]
        == "TEST-AGREEMENT"
    )


def test_eligible_requires_preferential_rate():

    with pytest.raises(
        PreferentialRateError,
        match="Preferential rate is required",
    ):
        calculate_preferential_rate(
            eligible=True,
            standard_rate_percent=Decimal("10"),
            preferential_rate_percent=None,
        )


def test_preferential_rate_cannot_exceed_standard():

    with pytest.raises(
        PreferentialRateError,
        match="cannot be greater",
    ):
        calculate_preferential_rate(
            eligible=True,
            standard_rate_percent=Decimal("5"),
            preferential_rate_percent=Decimal("10"),
        )


def test_negative_standard_rate_is_rejected():

    with pytest.raises(
        PreferentialRateError,
        match="Standard duty rate cannot be negative",
    ):
        calculate_preferential_rate(
            eligible=False,
            standard_rate_percent=Decimal("-1"),
            preferential_rate_percent=None,
        )


def test_negative_preferential_rate_is_rejected():

    with pytest.raises(
        PreferentialRateError,
        match="Preferential duty rate cannot be negative",
    ):
        calculate_preferential_rate(
            eligible=True,
            standard_rate_percent=Decimal("10"),
            preferential_rate_percent=Decimal("-1"),
        )


def test_provenance_is_preserved():

    provenance = {
        "source": "test",
        "version": "1",
    }

    result = calculate_preferential_rate(
        eligible=True,
        standard_rate_percent=Decimal("10"),
        preferential_rate_percent=Decimal("5"),
        provenance=provenance,
    )

    assert result["provenance"] == provenance