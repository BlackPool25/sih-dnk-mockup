# Legal & Primary Sources — Downloaded Documents

**Folder:** `06-legal-sources/` · **Updated:** 2026-08-08

All files below were downloaded directly from primary/government sources (L1) unless noted. Text extractions (`*.txt`) accompany PDFs where extracted.

## India Post / DoP / Customs (L1)

| File | What it is | Source | Status |
|---|---|---|---|
| `dnk-sop-wayback.pdf` (+`.txt`) | DNK Customer Portal SOP Ver 1.3 — full step-by-step booking flow, KYC rules, PBE-III/IV selection, validation rules, induction, payment modes, customs clearance, CN22/23 | dnk.cept.gov.in via Wayback Machine (2024 snapshot) | ✅ 38 pages, text extracted (1029 lines) |
| `so-659-e-gazette-2026-02-06.txt` | **S.O. 659(E)** Post Office (Amendment) Regulations 2026 — ITPS Table VIII, full 135-country rate table (first-50g + additional-50g ₹) | Gazette of India Extraordinary, 06-Feb-2026 (archive.org) | ✅ full table extracted |
| `circular-01-2026-customs.pdf` (+`.txt`) | **Circular 01/2026-Customs** (15-Jan-2026) — electronic Drawback/RoDTEP/RoSCTL for postal exports; ICEGATE registration + bank details + E-Sanchit mandates | info.eepcindia.org mirror | ✅ 1 page, text extracted |
| `notification-07-2026-customs.pdf` (+`.txt`) | **Notification 07/2026-Customs (N.T.)** — Postal Export (Electronic Declaration and Processing) Amendment Regulations 2026 — substituted PBE-III & PBE-IV forms with Drawback/RoDTEP/RoSCTL declaration clusters, RITC/DBK fields | ftp.caalley.com/cus26/csnt07-2026.pdf | ✅ text extracted |
| `indiapost-prohibited-items.html` | India Post official prohibited-items list (web page) | indiapost.gov.in | ✅ downloaded |
| `indiapost-international-services.html` | India Post international services overview (ITPS, EMS, letters) | indiapost.gov.in | ✅ downloaded |
| `indiapost-country-list-ireland.pdf` | Ireland country list (Next.js SPA shell — content NOT retrievable via curl; flagged) | indiapost.gov.in | ⚠️ HTML shell only |

## USA (L1)

| File | What it is | Source | Status |
|---|---|---|---|
| `cbp-de-minimis-suspension-factsheet.pdf` (+`.txt`) | **CBP factsheet: Suspension of Duty-Free De Minimis Treatment** (updated 18-Aug-2025) — effective 29-Aug-2025, all sub-$800 parcels dutiable; IEEPA ad-valorem vs specific duty; postal bond requirements; Feb-2026 ad-valorem-only | cbp.gov | ✅ text extracted |
| `cbp-global-guidance-international-mail.html` | CBP Global Guidance for International Mail | cbp.gov | ✅ downloaded |

## UAE (L1)

| File | What it is | Source | Status |
|---|---|---|---|
| `uae-ecommerce-vat-guide.pdf` (+`.txt`) | **UAE FTA E-Commerce VAT Guide** (VATGEC1, 09-Aug-2020) — import VAT 5%, importer obligation, exceptions | tax.gov.ae | ✅ 30 pages, text extracted |
| `pwc-gcc-vat-customs-ecommerce.pdf` | PwC GCC VAT & Customs rules for e-commerce — UAE AED 1,000 de minimis (duty-only), postal parcel channel | pwc.com | ✅ downloaded |

## Verification notes

- DNK portal migrated from `dnk.cept.gov.in` → `app.indiapost.gov.in/customer-selfservice` (Circular 01/2026) — the SOP PDF is the pre-migration v1.3; flows are identical but URLs differ.
- `indiapost-country-list-ireland.pdf` returns a Next.js app shell (JS-rendered); real content requires a browser. Flag for the product truth-table build (O13).
- US duty basis as of research date (24-Jul-2026): **Section 301 10% net-of-MFN** (USTR FRN 23-Jul-2026) — re-verify at build time (O11); it has changed 4× in 14 months.
