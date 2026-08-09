# DNK Export Enablement — Data Pack

**Purpose:** Machine-usable, organized reference data for the SIH260113 build. Every figure is a **config flag with source + last-updated timestamp** — never a hard-coded number (corpus FR-001).

**Updated:** 2026-08-08 · **Project:** SIH260113 (SIH 2026 internal hackathon)

---

## Folder map

| Folder | Contents |
|---|---|
| `01-countries/USA/` | US federal duties/taxes + **all 50 states sales tax** + shipping rates/lanes |
| `01-countries/UK/` | UK customs duty/VAT regime + shipping rates/lanes |
| `01-countries/UAE/` | UAE customs duty/VAT regime (CEPA) + shipping rates/lanes |
| `01-countries/Australia/` | Australia customs/GST + biosecurity + shipping rates/lanes |
| `02-dnk-documents/` | Full DNK document stack, PBE-III/IV forms field-by-field, artisan onboarding guide |
| `03-product-categories/` | 8 product categories: HS codes, descriptions, destination notes, certifications, lane fit |
| `04-payments-incentives/` | Payment rails (PA-CB), PBE-III vs IV rules, incentive claims (IGST/e-BRC/Drawback/RoDTEP) |
| `05-itps-ems-lanes/` | ITPS + EMS full lane documentation + rate tables + comparison |
| `06-legal-sources/` | Downloaded L1 primary documents (gazettes, circulars, SOP, CBP factsheet, UAE VAT guide) |

## Honesty rules (apply to every file)

1. **Every duty/VAT/rate is a config flag** with source link + last-updated timestamp (FR-001).
2. **Label estimates**: `<5% realization`, `30% savings`, volumetric blow-ups are n=1/unmeasured — never facts (FR-002).
3. **Label mock vs real**: no public API on DNK/ICEGATE/EDPMS — any integration is a labeled mock (FR-003).
4. **Never**: "EU is blocked" (reopened via PDDP 14-Jul-2026), "GSTIN blocks artisans", IOSS-brokering, hard-coded US duty.
5. **Ranges not points** for external figures (1,013 DNKs = Dec-2024 baseline; employment 113L vs 64.66L).

## Data freshness notes (2026-08-08)

- **US duty basis:** Section 301 10% net-of-MFN (since 24-Jul-2026, USTR FRN 23-Jul-2026) — changed 4× in 14 months; **re-verify at build** (O11). ~45% of exports exempt.
- **US ITPS cap:** raised 2 kg → **5 kg** (DoP OM CF-71/17/2025, 01-Jan-2026) — open question O10 resolved.
- **EU lane:** open via **PDDP** since 14-Jul-2026 (sender pays duties at booking); €3 flat duty ≤€150 from 1-Jul-2026; IOSS still suspended for DE/DK/AT/SE.
- **UK CETA:** India-UK CETA **in force since 15-Jul-2026** — preferential 0% duty with CoO (update to corpus).
- **UAE:** AED 1,000 duty-only de minimis (reinstated 1-Mar-2023; amended 3-Aug-2026 for e-commerce); **5% VAT on ALL**.
- **Portal:** migrated `dnk.cept.gov.in` → `app.indiapost.gov.in/customer-selfservice` (Circular 01/2026).

## Source of truth

- Parent research: `../../report.md`, `../../04-synthesis/` (findings, conclusions, requirements)
- Follow-ups: `../../follow-ups/` (order-to-delivery-flow, trade-connect, buyer-acquisition, etc.)
- Primary docs: `06-legal-sources/README.md`
