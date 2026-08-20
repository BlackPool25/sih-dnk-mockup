"""LLM conversation routes — the voice-first chat turn loop."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from app.models.profile import SellerProfile
from app.schemas.llm import ChatRequest, ChatResponse, SessionResponse
from app.services import chat
from auth.deps import get_current_user, require_role
router = APIRouter(prefix="/api/llm", tags=["llm"])
_REDIS_KEY_PREFIX = "chat_session"
async def _profile_identifiers(user_id: str) -> tuple[str | None, str | None, str | None]:
    from storage.db import get_session
    async with get_session()() as session:
        result = await session.execute(select(SellerProfile).where(SellerProfile.user_id == uuid.UUID(user_id)))
        profile = result.scalar_one_or_none()
    if profile is None:
        return None, None, None
    gstin: str | None = None
    if profile.gstin_encrypted:
        try:
            from app.services.profile_crypto import decrypt_value
            gstin = decrypt_value(profile.gstin_encrypted)  # type: ignore[arg-type]
        except Exception:
            gstin = None
    state_code: str | None = profile.state or None
    return profile.iec or None, gstin, state_code
async def _get_conv_state(redis, conv_id: str) -> dict[str, object]:
    state = await chat.load_state(redis, conv_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Conversation not found or expired")
    return state
def _snapshot_response(conv_id: str, state: dict[str, object]) -> dict[str, object]:
    history = state.get("history")
    last = history[-1]["content"] if isinstance(history, list) and history else ""
    resp = chat.build_state_response(conv_id, str(state["user_id"]), str(state["language"]), state, str(last))
    return resp.model_dump()
@router.post("/chat", status_code=201, response_model=ChatResponse, dependencies=[Depends(get_current_user), Depends(require_role("seller"))])
async def chat_endpoint(request: Request, body: ChatRequest) -> dict[str, object]:
    from storage.redis import get_redis
    user_id: str = str(request.state.user["user_id"])
    redis = get_redis()
    if body.conversation_id:
        state = await _get_conv_state(redis, body.conversation_id)
        if state.get("user_id", "") != user_id:
            raise HTTPException(status_code=403, detail="Not your conversation")
        conv_id = body.conversation_id
    else:
        conv_id = chat.new_conversation_id()
        state = chat.new_state(user_id, body.language)
    iec, gstin, state_code = await _profile_identifiers(user_id)
    result = await chat.run_turn(user_id=user_id, body=body, conv_id=conv_id, state=state, redis=redis, iec=iec, gstin=gstin, state_code=state_code)
    return result.model_dump()
@router.get("/session/{session_id}", response_model=SessionResponse, dependencies=[Depends(get_current_user), Depends(require_role("seller"))])
async def get_session(request: Request, session_id: str) -> dict[str, object]:
    from storage.redis import get_redis
    user_id: str = str(request.state.user["user_id"])
    redis = get_redis()
    state = await _get_conv_state(redis, session_id)
    if state.get("user_id", "") != user_id:
        raise HTTPException(status_code=403, detail="Not your conversation")
    return _snapshot_response(session_id, state)
@router.delete("/session/{session_id}", status_code=204, dependencies=[Depends(get_current_user), Depends(require_role("seller"))])
async def delete_session(request: Request, session_id: str):
    from starlette.responses import Response
    from storage.redis import get_redis
    user_id: str = str(request.state.user["user_id"])
    redis = get_redis()
    state = await _get_conv_state(redis, session_id)
    if state.get("user_id", "") != user_id:
        raise HTTPException(status_code=403, detail="Not your conversation")
    await redis.delete(f"{_REDIS_KEY_PREFIX}:{session_id}")
    return Response(status_code=204)
