import json
import logging
import uuid
import sys
from pathlib import Path
import importlib

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from storage.redis import get_redis
from auth.deps import get_current_user, require_role
from storage.config import settings

router = APIRouter(prefix="/api/llm", tags=["llm"])

class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    language: str = "en"

class ChatResponse(BaseModel):
    conversation_id: str
    user_id: str
    language: str
    current_step: str
    filled_fields: dict
    pending_fields: list[str]
    history: list[dict]
    db_info: dict = Field(default_factory=dict)

required_sequence = [
    "product_category",
    "quantity",
    "weight_grams",
    "destination_country",
    "consignee",
    "value_minor"
]

FIELD_QUESTIONS = {
    "product_category": "What product are you exporting?",
    "quantity": "How many units are you shipping?",
    "weight_grams": "What's the total weight of the shipment, in grams?",
    "destination_country": "Which country is this shipment going to?",
    "consignee": "Who is the consignee (name and address)?",
    "value_minor": "What's the total declared value of the shipment, in INR?",
}

def _get_next_question(filled: dict) -> str:
    missing = [f for f in required_sequence if f not in filled]
    if missing:
        return FIELD_QUESTIONS.get(missing[0], f"Please provide: {missing[0]}")
    return "All details collected! Please click 'Simulate Completing Order'"

def _get_settings():
    return settings

def _val_exec(fn, *args, **kwargs):
    val_dir = Path(__file__).resolve().parent.parent.parent.parent / "validation-engine"
    saved = {k: v for k, v in sys.modules.items() if k == 'app' or k.startswith('app.')}
    for k in list(sys.modules.keys()):
        if k == 'app' or k.startswith('app.'):
            del sys.modules[k]
    sys.path.insert(0, str(val_dir))
    try:
        return fn(*args, **kwargs)
    finally:
        for k in list(sys.modules.keys()):
            if k == 'app' or k.startswith('app.'):
                del sys.modules[k]
        sys.modules.update(saved)
        if str(val_dir) in sys.path:
            sys.path.remove(str(val_dir))

def _get_val_modules():
    val_dir = Path(__file__).resolve().parent.parent.parent.parent / "validation-engine"
    saved = {k: v for k, v in sys.modules.items() if k == 'app' or k.startswith('app.')}
    for k in list(sys.modules.keys()):
        if k == 'app' or k.startswith('app.'):
            del sys.modules[k]
    sys.path.insert(0, str(val_dir))
    try:
        importlib.import_module('app.services.docs.renderer')
        importlib.import_module('app.services.country_rules')
        val_extract = importlib.import_module('app.services.extract')
        val_db_tools = importlib.import_module('app.services.db_tools')
        val_validate = importlib.import_module('app.services.validate')
        val_document = importlib.import_module('app.services.docs.document')
        val_shipment = importlib.import_module('app.schemas.shipment')
    finally:
        for k in list(sys.modules.keys()):
            if k == 'app' or k.startswith('app.'):
                del sys.modules[k]
        sys.modules.update(saved)
        if str(val_dir) in sys.path:
            sys.path.remove(str(val_dir))
    return val_extract, val_db_tools, val_validate, val_document, val_shipment

def _clean_filled_placeholders(filled: dict) -> dict:
    cleaned = {}
    for k, v in filled.items():
        if v is None:
            continue
        s = str(v).strip().lower()
        if s in ("null", "none", "unknown", "-1", "—", "") or s.endswith("_val") or s.startswith("placeholder"):
            print(f"[LLM ROUTER SAFEGUARD] Purging placeholder value {v!r} for key '{k}'")
            continue
        if k in ("quantity", "weight_grams", "value_minor") and isinstance(v, (int, float)) and v <= 0:
            print(f"[LLM ROUTER SAFEGUARD] Purging non-positive number {v!r} for key '{k}'")
            continue
        cleaned[k] = v
    return cleaned

def _run_extraction(message: str, lang: str, existing_filled: dict, history: list = None) -> tuple[dict, list, str, str]:
    val_extract, val_db_tools, val_validate, val_document, val_shipment = _get_val_modules()
    filled = _clean_filled_placeholders(existing_filled)

    missing_fields = [f for f in required_sequence if f not in filled]
    if history is None:
        history = []

    reply = ""
    missing_before = [f for f in required_sequence if f not in filled]
    
    print(f"\n==================== [LLM EXTRACTION TURN] ====================")
    print(f"User Message: {message!r}")
    print(f"Language: {lang!r}")
    print(f"Existing Filled Fields: {filled}")
    print(f"Missing Fields Before: {missing_before}")

    # Attempt RuleExtractor First
    rule_reply = ""
    rule_extracted_something = False
    print(f"\n[CONTROL FLOW] -> Invoking RuleExtractor...")
    try:
        rule_shipment = _val_exec(val_extract.RuleExtractor().extract_from_text, message, lang)
        print(f"[EXTRACTOR RESULT] -> RuleExtractor returned: {rule_shipment}")
        if rule_shipment:
            if rule_shipment.product_category and rule_shipment.product_category != "unknown" and "product_category" not in filled:
                filled["product_category"] = rule_shipment.product_category
                rule_extracted_something = True
            if rule_shipment.quantity and rule_shipment.quantity != -1 and "quantity" not in filled:
                filled["quantity"] = rule_shipment.quantity
                rule_extracted_something = True
            if rule_shipment.weight_grams and rule_shipment.weight_grams != -1 and "weight_grams" not in filled:
                filled["weight_grams"] = rule_shipment.weight_grams
                rule_extracted_something = True
            if rule_shipment.destination_country and rule_shipment.destination_country != "unknown" and "destination_country" not in filled:
                filled["destination_country"] = rule_shipment.destination_country
                rule_extracted_something = True
    except Exception as e:
        if type(e).__name__ == "CategoryUnknownError":
            print(f"[EXTRACTOR RESULT] -> RuleExtractor raised CategoryUnknownError: {e}")
            if "product_category" not in filled:
                rule_reply = "I couldn't recognize that product category. We currently support: block-printed-textiles, embroidered-bags-pouches, embroidered-home-textiles, handloom-scarves-stoles, imitation-artisan-jewellery, jute-products, small-brass-metalware, small-woodware. Which one fits best?"
                pending = [f for f in required_sequence if f not in filled]
                return filled, pending, "collecting", rule_reply, {}
        else:
            print(f"[EXTRACTOR RESULT] -> RuleExtractor failed with exception: {e}")

    # Regex rule extraction for weight, consignee and value
    import re

    # Weight regex fallback (e.g. "500g", "500 grams", "2 kg")
    if "weight_grams" not in filled:
        w_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:g|gm|grams?|kg|kilo|kilograms?)\b", message, re.IGNORECASE)
        if w_match:
            try:
                w_val = float(w_match.group(1))
                if "kg" in w_match.group(0).lower() or "kilo" in w_match.group(0).lower():
                    w_val *= 1000
                filled["weight_grams"] = int(round(w_val))
                rule_extracted_something = True
            except ValueError:
                pass

    # Only match value when an explicit currency signal is present (₹/Rs/INR or "of ₹")
    # Prevents "500g" weight-only messages from being misread as money values
    _HAS_CURRENCY = bool(re.search(r"₹|\brs\.?\b|\binr\b|\brupees?\b", message, re.IGNORECASE))
    if _HAS_CURRENCY and "value_minor" not in filled:
        # Match the number that directly follows or precedes a currency symbol
        v_match = re.search(r"(?:₹|rs\.?|inr|rupees?)\s*([\d,]+)|([\d,]+)\s*(?:inr|rs\.?|rupees?)", message, re.IGNORECASE)
        if v_match:
            try:
                raw_num_str = (v_match.group(1) or v_match.group(2) or "").replace(",", "")
                val_num = int(raw_num_str)
                if val_num > 0:
                    filled["value_minor"] = val_num * 100
                    rule_extracted_something = True
            except ValueError:
                pass

    # Consignee extraction: Case A (explicit markers) + Case B (active pending question)
    if "consignee" not in filled:
        # Case A: Explicit consignee keyword markers
        if any(marker in message.lower() for marker in ["consignee is", "consignee:", "recipient is", "recipient:", "send to", "ship to"]):
            c_val = re.sub(r"(?i)^.*?(?:consignee|recipient|send\s*to|ship\s*to)\s*(?:is|:)?\s*", "", message).strip()
            if c_val:
                filled["consignee"] = c_val
                rule_extracted_something = True
        # Case B: Consignee was the active pending question being answered
        elif missing_before and missing_before[0] == "consignee":
            _IS_COMMAND = bool(re.search(r"(?i)^(simulate|order|restart|reset|help|cancel)", message.strip()))
            _IS_PURE_NUM = bool(re.match(r"^[\d\s,]+(?:g|kg|grams?|inr|rs|rupees?|₹)?$", message.strip(), re.IGNORECASE))
            cleaned_consignee = re.sub(r"(?i)^(?:to|name\s*(?:is|:))\s*", "", message).strip()
            if cleaned_consignee and len(cleaned_consignee) >= 3 and not _IS_COMMAND and not _IS_PURE_NUM and not _HAS_CURRENCY:
                filled["consignee"] = cleaned_consignee
                rule_extracted_something = True

    missing_after_rules = [f for f in required_sequence if f not in filled]
    print(f"[CONTROL FLOW] -> rule_extracted_something = {rule_extracted_something}, rule_reply = {bool(rule_reply)}, missing_after_rules = {missing_after_rules}")
    print(f"[STATE AFTER RULES] -> Filled fields: {filled}")

    reply = ""
    # Check if there are still required fields missing that Gemini can extract
    if missing_after_rules and not rule_reply:
        print(f"\n[CONTROL FLOW] -> Invoking GeminiExtractor for remaining missing fields: {missing_after_rules}...")
        # Fallback to GeminiExtractor (STRICT Architecture Guardrail: NO TRANSCRIPT)
        try:
            import os
            import google.generativeai as genai
            api_key = getattr(_get_settings(), "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3.5-flash')
                
                extractor = val_extract.GeminiExtractor(client=model)
                prior_draft = val_shipment.ShipmentDraft(**{k: v for k, v in filled.items() if k in val_shipment.ShipmentDraft.model_fields})
                
                extracted_draft = _val_exec(extractor.extract, previous=prior_draft, text=message, lang=lang)
                print(f"[EXTRACTOR RESULT] -> GeminiExtractor returned draft: {extracted_draft}")
                
                if extracted_draft:
                    if extracted_draft.product_category and extracted_draft.product_category != "unknown" and "product_category" not in filled:
                        filled["product_category"] = extracted_draft.product_category
                    if extracted_draft.quantity and extracted_draft.quantity != -1 and "quantity" not in filled:
                        filled["quantity"] = extracted_draft.quantity
                    if extracted_draft.weight_grams and extracted_draft.weight_grams != -1 and "weight_grams" not in filled:
                        filled["weight_grams"] = extracted_draft.weight_grams
                    if extracted_draft.destination_country and extracted_draft.destination_country != "unknown" and "destination_country" not in filled:
                        filled["destination_country"] = extracted_draft.destination_country
                    # Guard: reject Gemini placeholder/sentinel values
                    _CONSIGNEE_JUNK = {"null", "none", "unknown", "", "consignee_val"}
                    if extracted_draft.consignee and str(extracted_draft.consignee).strip().lower() not in _CONSIGNEE_JUNK and "consignee" not in filled:
                        filled["consignee"] = extracted_draft.consignee
                    if extracted_draft.value_minor and extracted_draft.value_minor > 0 and "value_minor" not in filled:
                        filled["value_minor"] = extracted_draft.value_minor

                reply = _get_next_question(filled)
            else:
                print("[CONTROL FLOW] -> GEMINI_API_KEY not configured!")
                reply = _get_next_question(filled)
        except Exception as e:
            print(f"GeminiExtractor failed: {e}")
            reply = _get_next_question(filled)
    else:
        if not reply:
            reply = _get_next_question(filled)
        print(f"[CONTROL FLOW] -> SKIPPING GeminiExtractor because all required fields already filled or rule_reply exists")

    print(f"[STATE AFTER ALL EXTRACTORS] -> Filled fields: {filled}")
    print(f"===============================================================\n")

    if not reply:
        reply = _get_next_question(filled)

    db_info = {}
    if "product_category" in filled and filled["product_category"] != "unknown":
        try:
            cats = _val_exec(val_db_tools.search_categories, filled["product_category"])
            if cats:
                db_info["category"] = cats[0]
                db_info["category_name"] = cats[0].get("name", filled["product_category"])
                default_hs = cats[0].get("hs6_default", "")
                
                hs_candidates = _val_exec(val_db_tools.lookup_hs_codes, category=filled["product_category"])
                if hs_candidates:
                    db_info["hs_candidates"] = hs_candidates
                    filled["hs_code"] = hs_candidates[0]["hs6"]
                elif default_hs:
                    filled["hs_code"] = default_hs
        except Exception as e:
            print(f"DB category/HS lookup failed: {e}")

    if filled.get("destination_country") and filled["destination_country"] != "unknown" and filled.get("hs_code"):
        try:
            duties = _val_exec(val_db_tools.lookup_duty, country_iso2=filled["destination_country"], hs6=filled["hs_code"])
            if duties:
                db_info["duties"] = duties
        except Exception as e:
            print(f"DB duty lookup failed: {e}")

    if filled.get("destination_country") == "US":
        state_code = filled.get("state_code")
        if not state_code and filled.get("consignee"):
            import re
            us_state_pattern = r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b"
            match = re.search(us_state_pattern, filled["consignee"].upper())
            if match:
                state_code = match.group(1)

        if state_code:
            try:
                state_tax = _val_exec(val_db_tools.get_state_sales_tax, state_iso2=state_code)
                if state_tax:
                    db_info["state_sales_tax"] = state_tax
            except KeyError:
                pass
            except Exception as e:
                print(f"DB state sales tax lookup failed: {e}")

    if filled.get("destination_country") and filled.get("destination_country") != "unknown" and filled.get("weight_grams") and filled["weight_grams"] > 0:
        try:
            q = _val_exec(
                val_db_tools.quote_lane,
                filled["destination_country"],
                filled["weight_grams"]
            )
            if q:
                if q.get('total_inr'):
                    db_info["quote_cost"] = f"₹{q['total_inr']:.2f}"
                if q.get('transit_min_days'):
                    db_info["transit_days"] = f"{q['transit_min_days']}–{q['transit_max_days']} days"
        except Exception as e:
            print(f"DB quote lane failed: {e}")

    step = "collecting"
    
    # 1. Per-field bounds validation (runs immediately per turn)
    try:
        s = val_shipment.Shipment(
            product_category=filled.get("product_category", "unknown"),
            quantity=filled.get("quantity", -1),
            weight_grams=filled.get("weight_grams", -1),
            destination_country=filled.get("destination_country", "unknown"),
            confidence="high"
        )
        _val_exec(val_validate.validate_shipment, s)
    except Exception as e:
        if hasattr(e, "errors"):
            errors = e.errors()
            if errors:
                err = errors[0]
                loc = str(err["loc"][0])
                msg = err["msg"]
                filled.pop(loc, None)
                reply = f"Validation Error: {msg}. Please provide a valid {loc}."
                pending = [f for f in required_sequence if f not in filled]
                return filled, pending, step, reply, db_info

    # 2. Check missing required fields
    missing = [f for f in required_sequence if f not in filled]
    if missing:
        pending = missing
        step = "collecting"
        return filled, pending, step, reply, db_info

    # 3. All 6 fields collected: run validate_document_rules once
    try:
        doc_data = _val_exec(
            val_document.build_document_data,
            shipment=s,
            form_type="PBE_IV",
            consignee=filled.get("consignee"),
            value_minor=filled.get("value_minor"),
            iec="0123456789",
        )
        rule_result = _val_exec(val_validate.validate_document_rules, doc_data)
        if rule_result.errors:
            err_msg = rule_result.errors[0]
            # Implicated field re-opening (e.g. category restriction/prohibition)
            if "category" in err_msg.lower() or "prohibited" in err_msg.lower() or "woodware" in err_msg.lower() or "restricted" in err_msg.lower():
                filled.pop("product_category", None)
                filled.pop("hs_code", None)
            elif "country" in err_msg.lower() or "destination" in err_msg.lower():
                filled.pop("destination_country", None)
            else:
                filled.pop("product_category", None)

            pending = [f for f in required_sequence if f not in filled]
            step = "collecting"
            reply = f"Compliance Rule Error: {err_msg}. Please update your selection: {FIELD_QUESTIONS.get(pending[0], 'Please provide valid input')}"
            return filled, pending, step, reply, db_info

        # Both missing_required == [] AND validate_document_rules passed clean
        step = "ready"
        pending = []
        reply = "All details collected! Please click 'Simulate Completing Order'"
    except Exception as e:
        import traceback
        print(f"build_document_data or validate_document_rules failed: {e}")
        traceback.print_exc()
        pending = [f for f in required_sequence if f not in filled]
        step = "collecting"

    return filled, pending, step, reply, db_info

async def _get_conv_state(redis, conv_id: str) -> dict[str, str]:
    key = f"chat_session:{conv_id}"
    raw = await redis.hgetall(key)
    if not raw:
        raise HTTPException(status_code=404, detail="Conversation not found or expired")
    return {k.decode('utf-8'): v.decode('utf-8') for k, v in raw.items()}

async def _save_conv_state(redis, conv_id: str, state: ChatResponse):
    key = f"chat_session:{conv_id}"
    flat = {
        "user_id": state.user_id,
        "language": state.language,
        "current_step": state.current_step,
        "filled_fields": json.dumps(state.filled_fields),
        "pending_fields": json.dumps(state.pending_fields),
        "history": json.dumps(state.history),
        "db_info": json.dumps(state.db_info)
    }
    await redis.hset(key, mapping=flat)
    ttl_seconds = _get_settings().LLM_CONVERSATION_TTL_HOURS * 3600
    await redis.expire(key, ttl_seconds)

def _hydrate_response(conv_id: str, raw: dict[str, str]) -> dict[str, object]:
    def _json_load(key: str) -> object:
        val = raw.get(key, "")
        if not val:
            return {} if key in ("filled_fields", "db_info") else [] if key in ("pending_fields", "history") else val
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {} if key in ("filled_fields", "db_info") else []
    
    return {
        "conversation_id": conv_id,
        "user_id": raw.get("user_id", ""),
        "language": raw.get("language", "en"),
        "current_step": raw.get("current_step", "collecting"),
        "filled_fields": _json_load("filled_fields"),
        "pending_fields": _json_load("pending_fields"),
        "history": _json_load("history"),
        "db_info": _json_load("db_info"),
    }

@router.post(
    "/chat",
    status_code=201,
    response_model=ChatResponse,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def chat(request: Request, body: ChatRequest) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    redis = get_redis()

    if body.conversation_id:
        raw = await _get_conv_state(redis, body.conversation_id)
        if raw.get("user_id", "") != user_id:
            raise HTTPException(status_code=403, detail="Not your conversation")
        history = json.loads(raw.get("history", "[]"))
        history.append({"role": "user", "content": body.message})
        existing_filled = json.loads(raw.get("filled_fields", "{}"))
        filled, pending, step, reply, db_info = _run_extraction(body.message, body.language, existing_filled, history)
        history.append({"role": "assistant", "content": reply})
        state = ChatResponse(
            conversation_id=body.conversation_id,
            user_id=user_id,
            language=body.language,
            current_step=step,
            filled_fields=filled,
            pending_fields=pending,
            history=history,
            db_info=db_info
        )
        await _save_conv_state(redis, body.conversation_id, state)
        return state.model_dump()
    else:
        conv_id = uuid.uuid4().hex
        history = [{"role": "user", "content": body.message}]
        filled, pending, step, reply, db_info = _run_extraction(body.message, body.language, {}, history)
        history.append({"role": "assistant", "content": reply})
        state = ChatResponse(
            conversation_id=conv_id,
            user_id=user_id,
            language=body.language,
            current_step=step,
            filled_fields=filled,
            pending_fields=pending,
            history=history,
            db_info=db_info
        )
        await _save_conv_state(redis, conv_id, state)
        return state.model_dump()

@router.get(
    "/session/{conversation_id}",
    response_model=ChatResponse,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def get_session(request: Request, conversation_id: str) -> dict[str, object]:
    redis = get_redis()
    raw = await _get_conv_state(redis, conversation_id)
    if raw.get("user_id", "") != str(request.state.user["user_id"]):
        raise HTTPException(status_code=403, detail="Not your conversation")
    return _hydrate_response(conversation_id, raw)
