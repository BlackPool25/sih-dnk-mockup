"""Human-reply echo limit."""
from __future__ import annotations
import asyncio
from app.schemas.llm import ChatRequest
from app.services.chat import build_reply, new_conversation_id, new_state, run_turn
from app.services.llm_reply import echo_line, options_line
from tests.fake_val_client import FakeValClient
from tests.test_chat_service import FakeRedis
def _run(coro): return asyncio.run(coro)
def test_echo_line_only_changed_fields() -> None:
    draft = {"product_category": "jute-products","quantity": 12,"weight_grams": 500,"destination_country": "DE","value_minor": 1500000,"consignee": "John Doe",}
    db_info = {"category_name": "Jute Products"}
    full = echo_line("hi", draft, db_info)
    assert "12" in full and "500" in full and "जर्मनी" in full
    limited = echo_line("hi", draft, db_info, only_fields=["quantity"])
    assert "12" in limited and "500" not in limited and "जर्मनी" not in limited and "Jute Products" not in limited
def test_build_reply_only_changed_fields() -> None:
    draft = {"product_category": "jute-products","quantity": 12,"weight_grams": 500,"destination_country": "DE","value_minor": 1500000,"consignee": "unknown",}
    db_info = {"category_name": "Jute Products"}
    reply = build_reply("hi", draft, db_info, "destination_country", [], changed_fields=["quantity"])
    assert "12" in reply and "500" not in reply
def test_options_line_prefers_name_hi_over_slug_title() -> None:
    candidates = [{"slug": "jute-products", "name": "Jute Products", "name_hi": "जूट उत्पाद"},{"slug": "small-woodware", "name": "Small Woodware"},]
    line = options_line("hi", candidates)
    assert "जूट उत्पाद" in line and "Small Woodware" in line
    line2 = options_line("hi", [{"slug": "jute-products"}])
    assert "jute-products" in line2
def test_end_to_end_echo_limited_to_newly_filled() -> None:
    client = FakeValClient(); redis = FakeRedis(); conv_id = new_conversation_id(); state = new_state("u1", "hi")
    body1 = ChatRequest(message="12 जूट बैग 500 ग्राम जर्मनी ₹15000", language="hi")
    resp1 = _run(run_turn(user_id="u1", body=body1, conv_id=conv_id, state=state, redis=redis, val_client=client))
    assert "12" in resp1.reply_text
    from app.services.val_client import ExtractResult
    class OnlyWeightClient(FakeValClient):
        async def extract(self, text, lang, previous=None, expected=None):
            self.calls.append("extract"); return ExtractResult(draft={"weight_grams": 700}, category_unknown=False, extractor="rule")
    only_weight = OnlyWeightClient(); body2 = ChatRequest(message="700 ग्राम", language="hi", conversation_id=conv_id)
    resp2 = _run(run_turn(user_id="u1", body=body2, conv_id=conv_id, state=state, redis=redis, val_client=only_weight))
    assert "700" in resp2.reply_text and resp2.reply_text.count("12") == 0
