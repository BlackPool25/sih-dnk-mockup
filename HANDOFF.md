# SIH-DNK Mockup — Handoff / Current State (for the next agent)

**Written:** 2026-08-09 · **Project:** `~/projects/sih-dnk-mockup` · **Branch:** `main` (14 commits)
**Status:** Foundation COMPLETE and verified. Next phase (order-capture workflow) NOT yet started — see §7.
**Plan artifact:** `.omo/plans/sih-dnk-db-setup.md` (18/18 checked) · Boulder: `completed` · `.omo/notepads/sih-dnk-db-setup/learnings.md` (append-only gotchas)

---

## 0. TL;DR

A **verified backend foundation** for the DNK export-assistant mockup: Dockerized Postgres 16 with the full curated data pack (provenance on every row), a read-only LLM tool surface, a deterministic extraction contract, and **official-format document generation** (PBE-III/IV per CBIC Notification 07/2026, CN22/23 per UPU) with **all official PBE filling rules enforced deterministically**. **120 tests pass, verify 28/28.** The user's *complete flow* (buyer-acquisition, onboarding→payment→tracking→incentives) is NOT built — see §7 for what's next.

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

### 2.1 Database (Postgres 16, schema via Alembic head `8d3617703da2`)
10 business tables + `alembic_version` (11 in `public`). NO findings.md §5 tables (artisans/orders/shipments/wallet/escrow — deliberately excluded).
| Table | Rows | Notes |
|---|---|---|
| `lanes` | 139 | 135 ITPS (L1) + 4 EMS (US/GB/AE/AU, **L5, is_estimate=true, `conflicts` JSONB with `alternatives` key**) |
| `state_sales_tax` | 51 | 50 states + DC, master table only |
| `product_categories` | 8 | slug, hs6_default, pbe_desc_template, certs/lane_fit JSONB |
| `hs_codes` | 99 | hs6/itc_hs_8/hts_10/description, FK→categories, confidence from 🟢🟡🔴⚠️ |
| `country_rates` | 88 | MFN/S301/VAT/GST/DE_MINIMIS in minor units |
| `config_flags` | 86 | scalar/flat-array JSONB shape (never object); incl. `labels.*` (hi/kn UI copy), `sdr.fx_minor_per_sdr=10942` |
| `pbe_field_schemas` | 116 | **OFFICIAL** Notification 07/2026 structure (PBE_III 60 + PBE_IV 56), sections Header/Parcel/Assessable value/Duty-Tax/Additional details/Declarations; only ~7 genuinely-sourced fields are `required` |
| `transcripts`/`lookups`/`documents` | 35 docs | business tables, NO provenance, NO config FKs (TRUNCATE-safe) |
- **Provenance mixin** (source_url NOT NULL, source_level, confidence, is_estimate, effective_from/to, verified_at) on ALL 7 config tables; absent from business tables.
- **FK policy:** config→config only (hs_codes→product_categories) + business→business (lookups→transcripts, documents self-FK). No business→config FKs.
- **Seeding:** `uv run python -m app.services.convert` with subcommands `--lanes`, `--categories`, `--states`, `--flags`, `--pbe`, `--all`. **Each subcommand truncates ONLY its own tables** (fixed in `bfbe758` — the old shared TRUNCATE wiped everything). `--all` = full serial re-seed (safe, idempotent).
- **Verification:** `uv run python -m app.services.verify` → 28/28 gates PASS, exit 0; writes `seed/verification_report.md` (git-ignored) with row-count gates, C-1…C-13 conflict log, tamper tests, psql auth probe.

### 2.2 Read-only LLM tool surface (`app/services/db_tools/__init__.py`)
Exactly 6 SELECT-only functions (the ONLY way the model touches the DB — no raw SQL, no generic query tool, row-capped via LIMIT):
`search_categories(query)` · `lookup_hs_codes(category, hs6)` · `lookup_duty(country_iso2, hs6)` ([] for unknown) · `quote_lane(country_iso2, weight_g, lane)` (slab math; LookupError unknown pair, ValueError over-cap) · `get_state_sales_tax(state_iso2)` (KeyError) · `get_config_flag(key)` (KeyError). Every result carries provenance.

### 2.3 Extraction contract (`app/schemas/shipment.py`, `app/services/extract.py`, `app/services/validate.py`)
- **USER REQUIREMENTS baked in:** (1) the model is NEVER passed the conversation transcript — the `Extractor.extract(previous, lang)` contract takes only the prior Shipment object + language tag; re-prompts use `previous.model_dump(exclude={"raw_transcript"})`. (2) **Verification is NEVER by the LLM** — `validate.py` is the only validator.
- `Shipment` (Pydantic, keys-only — no HS/duty values): product_category (Literal 8 slugs), quantity (-1 sentinel), weight_grams (-1 sentinel), destination_country (ISO2 or "unknown"), confidence (high/medium/low), raw_transcript (demo-log only).
- `RuleExtractor.extract_from_text(text, lang)` — deterministic demo default (hi/kn/en number words, category keywords, country aliases; raises `CategoryUnknownError` rather than inventing; **hi/kn weight-unit words like ग्राम/ಗ್ರಾಮ and compound numbers like ನಾನೂರು are NOT yet in the vocabulary — known gap**).
- `GeminiExtractor` — adapter with `response_schema` + thinking disabled; **mocked-only, no real client/API key wired** (needs a key to go live).
- `validate.py` — `validate_shipment` (real ISO2 via pycountry, qty 1..10k, weight 1..50kg), `missing_required(s, form_type)` → the list of required PBE fields the extractor did NOT supply (drives the "ask the user" flow), and **`validate_document_rules`** (todo 14) enforcing the official filling rules (see 2.4).

### 2.4 Document generation — OFFICIAL government/UPU format (todos 13–14, the user's critical requirements)
`uv run python -m app.services.docs render ...` with flags: `--category --qty --weight-g --country --form {PBE_III,PBE_IV,CN22,CN23,INVOICE,PACKING_LIST} --out [--preview] [--yes] [--ask-optional] [--value-minor] [--consignee] [--iec] [--gstin]`.
- **6 templates** in `app/services/docs/templates/` rebuilt to the official layouts: PBE-III/IV per **CBIC Notification No. 07/2026-Customs (N.T.) 15-Jan-2026** (verbatim headers "Foreign Post Office code", "GSTIN or as applicable", "AD code (if Applicable)", "Assessable value", "RITC code/ITC-HS code", "Nature of contract (CIF/CF/C&F/FOB)", the 6 declaration clusters with **exact legal wording** incl. Drawback (a)–(d)); CN22/CN23 per UPU (sender/consignee blocks, barcode placeholder, SDR note); invoice/packing-list (commercial).
- **Deterministic render gate (order matters):** `DocumentData.model_validate` → `validate_document_rules` (filling rules) → `missing_required == []` → **SDR enforcement** (CN22 ≤300 SDR / CN23 >300 SDR, auto-switches, never user-picked) → Jinja2 → WeasyPrint → sha256 → immutable `documents` row (version = max+1, supersedes_doc_id, never overwrite). **The LLM never validates.**
- **Official filling rules enforced with the portal's exact rejection strings:** gross ≤ 110% of net · FOB ≤ invoice · Σ piece values ≤ parcel value ("Value of Sub pieces does not match") · Σ piece weights ≤ parcel weight ("Weight of Sub pieces does not match") · Description ↔ HS/CTH mismatch ("Description does not match with HS Code/CTH", with a canonical-DB-name trust fallback) · ITCH restricted-policy WARN · DGFT/IEC gate ("DGFT registration data missing") · KYC gate ("booking requires at least one of IEC or GSTIN").
- **Preview/confirm:** `--preview` prints the form summary + hi/kn confirm labels (`labels.confirm.hi/kn`), no PDF without `--yes`; `--ask-optional` prompts for consignee/value (declined → "—"); **the rendered form content is ENGLISH-only** (hi/kn appears only in preview/UI).
- **Hands-on verified:** PBE_IV PDF contains 7 official headers + verbatim declaration wording, 0 hi/kn; CN22/CN23 auto-select by SDR verified live (₹50,000→CN23, ₹20→CN22).

### 2.5 Tests (120 pass, `uv run pytest -q`)
`test_iso2.py` (34) · `test_db_tools.py` (23) · `test_extract.py` (18) · `test_docs_renderer.py` (14) · `test_validate_rules.py` (23+ incl. SDR switch) · `test_convert.py` (2, truncate-scope regression). Tests run against the **live seeded DB** — keep the container up.

---

## 3. Key files (quick map)

| Path | What |
|---|---|
| `docker-compose.yml` | DB service (postgres:16-alpine, loopback 5433, tuned, healthcheck) |
| `.env` / `.env.example` | DB_PASSWORD (48-hex, git-ignored) / DB_PORT / POSTGRES_* / DATABASE_URL |
| `bin/psql` | sudo-free psql shim (docker dispatch) |
| `app/db.py` | engine + SessionLocal from DATABASE_URL |
| `app/models/*` | SQLAlchemy 2.0 models + ProvenanceMixin |
| `app/parsers/iso2.py`, `markdown_tables.py` | corpus parsing (135/135 ISO2 gate raises on unmapped) |
| `app/services/convert.py` | seeding CLI (`--lanes/--categories/--states/--flags/--pbe/--all`) |
| `app/services/verify.py` | 28/28 gates + verification_report.md |
| `app/services/db_tools/__init__.py` | the 6 read-only tool functions |
| `app/services/extract.py`, `validate.py` | extraction + deterministic validation |
| `app/services/docs/{document,renderer,__main__}.py` + `templates/` | doc pipeline + official templates |
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
uv run python -m app.services.verify           # 28/28 PASS

# Type a description → extract (hi/kn/en) → preview → render official PBE-IV
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form PBE_IV --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --out docs-out/demo.pdf
pdftotext docs-out/demo.pdf - | grep -c "Assessable value"   # official header present

# Preview with hi/kn confirm labels (no PDF without --yes)
uv run python -m app.services.docs render --category jute-products --qty 2 \
    --weight-g 800 --country US --form PBE_III --preview
```

---

## 5. Known gaps / TODOs the next agent should know

1. **hi/kn extraction vocabulary is partial** — the RuleExtractor lacks Hindi/Kannada *weight-unit* words (ग्राम/ग्राम, ಗ್ರಾಮ) and some compound numbers (ನಾನೂರು = 400). For a reliable hi/kn voice/text demo, extend `_NUMBER_WORDS`/`_WEIGHT_UNITS` in `app/services/extract.py` (and tests).
2. **GeminiExtractor is mocked-only** — to make "LLM fills details from user descriptions" live, add a `GEMINI_API_KEY` env var + a thin real-client path (the adapter is already structured for it). Zero-key fallback = RuleExtractor.
3. **No Order / quote entity yet** — the docs are CLI-driven, not order-prefilled. The user's workflow (describe → map → find missing → ask → full order → prefilled docs) needs an Order-capture layer (§7).
4. **`BULK_UPDATED_FILE/` in the repo root** — 16 India Post bulk-upload templates (domestic mail / money orders / ePost / legacy int'l mail) the user added; **they are NOT the PBE export schema** (no hscode/prd_desc/ecomm/origincountry columns). If the user wants a real PBE bulk Excel, generate the 23-column schema from `pbe-iii-iv-fields.md §6` (Information Sheet + Article Details Sheet). Currently nothing imports Excel.
5. **Notepad** `.omo/notepads/sih-dnk-db-setup/learnings.md` is append-only and holds environment facts + gotchas — READ before delegating work; append via `cat >>` (never overwrite).

---

## 6. The user's complete flow (reference — design, not built)

`/home/shreyas/Downloads/OmniLearn/.omnilearn/research/dnk-export-enablement/follow-ups/01-buyer-acquisition/complete-flow.md` — the DECIDED design: **artisan = exporter of record**, money straight to her Razorpay merchant balance with a settlement hold, platform is tooling + guarantee (never merchant/escrow/duty-collector). Phases: P0 onboarding (voice) → P1 quote (landed-cost engine, price hash, valid_until) → P2 order → P3 payment + dispute window → P4 fulfilment (doc pack + Article ID + 17TRACK) → P5 delivery + release → P6 incentives guidance. Plus §5A exporter binding (IEC+AD-code+bank lock, e-FIRA reconciliation), §5B webhook-driven state machine (no manual "paid"), §5C sign-and-go onboarding kit. The current mock covers the **doc-pack + landed-cost engine** rows of that flow's honesty table — nothing else yet.

---

## 7. What the user asked for NEXT (the order-capture workflow)

The user's requested workflow (verbatim intent, 2026-08-09):
> "users describe the order details → the AI/LLM maps them → finds the missing details → asks the user to fill them → ends with a full order + listing mapping → then generates the actually pre-filled docs. Leave the AI/LLM fill path + the strict data validation + the docs generation."

**Proposed scope (not yet planned as a work plan — needs Prometheus planning before execution):**
1. **Capture loop CLI** (`python -m app.services.order capture "<description>"`): extract (hybrid Gemini-if-key / RuleExtractor fallback) → `validate_shipment` + `missing_required` → **guided bilingual ask-loop** for each missing field (consignee, value, IEC, GSTIN, …) → re-validate → full captured Order → render prefilled docs.
2. **`Order` entity** (SQLAlchemy, business table, no config FKs): holds the full captured details so docs prefill instead of "—".
3. **Gemini live path** via `GEMINI_API_KEY` (free tier) — LLM fills what it can from the description; deterministic validation still gates everything.
4. Reuse everything verified (db_tools, validate.py rules, official templates, SDR auto-select, immutable versioning).

---

## 8. Guardrails (from the completed plan — keep these)

- The LLM is NEVER passed the conversation transcript; re-prompts carry only the Shipment object minus raw_transcript.
- The LLM NEVER validates — `validate.py` + Pydantic are the only verifiers.
- No raw-SQL / generic-query tool for the model — only the 6 db_tools functions.
- Business tables never auto-truncate; config tables TRUNCATE only their own set per subcommand.
- `.env` never committed; passwords only in `.env`; README/examples use `${DB_PASSWORD}`/`changeme` placeholders.
- No business→config FKs (TRUNCATE-without-CASCADE safety).
- Form content is ENGLISH-only; hi/kn labels only in preview/UI.
- No findings.md §5 business tables unless a new plan adds them deliberately.
