"""Document-pack generators — CI, PL, CN22/CN23, PBE-III/IV from order data.

Each generator accepts an ``order_data`` dict with the relevant fields
extracted from an Order row.  The returned dict is stored as JSONB in a
DocPack row — no PDF rendering is done here.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# SDR conversion — 1 SDR ≈ ₹109.42 (≈10 942 paise, per CN22/CN23 thresholds)
# ---------------------------------------------------------------------------

SDR_MINOR_PER_UNIT: int = 10_942  # paise
SDR_THRESHOLD: int = 300

# ---------------------------------------------------------------------------
# Commercial Invoice (CI)
# ---------------------------------------------------------------------------


def generate_ci(order_data: dict[str, Any]) -> dict[str, Any]:
    """Generate a Commercial Invoice document from order data.

    Includes exporter details, consignee, line items with HSN codes,
    FOB value, IEC, and bank details.
    """
    line_items = _normalise_line_items(order_data)
    total_fob = sum(item.get("total_minor", 0) for item in line_items)

    return {
        "document_type": "Commercial Invoice",
        "exporter_name": order_data.get("exporter_name", ""),
        "exporter_address": order_data.get("exporter_address", ""),
        "iec": order_data.get("iec", ""),
        "consignee": order_data.get("consignee", ""),
        "destination_country": order_data.get("destination_country", ""),
        "currency": order_data.get("currency", "INR"),
        "invoice_date": _utcnow_iso(),
        "line_items": [
            {
                "description": item.get("description", ""),
                "hsn_code": item.get("hsn_code", ""),
                "quantity": item.get("quantity", 0),
                "unit_price_minor": item.get("unit_price_minor", 0),
                "total_minor": item.get("total_minor", 0),
            }
            for item in line_items
        ],
        "total_items": len(line_items),
        "total_value_minor": order_data.get("value_minor", total_fob),
        "fob_value_minor": total_fob,
        "bank_details": {
            "bank_name": order_data.get("bank_name", ""),
            "ifsc": order_data.get("ifsc", ""),
            "account_number": order_data.get("bank_account", ""),
        },
    }


# ---------------------------------------------------------------------------
# Packing List (PL)
# ---------------------------------------------------------------------------


def generate_pl(order_data: dict[str, Any]) -> dict[str, Any]:
    """Generate a Packing List document from order data.

    Includes net/gross weights, item descriptions, and quantities.
    """
    line_items = _normalise_line_items(order_data)
    total_qty = sum(item.get("quantity", 0) for item in line_items)

    return {
        "document_type": "Packing List",
        "exporter_name": order_data.get("exporter_name", ""),
        "consignee": order_data.get("consignee", ""),
        "destination_country": order_data.get("destination_country", ""),
        "net_weight_g": order_data.get("net_weight_g", 0.0),
        "gross_weight_g": order_data.get("gross_weight_g", 0.0),
        "items": [
            {
                "description": item.get("description", ""),
                "hsn_code": item.get("hsn_code", ""),
                "quantity": item.get("quantity", 0),
                "unit": "PIECES",
            }
            for item in line_items
        ],
        "total_quantity": total_qty,
        "total_pieces": len(line_items),
    }


# ---------------------------------------------------------------------------
# CN22 / CN23 — auto-selected based on SDR threshold
# ---------------------------------------------------------------------------


def generate_cn(order_data: dict[str, Any]) -> dict[str, Any]:
    """Generate a CN22 or CN23 customs declaration, auto-selected by order value.

    - **CN22** (≤ 300 SDR): basic description + value
    - **CN23** (> 300 SDR): detailed customs declaration with HS codes,
      origin country, and value breakdown
    """
    value_minor: int = order_data.get("value_minor", 0)
    sdr_value = value_minor / SDR_MINOR_PER_UNIT

    if sdr_value <= SDR_THRESHOLD:
        return _generate_cn22(order_data, sdr_value)
    return _generate_cn23(order_data, sdr_value)


def _generate_cn22(order_data: dict[str, Any], sdr_value: float) -> dict[str, Any]:
    """CN22 — simplified customs declaration for low-value shipments."""
    line_items = _normalise_line_items(order_data)
    descriptions = [item.get("description", "") for item in line_items]

    return {
        "document_type": "CN22",
        "cn_type": "CN22",
        "sdr_value": round(sdr_value, 2),
        "sdr_threshold": SDR_THRESHOLD,
        "content_description": "; ".join(descriptions),
        "total_value_minor": order_data.get("value_minor", 0),
        "currency": order_data.get("currency", "INR"),
        "gross_weight_g": order_data.get("gross_weight_g", 0.0),
        "origin_country": "IN",
        "destination_country": order_data.get("destination_country", ""),
    }


def _generate_cn23(order_data: dict[str, Any], sdr_value: float) -> dict[str, Any]:
    """CN23 — detailed customs declaration for shipments above 300 SDR."""
    line_items = _normalise_line_items(order_data)

    return {
        "document_type": "CN23",
        "cn_type": "CN23",
        "sdr_value": round(sdr_value, 2),
        "sdr_threshold": SDR_THRESHOLD,
        "exporter_name": order_data.get("exporter_name", ""),
        "iec": order_data.get("iec", ""),
        "consignee": order_data.get("consignee", ""),
        "destination_country": order_data.get("destination_country", ""),
        "origin_country": "IN",
        "currency": order_data.get("currency", "INR"),
        "item_details": [
            {
                "description": item.get("description", ""),
                "hs_code": item.get("hsn_code", ""),
                "quantity": item.get("quantity", 0),
                "unit_value_minor": item.get("unit_price_minor", 0),
                "total_minor": item.get("total_minor", 0),
                "origin_country": "IN",
                "net_weight_g": order_data.get("net_weight_g", 0.0)
                / max(len(line_items), 1),
            }
            for item in line_items
        ],
        "total_value_minor": order_data.get("value_minor", 0),
        "net_weight_g": order_data.get("net_weight_g", 0.0),
        "gross_weight_g": order_data.get("gross_weight_g", 0.0),
        "total_items": len(line_items),
    }


# ---------------------------------------------------------------------------
# PBE-III / PBE-IV — Postal Bill of Export
# ---------------------------------------------------------------------------


def generate_pbe(order_data: dict[str, Any]) -> dict[str, Any]:
    """Generate PBE-III/IV (Postal Bill of Export) data from order data.

    Includes IEC, AD code, CTH/HS codes, exporter declarations, scheme code,
    drawback info, and IGST status.  PBE-III e-commerce columns are included
    only when ``ecommerce_info`` is present in order_data (otherwise PBE-IV).
    """
    line_items = _normalise_line_items(order_data)
    ecommerce_info = order_data.get("ecommerce_info")

    form_type = "PBE-III" if ecommerce_info else "PBE-IV"

    base: dict[str, Any] = {
        "document_type": form_type,
        "form_type": form_type,
        # Header block
        "exporter_name": order_data.get("exporter_name", ""),
        "exporter_address": order_data.get("exporter_address", ""),
        "iec": order_data.get("iec", ""),
        "state_code": order_data.get("state_code", ""),
        "ad_code": order_data.get("ad_code", ""),
        "gstin": order_data.get("gstin", ""),
        # Consignee
        "consignee": order_data.get("consignee", ""),
        "destination_country": order_data.get("destination_country", ""),
        # Parcel / line table
        "line_items": [
            {
                "description": item.get("description", ""),
                "cth_code": item.get("hsn_code", ""),
                "quantity": item.get("quantity", 0),
                "unit": "PIECES",
                "gross_weight_g": order_data.get("gross_weight_g", 0.0)
                / max(len(line_items), 1),
                "net_weight_g": order_data.get("net_weight_g", 0.0)
                / max(len(line_items), 1),
                "assessable_value_minor": item.get("total_minor", 0),
            }
            for item in line_items
        ],
        "parcel_summary": {
            "gross_weight_g": order_data.get("gross_weight_g", 0.0),
            "net_weight_g": order_data.get("net_weight_g", 0.0),
            "fob_value_minor": order_data.get("value_minor", 0),
            "currency": order_data.get("currency", "INR"),
            "total_items": len(line_items),
        },
        # 2026 additions — scheme-aware fields
        "additional_details_2026": {
            "ritc_itchs_code": order_data.get("ritc_itchs_code"),
            "dbk_serial_no": order_data.get("dbk_serial_no"),
            "drawback_quantity": order_data.get("drawback_quantity"),
            "igst_payment_status": order_data.get("igst_payment_status", "not_paid"),
            "end_use": order_data.get("end_use", "Export"),
            "scheme_code": order_data.get("scheme_code"),
            "add_freight_minor": order_data.get("add_freight_minor"),
            "nature_of_contract": order_data.get("nature_of_contract", "FOB"),
        },
        # Declaration clusters (6 per the 2026 amendment)
        "declarations": {
            "zero_rated_export_u_s16_igst": True,
            "exemption_cgst_sgst_utgst_igst": False,
            "drawback": {
                "claimed": bool(order_data.get("scheme_code") == "drawback"),
                "no_itc_availed": True,
                "no_igst_refund_on_same_goods": True,
            },
            "rodtep": {
                "claimed": bool(order_data.get("scheme_code") == "rodtep"),
            },
            "rosctl": {
                "claimed": bool(order_data.get("scheme_code") == "rosctl"),
            },
            "fema_undertaking": True,
        },
    }

    # PBE-III e-commerce columns
    if ecommerce_info:
        base["ecommerce_columns"] = {
            "gstin_of_ecomm_operator": ecommerce_info.get("ecomm_gstin", ""),
            "marketplace_url": ecommerce_info.get("marketplace_url", ""),
            "payment_transaction_id": ecommerce_info.get("payment_txn_id", ""),
            "sku_no": ecommerce_info.get("sku_no", ""),
            "postal_tracking_number": ecommerce_info.get("tracking_number", ""),
        }

    return base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_line_items(order_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return line_items as a list of dicts, guarding against missing key."""
    items = order_data.get("line_items", [])
    if not isinstance(items, list):
        return []
    return items


def _utcnow_iso() -> str:
    """Return current UTC datetime as ISO-8601 string."""
    return datetime.now(UTC).isoformat()
