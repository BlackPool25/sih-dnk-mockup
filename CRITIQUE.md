# CRITIQUE — implementation-plan.md (SIH260113 Voice→Docs mockup)

**Reviewed:** 2026-08-09 · against the full plan (302 lines), the curated `data/` pack, and `follow-ups/03-tech-implementation/findings.md`. **Citation convention:** `file.md:NN` = the file named in the item, line NN — every reference read and verified during review. Fixes only; the plan is not rewritten here.

## VERDICT
The plan is strong exactly where it matters: the keys-only extraction contract (§3.3/§4) and the §1.3 provenance contract are the right spine for this data pack, and deterministic DB lookup kills the hallucination risk the demo exists to prove. The gaps below are real but cheap: one stale demo beat, one missing table, L5 rows at risk of shipping as facts, and infra/contract holes that will bite on build day 1.

## BLOCKING

**B1. Schema omits `state_sales_tax` (and `documents`).**
The §2 table (plan:74-88) lists 8 tables; the 51-row `state-sales-tax-table.md` (rows 22-74) is the most parseable asset in the pack — fixed-width columns, one row per state — and 00-INDEX.md:15 says it exists "for the landed-cost engine's destination-state tax", yet no table consumes it. `findings.md:147` already defines `state_sales_tax` (rate, combined range, nexus logic, marketplace rule) in the source-of-truth inventory. `documents` (findings.md:143) is also absent although §5/§6 render a sample PBE pack.
**Fix:** add `state_sales_tax` + `documents` to the §2 schema and the §1.1 inputs table, and seed the 51 rows with the same provenance mixin (file.md:147 — findings.md; file.md:22 — state-sales-tax-table.md).

**B2. Demo §7 step 5 ships stale copy: "US ITPS cap 2kg vs 5kg — flagged, needs re-verification".**
O10 is resolved: US ITPS cap 5 kg (O10 resolved) — L1 via DoP OM CF-71/17/2025, 01-Jan-2026 (data/README.md:34; USA/shipping.md:57-65; 00-INDEX.md:108). The ITPS rate-table file's own line-147 note ("2 kg for USA/Australia/Canada… O10 open question… verify at build") is stale, and three category docs repeat the dead 2 kg cap (jute-products/category-doc.md:78; small-woodware/category-doc.md:85; small-brass-metalware/category-doc.md:67). Running the demo's "honesty beat" on a resolved question would be a credibility own-goal in front of judges who can check the OM.
**Fix:** replace the beat with a genuinely open flag (EMS L5, C-11) and point the §1.3 rule-check at asserting 5 kg, not re-verifying it; rewrite the stale line-147 note and the three category-doc cap lines (file.md:147 — itps-full-rate-table-s0659e.md).

**B3. EMS rates will be imported as facts though every EMS number is L5-conflicting (C-1..C-4).**
§1.1 maps shipping.md → `country_rates`/`lanes` carrying the working figures (₹865/₹100 US/UK; ₹630/₹155 AU), and §1.3's rule-check has no L5 guard, so convert.py will happily write them as high-confidence rows. The conflict table (ems-lane.md:69-77) shows UK ₹865 vs ₹955 vs ₹1,965, US ₹865 vs ₹1,820, AU ₹630 vs ₹1,125, UAE ₹600–1,400, and ems-lane.md:77 is explicit: "Do NOT ship ₹865 as fact." Schedule I has never been reproduced in any fetched source (ems-lane.md:6; 00-INDEX.md:112).
**Fix:** seed every EMS row with source_level=L5 and is_estimate=true, add a convert-time rule that refuses is_estimate=false on L5 rows, and surface the C-11 warning in every EMS UI row (file.md:77 — ems-lane.md).

**B4. Quote-response shape hardcodes `"is_estimate": false` on volatile US duty rows.**
plan:219 emits the S301_ADD row with `is_estimate: false`; the US duty basis (S.301 10% net-of-MFN) changed 4× in 14 months and is flagged re-verify-at-build O11 (data/README.md:33; 00-INDEX.md:107), and findings.md:158 mandates duty-rate snapshots precisely because config rates change. Shipping that row as "not an estimate" contradicts FR-002, which the pack's honesty rules exist to enforce.
**Fix:** derive is_estimate from the seeded config flag — S301_ADD rows seed true — never a literal in the response builder, and propagate it to the row's `⚠️ estimate` UI label (file.md:219 — implementation-plan.md).

**B5. §1.3's "EVERY record" provenance contract is not applied uniformly in §2.**
plan:45-51 requires source_url/source_level/confidence/is_estimate/effective_from/to/verified_at on every imported record, but `product_categories` (plan:77) and `pbe_field_schemas` (plan:82) list no provenance columns at all, and `hs_codes`/`country_rates` carry only subsets. `pbe_field_schemas` is exactly where it matters most: pbe-iii-iv-fields.md:68 flags its own field names as unverified corpus summaries of Ntf 07/2026.
**Fix:** apply the six-field provenance mixin to every seeded table and extend the fail-on-missing rule (plan:55 currently checks only source_url + confidence) to all six fields (file.md:172 — findings.md).

**B6. Schema cannot represent conflicts and ranges (EMS ₹600–1,400; divisor ÷4000/÷5000/÷6000).**
`lanes` (plan:80) has single slab/divisor/cap columns, but the pack's highest-value data is explicitly conflicted: UAE EMS first-250g ₹600–1,400 (ems-lane.md:59), the three-way divisor conflict (ems-lane.md:86), EMS caps 20/30/35 (ems-lane.md:103). Collapsing these to "one number" at import destroys the honesty structure the pack exists to preserve, and the data pack's own rule (FR-022) treats the divisor as a configurable parameter.
**Fix:** give `lanes` conflict-capable columns (rate_min/rate_max, divisor as a JSON list) and make the quote engine render ranges with the flag, never a single point (file.md:86 — ems-lane.md).

## MAJOR

**M1. §2's entire Docker section is one line — no compose/env/password/volume/healthcheck/port handling.**
plan:71 ("docker compose up -d db — postgres:16-alpine, port 5432, db sih_dnk") is the whole ops spec: no POSTGRES_PASSWORD source (env file? default?), no named volume (data loss on every rebuild), no pg_isready healthcheck (the seed will race a booting DB), no explicit port mapping, no Neon parity note for the demo/deploy path.
**Fix:** ship a complete docker-compose.yml — env-file password, named volume, pg_isready healthcheck, 5432:5432, db `sih_dnk` — as the first artifact of build day 1 (file.md:71 — implementation-plan.md).

**M2. No connection contract (DATABASE_URL).**
The plan names compose and Alembic (plan:71,88) but never defines how the app or alembic env.py resolve the connection string; dev/Neon/demo will drift into hardcoded URLs and opaque failures.
**Fix:** one config module resolving DATABASE_URL (env → .env → `postgresql+psycopg://postgres@localhost:5432/sih_dnk`), consumed by both the SQLAlchemy engine and Alembic (file.md:88 — implementation-plan.md).

**M3. No model tool-access boundary (context-poisoning risk).**
The keys-only contract (plan:191, 209-212) is right for today, but there is no written boundary for the moment Gemini gains tool access — "helpfully" stuffing the 135-row ITPS table or the 51 tax rows into the prompt would poison extraction exactly where the demo must prove it cannot.
**Fix:** write the boundary as a contract — the model receives only Shipment keys; all DB reads go through a read-only service; add a prompt-poison regression test to /api/extract — before Path B (audio mode) lands (file.md:191 — implementation-plan.md).

**M4. Prose-heavy files mapped to `config_flags` with no extraction design.**
plan:27-29 sends document-stack.md (13-doc matrix, 00-INDEX.md:42), onboarding-guide.md (8-step journey, 00-INDEX.md:44), payment-rails.md (00-INDEX.md:69), incentives.md (00-INDEX.md:70), pbe-iii-vs-iv-rules.md to `config_flags`, but these are prose decision documents with failure-modes, not tabular rates — and findings.md:171 mandates human-verify every record, a step the plan's verification pass (plan:53-57) has no slot for.
**Fix:** define a per-file flag_key naming convention plus an explicit human-review checklist step in convert.py (every flag_key logged with reviewer + verified_at) before config_flags is seeded (file.md:171 — findings.md).

**M5. No ISO2 mapping plan for ITPS country names.**
`lanes.country_iso2` (plan:60,80) is the join key to `country_rates`, but the gazette table carries display names: "Cote d'Ivoire" (itps:41), "Great Britain (UK)" (itps:62), "Türkiye" (itps:134) — a naive slug will silently fail to join and drop rows.
**Fix:** add an audited name→ISO2 mapping (diacritics, aliases, parentheticals) as the first step of convert.py, failing loudly with a verification-report entry on any unmapped name (file.md:134 — itps-full-rate-table-s0659e.md).

**M6. No row-count verification gates.**
plan:57 reports "converted count per table" but asserts nothing; the pack's expected counts are known — 135 ITPS rows (00-INDEX.md:79), 51 tax rows (state-sales-tax-table.md:22-74), 8 category docs (00-INDEX.md:48), 4 country packs — so a truncated parse or OCR skip imports silently.
**Fix:** assert 135/51/8/4 in the verification pass and fail the conversion on any mismatch, not just log it (file.md:57 — implementation-plan.md).

**M7. Postage rows conflict across category docs — seed must preserve per-doc provenance, never average.**
jute-products/category-doc.md:77 says 300 g → USA ₹505, which is the formula value for 200 g (USA/shipping.md:49) — off by one 50-g slab; imitation-artisan-jewellery/category-doc.md:80 says 200 g → USA ₹470, the formula value for 150 g (USA/shipping.md:47); embroidered-home-textiles/category-doc.md:102 (300 g → ₹575) and embroidered-bags-pouches/category-doc.md:98 (100 g → ₹435) are formula-correct. Averaging or "trusting the category doc" would silently corrupt the lane cost curve the demo quotes.
**Fix:** seed each postage row with its own source_url (category-doc.md:NN), and have verification flag cross-doc divergence (₹575 vs ₹505 at 300 g) as a warning rather than resolving it by averaging (file.md:77 — jute-products/category-doc.md).

**M8. No documents/render contract for the sample PBE pack.**
§5/§6 render a sample PBE (plan:249,291) but the schema has no `documents` table — findings.md:143 defines one (structured_json, checksum, supersedes_doc_id, immutable versioning) — and no render spec; findings.md:182-185 mandates WeasyPrint (Pango/HarfBuzz for Devanagari) + Noto fonts + render-once-immutable.
**Fix:** add `documents` to the schema and adopt the render-once-immutable + checksum contract, with the Noto Devanagari install step in the setup docs (file.md:143 — findings.md).

## MINOR

**m1. Three different confidence-glyph systems to normalize.** Markdown 🟢🟡🔴 (plan:48) vs source_level L1–L5 (plan:47) vs high/moderate/low confidence (plan:48) vs inline "Est." tags — map them to one canonical enum in convert.py so the verification report and UI speak one language (file.md:48 — implementation-plan.md).

**m2. EMS Schedule I was never published.** The plan's examples never show an EMS row (plan:220,247) even though §1.1 imports EMS figures from shipping.md; surfacing one L5-flagged EMS row (₹865 vs ₹1,820) would be the demo's honest "confidence system in action" beat after the stale cap beat is removed (file.md:24 — ems-lane.md).

**m3. USD/EMS cap C16 unresolved.** Air Parcel 20 kg general is resolved (USA/shipping.md:139), but EMS "20 kg general, destination governs" with 30/35 kg claims unverified (ems-lane.md:103,106) cannot live in a single weight_cap_g integer; store the cap as (value, basis, note) and keep the counter-verify flag (file.md:103 — ems-lane.md).
