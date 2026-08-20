"""GET /guidance/signup — explicit Hindi toggle, per-field Sarvam hints.

Source: validation-engine/data/02-dnk-documents/onboarding/onboarding-guide.md
§1–§2 (8 steps), complete-flow §5A/5C. All mocked, never live-claimed.
Hinglish simple_words are class-5 level (short, spoken Hindi).
"""

from __future__ import annotations

from typing import Final

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.sarvam import tts_url_for_field

router = APIRouter(prefix="/guidance", tags=["guidance"])

# ---------------------------------------------------------------------------
# Field registry — upfront order PAN→IEC→AD→ICEGATE→bank, then GSTIN/Udyam/RCMC “बाद में”
# Source: onboarding-guide.md §1–§2, complete-flow §5C minimal set
# ---------------------------------------------------------------------------

_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    {"pan", "iec", "ad_code", "icegate", "bank", "gstin", "udyam", "rcmc"}
)

# Canonical ordering for upfront vs skippable grouping
_UPFRONT_ORDER: Final[list[str]] = ["pan", "iec", "ad_code", "icegate", "bank"]
_SKIPPABLE_FIELDS: Final[frozenset[str]] = frozenset({"gstin", "udyam", "rcmc"})

# Normalise aliases (user typos / alternate spellings) before Levenshtein
_ALIASES: Final[dict[str, str]] = {
    "adcode": "ad_code",
    "ad-code": "ad_code",
    "ad": "ad_code",
    "pan_card": "pan",
    "iec_code": "iec",
    "iecc": "iec",
    "icgate": "icegate",
    "ice_gate": "icegate",
    "bank_account": "bank",
    "bankaccount": "bank",
    "gst": "gstin",
    "gstn": "gstin",
    "udyam_reg": "udyam",
    "rcms": "rcmc",
    "rcmc_code": "rcmc",
}


class FieldMeta(BaseModel):
    field: str
    simple_words: str
    hint: str
    required: bool
    skippable: bool
    source: str = "onboarding-guide.md §2"


# Hinglish — class-5 spoken, sourced from onboarding-guide.md §2 per field
_FIELD_META: Final[dict[str, FieldMeta]] = {
    "pan": FieldMeta(
        field="pan",
        simple_words="PAN कार्ड — 10 अक्षर (ABCDE1234F जैसा)",
        hint="PAN से IEC बनता है — पहले यही लगता है [guide §2 Step1]",
        required=True,
        skippable=False,
    ),
    "iec": FieldMeta(
        field="iec",
        simple_words="बाहर सामान भेजने का लाइसेंस (IEC) 10 अंक",
        hint="DGFT से बनता है, ₹500 फीस, OTP से तुरंत [guide §2 Step1]",
        required=True,
        skippable=False,
    ),
    "ad_code": FieldMeta(
        field="ad_code",
        simple_words="बैंक का 14 नंबर कोड बगल-बगल",
        hint="बैंक देता है, ICEGATE पर रजिस्टर होता है — incentive के लिए जरूरी [guide §2 Step3]",
        required=True,
        skippable=False,
    ),
    "icegate": FieldMeta(
        field="icegate",
        simple_words="कस्टम का ऑनलाइन खाता",
        hint="icegate.gov.in पर बनता है, बैंक खाता DNK site code से लिंक [guide §2 Step4]",
        required=True,
        skippable=False,
    ),
    "bank": FieldMeta(
        field="bank",
        simple_words="₹1 भेजकर खाता चेक",
        hint="फर्म के नाम का खाता — IEC और refund यहीं आता है [guide §2 Step2]",
        required=True,
        skippable=False,
    ),
    "gstin": FieldMeta(
        field="gstin",
        simple_words="GST नंबर — बाद में",
        hint="बाद में — अभी skip कर सकते हैं [guide §4 honesty: GSTIN not mandatory]",
        required=False,
        skippable=True,
    ),
    "udyam": FieldMeta(
        field="udyam",
        simple_words="छोटा उद्योग सर्टिफिकेट — बाद में",
        hint="बाद में — सिर्फ सरकारी योजना लेनी हो तो [guide §2 Step7]",
        required=False,
        skippable=True,
    ),
    "rcmc": FieldMeta(
        field="rcmc",
        simple_words="EPCH सदस्यता (RCMC) — बाद में",
        hint="बाद में — हस्तशिल्प निर्यात योजना के लिए [guide §2 Step7]",
        required=False,
        skippable=True,
    ),
}

# English slug fallback when hindi_help=false
_ENGLISH_FALLBACK: Final[dict[str, str]] = {
    "pan": "PAN card — 10 characters",
    "iec": "export licence (IEC) — 10 digits",
    "ad_code": "bank AD Code — 14 digits",
    "icegate": "customs online account (ICEGATE)",
    "bank": "bank account verification (Rs 1 check)",
    "gstin": "GSTIN — later (skippable)",
    "udyam": "Udyam certificate — later (skippable)",
    "rcmc": "RCMC membership — later (skippable)",
}


def _normalize_field(raw: str) -> str:
    s = raw.strip().lower().replace(" ", "_").replace("-", "_")
    # collapse double underscores
    while "__" in s:
        s = s.replace("__", "_")
    s = s.strip("_")
    if s in _ALIASES:
        return _ALIASES[s]
    # try alias without underscores
    compact = s.replace("_", "")
    if compact in _ALIASES:
        return _ALIASES[compact]
    if s in _ALLOWED_FIELDS:
        return s
    if compact in _ALLOWED_FIELDS:
        return compact
    return s


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * lb
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[lb]


def resolve_field(raw: str) -> str | None:
    """Typo-tolerant field resolution — alias → exact → Levenshtein ≤2."""
    norm = _normalize_field(raw)
    if norm in _ALLOWED_FIELDS:
        return norm
    # Levenshtein fallback (threshold 2)
    best: str | None = None
    best_dist = 999
    for cand in _ALLOWED_FIELDS:
        d = _levenshtein(norm, cand)
        if d < best_dist:
            best_dist = d
            best = cand
    if best is not None and best_dist <= 2:
        return best
    # also try without underscores for iec-like typos
    for cand in _ALLOWED_FIELDS:
        d = _levenshtein(norm.replace("_", ""), cand.replace("_", ""))
        if d < best_dist:
            best_dist = d
            best = cand
    if best is not None and best_dist <= 2:
        return best
    return None


class GuidanceResponse(BaseModel):
    field: str
    simple_words: str
    hint: str
    side_by_side: None = None
    tts_url: str | None = None
    required: bool
    skippable: bool
    verification_mode: str = "mock"
    mocked: bool = True
    hindi_help: bool
    source: str = "onboarding-guide.md §2"
    upfront_order: list[str] = _UPFRONT_ORDER


@router.get("/signup")
async def get_signup_guidance(
    field: str = Query(..., description="one of pan|iec|ad_code|icegate|bank|gstin|udyam|rcmc (typo-tolerant)"),
    hindi_help: bool = Query(..., description="explicit toggle: true=Hindi, false=English (no auto-detect)"),
) -> GuidanceResponse:
    resolved = resolve_field(field)
    if resolved is None:
        # still return 200 with best-effort — surface closest or pan
        resolved = "pan"
    meta = _FIELD_META[resolved]
    if hindi_help:
        # Every field gets a Sarvam mock tts_url when Hindi is on
        tts = tts_url_for_field(resolved, meta.simple_words)
        return GuidanceResponse(
            field=resolved,
            simple_words=meta.simple_words,
            hint=meta.hint,
            side_by_side=None,
            tts_url=tts,
            required=meta.required,
            skippable=meta.skippable,
            verification_mode="mock",
            mocked=True,
            hindi_help=True,
            source=meta.source,
            upfront_order=_UPFRONT_ORDER,
        )
    else:
        eng = _ENGLISH_FALLBACK.get(resolved, resolved)
        return GuidanceResponse(
            field=resolved,
            simple_words=eng,
            hint=eng,
            side_by_side=None,
            tts_url=None,
            required=meta.required,
            skippable=meta.skippable,
            verification_mode="mock",
            mocked=True,
            hindi_help=False,
            source=meta.source,
            upfront_order=_UPFRONT_ORDER,
        )
