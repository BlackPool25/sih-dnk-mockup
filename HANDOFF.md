# SIH-DNK Mockup — Handoff / Current State (for the next agent)

**Written:** 2026-08-09 · **Project:** `~/projects/sih-dnk-mockup` · **Branch:** `main` (14 commits)
**Status:** Foundation COMPLETE and verified. The field/rule rework (waves 0–5: `filling_rules` DB-driven validation, `field_values` as the single render source, DB-driven auto-generated CLI flags) is COMPLETE — **138 tests pass, verify 29/29**. Next phase (order-capture workflow) NOT yet started — see §7.
**Plan artifact:** `.omo/plans/sih-dnk-db-setup.md` (18/18 checked) · Boulder: `completed` · `.omo/notepads/sih-dnk-db-setup/learnings.md` (append-only gotchas)

---

## 0. TL;DR

A **verified backend foundation** for the DNK export-assistant mockup: Dockerized Postgres 16 with the full curated data pack (provenance on every row), a read-only LLM tool surface, a deterministic extraction contract, and **official-format document generation** (PBE-III/IV per CBIC Notification 07/2026, CN22/23 per UPU). Validation is **DB-driven**: the official PBE filling rules live in the `filling_rules` table (rule_key/enabled/severity/applies_to/params/message), every rendered PBE field value flows through `DocumentData.field_values` (`resolve_value` = single formatting point), and every `pbe_field_schemas` field is CLI-reachable via auto-generated argparse flags. **138 tests pass, verify 29/29.** The user's *complete flow* (buyer-acquisition, onboarding→payment→tracking→incentives) is NOT built — see §7 for what's next.

---

## 1. Environment facts (verified 2026-08-09 — read these BEFORE running anything)

- **DB container:** `sih-dnk-postgres` (postgres:16-alpine) — `Up (healthy)`, host port **5433** loopback-only (`127.0.0.1:5433→5432`). Host 5432 is occupied by `internapply-postgres` — never touch it.
- **Connection:** `set -a && . ./.env && set +a` exports `DATABASE_URL=postgresql+psycopg://sih_dnk:<pw>@localhost:5433/sih_dnk`.
- **psql access — TWO ways:**
  1. Host `psql` (PostgreSQL 18.4 client — the user installed it; `command -v psql` works).
  2. **Sudo-free shim** `~/projects/sih-dnk-mockup/bin/psql` — dispatch `psql "$DATABASE_URL"` via docker `postgres:16-alpine` on network `sih-dnk-mockup_dbnet` (translates `localhost:5433` → `db:5432`). Works when the host client is absent.
  ```bash
  export PATH="$HOME/projects/sih-dnk-mockup/bin:$PATH"   # picks up the shim if host psql missing
  set -a && . ./.env && set +a
  psql "$DATABASE_URL" -c "SELECT count(*) FROM lanes;"    # = 139
  ```
- **Runtime:** uv (`~/.local/bin/uv`) + `.venv` Python 3.12.9. Run everything with `uv run python -m ...` or `uv run pytest`.
- **Git identity** is set repo-locally: `Shreyas S Joshi <shreyasjoshi2511@gmail.com>`. Commits are Conventional Commits (`feat/fix/docs/chore(sih-dnk): ...`).
- **WeasyPrint 63.1** installed; host has pango 1.57.1 + cairo + Noto Sans Devanagari + Noto Sans Kannada (system fontconfig — do NOT bundle fonts).
- **No passwordless sudo** on this host — never plan a `sudo apt-get` step as required (use the psql shim; poppler-utils/pdftotext already installed).

---

## 2. What is built (all verified — don't re-verify unless you change it)

### 2.1 Database (Postgres 16, schema via Alembic heads `8d3617703da2` → `a1f4c9e2b7d6`)
11 tables + `alembic_version` (12 in `public`): **8 provenance-carrying config tables + 3 business tables**. NO findings.md §5 tables (artisans/orders/shipments/wallet/escrow — deliberately excluded).
| Table | Rows | Notes |
|---|---|---|
| `lanes` | 139 | 135 ITPS (L1) + 4 EMS (US/GB/AE/AU, **L5, is_estimate=true, `conflicts` JSONB with `alternatives` key**) |
| `state_sales_tax` | 51 | 50 states + DC, master table only |
| `product_categories` | 8 | slug, hs6_default, pbe_desc_template, certs/lane_fit JSONB |
| `hs_codes` | 99 | hs6/itc_hs_8/hts_10/description, FK→categories, confidence from 🟢🟡🔴⚠️ |
| `country_rates` | 88 | MFN/S301/VAT/GST/DE_MINIMIS in minor units |
| `config_flags` | 86 | scalar/flat-array JSONB shape (never object); incl. `labels.*` (hi/kn UI copy), `sdr.fx_minor_per_sdr=10942` |
| `pbe_field_schemas` | 116 | **OFFICIAL** Notification 07/2026 structure (PBE_III 60 + PBE_IV 56), sections Header/Parcel/Assessable value/Duty-Tax/Additional details/Declarations; 7 genuinely-sourced fields are `required` per form (consignee_details, product_description, cth, quantity_unit, gross_weight, net_weight, assessable_value) |
| `filling_rules` | 8 | **DB-driven filling rules** (rule_key/enabled/severity/applies_to/params/message, provenance, CHECK severity IN ('error','warning')) — seeded via `convert --rules`; read by `validate_document_rules` on EVERY call (a row edit changes behavior with no code change) |
| `transcripts`/`lookups`/`documents` | 35 docs | business tables, NO provenance, NO config FKs (TRUNCATE-safe) |
- **Provenance mixin** (source_url NOT NULL, source_level, confidence, is_estimate, effective_from/to, verified_at) on ALL 8 config tables (incl. `filling_rules`); absent from business tables.
- **FK policy:** config→config only (hs_codes→product_categories) + business→business (lookups→transcripts, documents self-FK). No business→config FKs.
- **Seeding:** `uv run python -m app.services.convert` is now a **thin facade** — the seeding logic lives in `app/services/seed/` (one module per domain: `lanes.py` `categories.py` `states.py` `flags.py` `pbe.py` `rules.py` + `_common.py` shared globals + `__init__.py` orchestration/CLI). Subcommands: `--lanes`, `--categories`, `--states`, `--flags`, `--pbe`, `--rules`, `--all` (**`--rules` was added in wave 0; `--all` includes it**). **Each subcommand truncates ONLY its own tables** (`_config_truncate`, single dynamic TRUNCATE + RESTART IDENTITY — idempotent re-runs). `--all` = full serial re-seed (safe, idempotent; `documents` never touched).
- **Verification:** `uv run python -m app.services.verify` → **29/29 gates PASS, exit 0** (G13 = `filling_rules` seeded == 8, added wave 0); writes `seed/verification_report.md` (git-ignored) with row-count gates, C-1…C-13 conflict log, tamper tests, psql auth probe.

### 2.2 Read-only LLM tool surface (`app/services/db_tools/__init__.py`)
Exactly 6 SELECT-only functions (the ONLY way the model touches the DB — no raw SQL, no generic query tool, row-capped via LIMIT):
`search_categories(query)` · `lookup_hs_codes(category, hs6)` · `lookup_duty(country_iso2, hs6)` ([] for unknown) · `quote_lane(country_iso2, weight_g, lane)` (slab math; LookupError unknown pair, ValueError over-cap) · `get_state_sales_tax(state_iso2)` (KeyError) · `get_config_flag(key)` (KeyError). Every result carries provenance.

### 2.3 Extraction contract (`app/schemas/shipment.py`, `app/services/extract.py`, `app/services/validate.py`)
- **USER REQUIREMENTS baked in:** (1) the model is NEVER passed the conversation transcript — the `Extractor.extract(previous, lang)` contract takes only the prior Shipment object + language tag; re-prompts use `previous.model_dump(exclude={"raw_transcript"})`. (2) **Verification is NEVER by the LLM** — `validate.py` is the only validator.
- `Shipment` (Pydantic, keys-only — no HS/duty values): product_category (Literal 8 slugs), quantity (-1 sentinel), weight_grams (-1 sentinel), destination_country (ISO2 or "unknown"), confidence (high/medium/low), raw_transcript (demo-log only).
- `RuleExtractor.extract_from_text(text, lang)` — deterministic demo default (hi/kn/en number words, category keywords, country aliases; raises `CategoryUnknownError` rather than inventing; **hi/kn weight-unit words like ग्राम/ಗ್ರಾಮ and compound numbers like ನಾನೂರು are NOT yet in the vocabulary — known gap**).
- `GeminiExtractor` — adapter with `response_schema` + thinking disabled; **mocked-only, no real client/API key wired** (needs a key to go live).
- `validate.py`:
  - `validate_shipment` (real ISO2 via pycountry, qty 1..10k, weight 1..50kg) — unchanged.
  - **`missing_required(data: DocumentData, form_type=None)` — wave 2: takes a DocumentData (NOT a Shipment) and covers ALL DB-required fields per form, including `assessable_value` (the old Shipment-projection gap is CLOSED — F3). A field is missing when `resolve_value(field_key)` renders "—".** PBE renders therefore REQUIRE a declared value (`--value-minor`) and a consignee (`--consignee`) unless the seller supplies them — the completeness gate lists exactly the missing keys.
  - **`validate_document_rules` — DB-driven (wave 2):** the ENABLED rows of `filling_rules` are loaded on every call; each row contributes its evaluator (dispatch by `rule_key` via `_EVALUATORS`), its `params`, its `severity` and its VERBATIM `message`. A DB row whose `rule_key` has no evaluator prints a stderr warning and is skipped. `MSG_*` constants mirror the seeded messages (tests reference them; the DB row is the runtime source of truth).
- `DocumentData` (wave 1) — the document payload now carries:
  - **`field_values: dict[str, int | str]`** — EVERY PBE field value (derived at build time from category/HS/shipment/CLI inputs, or provided by the seller via CLI flags); provided always beats derived (`{**derived, **provided}`).
  - **`field_schema: dict[str, dict]`** — the `pbe_field_schemas` metadata (value_type/options/label) loaded at build; a Pydantic validator verifies every provided `field_values` entry against it (number/money int-coercible, money non-negative, boolean/string-with-options within the DB choices, url `^https?://`).
  - **`sender: SenderBlock`** — the CN22/CN23 sender block (name_address/sender_ref/non_delivery/num_invoices).
  - **`resolve_value(field_key)`** — the SINGLE formatting point for rendering: provided/derived value with units (money → `₹2,000.00`, quantity_unit → "8 Nos", weights → "400 g"), "—" when absent.

### 2.4 Document generation — OFFICIAL government/UPU format (todos 13–14, the user's critical requirements)
`uv run python -m app.services.docs render ...` with the 13 legacy flags (`--category --qty --weight-g --country --form {PBE_III,PBE_IV,CN22,CN23,INVOICE,PACKING_LIST} --out [--preview] [--yes] [--ask-optional] [--value-minor] [--consignee] [--iec] [--gstin]`), the 8 dedicated flags (`--net-weight --fob --unit-value --piece-gross --sender --sender-ref --non-delivery --num-invoices`), and **~47 auto-generated per-field flags** derived from `pbe_field_schemas` (see CLI below).
- **6 templates** in `app/services/docs/templates/` rebuilt to the official layouts: PBE-III/IV per **CBIC Notification No. 07/2026-Customs (N.T.) 15-Jan-2026** (verbatim headers "Foreign Post Office code", "GSTIN or as applicable", "AD code (if Applicable)", "Assessable value", "RITC code/ITC‑HS code" — non-breaking hyphen, R5, "Nature of contract (CIF/CF/C&F/FOB)", the 6 declaration clusters with **exact legal wording** incl. Drawback (a)–(d)); CN22/CN23 per UPU (sender/consignee blocks, non-delivery + invoices boxes, barcode placeholder, SDR note); invoice/packing-list (commercial).
- **Deterministic render gate (order matters):** `DocumentData.model_validate` (incl. the per-field `field_values` verification against `pbe_field_schemas` value_type/options) → `validate_document_rules` (**DB-DRIVEN** — reads the enabled `filling_rules` rows every call; change a rule's params/message/enablement with an UPDATE, no code change; unknown rule_key → stderr warning) → `missing_required(data, doc_type) == []` (all 7 DB-required fields) → **SDR enforcement** (CN22 ≤300 SDR / CN23 >300 SDR, auto-switches, never user-picked) → Jinja2 → WeasyPrint → sha256 → immutable `documents` row (version = max+1, supersedes_doc_id, never overwrite). **The LLM never validates.**
- **Official filling rules enforced from the `filling_rules` table** (params/messages/enablement are DB data; evaluators dispatch per rule_key): gross ≤ 110% of net (`max_ratio` param) · FOB ≤ invoice · Σ piece values ≤ parcel value ("Value of Sub pieces does not match") · Σ piece weights ≤ parcel weight ("Weight of Sub pieces does not match") · Description ↔ HS/CTH mismatch (canonical-DB-name trust fallback) · ITCH restricted-policy WARN (`restricted_hs6` param) · DGFT/IEC gate · KYC gate. **The rule inputs are NOW CLI-reachable:** `--net-weight` / `--fob` / `--unit-value` / `--piece-gross` trigger the gross-110% / FOB / sub-piece checks (F5 closed).
- **Formatting (waves 1–3):** IEC/GSTIN and ALL exporter fields render when supplied (F2/F3 closed — `--exporter-name`, `--exporter-address`, `--state-code`, `--ad-code`, …); `consignee_details` is the consignee ONLY (no " / US" country suffix — F7); "ITC-HS" uses a non-breaking hyphen (U+2011) so it never splits (R5); the Declarations checkboxes mark the chosen Yes/No/NA with an X.
- **CLI (wave 4, F5/R3 closed):** one auto-generated flag per remaining `pbe_field_schemas` field (~47) — a DB row change propagates to the CLI with no code change; **money fields take INR minor units with a `-minor` suffix** (e.g. `--export-duty-amount-minor 50000` → renders "₹500.00"); `decl.*` accept Yes/No/NA; options fields accept the DB choices (e.g. `--scheme-code drawback`). Duty/Tax fields are seller-suppliable — note `lookup_duty` destination-market data stays on the preview/quote surface, not the PBE form.
- **Preview/confirm:** `--preview` prints the form summary + hi/kn confirm labels (`labels.confirm.hi/kn`), no PDF without `--yes`; `--ask-optional` prompts for consignee/value (declined → "—"); **the rendered form content is ENGLISH-only** (hi/kn appears only in preview/UI).
- **Hands-on verified:** PBE_IV PDF contains the official headers + verbatim declaration wording, 0 hi/kn; CN22/CN23 auto-select by SDR verified live (₹50,000→CN23, ₹20→CN22); seller-field demo PDF verified via pdftotext (Acme Exporters, state code, "[X] Yes" Drawback, "₹500.00", contiguous "ITC‑HS").

### 2.5 Tests (138 pass, `uv run pytest -q`)
`test_iso2.py` (34) · `test_validate_rules.py` (31, incl. DB-driven rule tests: disabling a rule in the DB disables the check; message read from the DB row) · `test_db_tools.py` (23) · `test_docs_renderer.py` (20, incl. sender block, decl-box marking, auto-flag rendering, money-minor, net-weight rule reachability, flag-collision pin) · `test_extract.py` (16 — the two old `missing_required(Shipment)` tests were REMOVED; their intent moved to `test_document_data.py`) · `test_document_data.py` (10 — field_values/resolve_value/validator + the 3 `missing_required(DocumentData)` tests incl. the 7-key coverage) · `test_convert.py` (4, truncate-scope regression + rules idempotency/scope). Tests run against the **live seeded DB** — keep the container up.

---

## 3. Key files (quick map)

| Path | What |
|---|---|
| `docker-compose.yml` | DB service (postgres:16-alpine, loopback 5433, tuned, healthcheck) |
| `.env` / `.env.example` | DB_PASSWORD (48-hex, git-ignored) / DB_PORT / POSTGRES_* / DATABASE_URL |
| `bin/psql` | sudo-free psql shim (docker dispatch) |
| `app/db.py` | engine + SessionLocal from DATABASE_URL |
| `app/models/*` | SQLAlchemy 2.0 models + ProvenanceMixin (incl. `filling_rules.py` — FillingRule) |
| `app/parsers/iso2.py`, `markdown_tables.py` | corpus parsing (135/135 ISO2 gate raises on unmapped) |
| `app/services/convert.py` | **thin facade** (18 lines) re-exporting the seed package's public API — `python -m app.services.convert` unchanged |
| `app/services/seed/` | the seeding logic: `lanes.py`/`categories.py`/`states.py`/`flags.py`/`pbe.py`/`rules.py` + `_common.py` + `__init__.py` (CONFIG_TABLES/_config_truncate/import_configs/main) |
| `app/services/verify.py` | **29/29 gates** (G13 filling_rules=8) + verification_report.md |
| `app/services/db_tools/__init__.py` | the 6 read-only tool functions |
| `app/services/extract.py`, `validate.py` | extraction + deterministic validation (DB-driven rules, `missing_required(DocumentData)`) |
| `app/services/docs/document.py` | DocumentData (field_values/field_schema/sender/resolve_value), SenderBlock, build_document_data, _money |
| `app/services/docs/cli_fields.py` | **DB-driven flag generation** (RESERVED_FIELDS/flag_name/pbe_field_specs/add_pbe_field_arguments/collect_field_values) |
| `app/services/docs/__main__.py` | CLI: legacy + 8 dedicated + ~47 auto flags; cmd_render order validate→build→ask-optional→completeness→preview→render |
| `app/services/docs/renderer.py` + `templates/` | render pipeline (resolve_value adoption, _cn_context sender, completeness gate) + official templates |
| `tests/test_document_data.py` | Wave-1/2 test home (field_values, resolve_value, missing_required 7-key coverage) |
| `CRITIQUE.md` | severity-ranked review of the original implementation-plan.md |
| `README.md` | full runbook (preconditions, run steps, env contract, LLM note, doc CLI) |

---

## 4. How to run the demo (already working)

```bash
cd ~/projects/sih-dnk-mockup
export PATH="$HOME/projects/sih-dnk-mockup/bin:$PATH"
set -a && . ./.env && set +a
docker compose ps                              # sih-dnk-postgres healthy

# Full verification
uv run python -m app.services.verify           # 29/29 PASS

# Render an official PBE-IV (PBE renders REQUIRE a declared value + consignee —
# assessable_value and consignee_details are completeness-gated)
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form PBE_IV --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 200000 --consignee "Jane Doe, 123 Main St" \
    --out docs-out/demo.pdf
pdftotext docs-out/demo.pdf - | grep -c "Assessable value"   # official header present

# Seller fields via the auto-generated flags (state code, Drawback chosen, scheme)
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form PBE_IV --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 200000 --consignee "Jane Doe, 123 Main St" \
    --exporter-name "Acme Exporters Pvt Ltd" --state-code 29 \
    --decl-drawback Yes --scheme-code drawback \
    --out docs-out/seller-fields.pdf
pdftotext docs-out/seller-fields.pdf - | grep -cE "Acme Exporters|\[X\] Yes"

# Preview with hi/kn confirm labels (no PDF without --yes)
uv run python -m app.services.docs render --category jute-products --qty 2 \
    --weight-g 800 --country US --form PBE_III \
    --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 200000 --consignee "Jane Doe, 123 Main St" --preview
```

---

## 5. Known gaps / TODOs the next agent should know

1. **hi/kn extraction vocabulary is partial** — the RuleExtractor lacks Hindi/Kannada *weight-unit* words (ग्राम/ಗ್ರಾಮ) and some compound numbers (ನಾನೂರು = 400). For a reliable hi/kn voice/text demo, extend `_NUMBER_WORDS`/`_WEIGHT_UNITS` in `app/services/extract.py` (and tests).
2. **GeminiExtractor is mocked-only** — to make "LLM fills details from user descriptions" live, add a `GEMINI_API_KEY` env var + a thin real-client path (the adapter is already structured for it). Zero-key fallback = RuleExtractor.
3. **No Order / quote entity yet** — the docs are CLI-driven, not order-prefilled. The user's workflow (describe → map → find missing → ask → full order → prefilled docs) needs an Order-capture layer (§7).
4. **`BULK_UPDATED_FILE/` in the repo root** — 16 India Post bulk-upload templates (domestic mail / money orders / ePost / legacy int'l mail) the user added; **they are NOT the PBE export schema** (no hscode/prd_desc/ecomm/origincountry columns). If the user wants a real PBE bulk Excel, generate the 23-column schema from `pbe-iii-iv-fields.md §6` (Information Sheet + Article Details Sheet). Currently nothing imports Excel.
5. **Notepad** `.omo/notepads/sih-dnk-db-setup/learnings.md` is append-only and holds environment facts + gotchas — READ before delegating work; append via `cat >>` (never overwrite).
6. **Filling-rule tuning is a DB edit** — `filling_rules.params` (gross `max_ratio` 1.10, `restricted_hs6` ["5303","4403"], …), `message`s and `enabled` flags are DATA: change them with an UPDATE and the next render honors them. But a NEW rule TYPE (a rule_key with no evaluator) requires a new evaluator + `_EVALUATORS` entry in `app/services/validate.py` (the DB row alone prints a stderr warning and is skipped).

---

## 6. The user's complete flow (reference — design, not built)

`/home/shreyas/Downloads/OmniLearn/.omnilearn/research/dnk-export-enablement/follow-ups/01-buyer-acquisition/complete-flow.md` — the DECIDED design: **artisan = exporter of record**, money straight to her Razorpay merchant balance with a settlement hold, platform is tooling + guarantee (never merchant/escrow/duty-collector). Phases: P0 onboarding (voice) → P1 quote (landed-cost engine, price hash, valid_until) → P2 order → P3 payment + dispute window → P4 fulfilment (doc pack + Article ID + 17TRACK) → P5 delivery + release → P6 incentives guidance. Plus §5A exporter binding (IEC+AD-code+bank lock, e-FIRA reconciliation), §5B webhook-driven state machine (no manual "paid"), §5C sign-and-go onboarding kit. The current mock covers the **doc-pack + landed-cost engine** rows of that flow's honesty table — nothing else yet.

---

## 7. What the user asked for NEXT (the order-capture workflow)

The user's requested workflow (verbatim intent, 2026-08-09):
> "users describe the order details → the AI/LLM maps them → finds the missing details → asks the user to fill them → ends with a full order + listing mapping → then generates the actually pre-filled docs. Leave the AI/LLM fill path + the strict data validation + the docs generation."

**Proposed scope (not yet planned as a work plan — needs Prometheus planning before execution):**
1. **Capture loop CLI** (`python -m app.services.order capture "<description>"`): extract (hybrid Gemini-if-key / RuleExtractor fallback) → `validate_shipment` + `missing_required` → **guided bilingual ask-loop** for each missing field (consignee, value, IEC, GSTIN, …) → re-validate → full captured Order → render prefilled docs.
2. **`Order` entity** (SQLAlchemy, business table, no config FKs): holds the full captured details so docs prefill instead of "—". The wave-1 `field_values` + `SenderBlock` shapes are the prefill contract — keep them EXACTLY as built.
3. **Gemini live path** via `GEMINI_API_KEY` (free tier) — LLM fills what it can from the description; deterministic validation still gates everything.
4. Reuse everything verified (db_tools, DB-driven validate.py rules, official templates, auto-flag CLI, SDR auto-select, immutable versioning).

---

## 8. Guardrails (from the completed plan — keep these)

- The LLM is NEVER passed the conversation transcript; re-prompts carry only the Shipment object minus raw_transcript.
- The LLM NEVER validates — `validate.py` + Pydantic are the only verifiers.
- **The official filling rules are DB-driven** — `validate.py` evaluators dispatch on the DB `rule_key`; params/messages/enablement are DB data, not code. New rule TYPES need a new evaluator in validate.py.
- **Every DB field is CLI-reachable via auto-generated flags** (cli_fields.py); required fields are enforced by `missing_required(DocumentData)` — PBE renders need a declared value + consignee (or the seller supplies them).
- No raw-SQL / generic-query tool for the model — only the 6 db_tools functions.
- Business tables never auto-truncate; config tables TRUNCATE only their own set per subcommand (`seed/__init__.py` `_config_truncate`).
- `.env` never committed; passwords only in `.env`; README/examples use `${DB_PASSWORD}`/`changeme` placeholders.
- No business→config FKs (TRUNCATE-without-CASCADE safety).
- Form content is ENGLISH-only; hi/kn labels only in preview/UI.
- No findings.md §5 business tables unless a new plan adds them deliberately.
