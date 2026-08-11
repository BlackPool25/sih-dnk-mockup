# DNK Mockup — Verification Report

**Generated:** 2026-08-11 04:59:00 UTC · **Exit code:** 0 = ALL PASS, non-zero = ANY FAIL

## Gates

| Gate | Result | Actual | Expected |
|---|---|---|---|
| G1 lanes ITPS | **PASS** | 135 | 135 |
| G2 lanes EMS | **PASS** | 4 | 4 |
| G3 EMS conflicts IS NULL | **PASS** | 0 of 4 | 0 |
| G3 EMS is_estimate=false | **PASS** | 0 of 4 | 0 (all EMS rows must be estimates, L5) |
| G4 state_sales_tax | **PASS** | 51 | 51 |
| G5 product_categories | **PASS** | 8 | 8 |
| G6 every category >= 1 hs_code | **PASS** | min=7 (imitation-artisan-jewellery) | >= 1 per category |
| G6 total hs_codes | **PASS** | 99 | >= 24 |
| G7 config_flags | **PASS** | 86 | >= 40 |
| G8 pbe_field_schemas | **PASS** | 116 | >= 30 |
| G9 ITPS NULL country_iso2 | **PASS** | 0 | 0 |
| G10 lanes source_url non-empty | **PASS** | 0 empty of 139 | 0 empty |
| G10 product_categories source_url non-empty | **PASS** | 0 empty of 8 | 0 empty |
| G10 hs_codes source_url non-empty | **PASS** | 0 empty of 99 | 0 empty |
| G10 country_rates source_url non-empty | **PASS** | 0 empty of 88 | 0 empty |
| G10 state_sales_tax source_url non-empty | **PASS** | 0 empty of 51 | 0 empty |
| G10 config_flags source_url non-empty | **PASS** | 0 empty of 86 | 0 empty |
| G10 pbe_field_schemas source_url non-empty | **PASS** | 0 empty of 116 | 0 empty |
| G11 US ITPS first_slab_rate_minor | **PASS** | 40000 | 40000 |
| G11 GB ITPS first_slab_rate_minor | **PASS** | 20000 | 20000 |
| G11 AE ITPS first_slab_rate_minor | **PASS** | 18500 | 18500 |
| G11 AU ITPS first_slab_rate_minor | **PASS** | 39500 | 39500 |
| G11 US ITPS addl_slab_rate_minor | **PASS** | 3500 | 3500 |
| G11 US ITPS weight_cap_g | **PASS** | 5000 | 5000 |
| G11 US ITPS transit 18..28 days | **PASS** | 18..28 | 18..28 |
| G11 flag us.usps_clearance_fee_minor present | **PASS** | present | present |
| G11 flag us.s301.rate_pct present | **PASS** | present | present |
| G12 psql auth SELECT 1 | **PASS** | exit 0 | exit 0 |
| G13 filling_rules seeded | **PASS** | 8 | 8 |

**29/29 gates PASS** — ALL GATES PASS

## Conflicts log (C-1..C-13 + data-quality flags)

### C-1..C-4 — EMS conflicting published figures (verbatim from `lanes.conflicts`)

- **C-3 AE EMS** — confidence=low, is_estimate=True; working figure ₹600 + ₹40/250 g (L5). Conflicting published figures verbatim from `lanes.conflicts`:
  - `alternatives`: [{"addl": 5000, "first": 89500, "source": "findpincode"}, {"addl": 5000, "first": 124000, "source": "indspeedpost"}, {"addl": 6000, "first": 60000, "source": "shiprocket"}, {"addl": 4000, "first": 140000, "source": "clickpost"}]
    - findpincode: first 250 g ₹895 + ₹50/250 g
    - indspeedpost: first 250 g ₹1240 + ₹50/250 g
    - shiprocket: first 250 g ₹600 + ₹60/250 g
    - clickpost: first 250 g ₹1400 + ₹40/250 g
- **C-4 AU EMS** — confidence=low, is_estimate=True; working figure ₹630 + ₹155/250 g (L5). Conflicting published figures verbatim from `lanes.conflicts`:
  - `alternatives`: [{"addl": 23000, "first": 112500, "source": "clickpost"}]
    - clickpost: first 250 g ₹1125 + ₹230/250 g
- **C-2 GB EMS** — confidence=low, is_estimate=True; working figure ₹865 + ₹100/250 g (L5). Conflicting published figures verbatim from `lanes.conflicts`:
  - `alternatives`: [{"addl": 10500, "first": 95500, "source": "findpincode"}, {"addl": 9000, "first": 196500, "source": "clickpost"}]
    - findpincode: first 250 g ₹955 + ₹105/250 g
    - clickpost: first 250 g ₹1965 + ₹90/250 g
- **C-1 US EMS** — confidence=low, is_estimate=True; working figure ₹865 + ₹100/250 g (L5). Conflicting published figures verbatim from `lanes.conflicts`:
  - `alternatives`: [{"addl": 15000, "first": 182000, "source": "clickpost"}, {"addl": null, "first": 58500, "source": "findpincode"}]
    - clickpost: first 250 g ₹1820 + ₹150/250 g
    - findpincode: first 250 g ₹585 (addl n/a)

### C-5 MPF wording contradiction — INVERTED wording between the two US files

- data/01-countries/USA/duties-taxes.md §4.2: *"EMS (Express Mail Service) parcels from India are subject to MPF"* (header: "MPF — **exempt for postal mail, EXCEPT Inbound EMS**").
- data/01-countries/USA/shipping.md §9:232: *"Merchandise Processing Fee (MPF) | **Exempt for inbound EMS** (\"Inbound Express Mail service\" / \"Inbound EMS\")"*.
- Both cite the same CBP E-Commerce FAQ yet reach inverted conclusions. DB flag `us.mpf.postal` = "exempt_itps_liable_ems" records the duties-taxes.md reading; resolve per item at build.

### C-6/C-7 US ITPS cap — RESOLVED 5 kg (overrides the stale table-file note)

- DoP OM CF-71/17/2025-CF-DOP, 01-Jan-2026 (L1): *"maximum permissible weight limit for the United States of America under the ITPS mail category has also been increased from 2 kg to 5 kg"* (USA shipping.md §1.3; data/README.md freshness note; Shiprocket 21-Jan-2026 corroborates).
- Overrides the STALE note at data/05-itps-ems-lanes/itps-full-rate-table-s0659e.md line 147: *"Weight caps: 2 kg for USA/Australia/Canada (top markets); 5 kg for ~29 destinations; per-table otherwise. O10 open question: US cap may have risen to 5 kg (Shiprocket Jan-2026 note) — verify at build."*
- DB: US ITPS weight_cap_g = 5000; AU/CA/GB = 2000; AE/SG = 5000 (convert.py ITPS_WEIGHT_CAP_G).

### C-8 UK EMS 1 kg upper bound untraceable

- data/01-countries/UK/duties-taxes.md (worked example): *"postage EMS 1 kg ≈ ₹1,165–₹2,275 (see shipping.md)"*.
- UK shipping.md computes 1 kg EMS = ₹1,165 and 2 kg = ₹2,665 — the ₹2,275 upper bound matches NO arithmetic in either file. Untraceable; treat as a typo until re-checked.

### C-9 AU EMS confidence-tier conflict

- Working figure ₹630 + ₹155/250 g stored from PO Rules §225 (statutory mirror — L1-text) and indiapost.org (L5).
- ClickPost 2026 quotes ₹1,125 + ₹230/250 g (AU shipping.md §2.1) — 1.8× higher; no authoritative Schedule I public (C11). Stored confidence=low, is_estimate=true.

### C-10 USPS $9.35 clearance fee — L1 partial

- Federal Register 91:603, 8-Jan-2026 (L1) sets the **competitive** customs clearance & delivery fee at $9.35 per dutiable item (USA shipping.md §9).
- The amount applicable to the postal-inbound class (India Post parcels) is NOT L1-confirmed — shipping.md §9: "Whether the $9.35 or the older ~$5 level applies to a given India Post parcel is not L1-confirmed for the postal-inbound class." DB flag `us.usps_clearance_fee_minor` = 935, confidence=high (fee level flagged at build).

### C-11 volumetric divisor — no official international figure

- ÷6000 (courierbook Oct-2025; shipmozo; singhxpress) · ÷5000 (clickpost; courierbook Jan-2026 "UPU standard alignment"; costcalculator) · ÷4000 (smartfree) — corpus F-H5-c, 82% High no-official-figure (ems-lane.md §5; USA shipping.md §4).
- Domestic reference ÷5000 (DoP OM 11-Dec-2025, L1) sometimes misapplied to international. DB flag `volumetric.divisors` = [4000, 5000, 6000], confidence=unverified, is_estimate=true; EMS lanes divisor=NULL.

### C-12 EMS weight caps 20/30/35 — unresolved claims

- Corpus C16 RESOLVED: Air Parcel 20 kg general (destination governs).
- 30 kg claims (indiapost.org 2026; ClickPost "up to 30 kg") vs legacy official table 31.5 kg for a few (Barbados, Kenya, Macao, Nepal, Romania, USA, Vietnam) and 20 kg for some (Bahrain, Belarus, Iceland, Iran, Israel, Mexico, Mongolia, Nauru, Pakistan, Poland, Spain, Taiwan, Thailand, Tunisia, Ukraine, Yemen) (ems-lane.md §6).
- No authoritative per-market EMS ceiling fetched → EMS weight_cap_g = NULL (never guessed).

### C-13 counter practice unverified

- Whether India Post counters actually apply volumetric to bulky crafts is UNVERIFIED (corpus 60% Moderate; field instrument O4 settles it).
- ClickPost (Jul-2026) counter-claim: "India Post EMS charges on actual weight only…" — a direct contradiction of PO Regs 2024 clause (r) (ems-lane.md §5). EMS lanes divisor=NULL until verified.

### Postage-row data-quality flags (category docs vs gazette Table VIII)

- jute-products/category-doc.md: "300 g → USA ₹505" — the gazette formula value at **200 g** (₹400 + 3×₹35 = ₹505); the 300 g row should be ₹575. Row mislabelled one slab (jute 300 g ≈ formula-200 g).
- imitation-artisan-jewellery/category-doc.md: "200 g → USA ₹470" — the formula value at **150 g**; correct 200 g = ₹505. Row mislabelled one slab down (jewellery 200 g).
- Both docs' UK columns shift the same way (jewellery UK 200 g ₹250 vs formula ₹275). Cosmetic examples only — the gazette formula in the DB is the source of truth.

### IEC application fee ₹500-vs-free

- data/02-dnk-documents/onboarding/onboarding-guide.md: "₹500 application fee; e-Sign via Aadhaar (free) or DSC (vendor-priced)".
- data/02-dnk-documents/document-stack.md (flags): "IEC fee 'free vs ₹500' (both appear in official sources)". Both values logged; no DB flag pinned (council-set fee, re-check at build).

### Brass 8306.29 MFN Free-vs-not

- small-brass-metalware/category-doc.md §3.4: "8306.29.00.00 other statuettes = Free (MFN)" — htshub shows Free; wove shows only China S.301 10%.
- Same section: "The 8306.29 MFN = Free result is worth a build-time re-check (two aggregators conflict on effective vs statutory)." Logged, not shipped as fact.

### GSTIN hard-block H2 — contested

- On paper no hard-block (70% Moderate): DGFT issues IEC without GSTIN ("GSTIN … if applicable", IEC Manual v2.0); PBE forms read "GSTIN or as applicable"; DNK SOP KYC Note-1 allows booking with IEC alone (document-stack.md).
- BUT the DNK SOP business-details table marks GSTIN "Mandatory", and whether the migrated portal (app.indiapost.gov.in/customer-selfservice) honours the escape hatch is UNTESTED — if it diverges, the hard-block branch is restored (findings H2).

### FEMA 9-vs-15 month realisation

- `fema.realisation_months` = 9: FEMA (Export of Goods and Services) (First Amendment) Regulations 2026, 5-Jun-2026 (taxguru).
- `fema.relaxation_months` = 15: RBI press release 31-Mar-2026 relaxation window. Both live flags coexist; the 15-month window is the relaxation, not the base rule.

### Wise e-FIRC $2-vs-$2.50

- payment-rails.md §2.4: "~US$2–2.50 e-FIRC fee" vs "the equivalent of US$2 in the requested currency per transfer (US$2.50 for USD)".
- DB flag `wise.efirc_fee_minor` = 200 ($2.00, non-USD corridors); USD transfers cost $2.50 — difference logged, not averaged.

### Magnet threshold 4.6 m-vs-4.5 m

- jewellery/category-doc.md §4.2: "≤ 0.418 A/m (≈0.00525 gauss) **at 4.6 m**" (radialmagnet, IATA PI 953) vs "0.00525 gauss **at 4.5 m**" (FAA PackSafe) — the same field limit quoted at two measurement distances.
- Neither blocks a magnet-free parcel; both cited in the doc; flagged as an open measurement discrepancy.

## Flagged rows (confidence=unverified OR is_estimate=true)

- lanes.EMS.US — confidence=low, is_estimate=True
- lanes.EMS.GB — confidence=low, is_estimate=True
- lanes.EMS.AE — confidence=low, is_estimate=True
- lanes.EMS.AU — confidence=low, is_estimate=True
- country_rates.US.S301 (hs6=—) — confidence=unverified, is_estimate=False
- country_rates.US.S301 (hs6=—) — confidence=unverified, is_estimate=False
- country_rates.US.S301 (hs6=—) — confidence=unverified, is_estimate=False
- country_rates.US.S301 (hs6=—) — confidence=unverified, is_estimate=False
- config_flags.ems.us.first250_minor — confidence=low, is_estimate=True
- config_flags.ems.us.addl250_minor — confidence=low, is_estimate=True
- config_flags.ems.uk.first250_minor — confidence=low, is_estimate=True
- config_flags.ems.uk.addl250_minor — confidence=low, is_estimate=True
- config_flags.ems.au.first250_minor — confidence=low, is_estimate=True
- config_flags.ems.au.addl250_minor — confidence=low, is_estimate=True
- config_flags.sdr.fx_minor_per_sdr — confidence=low, is_estimate=True
- config_flags.kyc.declared_value_minor — confidence=low, is_estimate=True
- config_flags.volumetric.divisors — confidence=unverified, is_estimate=True
- config_flags.itps.transit.us_days — confidence=low, is_estimate=True
- config_flags.itps.transit.uk_days — confidence=low, is_estimate=True
- config_flags.itps.transit.uae_days — confidence=low, is_estimate=True
- config_flags.itps.transit.au_days — confidence=low, is_estimate=True
- config_flags.ems.transit.us_days — confidence=low, is_estimate=True
- config_flags.ems.transit.uk_days — confidence=low, is_estimate=True
- config_flags.ems.transit.uae_days — confidence=low, is_estimate=True
- config_flags.ems.transit.au_days — confidence=low, is_estimate=True
- config_flags.wise.conversion_fee_range_pct — confidence=low, is_estimate=True
- config_flags.paypal.allin_fee_range_pct — confidence=low, is_estimate=True
- config_flags.etsy.payoneer_total_fee_range_pct — confidence=low, is_estimate=True
- config_flags.rodtep.scrip_discount_range_pct — confidence=low, is_estimate=True
