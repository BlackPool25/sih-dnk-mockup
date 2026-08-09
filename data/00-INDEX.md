# DNK Export Enablement — Data Pack Master Index

**Purpose:** Complete, organized, machine-usable data for the SIH260113 build — customs, duties, taxes, shipping, documents, HS codes, payments, incentives, lanes.
**Prepared:** 2026-08-08 · **Structure:** 6 top-level folders, 28 data files + 14 downloaded primary legal sources.
**Rule:** every figure is a config flag with source + last-updated timestamp — never a hard-coded number. Estimates are labeled. Mocks are labeled. See `README.md` (folder root) for honesty rules.

---

## 📁 01 — Countries (4 markets × duties+shipping)

### 🇺🇸 USA
| File | Contents |
|---|---|
| [`duties-taxes.md`](01-countries/USA/duties-taxes.md) | Federal regime: Section 301 10% net-of-MFN (24-Jul-2026, 92%), de minimis suspended (every parcel dutiable), Entry Type 13 test, mail informal entry, MPF (mail exempt except EMS), USPS clearance fee $9.35, Section 301 Annex exemptions |
| [`state-sales-tax-table.md`](01-countries/USA/state-sales-tax-table.md) | **All 50 states + DC**: state rate, combined range, economic-nexus threshold (Wayfair), marketplace rules — for the landed-cost engine's destination-state tax |
| [`shipping.md`](01-countries/USA/shipping.md) | ITPS (₹400+35/50g, cap **5 kg** — O10 resolved), EMS (₹865+100/250g L5), Air Parcel, courier comparison, volumetric divisor conflict, transit, USPS fees |

### 🇬🇧 UK
| File | Contents |
|---|---|
| [`duties-taxes.md`](01-countries/UK/duties-taxes.md) | £135 duty-free threshold; **20% VAT on ALL**; ≤£135 seller charges VAT at POS (Overseas Seller VAT); >£135 recipient pays; **India-UK CETA in force 15-Jul-2026** (0% preferential w/ CoO); UK Global Tariff rates for all 8 categories (L1 API) |
| [`shipping.md`](01-countries/UK/shipping.md) | ITPS (₹200+25/50g), EMS (₹865+100/250g L5), transit 4-14 days, courier comparison, volumetric notes |

### 🇦🇪 UAE
| File | Contents |
|---|---|
| [`duties-taxes.md`](01-countries/UAE/duties-taxes.md) | **AED 1,000 duty-ONLY de minimis** (reconciled AED 300 vs 1,000 history); **5% VAT on ALL**; recipient pays at pickup; India-UAE CEPA (in force 1-May-2022, 97% lines zero-duty w/ CoO); 8-category HS table |
| [`shipping.md`](01-countries/UAE/shipping.md) | ITPS (₹185+15/50g, 5 kg cap), EMS conflicting L5, transit 3-8 days, ITPS ~5-7× cheaper than couriers |

### 🇦🇺 Australia
| File | Contents |
|---|---|
| [`duties-taxes.md`](01-countries/Australia/duties-taxes.md) | AUD 1,000 duty-free; GST 10% vendor-collected (LVIG, ≤AUD 1,000); >AUD 1,000 recipient pays; **biosecurity BICON for wood/jute** (real blocker); India-Australia ECTA (0% w/ e-CoO) |
| [`shipping.md`](01-countries/Australia/shipping.md) | ITPS (₹395+45/50g, 2 kg cap), **EMS beats ITPS on AU lane** (exception), transit 5-14 days, biosecurity packaging |

---

## 📁 02 — DNK Documents (the compliance stack)

| File | Contents |
|---|---|
| [`document-stack.md`](02-dnk-documents/document-stack.md) | 13-document matrix: IEC, GSTIN (contested — never mandatory-as-fact), AD Code, ICEGATE+DNK-site bank link, E-Sanchit, UDYAM, EPCH RCMC, invoice+packing list, HS/CTH, CN22/23, CoO, product NOCs, e-BRC. Per-doc: What/Why/Status/Cost/Time/Friction |
| [`forms-pbe/pbe-iii-iv-fields.md`](02-dnk-documents/forms-pbe/pbe-iii-iv-fields.md) | PBE-III vs PBE-IV field-by-field; 2026 additions (RITC/DBK/RoDTEP/RoSCTL/FEMA); 6 declaration clusters; Excel bulk-upload column schema; validation rules; submission flow |
| [`onboarding/onboarding-guide.md`](02-dnk-documents/onboarding/onboarding-guide.md) | 8-step artisan journey: IEC → bank account → AD Code → ICEGATE → DNK portal (`app.indiapost.gov.in`) → KYC → UDYAM/RCMC → E-Sanchit; each step: what/where/cost/time/failure-modes/Sahayak help |

---

## 📁 03 — Product Categories (8 × HS codes + certifications + destination notes)

| Category | Key HS (6-digit) | File |
|---|---|---|
| Handloom scarves/stoles | **6214** (621410 silk, 621490 cotton) | [`category-doc.md`](03-product-categories/handloom-scarves-stoles/category-doc.md) |
| Block-printed textiles | **5208/5209** cotton, **5007** silk, **5210** | [`category-doc.md`](03-product-categories/block-printed-textiles/category-doc.md) |
| Embroidered bags/pouches | **4202.22/4202.32** (textile surface), **6307.90** | [`category-doc.md`](03-product-categories/embroidered-bags-pouches/category-doc.md) |
| Embroidered home textiles | **6304** (furnishing), **6302** (bed linen) | [`category-doc.md`](03-product-categories/embroidered-home-textiles/category-doc.md) |
| Small woodware | **4419/4420/4421** | [`category-doc.md`](03-product-categories/small-woodware/category-doc.md) |
| Imitation/artisan jewellery | **7117** (NOT 7113/7114) | [`category-doc.md`](03-product-categories/imitation-artisan-jewellery/category-doc.md) |
| Small brass/metalware | **7418/7419**, **8306** | [`category-doc.md`](03-product-categories/small-brass-metalware/category-doc.md) |
| Jute products | **5310**, **6305**, **4202** (jute bags) | [`category-doc.md`](03-product-categories/jute-products/category-doc.md) |

**Each category-doc contains:** HS 6-digit + India 8-digit ITC-HS codes · PBE description guidance · USA/UK/UAE/AU duty+VAT treatment · certifications (CITES/Lacey for wood, magnetic-clasp IATA for jewellery, BICON for jute/wood, Handloom Mark/GI for textiles) · shipping-lane fit with typical weights.

---

## 📁 04 — Payments & Incentives

| File | Contents |
|---|---|
| [`payment-rails.md`](04-payments-incentives/payment-rails.md) | Buyer→artisan rails: **Razorpay (full PA-CB**, 135 currencies, INR T+2/T+3, auto eFIRC, 3%/1%), **Wise** (~1.6-1.7%, e-FIRC 3 wd), **PayPal (PA-CB-E in-principle only**, ~7-8%), Etsy/Payoneer (12-15%); Stripe/cross-border-UPI NOT viable; FIRC-sender-mismatch trap; FEMA realisation rules; India Post postage payment modes |
| [`incentives.md`](04-payments-incentives/incentives.md) | The 4 schemes: **IGST refund** (GSTIN-keyed), **e-BRC** (EDPMS auto), **Duty Drawback** (electronic 15-Jan-2026), **RoDTEP/RoSCTL** (e-scrips NOT cash); eligibility/mechanism/docs/timelines/failure-modes; H1 realization-gap reality |
| [`pbe-iii-vs-iv-rules.md`](04-payments-incentives/pbe-iii-vs-iv-rules.md) | PBE-III (e-marketplace w/ electronic payment) vs PBE-IV (other) per Reg 5 Ntf 104/2022; 5 e-commerce columns; manual PBE-I/II legacy; rail-evidence implications |

---

## 📁 05 — ITPS & EMS Lanes

| File | Contents |
|---|---|
| [`itps-full-rate-table-s0659e.md`](05-itps-ems-lanes/itps-full-rate-table-s0659e.md) | **Complete 135-country ITPS rate table** from S.O. 659(E) gazette (L1, first-50g + additional-50g ₹) |
| [`itps-lane.md`](05-itps-ems-lanes/itps-lane.md) | ITPS full doc: what/coverage/rates/caps/volumetric-free/transit/tracking/docs/who-pays-duty |
| [`ems-lane.md`](05-itps-ems-lanes/ems-lane.md) | EMS full doc: 250-g slabs, ~97-108 countries (C11 flagged), volumetric divisor conflict, delay compensation 5%, insurance Schedule IV, BNPL |
| [`lane-comparison.md`](05-itps-ems-lanes/lane-comparison.md) | Decision matrix (bulky-light→ITPS, AU exception, US crossover ~1.3 kg), volumetric blow-up worked example (45%), weight-cap lookup, 4-market cost comparison |

---

## 📁 06 — Legal Sources (downloaded L1 primary docs)

See [`06-legal-sources/README.md`](06-legal-sources/README.md) for the full register. Highlights:

| Document | Type |
|---|---|
| `dnk-sop-wayback.pdf/.txt` | DNK Customer Portal SOP v1.3 — full booking flow (38 pp) |
| `so-659-e-gazette-2026-02-06.txt` | **S.O. 659(E)** — ITPS Table VIII, 135 countries (L1) |
| `circular-01-2026-customs.pdf/.txt` | Electronic Drawback/RoDTEP/RoSCTL + ICEGATE/E-Sanchit mandates |
| `notification-07-2026-customs.pdf/.txt` | PBE-III/IV substituted forms + declaration clusters |
| `cbp-de-minimis-suspension-factsheet.pdf/.txt` | US de minimis suspension (L1) |
| `uae-ecommerce-vat-guide.pdf/.txt` | UAE FTA E-Commerce VAT Guide (L1) |
| `dop-eu-resumption-om.txt` | DoP EU PDDP resumption OM 14-Jul-2026 (L1) |
| `notification-104-2022-taxguru.html` | Postal Export Regs 2022 (PBE-III/IV origin) |

---

## ⚠️ Data freshness flags (re-verify at build)

| Item | Status as of 2026-08-08 | Action |
|---|---|---|
| US duty basis | Section 301 10% net-of-MFN (24-Jul-2026) | **Re-check at build (O11)** — changed 4×/14 mo |
| US ITPS cap | 5 kg (DoP OM 01-Jan-2026) — corpus 2 kg was stale | Use 5 kg, verify |
| EU lane | Open via PDDP 14-Jul-2026; IOSS suspended DE/DK/AT/SE | Never "EU blocked" |
| UK CETA | In force 15-Jul-2026 (0% w/ CoO) | Update any "CETA pending" copy |
| UAE threshold | AED 1,000 duty-only (reinstated 1-Mar-2023) | Never "AED 1,000 = tax-free" |
| EMS rates | Schedule I not public — **all EMS rates L5 estimates** | Flag confidence in UI |
| DNK portal | `app.indiapost.gov.in/customer-selfservice` | Circular 01/2026 migration |

---

*Index generated 2026-08-08 after a 10-agent parallel research run + primary-source downloads. Every leaf file carries source URLs + access dates and obeys the honesty rules in `README.md`.*
