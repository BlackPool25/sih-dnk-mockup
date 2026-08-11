# SIH-DNK Mockup

Deterministic export-assistant backend for Indian handmade-goods sellers (SIH/DNK
prototype). It ships:

- **A seeded configuration database** (Postgres 16 in Docker): 139 ITPS/EMS
  lanes, 8 product categories + HS codes + country duty rates, 51 US state
  sales-tax rows, 86 config flags, 116 PBE field schemas, 8 DB-driven filling
  rules — every rate carrying provenance (source URL, level, confidence,
  verified-at).
- **A read-only LLM access layer** (`app/services/db_tools`) — exactly six
  SELECT-only functions; the model never touches raw data.
- **Deterministic extraction + document generation** — hi/kn speech → English
  form keys → validation (never by the LLM) → confirm preview → PDF
  (PBE-III/IV, CN22, CN23, invoice, packing list) with checksum + immutable
  versioning. Every PBE field is CLI-reachable via auto-generated flags; the
  official filling rules are enforced from the `filling_rules` table.

---

## 1. Preconditions

| Tool | Check command | If missing |
|---|---|---|
| Docker | `docker --version` | Install Docker Engine (daemon must be running) |
| Docker Compose | `docker compose version` | Ships with Docker Engine ≥ 23 |
| psql client | `command -v psql` | `sudo apt-get install -y postgresql-client` — **or skip it**: this project ships a sudo-free `bin/psql` docker shim (see §3) |
| pdftotext | `pdftotext -v` | `sudo apt-get install -y poppler-utils` (document-rendering sanity checks) |
| Devanagari/Kannada fonts | `fc-list \| grep -iE "Noto Sans (Devanagari\|Kannada)"` | `sudo apt-get install -y fonts-noto-core fonts-noto-devanagari` (hi/kn preview labels) |
| uv | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (project uses the `uv.lock` toolchain) |

> All data lives inside this repo (`data/`); nothing is read from `~/Downloads`.

---

## 2. Run steps (exact order)

From the project root (`~/projects/sih-dnk-mockup`):

```bash
# 1. Start the database (Postgres 16, bound to 127.0.0.1:5433 only)
docker compose up -d

# 2. Wait until the container is healthy
docker compose ps            # sih-dnk-postgres -> STATUS "healthy" (pg_isready)

# 3. Load the env contract into the shell
set -a && . ./.env && set +a

# 4. Apply the schema (alembic migrations — the single source of truth)
uv run alembic upgrade head

# 5. Seed every config table (serial re-seed; idempotent)
uv run python -m app.services.convert --all

# 6. Verify every gate (exit 0 = ALL PASS)
uv run python -m app.services.verify
```

`convert --all` is the full serial re-seed: lanes first, then the seven config
tables, each import in its own transaction (TRUNCATE + insert) so re-runs never
duplicate. Fine-grained variants exist for parallel-safe partial seeding:
`--lanes` alone, or `--categories --states --flags --pbe --rules` together
(`--rules` seeds the `filling_rules` table — the DB-driven validation rules).

`app/services/convert.py` is a thin facade: the seeding logic lives in the
`app/services/seed/` package (one module per domain + orchestration/CLI).

---

## 3. psql: host client vs the project shim

The project's `.env` `DATABASE_URL` points at the host-bound port
(`localhost:5433`), so a **host-installed** `psql` works directly:

```bash
export PATH="$HOME/projects/sih-dnk-mockup/bin:$PATH"
set -a && . ./.env && set +a

psql "$DATABASE_URL" -c "SELECT count(*) FROM lanes;"          # host psql
```

No host `postgresql-client`? The repo ships a sudo-free shim at `bin/psql` that
dispatches to a `postgres:16-alpine` container on the project's docker network
(`sih-dnk-mockup_dbnet`), translating the host URL into `db:5432`:

```bash
export PATH="$HOME/projects/sih-dnk-mockup/bin:$PATH"
set -a && . ./.env && set +a

psql "$DATABASE_URL" -c "SELECT count(*) FROM state_sales_tax;"  # docker shim
```

The PATH export alone is enough — with it, `psql` resolves to `bin/psql`
whenever the host client is absent.

---

## 4. Environment contract

Copy `.env.example` → `.env` and set the password. **Never commit `.env`**
(git-ignored). The defaults:

```bash
DB_PASSWORD=changeme
DB_PORT=5433
POSTGRES_DB=sih_dnk
POSTGRES_USER=sih_dnk
DATABASE_URL=postgresql+psycopg://sih_dnk:changeme@localhost:5433/sih_dnk
```

Two `DATABASE_URL` variants exist, depending on where the app process runs:

| Context | `DATABASE_URL` |
|---|---|
| **Host** (uv, alembic, tests, CLI) | `postgresql+psycopg://sih_dnk:${DB_PASSWORD}@localhost:5433/sih_dnk` |
| **Compose network** (future app container on `dbnet`) | `postgresql+psycopg://sih_dnk:${DB_PASSWORD}@db:5432/sih_dnk` |

- Host processes use `localhost:5433` (the published port).
- A future application container on the same compose network uses the service
  name `db` on the internal port `5432` — no host port needed.
- Port **5433** is deliberate: 5432 is occupied by another local Postgres.
- Postgres is bound to `127.0.0.1` **only** — never `0.0.0.0`.

---

## 5. LLM access layer (what the model may touch)

The model's ONLY database surface is `app/services/db_tools` — six curated,
**read-only** functions. There is no raw-SQL path, no generic query tool, and
the transcript of the user's speech is **never** sent to the model (the
extraction contract is `extract(previous, lang)` — only the prior Shipment
object and a language tag).

```python
from app.services import db_tools

db_tools.search_categories("jute")            # up to 5 category rows
db_tools.lookup_hs_codes("jute-products")     # up to 10 HS rows w/ provenance
db_tools.lookup_duty("US", hs6="5310")        # MFN / S301 / VAT / de-minimis
db_tools.quote_lane("US", weight_g=100)       # ITPS slab-price math (minor units)
db_tools.get_state_sales_tax("CA")            # one state's sales-tax record
db_tools.get_config_flag("us.s301.rate_pct")  # one pinned flag w/ provenance
```

Guardrails (pinned by tests):

- **SELECT-only** — every query is a SQLAlchemy ORM select; row caps are LIMITs
  inside the query, never post-hoc filtering.
- **Provenance on every result** — `source_url`, `source_level`, `confidence`,
  `is_estimate`, effective window — a figure is never presented as fact unless
  the research says so.
- **Pinned negatives** — unknown lane pair → `LookupError`; over-cap weight →
  `ValueError`; unknown state/flag key → `KeyError`; unknown duty country →
  `[]` (never an error).
- **Validation is deterministic** — business rules in `app/services/validate.py`
  (`validate_shipment`, `missing_required`, `validate_document_rules`) plus
  Pydantic model validation; the LLM never validates anything. The official
  PBE/CN22 filling rules are **DB-driven**: `validate_document_rules` reads the
  enabled rows of the `filling_rules` table on every call (rule_key → evaluator,
  params/messages/enablement are DB data).

---

## 6. Extraction + document flow (user requirements)

1. **hi/kn speech → English form keys.** The user speaks Hindi/Kannada; the
   extractor normalises it to English schema values: category slugs (8 seeded
   categories), ISO2 country codes, integer gram quantities. `RuleExtractor` is
   the default (keyword rules, hi/kn/English number words); `GeminiExtractor`
   is the LLM adapter — never called with a real client in this repo (tests
   inject a mock). Neither ever invents values: unstated fields stay sentinels
   (`-1` / `unknown`) so the CALLER asks the user.
2. **Deterministic validation.** `validate_shipment` (business rules) +
   `DocumentData` Pydantic validation (every provided field value is verified
   against the `pbe_field_schemas` DB metadata: value_type/options) +
   `validate_document_rules` (the official PBE/CN22 filling rules, **DB-driven
   from the `filling_rules` table**) + `missing_required(data)` (completeness
   per `pbe_field_schemas.required` — covers ALL 7 required fields per PBE
   form, including `assessable_value`) — no LLM in the loop.
3. **Preview before generate.** The CLI's `--preview` prints the full form
   summary — every section/field with its value, required fields marked, plus
   the hi/kn confirm labels from `config_flags` (`कृपया पुष्टि करें` /
   `ದಯವಿಟ್ಟು ದೃಢೀಕರಿಸಿ`). No PDF is written unless `--yes` is passed. The
   hi/kn text appears **only** in preview/UI — the rendered forms are English.
4. **Optional details.** A prompt collects the optional order fields
   (consignee name/address, declared value) before rendering; declined values
   render as "—" (the form is honest about what it does not know). For PBE
   forms, `consignee_details` and `assessable_value` are completeness-gated:
   a declared value + consignee are required unless the seller supplies them
   via the CLI flags below.
5. **Official filling rules.** Before any PDF, the renderer enforces the DNK
   portal's own error taxonomy (pbe-iii-iv-fields.md §7, SOP v1.3) with the
   **exact** official rejection strings — never paraphrased. The rule catalog
   is **DB-driven**: `validate_document_rules` loads the enabled rows of the
   `filling_rules` table on every call — each row's params, message and
   enablement are data (change them with an UPDATE, no code change), and the
   rule inputs are CLI-reachable via `--net-weight` / `--fob` / `--unit-value`
   / `--piece-gross`:

   | Rule | Rejection (verbatim) |
   |---|---|
   | gross ≤ 110% of net | `gross weight exceeds 110% of net weight` |
   | FOB ≤ invoice value | `FOB value exceeds invoice value` |
   | Σ piece values ≤ parcel value | `Value of Sub pieces does not match` |
   | Σ piece gross weights ≤ parcel weight | `Weight of Sub pieces does not match` |
   | Description ↔ HS/CTH mismatch | `Description does not match with HS Code/CTH` |
   | ITCH not applicable for restricted policy | `ITCH code not applicable for restricted policy` (WARN — never blocks) |
   | DGFT registration data missing | `DGFT registration data missing` (once ≥1 KYC doc exists) |
   | KYC Note-1: ≥1 of IEC/GSTIN | `booking requires at least one of IEC or GSTIN` |

   A violating document is rejected with a pydantic `ValidationError` listing
   the errors BEFORE WeasyPrint runs — no PDF, no `documents` row.  The
   `--iec`/`--gstin` flags satisfy the DGFT/KYC gates; without either, render
   is blocked.  `net_weight_g` defaults to the gross weight and `fob_minor` to
   the declared value when only one figure is known — a single known figure is
   never rejected for lacking the other.

6. **SDR → CN22/CN23 auto-selection.** The SDR value is auto-computed from the
   declared value using the seeded estimate `sdr.fx_minor_per_sdr` (1 SDR ≈
   ₹109.42, itps-lane.md — `is_estimate=true`); the 300-SDR threshold **only
   decides the label** (CN22 ≤ 300 SDR, CN23 > 300 SDR — document-stack.md
   §10).  The label is derived, never user-picked: requesting CN22 for a
   >300-SDR parcel auto-selects CN23.  The SDR value, threshold and resulting
   choice are shown on the CN22/CN23 form and in the preview.
7. **Render + immutable versioning.** Jinja2 → WeasyPrint → sha256 checksum;
   every render inserts a NEW `documents` row with `version = max(version)+1`
   and `supersedes_doc_id` pointing at the previous row — nothing is ever
   overwritten.

### Doc-render CLI

```bash
# Happy path — render a PBE-IV for a US shipment (IEC + GSTIN satisfy the
# DGFT/KYC gates; value + consignee satisfy the completeness gate)
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form PBE_IV --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 200000 --consignee "Jane Doe, 123 Main St" \
    --out docs-out/pbe_sample.pdf
# document rendered: docs-out/pbe_sample.pdf
# checksum: <sha256>   document id: <id> (version <n>)

# Seller fields via the auto-generated flags (one per pbe_field_schemas field)
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form PBE_IV --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 200000 --consignee "Jane Doe, 123 Main St" \
    --exporter-name "Acme Exporters Pvt Ltd" --exporter-address "42 MG Road, Bengaluru 560001" \
    --state-code 29 --ad-code A1234567 --decl-drawback Yes --scheme-code drawback \
    --export-duty-amount-minor 50000 --out docs-out/seller.pdf
pdftotext docs-out/seller.pdf - | grep -E "Acme Exporters|₹500.00|\[X\] Yes"   # all present

# Rule inputs are CLI-reachable: --net-weight 300 on a 400 g parcel ⇒ the
# gross ≤ 110%-of-net rule fires (exit 1, no PDF)
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form PBE_IV --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 200000 --consignee "Jane Doe, 123 Main St" \
    --net-weight 300 --out docs-out/never.pdf
# error: cannot render — document data rejected:
#   - rules: Value error, gross weight exceeds 110% of net weight

# Preview only — form summary + hi/kn confirm labels, NO PDF (exit 1)
uv run python -m app.services.docs render \
    --category jute-products --qty 2 --weight-g 800 \
    --country US --form PBE_III --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 200000 --consignee "Jane Doe, 123 Main St" --preview
# ... Document preview — Bill of Export — PBE-III ...
# Confirm (हिन्दी): कृपया पुष्टि करें
# Confirm (ಕನ್ನಡ): ದಯವಿಟ್ಟು ದೃಢೀಕರಿಸಿ
# confirm required: re-run with --yes to write the PDF

# Prompt for optional order details before rendering
uv run python -m app.services.docs render \
    --category small-brass-metalware --qty 3 --weight-g 250 \
    --country AE --form INVOICE --ask-optional \
    --iec IN1234567890 --gstin 29ABCDE1234F1Z5
# Optional order details (press Enter to omit — renders as '—'):
# Consignee name/address [empty]: ...
# Declared value (INR minor units) [empty]: ...

# Official-rule rejection — no --iec/--gstin ⇒ KYC gate blocks (exit 1)
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form PBE_IV --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 200000 --consignee "Jane Doe, 123 Main St"
# error: cannot render — document data rejected:
#   - rules: Value error, booking requires at least one of IEC or GSTIN

# Completeness gate — missing required fields listed, exit 1
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form PBE_IV --iec IN1234567890 --gstin 29ABCDE1234F1Z5
# error: cannot render — required fields missing: consignee_details, assessable_value

# SDR → CN22/CN23 auto-selection: the label is derived from the declared value,
# never user-picked.  A >300 SDR parcel (≈ ₹32,800) requested as CN22 renders
# CN23 instead, with the SDR value + choice shown on the form.
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form CN22 --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 4000000 --consignee "Jane Doe, 123 Main St" \
    --out docs-out/cn23-derived.pdf

# CN22 with the seller sender block (--sender/--sender-ref/--non-delivery/--num-invoices)
uv run python -m app.services.docs render \
    --category embroidered-home-textiles --qty 8 --weight-g 400 \
    --country US --form CN22 --iec IN1234567890 --gstin 29ABCDE1234F1Z5 \
    --value-minor 2000 --consignee "Jane Doe, 123 Main St" \
    --sender "Acme Exports, Delhi" --sender-ref IOSS0001 \
    --non-delivery return --num-invoices 2 --out docs-out/cn22-sender.pdf
```

Form types: `PBE_III`, `PBE_IV`, `CN22`, `CN23`, `INVOICE`, `PACKING_LIST`.
Exit codes: `0` rendered · `1` invalid shipment / missing required fields /
official filling-rule rejection / lane error / confirm required · `2` argparse
usage error. PDFs land in `docs-out/` (git-ignored); every render also
persists an immutable `documents` row.

---

## 7. Verification & tests

```bash
uv run python -m app.services.verify     # all 29 gates PASS -> exit 0
uv run pytest -q                          # full suite (138 tests)
```

`verify` regenerates `seed/verification_report.md` (git-ignored) with the
row-count gates (135 ITPS / 4 EMS / 51 states / 8 categories / ≥40 flags /
≥30 PBE / 8 filling rules), provenance and tamper gates, the C-1..C-13
conflict log, and a psql auth probe. Tests run against the live seeded DB —
keep the container up.
