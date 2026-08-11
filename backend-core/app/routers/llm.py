"""LLM conversation state management — create, read, and delete conversations.

State is held in Redis hashes under ``llm:conv:{id}`` with a configurable
TTL (reset on each interaction).  All endpoints require seller auth; the
owner check on GET/DELETE enforces that a seller can only access their own
conversations.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.llm import ChatRequest, ChatResponse, SessionResponse
from auth.deps import get_current_user, require_role

# Route prefix is /api/llm (see main.py registration)
router = APIRouter(prefix="/api/llm", tags=["llm"])

_REDIS_KEY_PREFIX = "llm:conv"


def _get_settings():
    """Lazily import settings so test patches apply."""
    from storage.config import settings as s

    return s


# ---------------------------------------------------------------------------
# Redis helpers
# ---------------------------------------------------------------------------


def _redis_key(conv_id: str) -> str:
    return f"{_REDIS_KEY_PREFIX}:{conv_id}"


async def _get_conv_state(redis, conv_id: str) -> dict[str, str]:
    """Fetch the hash for *conv_id*, raising 404 if missing or expired."""
    key = _redis_key(conv_id)
    raw: dict[bytes, bytes] = await redis.hgetall(key)
    if not raw:
        raise HTTPException(status_code=404, detail="Conversation not found or expired")
    return {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in raw.items()}


async def _save_conv_state(redis, conv_id: str, state: dict[str, object]) -> None:
    """Persist a conversation state hash and (re)set its TTL."""
    key = _redis_key(conv_id)
    # Only store string values — JSON-encode structured fields
    flat: dict[str, str] = {}
    for k, v in state.items():
        if isinstance(v, (dict, list)):
            flat[k] = json.dumps(v)
        else:
            flat[k] = str(v) if v is not None else ""
    await redis.hset(key, mapping=flat)
    ttl_seconds = _get_settings().LLM_CONVERSATION_TTL_HOURS * 3600
    await redis.expire(key, ttl_seconds)


def _hydrate_response(
    conv_id: str, raw: dict[str, str]
) -> dict[str, object]:
    """Convert raw Redis hash bytes → Python dict matching ``ChatResponse``."""
    def _json_load(key: str) -> object:
        val = raw.get(key, "")
        if not val:
            return {} if key == "filled_fields" else [] if key in ("pending_fields", "history") else val
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val

    return {
        "conversation_id": conv_id,
        "user_id": raw.get("user_id", ""),
        "language": raw.get("language", ""),
        "current_step": raw.get("current_step", "init"),
        "filled_fields": _json_load("filled_fields"),
        "pending_fields": _json_load("pending_fields"),
        "history": _json_load("history"),
    }


# ---------------------------------------------------------------------------
# POST /api/llm/chat — create or continue a conversation
# ---------------------------------------------------------------------------


@router.post(
    "/chat",
    status_code=201,
    response_model=ChatResponse,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def chat(
    request: Request,
    body: ChatRequest,
) -> dict[str, object]:
    """Create or continue an LLM conversation.

    - Omit ``conversation_id`` to start a new conversation.
    - Include it to continue an existing one (must be owned by the caller).

    The route does **not** invoke an LLM — it only manages state.  After
    the LLM produces a response, the caller updates ``filled_fields``,
    ``pending_fields``, and ``current_step`` via the body or a separate
    internal handler.
    """
    from storage.redis import get_redis

    user_id: str = str(request.state.user["user_id"])
    redis = get_redis()

    if body.conversation_id:
        # --- Continue existing conversation -----------------------------------
        raw = await _get_conv_state(redis, body.conversation_id)

        # Owner check
        if raw.get("user_id", "") != user_id:
            raise HTTPException(status_code=403, detail="Not your conversation")

        # Append message to history
        history: list[dict[str, str]] = json.loads(raw.get("history", "[]"))
        history.append({"role": "user", "content": body.message})

        state: dict[str, object] = {
            "user_id": user_id,
            "language": body.language,
            "current_step": raw.get("current_step", "init"),
            "filled_fields": json.loads(raw.get("filled_fields", "{}")),
            "pending_fields": json.loads(raw.get("pending_fields", "[]")),
            "history": history,
        }

        await _save_conv_state(redis, body.conversation_id, state)

        return _hydrate_response(body.conversation_id, await _get_conv_state(redis, body.conversation_id))

    # --- New conversation -----------------------------------------------------
    conv_id = uuid.uuid4().hex

    state = {
        "user_id": user_id,
        "language": body.language,
        "current_step": "init",
        "filled_fields": {},
        "pending_fields": [],
        "history": [{"role": "user", "content": body.message}],
    }

    await _save_conv_state(redis, conv_id, state)

    return _hydrate_response(conv_id, await _get_conv_state(redis, conv_id))


# ---------------------------------------------------------------------------
# GET /api/llm/session/{session_id} — retrieve conversation state
# ---------------------------------------------------------------------------


@router.get(
    "/session/{session_id}",
    response_model=SessionResponse,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def get_session(
    request: Request,
    session_id: str,
) -> dict[str, object]:
    """Return the full state of a conversation owned by the caller."""
    from storage.redis import get_redis

    user_id: str = str(request.state.user["user_id"])
    redis = get_redis()

    raw = await _get_conv_state(redis, session_id)

    # Owner check
    if raw.get("user_id", "") != user_id:
        raise HTTPException(status_code=403, detail="Not your conversation")

    return _hydrate_response(session_id, raw)


# ---------------------------------------------------------------------------
# DELETE /api/llm/session/{session_id} — delete a conversation
# ---------------------------------------------------------------------------


@router.delete(
    "/session/{session_id}",
    status_code=204,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def delete_session(
    request: Request,
    session_id: str,
):
    """Delete a conversation owned by the caller."""
    from starlette.responses import Response

    from storage.redis import get_redis

    user_id: str = str(request.state.user["user_id"])
    redis = get_redis()

    # Verify existence and ownership first
    raw = await _get_conv_state(redis, session_id)
    if raw.get("user_id", "") != user_id:
        raise HTTPException(status_code=403, detail="Not your conversation")

    await redis.delete(_redis_key(session_id))
    return Response(status_code=204)
