"""Binding validation — exporter binding checks and e-FIRA reconciliation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.models.order import Order
from app.services.graded import ErrorEntry

# ── regex patterns ────────────────────────────────────────────────────────
_UTR_RE = re.compile(r"^[A-Za-z0-9]{12,22}$")
_IFSC_RE = re.compile(r"^[A-Za-z]{4}0[A-Za-z0-9]{6}$")
_IEC_RE = re.compile(r"^[A-Za-z0-9]{10}$")
_AD_CODE_RE = re.compile(r"^\d{14}$")

# ── mock DGFT registered banks (demo only — never calls real DGFT) ────────
_DGFT_KNOWN_BANKS: frozenset[str] = frozenset(
    {
        "STATE BANK OF INDIA",
        "HDFC BANK",
        "ICICI BANK",
        "AXIS BANK",
        "PUNJAB NATIONAL BANK",
        "BANK OF BARODA",
        "CANARA BANK",
        "UNION BANK OF INDIA",
        "BANK OF INDIA",
        "KOTAK MAHINDRA BANK",
    }
)

# ── statuses at/above which binding fields are frozen ─────────────────────
if TYPE_CHECKING:
    from app.models.order import OrderStatus as _OrderStatus
else:
    from app.models.order import OrderStatus as _OrderStatus

_FROZEN_STATUSES: frozenset[_OrderStatus] = frozenset(
    {
        _OrderStatus.confirmed,
        _OrderStatus.paid_held,
        _OrderStatus.in_transit,
        _OrderStatus.delivered,
        _OrderStatus.disputed,
        _OrderStatus.settled,
        _OrderStatus.refunded,
    }
)

_BINDING_FIELDS: tuple[str, ...] = ("iec", "ad_code", "bank_account", "bank_name", "ifsc")


# ── public ────────────────────────────────────────────────────────────────


def validate_e_fira_reconciliation(
    order: Order,
    utr: str | None = None,
    remitter_ifsc: str | None = None,
) -> list[ErrorEntry]:
    """Mock e-FIRA reconciliation check.

    Validates UTR format and IFSC match against the order.
    Returns a list of ErrorEntry — empty when all checks pass.
    """
    errors: list[ErrorEntry] = []

    # ── UTR format check (alphanumeric, 12-22 chars) ──
    if utr is not None and not _UTR_RE.match(utr):
        errors.append(
            ErrorEntry(
                field="utr",
                severity="error",
                action="blocking",
                message="e-FIRA UTR mismatch",
            )
        )

    # ── remitter IFSC format check (4alpha+0+6alphanumeric) ──
    if remitter_ifsc is not None and not _IFSC_RE.match(remitter_ifsc):
        errors.append(
            ErrorEntry(
                field="remitter_ifsc",
                severity="error",
                action="blocking",
                message=f"e-FIRA IFSC format invalid: {remitter_ifsc!r}",
            )
        )
        return errors  # cannot compare if remitter IFSC is malformed

    # ── IFSC mismatch check ──
    if remitter_ifsc is not None and order.ifsc is not None and remitter_ifsc != order.ifsc:
        errors.append(
            ErrorEntry(
                field="ifsc",
                severity="error",
                action="blocking",
                message="e-FIRA IFSC mismatch: remitter IFSC does not match order IFSC",
            )
        )
        # Freeze payouts on IFSC mismatch
        errors.append(
            ErrorEntry(
                field="ifsc",
                severity="error",
                action="freeze_payout",
                message="e-FIRA IFSC mismatch: payouts frozen",
            )
        )

    return errors


def validate_exporter_binding(order: Order) -> list[ErrorEntry]:
    """Validate exporter binding fields on an Order.

    Checks executed:
    1.  **IEC** — 10-char alphanumeric (``^[A-Za-z0-9]{10}$``).
    2.  **AD Code** — 14-digit numeric (``^\\d{14}$``).
    3.  **IFSC** — 4-alpha + 0 + 6-alphanumeric (``^[A-Za-z]{4}0[A-Za-z0-9]{6}$``).
    4.  **Bank account** — ``bank_name`` is required when ``bank_account`` is set.
    5.  **Bank mismatch** — mock DGFT lookup: checks ``bank_name`` against a
       hard-coded known-banks set; a *warning* is produced when the name is
       unknown (demo only — never calls real DGFT).
    6.  **Lock-on-order** — once ``Order.status >= OrderStatus.confirmed``,
       binding fields (iec, ad_code, bank_account, bank_name, ifsc) are
       frozen.  Any non-None value on a confirmed order produces a *block*
       entry — the caller must discard payload changes before calling this
       function.
    7.  **Version check** — confirmed orders must have ``version >= 1``.

    Returns a (possibly empty) list of ``ErrorEntry`` objects.  This function
    never raises — all violations are structured entries.
    """
    errors: list[ErrorEntry] = []

    # ── 1. IEC format ──────────────────────────────────────────────────
    _iec = order.iec
    if _iec is not None and not _IEC_RE.match(_iec):
        errors.append(
            ErrorEntry(
                field="iec",
                severity="error",
                message=f"invalid IEC format: {_iec!r} (expect 10-char alphanumeric)",
                action="blocking",
            )
        )

    # ── 2. AD Code format ──────────────────────────────────────────────
    _ad_code = order.ad_code
    if _ad_code is not None and not _AD_CODE_RE.match(_ad_code):
        errors.append(
            ErrorEntry(
                field="ad_code",
                severity="error",
                message=f"invalid AD code format: {_ad_code!r} (expect 14 digits)",
                action="blocking",
            )
        )

    # ── 3. IFSC format ─────────────────────────────────────────────────
    _ifsc = order.ifsc
    if _ifsc is not None and not _IFSC_RE.match(_ifsc):
        errors.append(
            ErrorEntry(
                field="ifsc",
                severity="error",
                message=(f"invalid IFSC format: {_ifsc!r} (expect 4alpha+0+6alphanumeric)"),
                action="blocking",
            )
        )

    # ── 4. bank_account / bank_name consistency ────────────────────────
    _bank_account = order.bank_account
    _bank_name = order.bank_name
    if _bank_account is not None and not _bank_name:
        errors.append(
            ErrorEntry(
                field="bank_name",
                severity="error",
                message="bank_name is required when bank_account is provided",
                action="blocking",
            )
        )

    # ── 5. bank mismatch (mock DGFT lookup) ────────────────────────────
    if (
        _bank_account is not None
        and _ad_code is not None
        and _bank_name is not None
        and _bank_name.upper() not in _DGFT_KNOWN_BANKS
    ):
        errors.append(
            ErrorEntry(
                field="bank_name",
                severity="warning",
                message=(
                    f"bank_name {_bank_name!r} not found in DGFT registered banks (mock lookup)"
                ),
                action="check_input",
            )
        )

    # ── 6 + 7. lock-on-order + version check ───────────────────────────
    _status = order.status
    if _status is not None and _status in _FROZEN_STATUSES:
        # Version check — confirmed orders must have version >= 1.
        if order.version < 1:
            errors.append(
                ErrorEntry(
                    field="version",
                    severity="block",
                    message=(f"invalid version {order.version} for confirmed order (expect >= 1)"),
                    action="blocking",
                )
            )

        # Binding fields are frozen — any non-None value on a confirmed
        # order means a change attempt was detected (the caller must have
        # already discarded the payload changes before calling).
        frozen_fields = [f for f in _BINDING_FIELDS if getattr(order, f, None) is not None]
        if frozen_fields:
            errors.append(
                ErrorEntry(
                    field="binding",
                    severity="block",
                    message="Binding fields frozen after order is confirmed",
                    action="blocking",
                )
            )

    return errors


__all__ = [
    "validate_e_fira_reconciliation",
    "validate_exporter_binding",
]
