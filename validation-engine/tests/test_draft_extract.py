"""Draft extractors — the multi-turn accumulation contract (Wave 1).

Pins: RuleDraftExtractor's six-field extraction + carry-forward + category
re-raise; _extract_consignee / _extract_value_minor; and GeminiDraftExtractor's
transcript discipline (initial content only, never stored, never re-prompted).
"""

from __future__ import annotations

import json

import pytest

from app.schemas.shipment import (
    CONSIGNEE_UNSTATED,
    VALUE_UNSTATED,
    ShipmentDraft,
)
from app.services.extract import (
    CategoryUnknownError,
    GeminiDraftExtractor,
    RuleDraftExtractor,
    _extract_consignee,
    _extract_value_minor,
)


def test_rule_draft_full_utterance() -> None:
    draft = RuleDraftExtractor().extract_from_text(
        "12 jute bags to Germany, 500 grams, 15000 rupees", "hi"
    )
    assert draft.product_category == "jute-products"
    assert draft.quantity == 12
    assert draft.weight_grams == 500
    assert draft.destination_country == "DE"
    assert draft.consignee == CONSIGNEE_UNSTATED
    assert draft.value_minor == 1500000
    assert draft.confidence == "high"


def test_rule_draft_hindi_utterance_with_devanagari_gram() -> None:
    """Devanagari conjuncts (ग्राम) must tokenize as ONE weight-unit token."""
    draft = RuleDraftExtractor().extract_from_text(
        "12 जूट बैग जर्मनी भेजने हैं 500 ग्राम 15000 रुपये", "hi"
    )
    assert draft.product_category == "jute-products"
    assert draft.weight_grams == 500
    assert draft.value_minor == 1500000
    assert draft.destination_country == "DE"


def test_rule_draft_consignee_turn_does_not_steal_quantity() -> None:
    """An address with digits ('जॉन डो, 123 बर्लिन…') answers the consignee
    question — the '123' must NOT overwrite the already-stated quantity."""
    previous = ShipmentDraft(
        product_category="jute-products",
        quantity=12,
        weight_grams=500,
        destination_country="DE",
        value_minor=1500000,
        confidence="high",
    )
    draft = RuleDraftExtractor().extract_from_text(
        "जॉन डो, 123 बर्लिन स्ट्रीट को भेजना है", "hi", previous=previous
    )
    assert draft.consignee == "जॉन डो, 123 बर्लिन स्ट्रीट"
    assert draft.quantity == 12  # NOT 123
    assert draft.weight_grams == 500
    assert draft.value_minor == 1500000
    assert draft.destination_country == "DE"


def test_rule_draft_expected_consignee_takes_plain_address() -> None:
    """Case B: answering the consignee question with a plain name+address
    (no marker) uses the WHOLE utterance as the consignee — '500' in the
    address must NOT become the quantity."""
    previous = ShipmentDraft(
        product_category="jute-products",
        quantity=12,
        weight_grams=500,
        destination_country="US",
        value_minor=1500000,
        confidence="high",
    )
    draft = RuleDraftExtractor().extract_from_text(
        "जॉन डो, 500 मैडिसन एवेन्यू, न्यूयॉर्क", "hi", previous=previous, expected="consignee"
    )
    assert draft.consignee == "जॉन डो, 500 मैडिसन एवेन्यू, न्यूयॉर्क"
    assert draft.quantity == 12  # NOT 500
    assert draft.weight_grams == 500


def test_rule_draft_expected_consignee_rejects_pure_number() -> None:
    """A bare number answer is never a consignee."""
    previous = ShipmentDraft(product_category="jute-products", quantity=12)
    draft = RuleDraftExtractor().extract_from_text("500", "en", previous=previous, expected="consignee")
    assert draft.consignee == CONSIGNEE_UNSTATED
    assert draft.quantity == 500  # re-parsed as a quantity answer


def test_rule_draft_carry_forward_category() -> None:
    previous = ShipmentDraft(product_category="embroidered-home-textiles")
    draft = RuleDraftExtractor().extract_from_text("500 grams", "hi", previous=previous)
    assert draft.product_category == "embroidered-home-textiles"
    assert draft.weight_grams == 500


def test_rule_draft_carry_forward_keeps_previous_when_sentinel() -> None:
    previous = ShipmentDraft(
        product_category="jute-products",
        quantity=12,
        weight_grams=500,
        destination_country="DE",
    )
    draft = RuleDraftExtractor().extract_from_text("to germany", "hi", previous=previous)
    assert draft.destination_country == "DE"
    assert draft.quantity == 12
    assert draft.weight_grams == 500


def test_rule_draft_category_unknown_reraises_without_previous() -> None:
    with pytest.raises(CategoryUnknownError) as exc_info:
        RuleDraftExtractor().extract_from_text("five hundred grams to america", "en")
    # The partial draft preserves the OTHER extracted fields (weight/country)
    # so the caller does not lose the turn's progress when it re-asks.
    partial = exc_info.value.partial_draft
    assert partial is not None
    assert partial.weight_grams == 500
    assert partial.destination_country == "US"
    assert partial.product_category is None


def test_rule_draft_category_unknown_carried_when_previous_has_it() -> None:
    previous = ShipmentDraft(product_category="small-brass-metalware", quantity=3)
    draft = RuleDraftExtractor().extract_from_text(
        "250 grams", "en", previous=previous
    )
    assert draft.product_category == "small-brass-metalware"
    assert draft.quantity == 3


def test_extract_consignee_hindi_preposition() -> None:
    assert _extract_consignee("जॉन को भेजें, बर्लिन") == "जॉन"
    assert _extract_consignee("मेरी को भेजना है, न्यूयॉर्क") == "मेरी"


def test_extract_consignee_english_markers() -> None:
    assert _extract_consignee("send to John Doe, 123 Main St") == "John Doe, 123 Main St"
    assert _extract_consignee("ship to the consignee Acme Exports") == "consignee Acme Exports"
    assert _extract_consignee("no marker here") == CONSIGNEE_UNSTATED


def test_extract_value_minor() -> None:
    assert _extract_value_minor("₹15000") == 1500000
    assert _extract_value_minor("15000 रुपये") == 1500000
    assert _extract_value_minor("15000 rupees") == 1500000
    assert _extract_value_minor("१५००० रुपये") == 1500000
    assert _extract_value_minor("$200") == 20000
    assert _extract_value_minor("no currency here") == VALUE_UNSTATED


def test_rule_draft_time_unit_not_quantity() -> None:
    """'चार सौ ग्राम और उसके दो घंटे का' — the 'दो घंटे' run is a time
    reference, never a quantity re-statement; the weight is still 400 g."""
    previous = ShipmentDraft(
        product_category="jute-products",
        quantity=1,
        destination_country="US",
    )
    draft = RuleDraftExtractor().extract_from_text(
        "चार सौ ग्राम और उसके दो घंटे का", "hi", previous=previous, expected="weight_grams"
    )
    assert draft.weight_grams == 400, f"weight_grams must be 400, got {draft.weight_grams}"
    assert draft.quantity == 1, f"time unit run must not steal quantity: got {draft.quantity}"


def test_rule_draft_time_words_never_quantity() -> None:
    """'दो बजे' / 'दो दिन' / 'दो मिनट' are clock/calendar references — the
    number run immediately before a time unit is never a quantity."""
    previous = ShipmentDraft(product_category="jute-products", quantity=1)
    for phrase in ("दो बजे", "दो दिन", "दो मिनट"):
        draft = RuleDraftExtractor().extract_from_text(
            phrase, "hi", previous=previous
        )
        assert draft.quantity == 1, (
            f"'{phrase}' must not set quantity: got {draft.quantity}"
        )


def test_rule_draft_price_marker_value_not_quantity() -> None:
    """'दो हजार पे' declares the value (₹2000) — the number run must NOT be
    re-read as the quantity."""
    previous = ShipmentDraft(product_category="jute-products", quantity=1)
    draft = RuleDraftExtractor().extract_from_text(
        "दो हजार पे", "hi", previous=previous, expected="value_minor"
    )
    assert draft.value_minor == 200000, f"value_minor must be ₹2000: got {draft.value_minor}"
    assert draft.quantity == 1, f"quantity must not steal value: got {draft.quantity}"


def test_rule_draft_expected_value_hint_routes_number_to_value() -> None:
    """When the pending question is value (expected='value_minor'), a bare
    number run is the declared value — never a quantity re-statement."""
    previous = ShipmentDraft(product_category="jute-products", quantity=1)
    draft = RuleDraftExtractor().extract_from_text(
        "दो हजार", "hi", previous=previous, expected="value_minor"
    )
    assert draft.value_minor == 200000, f"value_minor must be ₹2000: got {draft.value_minor}"
    assert draft.quantity == 1, f"quantity must not steal value: got {draft.quantity}"


def test_rule_draft_consignee_recipient_ko() -> None:
    """'शिखा को अमेरिका में भेजना है' — no contiguous 'को भेजना है' marker
    exists, but the pre-को name is the consignee and अमेरिका still resolves."""
    previous = ShipmentDraft(product_category="embroidered-home-textiles")
    draft = RuleDraftExtractor().extract_from_text(
        "शिखा को अमेरिका में भेजना है", "hi", previous=previous
    )
    assert draft.consignee == "शिखा", f"consignee must be शिखा: got {draft.consignee!r}"
    assert draft.destination_country == "US", (
        f"destination must be US: got {draft.destination_country}"
    )


def test_rule_draft_inline_currency_not_quantity() -> None:
    """'माल ₹15000 का' declares the value mid-sentence — the digit run next to
    the ₹ signal must never be re-read as the quantity."""
    previous = ShipmentDraft(product_category="jute-products", quantity=1)
    draft = RuleDraftExtractor().extract_from_text(
        "माल ₹15000 का", "hi", previous=previous
    )
    assert draft.value_minor == 1500000, f"value_minor must be ₹15000: got {draft.value_minor}"
    assert draft.quantity == 1, f"quantity must not steal value: got {draft.quantity}"


def test_extract_consignee_recipient_ko() -> None:
    """The recipient-को rule captures the pre-को name even when the send verb
    is not adjacent to the को."""
    assert _extract_consignee("शिखा को अमेरिका में भेजना है") == "शिखा"
    assert _extract_consignee("राहुल को भेजो") == "राहुल"


# ---------------------------------------------------------------------------
# Mocks for the GeminiDraftExtractor tests (NEVER a real client / API / key).
# ---------------------------------------------------------------------------


class _MockPart:
    def __init__(self, text: str, thought: bool = False) -> None:
        self.text = text
        self.thought = thought


class _MockResponse:
    def __init__(self, parts: list[_MockPart]) -> None:
        self.parts = parts


class _MockClient:
    def __init__(self, responses: list[_MockResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[dict, list[dict]]] = []

    def generate_content(self, config: dict, contents: list[dict]) -> _MockResponse:
        self.calls.append((config, contents))
        return self.responses.pop(0)


_VALID_DRAFT_PAYLOAD = {
    "product_category": "jute-products",
    "quantity": 5,
    "weight_grams": 500,
    "destination_country": "US",
    "consignee": "John Doe",
    "value_minor": 1500000,
    "confidence": "high",
}

_SCHEMA_INVALID_DRAFT_PAYLOAD = {
    "product_category": "not-a-real-slug",  # fails the Literal -> reprompt
    "quantity": 3,
    "weight_grams": 200,
    "destination_country": "US",
    "consignee": "Jane Doe",
    "value_minor": 10000,
    "confidence": "medium",
}


def test_gemini_draft_transcript_only_in_first_call() -> None:
    """The transcript is the FIRST call's content; the re-prompt carries only
    the schema + prior draft (raw_transcript stripped) and the produced draft
    never stores it."""
    client = _MockClient(
        [
            _MockResponse([_MockPart(json.dumps(_VALID_DRAFT_PAYLOAD))]),
        ]
    )
    previous = ShipmentDraft(
        product_category="embroidered-home-textiles",
        quantity=8,
        weight_grams=400,
        destination_country="US",
        raw_transcript="SECRET TRANSCRIPT: eight cushion covers, four hundred grams",
    )

    draft = GeminiDraftExtractor(client).extract(
        "six jute bags to america, five hundred grams", previous, "en"
    )

    assert draft.product_category == "jute-products"
    assert draft.quantity == 5
    assert draft.raw_transcript is None

    assert len(client.calls) == 1
    config, contents = client.calls[0]
    assert config["response_schema"] == _clean_schema(ShipmentDraft.model_json_schema())
    assert config["thinking_config"] == {"thinking_budget": 0}
    first_blob = json.dumps(contents, ensure_ascii=False)
    assert "six jute bags to america, five hundred grams" in first_blob
    assert "SECRET TRANSCRIPT" not in first_blob  # prior draft never leaked


def test_gemini_draft_reprompt_excludes_transcript_and_raw_transcript() -> None:
    client = _MockClient(
        [
            _MockResponse([_MockPart(json.dumps(_SCHEMA_INVALID_DRAFT_PAYLOAD))]),
            _MockResponse([_MockPart(json.dumps(_VALID_DRAFT_PAYLOAD))]),
        ]
    )
    previous = ShipmentDraft(
        product_category="embroidered-home-textiles",
        quantity=8,
        weight_grams=400,
        destination_country="US",
        raw_transcript="SECRET TRANSCRIPT: eight cushion covers",
    )

    draft = GeminiDraftExtractor(client).extract(
        "six jute bags to america", previous, "en"
    )

    assert draft.product_category == "jute-products"
    assert draft.raw_transcript is None
    assert len(client.calls) == 2

    first_blob = json.dumps(client.calls[0][1], ensure_ascii=False)
    assert "six jute bags to america" in first_blob  # initial content only

    reprompt_blob = json.dumps(client.calls[1][1], ensure_ascii=False)
    assert "six jute bags to america" not in reprompt_blob  # no transcript
    assert "SECRET TRANSCRIPT" not in reprompt_blob  # no raw_transcript
    assert "prior_draft" in reprompt_blob
    assert "embroidered-home-textiles" in reprompt_blob  # prior draft values present


def test_gemini_draft_schema_invalid_then_reprompt_valid() -> None:
    client = _MockClient(
        [
            _MockResponse([_MockPart(json.dumps(_SCHEMA_INVALID_DRAFT_PAYLOAD))]),
            _MockResponse([_MockPart(json.dumps(_VALID_DRAFT_PAYLOAD))]),
        ]
    )
    draft = GeminiDraftExtractor(client).extract("text", None, "hi")
    assert draft.quantity == 5
    assert len(client.calls) == 2


def test_gemini_draft_exhausts_reprompts() -> None:
    client = _MockClient(
        [
            _MockResponse([_MockPart(json.dumps(_SCHEMA_INVALID_DRAFT_PAYLOAD))]),
            _MockResponse([_MockPart(json.dumps(_SCHEMA_INVALID_DRAFT_PAYLOAD))]),
            _MockResponse([_MockPart(json.dumps(_SCHEMA_INVALID_DRAFT_PAYLOAD))]),
            _MockResponse([_MockPart(json.dumps(_SCHEMA_INVALID_DRAFT_PAYLOAD))]),
        ]
    )
    with pytest.raises(ValueError):
        GeminiDraftExtractor(client).extract("text", None, "hi")


def test_gemini_draft_no_key_raises_runtime_error(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY not set"):
        GeminiDraftExtractor().extract("text", None, "hi")


class _RealSdkModel:
    """A fake genai model that enforces the REAL SDK's content contract.

    The real ``google.generativeai`` SDK rejects a ``contents`` list of bare
    dicts (``KeyError: Unable to determine the intended type of the dict`` —
    it expects ``Content``/``Part`` objects or a plain string).  The
    ``_GenaiModelAdapter`` must translate the mock-shaped ``(config, contents)``
    call into a real ``generate_content(prompt_text, generation_config=...)``
    call — this test pins that boundary so the live Gemini path actually works.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[object, dict]] = []
        self._payload = json.dumps(_VALID_DRAFT_PAYLOAD)

    def generate_content(self, contents: object, **kwargs: object) -> _MockResponse:
        if isinstance(contents, list) and any(isinstance(c, dict) for c in contents):
            raise KeyError(
                "Unable to determine the intended type of the `dict`. For "
                "`Content`, a 'parts' key is expected."
            )
        self.calls.append((contents, kwargs))
        return _MockResponse([_MockPart(self._payload)])


def test_gemini_adapter_translates_to_real_sdk_call_shape() -> None:
    from app.services.extract import _GenaiModelAdapter

    sdk = _RealSdkModel()
    adapter = _GenaiModelAdapter(sdk)
    schema = _clean_schema(ShipmentDraft.model_json_schema())

    draft = GeminiDraftExtractor(adapter).extract(
        "six jute bags to america, five hundred grams", None, "en"
    )

    assert draft.product_category == "jute-products"
    assert draft.quantity == 5
    assert len(sdk.calls) == 1
    prompt, kwargs = sdk.calls[0]
    assert isinstance(prompt, str), f"adapter must pass a str prompt, got {type(prompt)}"
    assert "six jute bags to america" in prompt
    assert kwargs["generation_config"]["response_mime_type"] == "application/json"
    assert kwargs["generation_config"]["response_schema"] == schema
    assert "raw_transcript" not in str(prompt)


class _ToolCallingModel:
    """Fake real-SDK model that first emits a search_categories function call
    (as a real protos.Part, like the SDK), then (after the adapter feeds
    results back) returns the draft JSON."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, dict]] = []
        self.round = 0

    def generate_content(self, contents: object, **kwargs: object) -> _MockResponse:
        from google.generativeai import protos

        self.calls.append((contents, kwargs))
        tools = kwargs.get("tools")
        assert tools, "adapter must pass tools for function calling"
        if self.round == 0:
            self.round += 1
            return _MockResponse(
                [
                    protos.Part(
                        function_call=protos.FunctionCall(
                            name="search_categories", args={"query": "कपड़ा"}
                        )
                    )
                ]
            )
        self.round += 1
        serialized = str(contents)
        assert "block-printed-textiles" in serialized, (
            f"tool result must reach the model: {serialized[:300]}"
        )
        payload = dict(_VALID_DRAFT_PAYLOAD, product_category="block-printed-textiles")
        return _MockResponse([_MockPart(json.dumps(payload))])


def test_gemini_adapter_runs_search_categories_tool_loop() -> None:
    """When the model emits a function call, the adapter must execute the tool
    and feed results back until a schema-valid draft is produced — the live
    'मुझे कपड़ा भी यू एस पी ओ' path depends on this."""
    from app.services.extract import _GenaiModelAdapter

    sdk = _ToolCallingModel()
    tool_results: list[dict] = []

    def fake_search(query: str) -> list[dict]:
        tool_results.append({"query": query})
        return [
            {"slug": "block-printed-textiles", "name": "Block-Printed Textiles"},
            {"slug": "handloom-scarves-stoles", "name": "Handloom Scarves & Stoles"},
        ]

    adapter = _GenaiModelAdapter(sdk, tools=[("search_categories", fake_search)])
    draft = GeminiDraftExtractor(adapter).extract("मुझे कपड़ा भी यू एस पी ओ", None, "hi")

    assert draft.product_category == "block-printed-textiles"
    assert tool_results == [{"query": "कपड़ा"}], f"tool must run: {tool_results}"
    assert sdk.round == 2  # function-call round + final round


def test_gemini_schema_is_sdk_compatible() -> None:
    """The response_schema must be accepted by the real SDK's Schema proto.

    Pydantic v2 encodes ``X | None`` as ``anyOf: [{...}, {"type": "null"}]``,
    which the google.generativeai SDK rejects (``ValueError: Unknown field for
    Schema: anyOf``).  ``_clean_schema`` must rewrite null-anyOf branches into
    ``nullable: true`` so the live path works.
    """
    from app.services.extract import _clean_schema as prod_clean_schema

    schema = prod_clean_schema(ShipmentDraft.model_json_schema())
    blob = json.dumps(schema, ensure_ascii=False)
    assert "anyOf" not in blob, f"SDK rejects anyOf: {blob[:200]}"
    category = schema["properties"]["product_category"]
    assert category.get("nullable") is True
    assert category["type"] == "string"
    assert "block-printed-textiles" in category["enum"]
    assert schema["properties"]["quantity"]["type"] == "integer"


def test_gemini_draft_adapter_live_sdk_compatible() -> None:
    """The cleaned schema must carry the fields the SDK converts at request
    time — the SDK kept this dict verbatim and exploded on ``anyOf`` when the
    live path ran (ValueError: Unknown field for Schema: anyOf)."""
    from google.generativeai.types import GenerationConfig

    from app.services.extract import _clean_schema as prod_clean_schema

    schema = prod_clean_schema(ShipmentDraft.model_json_schema())
    config = GenerationConfig(
        response_mime_type="application/json", response_schema=schema
    )
    stored = config.response_schema
    assert isinstance(stored, dict)
    assert "anyOf" not in json.dumps(stored, ensure_ascii=False)
    assert stored["properties"]["product_category"]["nullable"] is True


def test_gemini_draft_country_normalized_to_iso2() -> None:
    """Gemini may answer a country as a free-form name ('United States',
    'अमेरिका', 'भारत'); the parse boundary must normalize it to the ISO2 the
    validation contract requires (else document_ready never flips)."""
    client = _MockClient(
        [
            _MockResponse(
                [
                    _MockPart(
                        json.dumps(
                            {
                                **_VALID_DRAFT_PAYLOAD,
                                "destination_country": "United States",
                            }
                        )
                    )
                ]
            ),
        ]
    )
    draft = GeminiDraftExtractor(client).extract("to america", None, "en")
    assert draft.destination_country == "US", (
        f"free-form country must normalize to ISO2: {draft.destination_country!r}"
    )


def test_gemini_draft_already_iso2_untouched() -> None:
    client = _MockClient(
        [
            _MockResponse([_MockPart(json.dumps(_VALID_DRAFT_PAYLOAD))]),
        ]
    )
    draft = GeminiDraftExtractor(client).extract("to america", None, "en")
    assert draft.destination_country == "US"


def _clean_schema(schema: dict) -> dict:
    """Test-local mirror of the production ``_clean_schema`` (extract.py).

    Must stay behavior-identical so the transcript-discipline tests can assert
    the exact ``response_schema`` the extractor sends: drop title/default,
    rewrite Pydantic ``anyOf`` null-branches into SDK ``nullable: true``.
    """
    cleaned: dict[str, object] = {}
    for key, value in schema.items():
        if key in ("title", "default"):
            continue
        if key == "anyOf" and isinstance(value, list):
            non_null = [item for item in value if isinstance(item, dict) and item.get("type") != "null"]
            if len(non_null) == 1 and isinstance(non_null[0], dict):
                cleaned.update({k: _clean_schema(v) if isinstance(v, dict) else v for k, v in non_null[0].items() if k not in ("title", "default")})
                cleaned["nullable"] = True
                continue
        cleaned[key] = _clean_schema(value) if isinstance(value, dict) else value
    return cleaned


class _MultiToolCallingModel:
    """Fake SDK model that emits a lookup_duty call (named args, not query),
    then asserts the adapter built per-tool declarations (not the hardcoded
    single-query schema) before returning a valid draft."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, dict]] = []
        self.round = 0
        self.declarations: list[object] = []

    def generate_content(self, contents: object, **kwargs: object) -> _MockResponse:
        from google.generativeai import protos

        self.calls.append((contents, kwargs))
        tools = kwargs.get("tools")
        assert tools, "adapter must pass tools for function calling"
        declaration_list = tools[0].function_declarations
        self.declarations = list(declaration_list)
        by_name = {d.name: d for d in declaration_list}
        # Per-tool declarations must NOT all carry the hardcoded query:string.
        assert set(by_name) == {"lookup_duty", "search_categories"}, (
            f"registry must expose the curated tools: {sorted(by_name)}"
        )
        duty = by_name["lookup_duty"]
        assert duty.parameters.properties.keys() >= {"country_iso2", "hs6"}, (
            f"lookup_duty schema must be precise, got {list(duty.parameters.properties)}"
        )
        assert "country_iso2" in duty.parameters.required
        if self.round == 0:
            self.round += 1
            return _MockResponse(
                [
                    protos.Part(
                        function_call=protos.FunctionCall(
                            name="lookup_duty",
                            args={"country_iso2": "US", "hs6": "5310"},
                        )
                    )
                ]
            )
        self.round += 1
        payload = dict(_VALID_DRAFT_PAYLOAD, product_category="jute-products")
        return _MockResponse([_MockPart(json.dumps(payload))])


def test_gemini_adapter_builds_per_tool_declarations_and_named_args() -> None:
    """The MCP registry must flow into the SDK function declarations verbatim:
    precise per-tool parameter schemas and named-argument dispatch
    (executor(**call.args)), not the legacy single-query:string schema."""
    from app.services.extract import _GenaiModelAdapter
    from app.services.mcp_tools import get_mcp_tools

    sdk = _MultiToolCallingModel()
    tool_results: list[dict] = []

    def fake_lookup_duty(country_iso2: str, hs6: str | None = None) -> list[dict]:
        tool_results.append({"country_iso2": country_iso2, "hs6": hs6})
        return [{"country_iso2": "US", "hs6": "5310", "rate_type": "MFN", "rate_pct": 10.0}]

    from app.services.mcp_tools import MCPTool

    search_tool = next(t for t in get_mcp_tools() if t.name == "search_categories")
    tools = [
        search_tool,
        MCPTool(
            name="lookup_duty",
            description="Look up duty.",
            parameters={
                "type": "object",
                "properties": {
                    "country_iso2": {"type": "string"},
                    "hs6": {"type": "string"},
                },
                "required": ["country_iso2"],
            },
            handler=fake_lookup_duty,
        ),
    ]
    adapter = _GenaiModelAdapter(sdk, tools=tools)
    draft = GeminiDraftExtractor(adapter).extract(
        "six jute bags to america", None, "hi"
    )

    assert draft.product_category == "jute-products"
    assert tool_results == [{"country_iso2": "US", "hs6": "5310"}], (
        f"named args must reach the handler: {tool_results}"
    )
    assert sdk.round == 2
