# Category Doc — Block-Printed Textiles

**DNK export-enablement · SIH260113 · prepared 2026-08-08**
**Scope:** hand block-printed textiles sold as **fabric by the metre**, dupattas/odhanis, sarees, stoles, and printed yardage (Bagru/Sanganeri/Ajrakh/Bagh/Kalamkari styles) — printed woven cotton or silk, made-to-order artisan goods.
**Confidence legend:** 🟢 High 80-95% · 🟡 Moderate 60-80% · 🔴 Low 40-60% · ⚠️ Flagged/verify at build.
**Build rule (report §4.3):** every duty/VAT/postage figure is a **snapshot** → land as config flags with source + timestamp, never hard-coded.

---

## 1. HS / CTH Classification

### 6-digit HS candidates

| 6-digit | Description | Use for |
|---|---|---|
| **5208** | Woven cotton, ≥85% cotton, **≤200 g/m²** | 🟢 lightweight block-printed cotton (the classic block-print weight) |
| **5209** | Woven cotton, ≥85% cotton, **>200 g/m²** | 🟡 heavier printed cotton |
| **5210** | Woven cotton **<85% cotton** mixed mainly with man-made, ≤200 g/m² | 🟡 cotton-viscose/poly blends |
| **5007** | Woven fabrics of silk or silk waste | 🟢 silk block-printed fabric/dupatta |

**How printed-fabric subheadings work (HS 2022):** within 5208, the **printed** lines are:
- **5208.51** plain weave ≤100 g/m² · **5208.52** plain weave >100-200 g/m² · **5208.53** 3-/4-thread twill · **5208.59** other printed. 🟢
- 5209 printed = **5209.51** (plain >200 g/m²) / 5209.59. 5210 printed = **5210.51** / 5210.59. 5007 has no printed split at 6-digit — silk is silk. 🟡

**Fabric-by-metre vs made-up trap:** fabric sold **by the metre** → 5208/5209/5007. Once **cut to shape + hemmed/finished** (a scarf, dupatta with finished edges) it is a made-up article → **6214** (see scarves-stoles doc) or 6304 (furnishing). Block-printed **handkerchief squares ≤60 cm → 6213**. 🟢 Get the finished-state right or the whole declaration is wrong.

### Likely 8-digit ITC-HS India codes

| ITC-HS 8-digit | Description | Confidence |
|---|---|---|
| **5208 52 10 / 5208 52 20 / 5208 52 90** | Printed plain-weave cotton >100-200 g/m² | 🔴 exact 8-digit split for India not reproduced in fetched sources — verify on trade.gov.in |
| **5208 59 20** | Sarees of handlooms (printed, other cotton ≤200 g/m²) | 🟡 HEPC-attested handloom line — **preferred for handloom block-printed sarees** |
| 5208 49 21 | Real Madras Handkerchiefs, of handloom | 🟡 specific to RMHK (cotton checks/prints) |
| 5208 51 90 / 5208 53 90 | other printed ≤100 g / twill | 🔴 verify 8-digit |
| 5209 51 11 | Lungi, of handloom | 🟡 not scarves — only if lungi |
| **5007 90 10** | Woven fabrics of silk or silk waste, of handloom | 🟢 HEPC-attested — **preferred for silk block-printed yardage/dupatta** |
| 5007 20 xx | Other silk fabrics ≥85% silk (non-handloom) | 🟡 verify 8-digit |

**Which variant fits made-to-order artisan goods:** a block-printed **silk dupatta/fabric** → **5007 90 10** (handloom silk) or 5007 20 if powerloom. A **cotton block-print dupatta/saree** → **5208 59 20** (handloom saree line) when saree; otherwise the generic 5208.52/5208.59 8-digit for yardage. Because India's 8-digit schedule for the generic printed-cotton lines wasn't reproducibly fetched, **treat every 8-digit below 🟢 as needing a live trade.gov.in / ICEGATE check before PBE filing.**

---

## 2. PBE Declaration (prd_desc) Guidance

**Do:** `hand block-printed cotton fabric, 100% cotton, handloom base, plain weave 120 gsm, natural dye (indigo/iron), width 44 inch, length 3 metre`
**Don't:** `printed cloth`, `fabric`, `cotton piece`.

Template:
```
hand block-printed {material: 100% cotton | pure silk | cotton-viscose} {form: fabric by the metre | dupatta | saree | stole}, {handloom|powerloom} base, {plain|twill} weave {X} gsm, {natural|azo} dye, width {W} inch, length {L} {metre|pieces}
```

Tips:
- **"hand block-printed" + "handloom"** both matter: "handloom" keys the 8-digit handloom line + Handloom Mark; "hand block-printed" describes the process for the buyer/customs and supports a GI/marketing claim.
- **State gsm & width/length** — gsm is the actual classifier between 5208 (≤200) and 5209 (>200); wrong gsm = wrong heading.
- Square ≤60 cm printed pieces → describe as "bandana/square" and use **6213**, not fabric.
- Keep Σ values/weights coherent with parcel totals (report §2.3 validation).

---

## 3. Destination Notes (duty / VAT)

| Market | Duty (base) | VAT/GST | Notes |
|---|---|---|---|
| **USA** | Cotton woven printed (5208.52/5208.59): general **~10%** 🟡 (credlix shows 5208.52.40 = 10%). "Certified hand-loomed fabrics" special-rate lines exist in some 5208 subheadings 🟡. Silk woven (5007.20): **low, ~0-2%** 🟡. **Plus Section 301 10% on India (24-Jul-2026)** ⚠️ | State sales tax; usually not postal-collected | De minimis suspended — every parcel dutiable 🟢 (report H5). Note "certified hand-loomed" status may open the US handloom duty-concession route → pair with Handloom Origin Certificate (see §4) |
| **UK** | Duty-free ≤ **£135** 🟢. UKGT MFN on cotton woven 5208 ≈ **8%** 🟡 (typical UKGT cotton-fabric rate; verify heading 5208) | **20% VAT on all** 🟢 | Below £135 most yardage/dupatta parcels escape duty; VAT always due |
| **UAE** | Duty de minimis **AED 1,000** (duty-only) 🟢; **5% on CIF** above 🟢 | **5% VAT on all** 🟢 | AED 1,000 exempts duty, not VAT (report §4.4) |
| **Australia** | Duty-free ≤ **AUD 1,000** 🟢; cotton/silk woven lines generally **Free under ECTA** from India 🟢 | **10% GST on all** 🟢 | GST is the only real landed-cost line for small parcels |

---

## 4. Certifications & Document Needs

| Need | Required? | Detail |
|---|---|---|
| **IEC** | ✅ Mandatory for PBE (report §5.1) | free under FTP 2023 |
| **GSTIN** | 🟡 not hard-required for booking; **needed for IGST-refund rail** | GSTIN-less artisan can ship; refunds need ICEGATE + AD code + bank |
| **Handloom Mark (HLM)** | 🟢 Voluntary — **recommended** if handloom base | Certification trademark via Textiles Committee (hlm.gov.in), issued post onsite verification; 22k+ registered users. Not a customs NOC but authenticates the handloom claim in the 8-digit code. |
| **Handloom Origin Certificate** | 🟢 Voluntary — **valuable for US/EU/AU duty concessions** | Textiles Committee issues under India's bilateral textile agreements (USA, EU, Switzerland, Australia); enables importer duty-concession claims on handloom-origin fabric. |
| **GI tag** | 🟡 Only for GI-listed prints | **Bagh** (MP), **Sanganeri** & **Bagru** (Rajasthan), **Ajrakh** (Kutch), **Kalamkari** (AP/Telangana) are GI-registered; if the artisan is in a GI cluster, GI registration is a brand asset — **not** a customs NOC. |
| **AYUSH / NOC** | ❌ Not needed | no ayurvedic/herbal content |
| **Wood / plant material** | ✅ None | pure textile — no phytosanitary |
| **Natural dyes** | ⚠️ Monitor | EU/UK **REACH azo-dye** limits apply to dyed textiles; natural-dye certificates help EU/UK sales and satisfy "eco" claims. Not a DNK requirement. |

⚠️ **Flagged:** block prints are the category most likely to carry **indigo/iron/tannin heavy-metal traces** in natural dye — for EU/UK commercial shipments a **lab test report (EN 14362 azo, heavy metals)** is good diligence even though postal parcels usually clear on declaration. This is a buyer-conformance issue, not a DNK NOC.

---

## 5. Shipping Lane Fit (ITPS vs EMS)

**Typical parcel weight:** fabric yardage 100-200 g/m² → 3 m ≈ **300-600 g**; dupatta 250-450 g; saree 400-700 g. → **≤2 kg → ITPS** 🟢.

| Destination | 300 g | 500 g | 700 g | 1,000 g | Lane verdict |
|---|---|---|---|---|---|
| **USA** | ₹575 | ₹715 | ₹855 | ₹1,065 | ITPS ✅ |
| **UK** | ₹325 | ₹425 | ₹525 | ₹675 | ITPS ✅ |
| **UAE** | ₹260 | ₹320 | ₹380 | ₹470 | ITPS ✅ |
| **Australia** | ₹620 | ₹800 | ₹980 | ₹1,250 | ITPS ✅ |

(ITPS first-50g/additional-50g per report §4.1: USA ₹400+₹35, UK ₹200+₹25, UAE ₹185+₹15, Australia ₹395+₹45.)

**EMS fallback:** whole-bolt/multi-saree commercial runs > 2 kg. EMS bills 250-g slabs and may apply volumetric weight — steer ≤2 kg to ITPS (report §4.3).

⚠️ **Flagged:** US ITPS cap per S.O. 659(E) is **2 kg** but a Jan-2026 DoP OM raised the US cap to **5 kg** — resolve at build (report O10).

---

## 6. Sources

1. HEPC handloom HS list (5007 90 10 silk-handloom; 5208 59 20 sarees-handloom; 5208 49 21 RMHK): https://hepcindia.com/membership/page/hscodes
2. UNSD HS 2017 detail — 5208 printed subheadings (5208.51/52/59): https://unstats.un.org/unsd/classifications/Econ/Detail/EN/2089/5208
3. EximGuru 5210 woven cotton mixed: https://www.eximguru.com/hs-codes/5210-woven-fabricss-of-cotton-containing.aspx ; 5007 silk: https://www.eximguru.com/hs-codes/5007-woven-fabrics-of-silk-or.aspx/1000
4. UK Trade Info 5208/5210 commodity codes: https://www.uktradeinfo.com/commodities/5208
5. US HTS 5208.52 (10% general; certified hand-loomed lines): https://www.credlix.com/hts-code/520852 ; TariffLens 5208.52 (Free/other by origin): https://www.tarifflens.ai/hts/5208.52
6. UK Integrated Online Tariff, heading 5208 (verify UKGT rate): https://trade-tariff.service.gov.uk/headings/5208
7. Australia Customs Tariff Act 1995 (Section XI textiles): https://www.legislation.gov.au/C2004A04997/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_4/document_4.html ; GST 10%: https://www.abf.gov.au/importing-exporting-and-manufacturing/importing/cost-of-importing-goods/gst-and-other-taxes ; ECTA tariff guide: https://www.dfat.gov.au/sites/default/files/using-ecta-do-business-india.pdf
8. UAE: Dubai Customs FAQ (5% CIF): https://www.dubaicustoms.gov.ae/en/mobile/pages/faq.aspx ; report §4.4 (AED 1,000 duty de minimis, 5% VAT on all)
9. Handloom Mark: https://textilescommittee.gov.in/handloom-mark-scheme/ ; https://www.hlm.gov.in/
10. Handloom Origin Certificate: https://textilescommittee.nic.in/certification-0
11. GI textile clusters (Bagh/Sanganeri/Ajrakh/Kalamkari) — GI Registry, Tamil Nadu Agricultural University portal (search per print)
12. ITPS rates (S.O. 659(E) Feb-2026 + DoP OM Jan-2026): report §4.1; https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html

**Confidence flags recap:** exact India 8-digit for generic printed-cotton lines 🔴 verify on trade.gov.in · US 5208 general rate 🟡 · UK 5208 UKGT rate 🟡 · US S.301 per item ⚠️ · US ITPS cap 2 vs 5 kg ⚠️.
