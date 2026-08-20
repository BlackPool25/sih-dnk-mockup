# DB Consistency Audit — sih_dnk (shared Postgres 127.0.0.1:5433)

**Date:** 2026-08-19  
**Scope:** 3 SQLAlchemy bases + 1 stateless service sharing one Postgres DB (`sih_dnk`).  
**Audited at:** `alembic_version=c9e8f1a2b3c4`, `auth_alembic_version=dd7cbe9d8ad4`, `core_alembic_version=2ae521447228`.

---

## 1. Ownership Matrix (single writer per table)

| Table | Owner | Base / Alembic | How it is migrated | Statuses / notes |
|---|---|---|---|---|
| `users`, `refresh_tokens` | **auth** | `auth/app/models` + `auth_alembic_version` | Alembic (auth) | `users.id UUID PK`, `user_role` enum. FK target for orders/seller_profiles. |
| `orders`, `line_items`, `documents` | **validation-engine** | `validation-engine/app/models` + `alembic_version` | Alembic (validation-engine) — single source of truth post-`8382b870f54f` unification | `orders.status` lifecycle enum (`quote_accepted→refunded`), `validation_state`, `last_report JSONB`, `qr_token_jti`. New: `pricing_breakdown JSONB`, `parcels JSONB`, `qr_tokens JSONB`, `documents.parcel_id`. `line_items` normalized FK `orders.id CASCADE`. |
| `seller_profiles`, `profile_documents` | **backend-core** | `backend-core/app/models` + `core_alembic_version` (`storage.db` async) | Alembic (backend-core) via `storage` | `seller_profiles` async engine, encrypted fields `*_encrypted JSONB`, FK `users.id CASCADE`. No order tables — unified orders live in validation-engine. |
| `shipments`, `tracking_events` | **tracking-api** | `tracking-api/app/models` + **new** `tracking-api/alembic` (`5f6d15dbe3f4`) | **Alembic** (tracking-api) — was `Base.metadata.create_all` anti-pattern, now removed | `shipments` holds `tracking_number unique`, `carrier`, `status`. New: `order_id VARCHAR(64) nullable`, `parcel_id VARCHAR(64) nullable` (logical linkage, no hard FK to avoid cross-service coupling). |
| `lanes`, `product_categories`, `hs_codes`, `country_rates`, `config_flags`, `state_sales_tax`, `pbe_field_schemas`, `filling_rules`, `lookups`, `transcripts` | **validation-engine** (seeded config) | `validation-engine/app/models` | Alembic + `app.services.seed` (TRUNCATE+insert, idempotent) | Provenance mixin (`source_url`, `source_level`, `confidence`, `is_estimate`, `effective_from/to`, `verified_at`) on all config tables. Pricing-engine reads but does not own. |
| — | **pricing-engine** | stateless | **No tables** | Owns pricing math + Razorpay flow, reads `lanes`/`country_rates` via API, never creates tables. Must stay stateless. |

**Read-only cross-service tables:** validation-engine temporarily mirrors `users` via `app/models/user_ref.py` (read-only FK target, no DDL ownership). tracking-api does NOT declare `orders` ORM; it stores `shipments.order_id` as opaque string to avoid coupling. pricing-engine declares mirrored `Base` for price-reads but never calls `create_all` against the shared DB in production.

---

## 2. Divergences Found (pre-migration)

### D1 — Missing parcel/pricing linkage on orders (validation-engine)
- `orders` lacked `pricing_breakdown`, `parcels`, `qr_tokens`. Business now needs per-order pricing detail + split-parcel array + per-parcel QR JTIs. Existing code hardcoded single-parcel ITPS. **Fix:** `0466db8fdaf5` adds three nullable JSONB columns to `orders` (`keep qr_token_jti` for compat).
- `documents` lacked `parcel_id` — single pack per order only. **Fix:** `0466db8fdaf5` adds `documents.parcel_id VARCHAR(64) nullable` + index `ix_documents_parcel_id`.

### D2 — tracking-api `Base.metadata.create_all` anti-pattern
- `tracking-api/main.py` called `Base.metadata.create_all(bind=engine)` on import — races `alembic_version`, bypasses migrations, and can silently create partial schemas. Verified in `app/models.py` + `app/database.py` (sync engine, no Alembic before this audit). **Fix:** removed `create_all` from `main.py`; introduced `tracking-api/alembic` (`env.py`, `alembic.ini`, `5f6d15dbe3f4_add_order_parcel_to_shipments`); `shipments.order_id/parcel_id` added via migration with FK-as-logical-link.

### D3 — tracking-api shipments missing order linkage
- `shipments` had only `tracking_number/carrier/status`; no nullable `order_id/parcel_id` to tie shipments to validation-engine orders/parcels. **Fix:** migration adds both nullable indexed VARCHAR(64) columns (idempotent inspector check; backfill leaves existing row `NULL`).

### D4 — Cross-service `users` FK shape drift risk
- `validation-engine/app/models/user_ref.py` declares `users` with `String(255)` email, `String(255)` password_hash; live `public.users` (auth) is `varchar(320)` email, `varchar(128)` password_hash, `user_role` enum, `is_active bool default true`. Drift is harmless (read-only FK target, never DDL), but noted for guard: validation-engine must **never** emit DDL for `users` — enforce via `alembic/env.py` exclude or `include_object` filter if autogenerate is used.

### D5 — pricing-engine stateless invariant at risk
- `pricing-engine/app/models.py` declares its own `Base(DeclarativeBase)` + mirrored config models (`ProductCategory`, `HsCode`, `CountryRate`, `Lane`) with `JsonType = JSONB().with_variant(JSON(), "sqlite")`. No `create_all` against shared DB observed (currently placeholder), but `Base` divergence could tempt a future `create_all`. **Guard:** pricing-engine must stay read-only; forbid `create_all` / `alembic upgrade` against shared `sih_dnk` from that service.

### D6 — Multiple Alembic version tables on one DB
- `alembic_version` (validation-engine), `auth_alembic_version`, `core_alembic_version` all coexist on `public` schema. tracking-api now adds its versioning to `alembic_version` would collide; **Fix:** tracking-api Alembic uses default `alembic_version` is collision — **recommendation:** rename tracking-api version table to `tracking_alembic_version` via `version_table = tracking_alembic_version` in `tracking-api/alembic.ini` (see Guard R1). Interim: migration guards ensure idempotency even if version table collides; operators must run each service's `alembic upgrade head` from its own directory.

### D7 — `orders.line_items` vs backend-core legacy `orders.line_items JSONB`
- Unified in `8382b870f54f` (JSONB unfolded to `line_items` table before dropping). No residual divergence; downgrade is lossy by design — documented.

---

## 3. Post-Migration Schema (verified 2026-08-19)

```
orders (validation-engine, via alembic 0466db8fdaf5)
  id uuid PK, status order_status, validation_state, destination_country varchar(64),
  value_minor int, currency varchar(3) default INR, consignee varchar(256),
  net_weight_g int, gross_weight_g int, article_id varchar, iec varchar(16),
  gstin varchar(16), ad_code varchar(16), bank_account varchar(32), bank_name varchar(128),
  ifsc varchar(16), quote_id varchar(64), exporter_name varchar(256),
  exporter_address varchar(512), state_code varchar(2),
  seller_id uuid FK users.id, buyer_id uuid FK users.id,
  qr_token_jti varchar(64) nullable (compat),
  pricing_breakdown jsonb nullable, parcels jsonb nullable, qr_tokens jsonb nullable,
  version int default 1, last_report jsonb nullable,
  created_at timestamptz, updated_at timestamptz

documents
  id serial PK, doc_type varchar(32), version int, checksum varchar(64),
  structured_json jsonb, file_path varchar, order_id uuid FK orders.id nullable,
  supersedes_doc_id int FK documents.id nullable, parcel_id varchar(64) nullable,
  created_at timestamptz
  index ix_documents_parcel_id (parcel_id)

shipments (tracking-api, via 5f6d15dbe3f4)
  id serial PK, tracking_number varchar unique indexed, carrier varchar,
  status varchar default 'Booked', order_id varchar(64) nullable indexed,
  parcel_id varchar(64) nullable indexed, created_at timestamptz, updated_at timestamptz
```

---

## 4. Guard Recommendations (enforce in CI)

**R1 — One writer per table (Alembic ownership):**
- validation-engine owns DDL for `orders/line_items/documents` + config tables → `alembic_version`.
- auth owns `users/refresh_tokens` → `auth_alembic_version`.
- backend-core owns `seller_profiles/profile_documents` → `core_alembic_version`.
- tracking-api owns `shipments/tracking_events` → **use `tracking_alembic_version`** (set `version_table = tracking_alembic_version` in `tracking-api/alembic.ini`) to avoid colliding with validation-engine's `alembic_version`. Add to CI.

**R2 — Forbid `Base.metadata.create_all` on shared DB:**
- Grep gate in CI: `grep -R "create_all" --include="*.py" tracking-api/ pricing-engine/ backend-core/ validation-engine/app/main.py` must be empty. The only allowed `create_all` is in tests with `sqlite`/`:memory:`. tracking-api fixed in this PR (removed from `main.py`).

**R3 — Autogenerate guard for `users` mirror:**
- validation-engine `alembic/env.py` should set `include_object` to skip `users` (auth-owned). Example:
  ```python
  def include_object(obj, name, type_, reflected, compare_to):
      if type_ == "table" and name == "users":
          return False
      return True
  ```

**R4 — pricing-engine stays stateless:**
- CI check: `gil grep -R "create_engine.*DATABASE_URL" pricing-engine/` should show no `Base.metadata.create_all` / `alembic upgrade` against `sih_dnk`. Pricing-engine may keep its `app/models.py` for type hints/tests against sqlite, but never migrates the shared DB.

**R5 — Migration idempotency & downgrade tests:**
- Run `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` in CI for validation-engine and tracking-api. The two new migrations are idempotent via inspector and safe to rerun.

**R6 — Naming convention:**
- Use `parcel_id` (string, `varchar(64)`) canonically on both `documents.parcel_id` and `shipments.parcel_id`. If an integer index is preferred elsewhere, store as stringified index in same column — do not add `parcel_index` as a second column.

---

## 5. Verification (what to run)

```bash
# validation-engine
set -a && . ./.env && set +a
uv run --project validation-engine alembic upgrade head
PGPASSWORD="$DB_PASSWORD" psql -h 127.0.0.1 -p 5433 -U sih_dnk -d sih_dnk -c "\d orders"   # expect pricing_breakdown/parcels/qr_tokens
PGPASSWORD="$DB_PASSWORD" psql -h 127.0.0.1 -p 5433 -U sih_dnk -d sih_dnk -c "\d documents" # expect parcel_id + ix_documents_parcel_id

# tracking-api
uv run --project tracking-api alembic upgrade head
PGPASSWORD="$DB_PASSWORD" psql -h 127.0.0.1 -p 5433 -U sih_dnk -d sih_dnk -c "\d shipments" # expect order_id/parcel_id

# full verification script (covers both + downgrade smoke):
python scripts/verify_db_consistency.py

# tests
uv run --project validation-engine pytest -q
```

---

## 7. Weight Caps Update (c9e8f1a2b3c4 — 2026-08-19)

**Provenance:** S.O. 659(E) Gazette of India 06-Feb-2026 (L1) + DoP OM CF-71/17/2025-CF-DOP 01-Jan-2026 raising USA to 5kg; EMS Schedule I (L5 estimate, flagged).

| Lane | US | GB | AE | AU | volume_free | divisor |
|------|----|----|----|----|-------------|---------|
| ITPS | 5000 | 5000 | 5000 | 5000 | TRUE | NULL |
| EMS | 31500 | 30000 | 30000 | 20000 | FALSE | 5000 |

- ITPS chargeable = actual weight (volume_free TRUE, no divisor); cap enforced on actual_weight_g.
- EMS chargeable = max(actual, volumetric) with divisor 5000 (volumetric = L×W×H/5000×1000); cap enforced on chargeable_weight_g.
- Optimizer: candidate generation filters via weight_cap_g — parcels exceeding cap are infeasible and force split via max_parcels.
- Tests pin borders: 5000 feasible/5001 infeasible ITPS; 31500/31501 US EMS, 30000/30001 GB/AE, 20000/20001 AU EMS; 6kg USA split 5+1 or EMS; 21kg AU EMS infeasible.

## 6. Files Changed in This Audit

- `validation-engine/alembic/versions/0466db8fdaf5_pricing_parcel_qr.py` — idempotent upgrade/downgrade for orders+documents.
- `validation-engine/app/models/order.py` — added `pricing_breakdown/parcels/qr_tokens` JSONB.
- `validation-engine/app/models/documents.py` — added `parcel_id`.
- `validation-engine/app/schemas/order.py` — added optional `pricing_breakdown/parcels/qr_tokens/qr_token_jti` to `OrderPayload`.
- `tracking-api/app/models.py` — added `shipments.order_id/parcel_id` nullable indexed.
- `tracking-api/main.py` — removed `Base.metadata.create_all` anti-pattern.
- `tracking-api/alembic/*` — new Alembic project (`env.py`, `alembic.ini`, `5f6d15dbe3f4_add_order_parcel_to_shipments.py`).
- `scripts/verify_db_consistency.py` — verification script.
