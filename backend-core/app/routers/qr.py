"""QR code generation and document access routes.

POST /orders/{order_id}/generate-qr — generate a QR code PNG encoding a
short-lived JWT URL that grants access to the order's documents.

GET /orders/{order_id}/docs?token=X — public document access endpoint
used via QR codes (requires doc_access JWT + valid user Authorization).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import qrcode
from auth.deps import get_current_user, require_role
from auth.services.jwt import decode_token, is_revoked, revoke_token
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from storage.config import settings
from storage.crypto import DecryptionError, decrypt_field
from storage.db import get_session
from storage.redis import get_redis

from app.models.doc_pack import DocPack
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


# ---------------------------------------------------------------------------
# Helpers — doc access decryption
# ---------------------------------------------------------------------------

_SNAPSHOT_ENCRYPTED_MAP: dict[str, str] = {
    "pan_encrypted": "pan",
    "bank_account_encrypted": "bank_account",
    "ad_code_encrypted": "ad_code",
    "gstin_encrypted": "gstin",
}


def _looks_encrypted(value: object) -> bool:
    """Return True when *value* is a dict carrying ``ciphertext_b64``."""
    return isinstance(value, dict) and "ciphertext_b64" in value


def _decrypt_snapshot_field(
    snapshot: dict,
    encrypted_key: str,
    plain_key: str,
    seller_uuid: str,
    master_key: bytes,
) -> str | None:
    """Decrypt one encrypted field from the profile snapshot.

    Returns None if the field is missing, not encrypted, or decryption fails.
    """
    enc_value = snapshot.get(encrypted_key)
    if not _looks_encrypted(enc_value):
        return None
    try:
        return decrypt_field(enc_value, seller_uuid, master_key)
    except DecryptionError:
        return None


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

    Requires:
    - ``token`` query param: a valid doc_access JWT (purpose="doc_access")
    - ``Authorization`` header: user must be the order seller or a sahayak

    Returns decrypted PAN, bank account, AD code, IEC, GSTIN, and all
    DocPack documents.
    """
    # 1. Extract token from query param — 401 if missing -----------------------
    if not token:
        raise HTTPException(status_code=401, detail="Missing document access token")

    # 2. Decode doc_access JWT — 401 if invalid/expired ------------------------
    try:
        payload = decode_token(token, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Document access token has expired"
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401, detail="Invalid document access token"
        ) from None

    # 3. Check purpose — 401 if wrong ------------------------------------------
    if payload.get("purpose") != "doc_access":
        raise HTTPException(status_code=401, detail="Invalid document access token")

    jti: str | None = payload.get("jti")
    if not jti or not isinstance(jti, str):
        raise HTTPException(status_code=401, detail="Invalid document access token")

    # 4. Check is_revoked in Redis blacklist — 401 if revoked ------------------
    redis_client = get_redis()
    if await is_revoked(jti, redis_client):
        raise HTTPException(
            status_code=401, detail="Document access token has been revoked"
        )

    # 5. Match order_id from URL to token.sub — 403 if mismatch ----------------
    if payload.get("sub") != order_id:
        raise HTTPException(status_code=403, detail="Token does not match order")

    # 6. Authorization check — seller owner or sahayak -------------------------
    user: dict[str, str] = request.state.user
    user_id = user["user_id"]
    role = user["role"]

    # 7. Fetch order -----------------------------------------------------------
    try:
        oid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID") from None

    async with get_session()() as session:
        result = await session.execute(select(Order).where(Order.id == oid))
        order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # 8. Enforce seller-owner or sahayak access --------------------------------
    if role != "sahayak" and not (
        role == "seller" and str(order.seller_id) == user_id
    ):
        raise HTTPException(status_code=403, detail="Access denied to this order")

    # 9. Decrypt profile snapshot + encrypted order fields ---------------------
    # Lazily resolve settings so test monkeypatches apply (module-level import
    # captures the pre-patch object).
    from storage.config import settings as _s

    master_key = bytes.fromhex(_s.ENCRYPTION_MASTER_KEY)
    seller_uuid = str(order.seller_id)

    # Decrypt the outer snapshot blob to get the inner profile JSON
    snapshot_json = decrypt_field(
        order.profile_snapshot_encrypted, seller_uuid, master_key
    )
    snapshot = json.loads(snapshot_json)

    # Decrypt individual encrypted sub-fields inside the snapshot
    decrypted: dict[str, str | None] = {}
    for encrypted_key, plain_key in _SNAPSHOT_ENCRYPTED_MAP.items():
        decrypted[plain_key] = _decrypt_snapshot_field(
            snapshot, encrypted_key, plain_key, seller_uuid, master_key
        )

    # Override with order-level encrypted fields (higher priority)
    try:
        decrypted["ad_code"] = decrypt_field(
            order.ad_code_encrypted, seller_uuid, master_key
        )
    except DecryptionError:
        pass
    try:
        decrypted["bank_account"] = decrypt_field(
            order.bank_account_encrypted, seller_uuid, master_key
        )
    except DecryptionError:
        pass

    # 10. Fetch DocPack --------------------------------------------------------
    doc_pack = None
    if order.doc_pack_id is not None:
        async with get_session()() as session:
            doc_pack = await session.get(DocPack, order.doc_pack_id)

    # 11. Build response -------------------------------------------------------
    response: dict[str, object] = {
        "order_id": str(order.id),
        "status": order.status.value,
        "pan": decrypted.get("pan"),
        "bank_account": decrypted.get("bank_account"),
        "ad_code": decrypted.get("ad_code"),
        "iec": order.iec,
        "gstin": decrypted.get("gstin"),
        "exporter_name": order.exporter_name,
        "exporter_address": order.exporter_address,
        "bank_name": order.bank_name,
        "ifsc": order.ifsc,
        "destination_country": order.destination_country,
        "value_minor": order.value_minor,
        "currency": order.currency,
        "consignee": order.consignee,
        "line_items": order.line_items,
    }

    if doc_pack is not None:
        response["doc_pack"] = {
            "commercial_invoice": doc_pack.ci_json,
            "packing_list": doc_pack.pl_json,
            "cn22_cn23": doc_pack.cn_json,
            "pbe": doc_pack.pbe_json,
            "rendered_pdf_path": doc_pack.rendered_pdf_path,
            "qr_image_path": doc_pack.qr_image_path,
        }
    else:
        response["doc_pack"] = None

    return response
