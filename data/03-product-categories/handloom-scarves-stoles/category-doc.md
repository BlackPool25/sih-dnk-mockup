# Category Doc — Handloom Scarves & Stoles

**DNK export-enablement · SIH260113 · prepared 2026-08-08**
**Scope:** handloom-woven scarves, stoles, shawls, mufflers, odhanis (cotton / silk / wool / man-made), made-to-order artisan goods.
**Confidence legend:** 🟢 High 80-95% · 🟡 Moderate 60-80% · 🔴 Low 40-60% · ⚠️ Flagged/verify at build.
**Build rule (from report §4.3):** every duty/VAT/postage number below is a **snapshot** — land it in the landed-cost engine as a config flag with source link + last-updated timestamp, never a hard-coded constant.

---

## 1. HS / CTH Classification

### 6-digit HS: **6214** — Shawls, scarves, mufflers, mantillas, veils and the like (NOT knitted/crocheted) 🟢

The 6-digit heading is stable and unambiguous for non-knitted scarves/stoles. Two classification traps:

- **Square scarves ≤ 60 cm on any side → HS 6213** (handkerchiefs), not 6214 (UK tariff note + WCO note confirm). Block-printed square bandanas/neckerchiefs under 60 cm must use **6213**. 🟢
- **Knitted/crocheted scarves → Chapter 61** (6117), not 6214. Most handloom scarves are woven → 6214. 🟢

### Likely 8-digit ITC-HS India codes (use in PBE piece details)

| ITC-HS 8-digit | Description | Fit for made-to-order artisan goods |
|---|---|---|
| **6214 10 30** | Scarves of silk, handloom ("Of handloom") | 🟢 Silk handloom scarves/stoles — HEPC's designated handloom code; prefer over generic silk lines |
| 6214 10 10 | Of silk: scarves of silk ≤ 60 cm | 🟡 silk scarf squares ≤60 cm |
| 6214 10 20 | Of silk: shawls/scarves > 60 cm | 🟡 silk stoles/dupattas |
| 6214 10 90 | Of silk: other | 🟡 silk mix/stole not matching above |
| 6214 20 10 / 20 / 30 / 90 | Of wool: shawls / scarves / mufflers / other | 🟢 wool & pashmina shawls/stoles |
| 6214 30 00 | Of synthetic fibres | 🟢 man-made (poly/acrylic) stoles |
| 6214 40 00 | Of artificial fibres | 🟡 viscose/rayon stoles |
| 6214 90 40 | Odhani, cotton: scarves, cotton | 🟡 cotton scarf |
| 6214 90 50 | Odhani, cotton: shawls, mufflers and the like, of cotton | 🟡 cotton stole/shawl |
| 6214 90 90 | Odhani, cotton: other | 🟡 catch-all cotton stole — prefer 6214 90 40/50 when they match |
| 6214 90 10 | Abrabroomal, cotton | 🔴 very specific term; rarely correct |

**Which variant fits made-to-order artisan goods:** most artisan consignments are a 1-3 piece run of a woven scarf/stole — use the **material + handloom** line:
- Silk handloom scarf → **6214 10 30** (matches HEPC's handloom tariff-item list; Seair export data shows real shipments under this code)
- Wool/pashmina shawl → **6214 20 10** (shawls) or 6214 20 20 (scarves)
- Cotton stole/shawl → **6214 90 50** (shawls, mufflers of cotton) — note no separate handloom line exists at 8-digit for cotton 6214, so pair it with Handloom Mark/label for the handloom claim.

⚠️ **Flagged:** the 6214 10 30 silk-handloom line is attested by HEPC + EximPe + Seair, but India's ITC-HS is not fully reproducible from any single free source; the 6214 10 3x range has also been shown as "Other" in some mirrors. **Verify the live 8-digit schedule at trade.gov.in / ICEGATE before PBE filing.**

---

## 2. PBE Declaration (prd_desc) Guidance

PBE rules demand a **specific description** — "no vague descriptions" (report §2.3/§5.1; wrong HS/description is the #1 documented failure mode).

**Do:** `handwoven silk scarf, handloom, 200 cm x 60 cm, natural-dyed, 100% mulberry silk` — material + construction + dimensions + finish + fibre %.
**Don't:** `scarf`, `stole`, `winter wear`, `silk cloth`.

Template for prd_desc:
```
handwoven {material: 100% mulberry silk | cotton | pashmina wool | viscose} {article: scarf|stole|shawl|muffler|odhani}, handloom, {L cm x W cm}, {plain|striped|block-printed|embroidered}, {natural-dyed|undyed|dyed}
```

Tips:
- State **"handloom"** explicitly when true — it justifies the 8-digit handloom line and any Handloom Mark label on the parcel.
- Put **dimensions** on the invoice; a square piece ≤60 cm flips HS to 6213 — avoid describing a 6213 piece as "scarf" to dodge misdeclaration.
- Value/weight fields: Σ piece values ≤ parcel value, Σ piece weights ≤ parcel weight, gross weight ≤ 110% of net (report §2.3 validation rules).

---

## 3. Destination Notes (duty / VAT)

Landed cost = postage + destination duty + destination VAT + handling. **All US numbers are volatile — re-check at build (report O11).**

| Market | Duty (base, HS 6214) | VAT/GST | Notes |
|---|---|---|---|
| **USA** | Silk scarf ≥70% silk (6214.10.10): **1.2%** 🟢. Wool (6214.20.00): **6.7%** 🟢. Other silk / man-made / "other" (859): **~11.3%** 🟡. Cotton (6214.90.00.10): **~4.3%** 🟡. **Plus Section 301 10% on India since 24-Jul-2026** (report §4.4; ~45% of exports exempt — verify per item) ⚠️ | State sales tax varies; not collected by postal import in most states | **De minimis suspended since 29-Aug-2025 — every parcel is dutiable** 🟢 (report H5). Duty basis changed 4× in ~14 months; 6214 rates are MFN + S.301 at build time |
| **UK** | Duty-free ≤ **£135** consignment value (report §4.4) — most single scarf/stole parcels fall below 🟢. UK Global Tariff MFN on 6214 = **8%** 🟢 (trade-tariff.service.gov.uk) | **20% VAT on all** parcels 🟢 | VAT always due even below £135. GST-registered seller uses import-VAT-accounting or merchant handles at clearance |
| **UAE** | Duty de minimis **AED 1,000** (duty-only) 🟢; GCC common tariff **5% on CIF** above that 🟢 | **5% VAT on all** commercial imports 🟢 | AED 1,000 exempts duty, NOT VAT (report §4.4) |
| **Australia** | Duty-free ≤ **AUD 1,000** 🟢; 6214 lines are Free in AU Customs Tariff Act 1995 even at MFN 🟢; India-Australia **ECTA** preferential 🟢 | **10% GST on all** imports (vendor-collected since 2018) 🟢 | GST is the real cost; duty rarely bites for small parcels |

---

## 4. Certifications & Document Needs

| Need | Required? | Detail |
|---|---|---|
| **IEC** | ✅ Mandatory for any PBE filing (report §5.1) | 10-digit, free under FTP 2023; booking disabled if suspended |
| **GSTIN** | 🟡 Not hard-required for booking (≥1 of IEC/GSTIN), but **needed for IGST-refund rail** (ICES Advisory 012/2017) | GSTIN-less artisan can still ship; IGST refund/e-BRC need ICEGATE + AD code + linked bank |
| **Handloom Mark (HLM)** | 🟢 Voluntary certification mark — **recommended** for genuine handloom | Registered certification trademark (Trademark Act 1999), issued by Textiles Committee since 2006 after **onsite verification**; portal hlm.gov.in; 22k+ users, 13 crore+ tagged products. Adds authenticity to the 6214 10 30 handloom claim and buyer trust. Not a customs NOC. |
| **Handloom Origin Certificate** | 🟢 Voluntary but materially useful | Textiles Committee issues under India's bilateral textile agreements (USA, EU, Switzerland, Australia) — lets the importer claim **duty concessions** on handloom origin. Apply via Textiles Committee certification form. |
| **GI tag** | 🟡 Only if the product is a GI-listed good | e.g., **Pashmina/Kani/Kashmir** shawls, **Chanderi**, **Banarasi** (silk saree usually; some stoles) — GI is a marketing/authenticity asset, **not** an export NOC. Optional; cite GI registration number in marketing copy, not customs docs. |
| **AYUSH / NOC** | ❌ Not needed | No ayurvedic/herbal content in scarves/stoles |
| **Wood / plant material** | ✅ None | Pure textile → no phytosanitary, no wood restriction |
| **Natural dyes** | ⚠️ Monitor only | EU/UK **REACH & azo-dye restrictions** apply to dyed textiles; natural dyes are generally compliant but a certificate/test report strengthens EU sales. Not a DNK/PBE requirement for US/UK/UAE/AU postal parcels. |

⚠️ **Flagged:** **Shahtoosh** (Tibetan antelope wool) is **CITES-banned** — never label pashmina as shahtoosh and never source it; genuine pashmina is fine. Also, if stoles carry **sequins/beads/wooden tassels**, those trims may trip wood (beads/tassels) or plastic rules on some lanes — see report §5.2.

---

## 5. Shipping Lane Fit (ITPS vs EMS)

**Typical parcel weight:** single cotton/silk scarf 80-200 g; wool/pashmina shawl 200-450 g; 2-3 piece set 400-800 g. → **Almost always ≤ 2 kg → ITPS is the right lane** 🟢 (ITPS bills actual weight in 50-g slabs, no volumetric charge — report §4.1).

| Destination | 100 g | 200 g | 300 g | 500 g | Lane verdict |
|---|---|---|---|---|---|
| **USA** | ₹435 | ₹505 | ₹575 | ₹715 | ITPS ✅ (≤2 kg cap per S.O. 659(E)) |
| **UK** | ₹225 | ₹275 | ₹325 | ₹425 | ITPS ✅ |
| **UAE** | ₹200 | ₹230 | ₹260 | ₹320 | ITPS ✅ (cheapest lane) |
| **Australia** | ₹440 | ₹530 | ₹620 | ₹800 | ITPS ✅ (≤2 kg cap) |

(Computed from ITPS first-50g/additional-50g rates in report §4.1: USA ₹400+₹35, UK ₹200+₹25, UAE ₹185+₹15, Australia ₹395+₹45.)

**EMS fallback:** only needed for multi-piece/commercial bundles > 2 kg; EMS bills 250-g slabs and can hit volumetric weight — steer ≤2 kg bulky-light to ITPS (report §4.3 build rule).

⚠️ **Flagged:** report C17 says ITPS weight cap is **2 kg for USA/Australia/Canada**, but a DoP OM (31-Dec-2025) raised the **US ITPS cap to 5 kg** (potoolsblog). Resolve per-destination at build (report O10).

**PBE form:** PBE-III (e-commerce orders) or PBE-IV (direct artisan orders) both carry the HS/CTH field; choose per order source (report §2.2).

---

## 6. Sources

1. HEPC HS-codes list (6214 10 30 silk-handloom; 6216 00 20 gloves): https://hepcindia.com/membership/page/hscodes
2. EximGuru ITC-HS 6214 full 8-digit list (India, Policy: Free): https://www.eximguru.com/hs-codes/6214-shawls-scarves-mufflers-mantillas-veils.aspx
3. Seair export data, HS 62141030 silk handloom scarves: https://www.seair.co.in/scarves-export-data/hs-code-62141030.aspx
4. EximPe 62141030 ("Of handloom"): https://eximpe.com/hsncode-finder/62141030 ; GST rate 12% (Vakilsearch: https://vakilsearch.com/hsn-code/6214)
5. US HTS 6214.10.10 = 1.2% (htshub): https://www.htshub.com/us-hs/detail/6214101000 ; CBP ruling NY R00470 (silk 6214.10.1000 = 1.2%, pashmina 6214.20.0000): https://www.customsmobile.com/rulings/docview?doc_id=NY+R00470
6. TariffLens US rates: 6214.90.00 ~11.3% + S.301/S.122: https://www.tarifflens.ai/hts/6214.90.00 ; 6214.20.00 = 6.7%: https://www.tarifflens.ai/hts/6214.20.00.00
7. UK Integrated Online Tariff, heading 6214 (8% MFN, 20% VAT): https://trade-tariff.service.gov.uk/headings/6214
8. Australia Customs Tariff Act 1995 (6214 lines Free): https://www.legislation.gov.au/C2004A04997/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_4/document_4.html ; GST 10% (ABF): https://www.abf.gov.au/importing-exporting-and-manufacturing/importing/cost-of-importing-goods/gst-and-other-taxes
9. UAE: Dubai Customs 5% GCC tariff: https://www.dubaicustoms.gov.ae/en/mobile/pages/faq.aspx ; 5% VAT all commercial imports (report §4.4, UAE FTA guide)
10. Handloom Mark scheme (Textiles Committee): https://textilescommittee.gov.in/handloom-mark-scheme/ ; https://www.hlm.gov.in/what_is_handloom.php (certification trademark)
11. Handloom Origin Certificate (Textiles Committee, bilateral duty concessions): https://textilescommittee.nic.in/certification-0
12. ITPS rates (S.O. 659(E), Feb-2026 + DoP OM Jan-2026): report §4.1; https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html

**Confidence flags recap:** 6214 10 30 existence/currency 🟡 verify on trade.gov.in · US 6214.90/6214.10.20 MFN 🟡 · US S.301 applicability per item ⚠️ · ITPS US weight cap 2 vs 5 kg ⚠️.
