"""QR code generation and document access routes — thin proxy.

POST /orders/{order_id}/generate-qr — generate a QR code PNG encoding a
short-lived JWT URL that grants access to the order's documents.  The order's
documents live in validation-engine; the QR token JTI is persisted there via
``set_qr_token``.  The JWT/revocation logic is preserved from the original
backend-core implementation (unchanged semantics).

GET /orders/{order_id}/docs?token=X — public document access endpoint used via
QR codes (requires doc_access JWT + valid user Authorization).  Order data and
documents come from validation-engine (plaintext — no decryption).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from qrcode.constants import ERROR_CORRECT_L

from app.routers.orders import _get_order_or_404, _split_order_data
from app.services.val_client import (
    InvalidInputError,
    NotFoundError,
    ServiceUnavailable,
    val_client,
)
from auth.deps import get_current_user, require_role
from auth.services.jwt import decode_token, is_revoked, revoke_token
from storage.config import settings
from storage.redis import get_redis

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/orders/{order_id}", tags=["qr"])

_QR_DIR = Path("qr_codes")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_doc_access_jwt(order_id: str) -> tuple[str, str, datetime]:
    """Create a doc-access JWT with purpose='doc_access'.

    Returns:
        (encoded_token, jti, expiry_datetime)
    """
    now = datetime.now(UTC)
    expiry = now + timedelta(days=settings.DOC_ACCESS_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())

    payload = {
        "sub": order_id,
        "purpose": "doc_access",
        "iat": now,
        "exp": expiry,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expiry


def _generate_qr_png(data: str, filepath: Path) -> None:
    """Render a QR code PNG to *filepath*."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    with filepath.open("wb") as fh:
        img.save(fh)


def _enforce_doc_access(order: dict[str, object], user: dict[str, str]) -> None:
    """Raise 403 unless the user is the order's seller or a sahayak."""
    user_id = user["user_id"]
    role = user["role"]
    seller_id = str(order.get("seller_id") or "")
    if role != "sahayak" and not (role == "seller" and seller_id == user_id):
        raise HTTPException(status_code=403, detail="Access denied to this order")


async def _fetch_documents(order_id: str) -> list[object]:
    """Fetch the order's documents from validation-engine; [] if none yet."""
    try:
        data = await val_client.get_order_documents(order_id)
    except NotFoundError:
        return []
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    documents = data.get("documents", [])
    return documents if isinstance(documents, list) else []


# ---------------------------------------------------------------------------
# POST /orders/{order_id}/generate-qr
# ---------------------------------------------------------------------------


@router.post(
    "/generate-qr",
    status_code=201,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def generate_qr(
    request: Request,
    order_id: str,
) -> dict[str, object]:
    """Generate a QR code for document access.

    Requires the order to have generated documents.  Revokes any previous QR
    token before issuing a new one, persists the new JTI in validation-engine,
    and returns the QR URL, token details, and image path.
    """
    user = request.state.user
    user_id: str = str(user["user_id"])

    # 1. Fetch order + owner check --------------------------------------------
    order_data = await _get_order_or_404(order_id)
    order, _line_items = _split_order_data(order_data)
    if str(order.get("seller_id") or "") != user_id:
        raise HTTPException(status_code=403, detail="Only the order owner can generate QR")

    # 2. Documents must exist ------------------------------------------------
    if not await _fetch_documents(order_id):
        raise HTTPException(
            status_code=400,
            detail="Generate documents first",
        )

    # 3. Revoke previous QR token if one exists -------------------------------
    redis_client = get_redis()
    existing_jti = order.get("qr_token_jti")
    if existing_jti and isinstance(existing_jti, str):
        already_revoked = await is_revoked(existing_jti, redis_client)
        if not already_revoked:
            # Generous TTL — the old token's exp isn't available post-proxy.
            await revoke_token(
                existing_jti,
                datetime.now(UTC) + timedelta(days=settings.DOC_ACCESS_TOKEN_EXPIRE_DAYS),
                redis_client,
            )

    # 4. Generate new doc-access JWT ------------------------------------------
    token, jti, expiry = _create_doc_access_jwt(order_id)

    # 5. Build QR URL and render image ----------------------------------------
    qr_url = f"{settings.APP_BASE_URL}/orders/{order_id}/docs?token={token}"

    _QR_DIR.mkdir(exist_ok=True)
    image_path = _QR_DIR / f"{order_id}.png"
    _generate_qr_png(qr_url, image_path)

    # 6. Persist the new JTI in validation-engine -----------------------------
    try:
        await val_client.set_qr_token(order_id, jti)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "order_id": order_id,
        "qr_url": qr_url,
        "token": token,
        "token_jti": jti,
        "token_expiry": expiry.isoformat(),
        "qr_image_path": str(image_path),
    }


# ---------------------------------------------------------------------------
# GET /orders/{order_id}/docs — Document access
# ---------------------------------------------------------------------------


@router.get(
    "/docs",
    dependencies=[Depends(get_current_user)],
)
async def get_qr_docs(
    request: Request,
    order_id: str,
    token: str = Query(default=None),
) -> dict[str, object]:
    """Access order documents via QR-code doc_access token.

    Preserves the original JWT validation + revocation flow:
    - ``token`` query param: a valid doc_access JWT (purpose="doc_access")
    - ``Authorization`` header: user must be the order seller or a sahayak

    Order data is read from validation-engine as plaintext (no decryption);
    the response drops ``pan`` and exposes ``gstin``.
    """
    # 1. Extract token from query param — 401 if missing -----------------------
    if not token:
        raise HTTPException(status_code=401, detail="Missing document access token")

    # 2. Decode doc_access JWT — 401 if invalid/expired ------------------------
    try:
        payload = decode_token(token, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Document access token has expired") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid document access token") from None

    # 3. Check purpose — 401 if wrong ------------------------------------------
    if payload.get("purpose") != "doc_access":
        raise HTTPException(status_code=401, detail="Invalid document access token")

    jti: object = payload.get("jti")
    if not jti or not isinstance(jti, str):
        raise HTTPException(status_code=401, detail="Invalid document access token")

    # 4. Check is_revoked in Redis blacklist — 401 if revoked ------------------
    redis_client = get_redis()
    if await is_revoked(jti, redis_client):
        raise HTTPException(status_code=401, detail="Document access token has been revoked")

    # 5. Match order_id from URL to token.sub — 403 if mismatch ----------------
    if payload.get("sub") != order_id:
        raise HTTPException(status_code=403, detail="Token does not match order")

    # 6. Fetch order + enforce seller-owner or sahayak access ------------------
    user: dict[str, str] = request.state.user

    order_data = await _get_order_or_404(order_id)
    order, _line_items = _split_order_data(order_data)
    _enforce_doc_access(order, user)

    # 7. Fetch documents from validation-engine --------------------------------
    documents = await _fetch_documents(order_id)

    # 8. Build response — plaintext order data + engine documents --------------
    return {
        "order_id": str(order.get("id") or order_id),
        "status": str(order.get("status") or ""),
        "bank_account": order.get("bank_account"),
        "ad_code": order.get("ad_code"),
        "iec": order.get("iec"),
        "gstin": order.get("gstin"),
        "exporter_name": order.get("exporter_name"),
        "exporter_address": order.get("exporter_address"),
        "bank_name": order.get("bank_name"),
        "ifsc": order.get("ifsc"),
        "destination_country": order.get("destination_country"),
        "value_minor": order.get("value_minor"),
        "currency": order.get("currency") or "INR",
        "consignee": order.get("consignee"),
        "line_items": _line_items,
        "documents": documents,
    }
