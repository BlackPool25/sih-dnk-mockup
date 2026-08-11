"""QR code generation routes — create scannable QR codes for document access.

POST /orders/{order_id}/generate-qr — generate a QR code PNG encoding a
short-lived JWT URL that grants access to the order's documents.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import qrcode
from auth.deps import get_current_user, require_role
from auth.services.jwt import is_revoked, revoke_token
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from storage.config import settings
from storage.db import get_session
from storage.redis import get_redis

from app.models.order import Order, OrderStatus

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
    """Render a QR code PNG at 300 dpi to *filepath*."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(str(filepath), dpi=(300, 300))


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
) -> dict:
    """Generate a QR code for document access.

    Requires the order to be in ``docs_generated`` status.  Revokes any
    previous QR token before issuing a new one.

    Returns 201 with the QR URL, token details, and image path.
    """
    user = request.state.user
    user_id: str = str(user["user_id"])

    # 1. Parse and fetch order ------------------------------------------------
    try:
        oid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID") from None

    async with get_session()() as session:
        result = await session.execute(select(Order).where(Order.id == oid))
        order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2. Owner check — only the seller who owns the order ---------------------
    if str(order.seller_id) != user_id:
        raise HTTPException(status_code=403, detail="Only the order owner can generate QR")

    # 3. Status must be docs_generated or qr_generated (regeneration) ----------
    if order.status not in (OrderStatus.docs_generated, OrderStatus.qr_generated):
        raise HTTPException(
            status_code=400,
            detail="Documents must be generated before QR code can be created",
        )

    # 4. Revoke previous QR token if one exists -------------------------------
    redis_client = get_redis()
    if order.qr_token_jti is not None:
        already_revoked = await is_revoked(order.qr_token_jti, redis_client)
        if not already_revoked:
            # Use a generous TTL (30 days) since we don't have the old token's exp handy
            await revoke_token(
                order.qr_token_jti,
                datetime.now(UTC) + timedelta(days=settings.DOC_ACCESS_TOKEN_EXPIRE_DAYS),
                redis_client,
            )

    # 5. Generate new doc-access JWT ------------------------------------------
    token, jti, expiry = _create_doc_access_jwt(order_id)

    # 6. Build QR URL and render image ----------------------------------------
    qr_url = f"{settings.APP_BASE_URL}/orders/{order_id}/docs?token={token}"

    _QR_DIR.mkdir(exist_ok=True)
    image_path = _QR_DIR / f"{order_id}.png"
    _generate_qr_png(qr_url, image_path)

    # 7. Persist — update order with new jti and status -----------------------
    async with get_session()() as session:
        order = await session.get(Order, order.id)
        order.qr_token_jti = jti
        order.status = OrderStatus.qr_generated
        await session.commit()

    return {
        "order_id": order_id,
        "qr_url": qr_url,
        "token": token,
        "token_jti": jti,
        "token_expiry": expiry.isoformat(),
        "qr_image_path": str(image_path),
    }
