# USA — Import Duties, Taxes & Postal Customs Regime for Indian Postal Parcels (ITPS/EMS)

**File:** `data/01-countries/USA/duties-taxes.md`
**Snapshot date:** 2026-08-08 (research window 2026-08-05 → 2026-08-08)
**Scope:** Federal import duty + postal entry regime for cross-border e-commerce parcels (ITPS / EMS / Air Parcel) shipped from India via the DNK postal spine. State sales/use tax lives in the sibling file [`state-sales-tax-table.md`](./state-sales-tax-table.md).
**Owner:** dnk-export-enablement · **Related corpus:** report.md §4.4, §11; 04-synthesis/findings.md F-H5; 03-evidence/supporting/E-H5 (E5.3, E5.4).

> **⚠️ READ FIRST — this regime changed 4× in ~14 months.** Every number below is dated and sourced. Do **not** treat any duty rate as "current forever". The corpus proved a static figure is wrong within weeks (findings F-H5-a; 92% confidence). **Re-verify at build time** — the flags in this file (esp. §1 duty basis, §3 entry processes) are the config flags the landed-cost engine must expose (report F3, O11).

---

## 0. Executive summary (what actually happens to a DNK parcel to the US, 2026-08)

| Element | Status (2026-08-08) | Source / date |
|---|---|---|
| **De minimis $800 exemption** | **INDEFINITELY SUSPENDED** (since 29-Aug-2025 for all countries; made permanent/regulatory by CBP IFR effective 24-Jul-2026). **Every postal parcel is dutiable.** | E.O. 14324 (30-Jul-2025); CBP factsheet CBP Pub. 5129-0825; FR 2026-12669 (24-Jun-2026); CBP E-Commerce FAQ (17-Jul-2026) |
| **Current duty basis for Indian goods** | **Section 301 FLIP 10% net-of-MFN**, effective 12:01 am ET **24-Jul-2026**, **in addition to** MFN. India code **HTS 9903.05.44**. ~45% of Indian exports exempt via Annexes (below). | USTR FRN 23-Jul-2026; CBP CSMS #69326983 (23-Jul-2026); EY Tax News 2026-1607; FE/PIB 04-Aug-2026 |
| **Regime history (the 4 changes in 14 months)** | IEEPA 26% → 25% → 18% → combined 50% (2025) → **Section 122 10%** (24-Feb-2026, 150-day surcharge) → **expired 24-Jul-2026** → **Section 301 10%** (24-Jul-2026) | Federal Register FR-2026-06-24/2026-12669; FR 2026-12668; gettransport; findings F-H5-a |
| **Entry process for postal parcels ≤ $2,500** | New **postal informal entry process** (19 CFR 145.12(b)) effective 24-Jul-2026, + voluntary **Entry Type 13 (electronic informal) test** in ACE from **22-Sep-2026**. Formal entry for >$2,500, quota, or AD/CVD. | CBP E-Commerce FAQ; FR 2026-12668 (ET13 test notice) |
| **Who pays/collects duty** | Carrier (USPS) or CBP-qualified party remits monthly to CBP (IMD worksheet → CBPDM@cbp.dhs.gov by 7th of month following arrival; payment via Pay.gov). Recipient pays at delivery in the old model. | CSMS #69183472 (08-Jul-2026); CBP FAQ; UPU FAQ (30-Aug-2025, upd. 29-Sep-2025) |
| **MPF (Merchandise Processing Fee)** | **Mail shipments are EXEMPT from MPF** *except* items sent by **Inbound Express Mail / Inbound EMS** — i.e. **EMS parcels ARE subject to MPF**; ITPS/registered/packet items are not (verify per-item classification). FY2026 formal MPF: 0.3464%, min $33.58 / max $651.50. | CBP E-Commerce FAQ (17-Jul-2026); CBP General Notice 2025-13869 (23-Jul-2025) |
| **USPS customs clearance fee** | **$9.35 per dutiable item** collected from addressee (was $6.50 flat per GAO 2020). Not refundable. | FR 2026-00164 (08-Jan-2026, eff. 18-Jan-2026); IMM §712 |
| **VAT/GST** | **None at federal level.** US has no VAT. (Sales/use tax is state-level — see sibling file.) | UPU FAQ Q11 |
| **India Post US service status** | All categories restored since **15-Oct-2025** (EMS, Air Parcels, Registered Letters, Tracked Packets/ITPS) after a 22-Aug→14-Oct-2025 suspension; fully compliant with CBP qualified-party regime. | The Hindu, 14-Oct-2025 |

---

## 1. Federal duty basis — CURRENT (2026-08-08)

### 1.1 The live regime: Section 301 "FLIP" 10% on products of India

- **Action:** USTR final action in Section 301 forced-labour investigations (FLIP 301) against 60 economies. Effective **12:01 a.m. ET Friday 24-Jul-2026**. Published as FRN 23-Jul-2026 (`91 FR 47318`, 28-Jul-2026); whitehouse.gov presidential action 23-Jul-2026.
- **India's rate: 10% additional, net-of-MFN** (imposed on products of India, **in addition to** the normal MFN/column-1 duty rate). India initially proposed at 12.5%, lowered to 10% after India amended its Foreign Trade Policy to curb forced-labour-linked imports.
- **HTS Chapter 99 code for India: `9903.05.44`** — "Except for products described in headings 9903.05.85–9903.05.92, articles the product of India, as provided for in U.S. note 52 to this subchapter, [additional duty]."
- **Exemptions (the ~45%):** Exempt products listed in **Annex I** (writes the action into the tariff schedule; 101 new Ch99 headings; U.S. note 52) and **Annex II, Part A** (a universal exemption list of 2,120 tariff codes across all 60 economies; only 863 exempt as entered; 541 civil-aircraft-use only; 700 pharmaceutical-use only; 16 named articles). U.S. Note 52 also exempts: goods under Section 232 programmes, USMCA-free goods of Canada/Mexico, CAFTA-DR textiles, donations for relief, informational materials, Chapter 98 entries (other than 9802 repair/alteration). **India has no economy-specific additional list (Annex II Parts B–O belong to other economies).**
- **Coverage maths:** PIB/Commerce Ministry clarification (early Aug-2026): **~45% of Indian exports to the US remain outside** the additional duty; ~55% (per Policy Circle, 03-Aug-2026) or ~70% (per Economic Times, 25-Jul-2026 — ET's number counts all non-exempt) do bear it. **Textiles/apparel are the most exposed sector** (Policy Circle 03-Aug-2026). Generic pharmaceuticals, smartphones and certain specified products are excluded.
- **Transit rule:** goods loaded on final mode of transit before 12:01 a.m. ET 24-Jul-2026 and entered before 12:01 a.m. ET 28-Jul-2026 escape the duty (Alston & Bird, 24-Jul-2026).
- **Duration:** indefinite, until USTR acts (no sunset in the notice). **Litigation:** 25 Democratic-led US states filed suit in the US Court of International Trade on 03-Aug-2026 challenging the Section 301 re-imposition. **No injunction as of 08-Aug-2026 — regime still in force.** (CNBC TV18/IBTimes/BBC, 04-Aug-2026.)
- **Exemption headings block** (`9903.05.85–9903.05.92`): in-transit goods; U.S. note 52 subdiv. (b)/(c) goods; civil-aircraft articles; pharmaceutical-application articles; steel/aluminum/copper + passenger vehicles; donations for relief; informational materials.

**Sources:**
- USTR final-action FRN PDF (23-Jul-2026): https://ustr.gov/sites/default/files/files/Press/Releases/2026/FLIP%20301%20Investigation%20Final%20Action%20FRN%207-23-26%20FINAL.pdf
- USTR press release (23-Jul-2026): https://ustr.gov/about/policy-offices/press-office/press-releases/2026/july/ustr-takes-action-forced-labor-section-301-investigations
- CBP CSMS #69326983 "GUIDANCE: Section 301 Forced Labor Import Duties" (23-Jul-2026): https://content.govdelivery.com/accounts/USDHSCBP/bulletins/421d887 (India code **9903.05.44**)
- EY Tax News 2026-1607 (24-Jul-2026): https://taxnews.ey.com/news/2026-1607-...
- Livingston International (24-Jul-2026): https://www.livingstonintl.com/ustr-section-301-forced-labor-duties-take-effect-july-24-2026/
- Global Trade Alert (24-Jul-2026): https://globaltradealert.org/blog/forced-labour-section-301-final-action
- Business Standard (24-Jul-2026); Economic Times (25-Jul-2026); Financial Express (04-Aug-2026); Policy Circle (03-Aug-2026)
- HTSUS current (USITC): https://hts.usitc.gov/current (verified 08-Aug-2026: `9903.05.44` live)

### 1.2 Regime history (the "4 changes in ~14 months") — for the landed-cost flag

| Window | Basis | Rate | Source |
|---|---|---|---|
| Aug 2025 – Feb 2026 | IEEPA (national-emergency tariffs) | 26% → 25% → 18% → combined 50% (per-country/product variants) | E.O. 14193/14194/14195/14257; FR 90 FR 42418 (02-Sep-2025) |
| 20-Feb-2026 | **IEEPA struck down** by SCOTUS (*Learning Resources, Inc. v. Trump*) | n/a | 607 U.S. __ (2026); E.O. 14389 (91 FR 9437) |
| **24-Feb-2026** | **Section 122 flat 10% surcharge** (Proclamation 11012, 150-day) | 10% | FR 24-Jun-2026 doc 2026-12669 (background); FR 2026-12668 |
| **24-Jul-2026** | Section 122 **expired**; **Section 301 FLIP 10% (net-of-MFN) began same day** — no gap | 10% | USTR FRN 23-Jul-2026; Alston & Bird; gettransport |
| 08-Aug-2026 | **Still Section 301 10%** (pending 25-state CIT lawsuit) | 10% | news 04/08-Aug-2026 |

**Implementation note:** The corpus's own "current 10% (S.122)" was stale within 12 days of being written (findings F-H5-a). The config flag must carry: rate + basis + effective date + source URL + "verified on" date.

---

## 2. De minimis — gone, indefinitely

- **E.O. 14324 (30-Jul-2025)**, effective **29-Aug-2025**, suspended the duty-free de minimis administrative exemption under **19 U.S.C. §1321(a)(2)(C)** for imports ≤ $800 for **all countries**, all modes, incl. the international postal network.
- **E.O. 14388 (20-Feb-2026)** continued the suspension (91 FR 9433). IEEPA tariff collapse to a single ad valorem method for postal items from 28-Feb-2026 (the temporary postal "specific duty" $80–$200/item option expired 28-Feb-2026 — CBP factsheet).
- **CBP IFR (24-Jun-2026, FR 2026-12669)**: made the suspension **indefinite** for postal items by regulation (19 CFR part 145 amendment), effective **24-Jul-2026**, and created the **new postal informal entry process** (below). A concurrent rule (FR 2026-12668) announced the **Entry Type 13 test**.
- **Consequence:** *every* DNK postal parcel to the US is now dutiable and must be entered. There is **no sub-threshold safety valve** (findings H5-b, 90%).
- **Still exempt:** (a) bona fide gifts ≤ $100 (19 U.S.C. 1321(a)(2)(A); 19 CFR 10.152/10.153 — gifts must be reported as zero-duty on the IMD worksheet); (b) documents / items of no monetary value (incl. EMS documents, E-format bulky letters with 0-value documents, letter-post documents); (c) personal/household articles accompanying travellers; (d) donations & informational materials under 50 U.S.C. 1702(b); (e) undeliverable items returned to the US with original S10 barcode intact.

**Sources:**
- CBP de minimis factsheet (updated 18-Aug-2025): https://www.cbp.gov/sites/default/files/2025-08/factsheet_suspension_of_duty-free_de_minimis_treatment.pdf
- FR 2026-12669 (24-Jun-2026): https://www.govinfo.gov/content/pkg/FR-2026-06-24/html/2026-12669.htm
- CBP E-Commerce FAQ (last modified 17-Jul-2026): https://www.cbp.gov/trade/basic-import-export/e-commerce/faqs
- CSMS #69183472 (08-Jul-2026): https://content.govdelivery.com/accounts/USDHSCBP/bulletins/41fa7f0
- UPU FAQ "Frequently asked questions – US de minimis suspension": https://www.upu.int/getmedia/d79e0dd5-...
- KPMG TaxNewsFlash (23-Jun-2026): https://kpmg.com/us/en/taxnewsflash/news/2026/06/cbp-suspends-de-minimis-exemption.html

---

## 3. Entry processes for postal parcels (ITPS/EMS) — 2026 regime

Value-band logic (CBP FAQ + FR 2026-12669/12668):

| Parcel value | Entry path (2026-08) |
|---|---|
| **≤ $2,500**, Ch 1–97 goods | **New postal informal entry process** (19 CFR 145.12(b)), effective 24-Jul-2026. Manual/email/worksheet-based. **OR** voluntary electronic **Entry Type 13** (test starts 22-Sep-2026 in ACE PROD). |
| ≤ $2,500 but subject to **PGA requirements, Ch 98/99 duties, FTA duty-free claims** | Ineligible for the informal process; must use **Entry Type 13** or **formal entry**. (Compliance date for 19 CFR 145.12(a)(2)(v)/(vi): **22-Oct-2026** — until then the interim process tolerates these.) ET13 test **waives** the formal-entry requirement for PGA / Ch 98–99 goods during the test. |
| **> $2,500** | **Formal entry** (19 CFR part 142; for mail: 19 CFR 145.12(a)). |
| Any value, but **quota** or **AD/CVD** | **Formal entry** — never eligible for informal (even under ET13 test). |

### 3.1 New postal informal entry process (19 CFR 145.12(b)) — the default for DNK ≤$2,500 parcels

- **Filer:** only parties with right to make entry (owner/purchaser of the mailed merchandise, or a licensed customs broker designated by owner/purchaser/consignee) — 19 CFR 143.26(a).
- **Data submitted** via Excel/CSV **International Mail Duty (IMD) worksheet** to CBPDM@cbp.dhs.gov **no later than the 7th day of the month following arrival**; payment via Pay.gov (same deadline). Data elements: filer code, value, bond number, total duty, description, carrier, country of origin, conveyance/flight no., **10-digit HTSUS** classification(s), **UPU S-10 tracking barcode**, qty/weight (if specific-duty), arrival port, duty rate, arrival date. Gifts must be flagged (line 8 of IMD worksheet).
- **Bond:** basic importation and entry bond (single-transaction or continuous), 19 CFR 113.62 activity code 1, on file in ACE eBond before filing.
- **Who collects duty:** USPS (as carrier) or a CBP-qualified party (e.g. a licensed broker) collects and remits monthly. Under E.O. 14324 interim process, India Post dispatches through a CBP-qualified party; the qualified party's bond is liable, not the carrier's (UPU FAQ Q12).
- **Duties that must be paid:** all applicable duties based on HTSUS + country of origin + dutiable value at entry — **this is where the Section 301 10% (9903.05.44) is added for India**, plus any applicable Ch 98/99 duties.

### 3.2 Entry Type 13 Test (electronic informal mail entry) — from 22-Sep-2026

- FRN 2026-12668 (24-Jun-2026); test commences **22-Sep-2026** (ACE CERT 24-Jul-2026, PROD 22-Sep-2026 per CSMS #69289734), until concluded by FRN.
- Voluntary; no separate application; eligible parties = right-to-make-entry parties + carriers reporting S-10 tracking numbers on manifests.
- Data elements: filer code, **IOR number**, description, country of origin, **all applicable 10-digit HTSUS incl. Ch 98/99**, qty/weight (if specific duty), duty rate, value, total duty, carrier, S-10 tracking number, arrival port. Bond required.
- **ET13 temporarily creates an informal pathway for low-value mail subject to PGA requirements or Ch 98/99 duties** (normally formal-entry items) — **waives 19 CFR 145.12(a)(2)(v)/(vi)** for test participants. AD/CVD + quota remain excluded.
- Note for ITPS/EMS: ET13 is designed to be the automated successor to the manual postal informal process; expect ITPS/EMS parcels to move onto it once operational.

### 3.3 Formal entry (>$2,500 or special)

- Full formal entry (CBP Form 7501 etc.) under 19 CFR part 142 / 145.12(a). MPF applies (see §4.2). For DNK-scale artisan parcels (typically $30–300) this is irrelevant, but **know the $2,500 ceiling** — a single "invoice for export" > $2,500 (or a consolidation) forces formal entry and its cost structure.

**Sources:** CBP E-Commerce FAQ (17-Jul-2026); FR 2026-12669; FR 2026-12668; CSMS #69289734; CSMS #69183472; GHY (21-Jul-2026) Entry Type 13 ACE test.

---

## 4. Fees (non-duty) that land on a US parcel

### 4.1 USPS Customs Clearance and Delivery Fee — **$9.35 per dutiable item**

- Collected by the Post Office from the addressee **for each item on which customs duty (or IR tax) is collected** (IMM §712). Not refundable even if duty is later refunded.
- **Current amount: $9.35** (raised from the previous competitive level; effective 18-Jan-2026, FR 2026-00164). History: USPS OIG (2016) reported CBP $5.50 processing + USPS $6.00 handling per item; GAO (2020) cited a flat **$6.50**. **Flag for re-check at build time** — this is a "competitive" USPS fee and changes with each Notice 123 price change (next expected Jul-2026+).
- Only charged on the package bearing CBP Form 3419ALT (dutiable mail entry). In the new postal informal process the fee may be collected by USPS at delivery alongside duties.
- Sources: FR 2026-00164 (08-Jan-2026): https://www.govinfo.gov/content/pkg/FR-2026-01-08/html/2026-00164.htm ; USPS IMM §712: https://pe.usps.com/IMM_Archive/NHTML/IMM_Archive_20260118/immc7_002.htm ; GAO-20-340R; USPS OIG NL-AR-16-002.

### 4.2 Merchandise Processing Fee (MPF) — **exempt for postal mail, EXCEPT Inbound EMS**

- CBP E-Commerce FAQ (17-Jul-2026): *"Other than items sent through the international postal network by 'Inbound Express Mail service' or 'Inbound EMS'… mail shipments are exempt from MPF."*
  - ⇒ **EMS (Express Mail Service) parcels from India are subject to MPF.** India Post EMS is the classic "Inbound EMS"; DNK EMS legs should be quoted **with** MPF.
  - ⇒ **ITPS (International Tracked Packet Service) / registered / ordinary packets and letter-post items are exempt from MPF** (subject to per-item classification — confirm a given ITPS item is not treated as EMS; this is a config flag).
- **FY2026 MPF schedule** (effective 01-Oct-2025): ad valorem **0.3464%** (unchanged); formal-entry **min $33.58 / max $651.50**; manual surcharge $4.03; informal-entry flat fees **$2.69 / $8.06 / $12.09** depending on processing path (TariffCheck 2026).
- **Bottom line for landed cost:** DNK EMS parcel → add ~0.35% MPF (but below the informal flat fee, so realistically the flat informal MPF tier applies where MPF is due); ITPS parcel → no MPF.
- Sources: CBP FAQ; CBP General Notice on customs user fees FY2026, FR 23-Jul-2025 (2025-13869) / CSMS #3eb24a9; TariffCheck (15-Apr-2026); Expeditors NewsFlash (31-Jul-2025); Buckland (28-Jul-2025).

### 4.3 No federal VAT / import tax

- The US has **no VAT or GST** at the federal level (UPU FAQ Q11). Duties + MPF + USPS clearance fee are the only federal import charges. State sales/use tax is separate and generally **not collected at customs** for postal deliveries (see sibling file for nexus rules that matter once a seller exceeds thresholds).

---

## 5. Duty rates + HTS codes for the 8 target product categories (India-origin, MFN/column-1)

**Verified against the current US HTS** (hts.usitc.gov REST API + chapter PDFs, Revision 15 (2026), checked 08-Aug-2026). Column-1 general (MFN) rates. These are **base rates**; add the **Section 301 10% (9903.05.44)** unless the exact 10-digit line appears in the Annex II Part A exemption list (see §5.9).

> Textile/apparel items carry **quota-category numbers** (e.g. "359", "330", "369") — these are **not** quotas for India; India-origin textiles/apparel are generally not subject to US textile quotas (only visa/statement requirements apply to certain countries). **No US textile quota applies to India** in 2026. PGA = none of the listed goods are FDA/CPSC-controlled in a way that blocks informal entry (confirm per item).

### 5.1 Handloom scarves / stoles / shawls (heading 6214)

| HTS (8-digit) | Description | MFN rate | Notes |
|---|---|---|---|
| **6214.10.10.00** | Silk scarves, ≥70% silk | **1.2%** | |
| **6214.10.20.00** | Silk scarves, other | **3.9%** | |
| **6214.20.00.00** | Of wool/fine animal hair | **6.7%** | |
| **6214.30.00.00** | Of synthetic fibers | ~Free–6.7% (ch.62) | verify line |
| **6214.90.00** (suffix .10 cotton; .90 other) | **Cotton & other textile materials** | **11.3%** | **Most common for handloom cotton stoles.** Statistical suffix .10 = "Of cotton (359)". |
| 9902.13.69 | Women's shawls/scarves wholly of silk | Free (temp. suspension) | product-specific suspension — rare to rely on |

**Typical DNK item:** cotton handloom stole → 6214.90.00.10 @ **11.3% + 10% S.301** ≈ 21.3% total (net of MFN; check Annex II exemption).

### 5.2 Block-printed textiles (cotton fabrics / handkerchiefs / dress materials)

**Fabrics by the metre (printed cotton woven):**

| HTS | Description | MFN rate |
|---|---|---|
| **5208.52.10.00** | **Certified hand-loomed fabrics**, cotton plain weave >100 g/m², printed | **3%** (!!) |
| **5208.52.40** | Cotton plain weave >100 g/m², printed, num 43–68 | **11.4%** |
| **5208.59.40** | Cotton plain weave >100 g/m², printed, num ≤42 | **6%** |
| **5209.52.00** (line .60) | Cotton plain weave >200 g/m², printed | **8.4%** |
| **5210.52 / 5210.59.40** | Cotton <85%, ≤200 g/m², printed | **8.8%** |
| **5211.52 / 5211.59.40** | Cotton <85%, >200 g/m², printed | ~8.8% (verify) |
| **5212.24.60** | Other cotton woven, printed | **7.8%** |

**Handkerchiefs (heading 6213):**

| HTS | Description | MFN rate |
|---|---|---|
| **6213.20.10.00** | Cotton handkerchiefs, hemmed, no lace/embroidery (330) | **13.2%** |
| **6213.20.20.00** | Cotton handkerchiefs, other | **7.1%** |
| 6213.90.xx | Other textile materials | 4.8–8.8% (verify line) |

**Dress materials** (made-up / unsewn fabrics in 5208–5212) → use fabric lines above; made-up garments → ch. 62 (e.g. 6204.43 dresses 16%, 6204.49.50 6.9%).

> **Key lever:** **certified hand-loomed cotton printed fabric (5208.52.10) = 3%** vs 11.4% for standard — a large saving IF the exporter can certify hand-looming (relevant for block-printed handloom textiles; the certification basis is in U.S. note to ch. 52).

### 5.3 Embroidered bags / pouches (heading 4202 + embroidery heading 5810)

| HTS | Description | MFN rate |
|---|---|---|
| **4202.22.40** | Handbags with outer surface of textile materials, other | **7.4%** |
| **4202.22.80** | Handbags, textile surface, silk/linen/other | verify (≈0.9–6.3%) |
| **4202.32.20** | Pocket/wallet articles, other (incl. textile) | **20%** |
| **4202.32.40** | Pocket/wallet articles of cotton (369) | **6.3%** |
| **5810.91.00** | Embroidery in the piece, of cotton | Free* (not less than un-embroidered fabric rate) |
| **5810.92.10** | Embroidery in the piece, of man-made fibers | **4.2%** |
| **5810.92.90** | Embroidery in the piece, of man-made fibers | **7.4%** |
| **5810.99.10** | Embroidery in the piece, of wool | **7.4%** |
| **5810.99.90** | Embroidery in the piece, other textile | **4.2%** |

*5810.91.00 general = Free, but **not less than the rate that would apply to the fabric un-embroidered** (U.S. Additional Note 1 to ch. 58).

### 5.4 Small woodware (headings 4419, 4420, 4421)

| HTS | Description | MFN rate |
|---|---|---|
| **4419.11.00** | Bread/chopping boards of wood | **3.2%** |
| **4419.90.91** | Wooden forks/spoons | **5.3%** |
| **4419.90.90** | Other wooden tableware/kitchenware | **3.2%** |
| **4420.19.00 / 4420.90.80** | Wood marquetry, statuettes, ornaments | **3.2%** |
| **4421.99.98** | Other articles of wood | **3.3%** |
| 9403.60.80 | Wooden furniture | Free |

### 5.5 Imitation / artisan jewellery (heading 7117)

| HTS | Description | MFN rate |
|---|---|---|
| **7117.19.90** | Imitation jewellery of base metal, not plated with precious metal | **11%** |
| **7117.90.55** | Other imitation jewellery | **7.2%** |
| **7117.90.90** | Other imitation jewellery | **11%** |
| 7117.19.60 | Toy jewellery ≤ 8¢/piece | Free |

**Column-2 note:** base-metal imitation jewellery (7117.19.90) shows column-2 110% — irrelevant for India (MFN/column-1 applies). **11% is the standard MFN rate for costume/artisan jewellery.**

### 5.6 Small brass / metalware (headings 8306, 7418, 7419)

| HTS | Description | MFN rate |
|---|---|---|
| **8306.10.00** | Bells, gongs and parts | **5.8%** |
| **8306.21.00** | Statuettes/ornaments plated with precious metal | **4.5%** |
| **8306.29.00** | **Statuettes & other ornaments of base metal, not plated — FREE** | **Free** |
| **8306.30.00** | Photo/picture frames of base metal | **2.7%** |
| **7418.10.00** | **Brass table/kitchen/household articles** | **3%** |
| **7419.99.50** | Other articles of copper/brass | ~3% (verify) |

> Most **small brass figurines/home decor** = 8306.29.00 → **Free MFN + 10% S.301** = 10% total (net-of-MFN). **Brass tableware** (7418.10.00) = 3% + 10% S.301 = 13%.

### 5.7 Jute products (headings 6305, 5702, 5705, 4602)

| HTS | Description | MFN rate |
|---|---|---|
| **6305.10.00** | Sacks/bags of jute (hessian shopping bags) | **FREE** |
| **5702.39.10** | **Jute woven floor coverings (rugs/carpets)** | **FREE** |
| **5705.00.20** | Other floor coverings (incl. jute/other) | **3.3%** |
| **4602.90.00** | Basketwork/wickerwork of plaiting materials (jute baskets) | **3.5%** |
| 4602.11/4602.12 | Bamboo/rattan basketwork | Free–10% (by line) |

> **Jute is a winner:** jute bags (6305.10) and jute rugs (5702.39.10) are **duty-free at MFN** → only the Section 301 10% applies (verify Annex II exemption for the exact line).

### 5.8 Embroidered home textiles (headings 6302, 6303, 6304)

| HTS | Description | MFN rate |
|---|---|---|
| **6302.21.90** | Bed linen of cotton, printed, not napped | **6.7%** |
| **6302.53.00** | Bed linen of man-made fibers | **11.3%** |
| **6302.59.10** | Table linen of flax (tablecloths/napkins) | **5.1%** |
| **6302.59.20** | Table linen of other textile materials | **Free** |
| **6302.59.30** | Table linen, other textile materials (embr.) | **8.8%** |
| **6302.60.00** | Toilet/kitchen linen of terry towelling | **9.1%** |
| **6302.91.00** | Toilet/kitchen linen of cotton (embr. cushion covers) | **9.2%** |
| **6303.91.00** | Curtains/drapes of cotton | **10.3%** |
| **6303.99.00** | Curtains of other textile materials | **11.3%** |
| **6304.19.30** | Bedspreads, other | **6.3%** |
| **6304.93.00** | Furnishing articles of synthetic fibers, not knitted | **9.3%** |
| **6304.99.60** | Furnishing articles, other (incl. silk/wool mixes) | **3.2%** |
| 9817.57.01 | Needle-craft display models, primarily hand-stitched | Free |

**Typical DNK item:** embroidered cotton cushion cover → 6302.91.00 @ **9.2% + 10% S.301** ≈ 19.2% total (or 6304.99.60 @ 3.2% + 10% for silk-mix). Embroidered **table linen** 6302.59.10 @ 5.1% + 10%.

### 5.9 Section 301 (9903.05.44) applicability to the 8 categories — guidance

- **In principle, all 8 categories (textiles, jewellery, metalware, wood, jute) are products of India and therefore carry the 10% Section 301 duty — UNLESS** the specific 10-digit HTS line appears in **Annex II Part A** (863 codes exempt "as entered") or the item falls under a U.S. note 52 carve-out (Section 232, pharma-use, civil-aircraft, donations, informational materials, USMCA, Ch 98).
- **Textiles/apparel are explicitly the MOST exposed sector** (Policy Circle 03-Aug-2026); most textile lines are **not** in the exempt list. Handloom textiles are not listed among the carve-outs in the trade press reviewed.
- **Practical rule for the landed-cost engine:** assume **MFN + 10% S.301** for all 8 categories by default, but implement an **Annex II lookup flag** per 10-digit HTS line (a config table seeded from the FRN Annex II, Part A). Mark lines 8306.29.00, 6305.10.00, 5702.39.10, 6214.90.00 as "verify — candidate exempt" only after checking the actual Annex list.
- ⚠️ **Cannot be fully resolved from public trade-press sources**: the definitive answer requires the 431-page FRN Annex II Part A (863 codes) vs each exact 10-digit line. **Flag for build-time verification** against the current HTS/CSMS guidance (CSMS #69326983 attachment lists Ch 1–97 codes ↔ Ch 99 headings).

---

## 6. Worked landed-cost examples (federal duty + fees only; NO shipping, NO state tax)

Assumptions: parcel value = customs value (transaction value), no de minimis (suspended), duty basis S.301 10% net-of-MFN, MPF exempt except where noted, USPS clearance fee $9.35 on dutiable items.

| Product | HTS | MFN | +S.301 10% | Duty (on $50) | USPS fee | MPF | **Total federal cost** |
|---|---|---|---|---|---|---|---|
| Silk stole | 6214.10.20 | 3.9% | 13.9% | $6.95 | $9.35 | – | **$16.30 (32.6%)** |
| Cotton handloom stole | 6214.90.00.10 | 11.3% | 21.3% | $10.65 | $9.35 | – | **$20.00 (40%)** |
| Certified handloom printed cotton fabric | 5208.52.10 | 3% | 13% | $6.50 | $9.35 | – | **$15.85 (31.7%)** |
| Cotton handkerchief | 6213.20.20 | 7.1% | 17.1% | $8.55 | $9.35 | – | **$17.90 (35.8%)** |
| Textile handbag | 4202.22.40 | 7.4% | 17.4% | $8.70 | $9.35 | – | **$18.05 (36.1%)** |
| Wooden bowl | 4419.90.90 | 3.2% | 13.2% | $6.60 | $9.35 | – | **$15.95 (31.9%)** |
| Imitation jewellery | 7117.19.90 | 11% | 21% | $10.50 | $9.35 | – | **$19.85 (39.7%)** |
| Brass figurine | 8306.29.00 | Free | 10% | $5.00 | $9.35 | – | **$14.35 (28.7%)** |
| Brass tableware | 7418.10.00 | 3% | 13% | $6.50 | $9.35 | – | **$15.85 (31.7%)** |
| Jute shopping bag | 6305.10.00 | Free | 10% | $5.00 | $9.35 | – | **$14.35 (28.7%)** |
| Embroidered cushion cover | 6302.91.00 | 9.2% | 19.2% | $9.60 | $9.35 | – | **$18.95 (37.9%)** |

> **Structural insight:** with de minimis gone, the **USPS $9.35 clearance fee** is a large fixed cost on low-value parcels — on a $50 parcel it is 18.7% by itself. Duty rates matter less than the fixed fee + the 10% S.301. EMS legs additionally attract MPF (≈$2.69–12.09 flat informal tier; on a $50 EMS parcel ≈ $2.69+).

---

## 7. Config flags the landed-cost engine MUST expose (report F3 / O11)

1. `us.duty_basis` — current basis string (e.g. `S301_10_pct_netofmfn`) + effective date + source URL + last-verified date. Never a bare number.
2. `us.s301.exempt_annex2_partA` — per-10-digit-line exemption lookup (Annex II Part A, 863 codes).
3. `us.deminimis.suspended` — `true` (29-Aug-2025; regulatory indefinite 24-Jul-2026). Config to flip back if restored.
4. `us.entry_formal_threshold` — $2,500 (formal > $2,500 / quota / AD-CVD).
5. `us.mpf.postal` — `exempt` for letter-post/packets (ITPS), `liable` for **Inbound EMS**; flat tiers $2.69/$8.06/$12.09; formal 0.3464% min $33.58 max $651.50.
6. `us.usps_clearance_fee` — **$9.35** per dutiable item (competitive fee, re-check each USPS price change).
7. `us.sales_tax` — see sibling file (state + local rates and nexus thresholds).
8. `us.volumetric_divisor` — NOT a US customs matter; keep in DNK/EMS postage layer (findings F-H5-c).

---

## 8. Source register

| # | Source | URL | Level | Date |
|---|---|---|---|---|
| S1 | USTR FLIP 301 final action FRN | https://ustr.gov/sites/default/files/files/Press/Releases/2026/FLIP%20301%20Investigation%20Final%20Action%20FRN%207-23-26%20FINAL.pdf | L1 | 23-Jul-2026 |
| S2 | CBP CSMS #69326983 (India code 9903.05.44) | https://content.govdelivery.com/accounts/USDHSCBP/bulletins/421d887 | L1 | 23-Jul-2026 |
| S3 | FR 2026-12669 (postal de minimis suspension + informal entry IFR) | https://www.govinfo.gov/content/pkg/FR-2026-06-24/html/2026-12669.htm | L1 | 24-Jun-2026 |
| S4 | FR 2026-12668 (Entry Type 13 test notice) | https://www.govinfo.gov/content/pkg/FR-2026-06-24/html/2026-12668.htm | L1 | 24-Jun-2026 |
| S5 | CBP E-Commerce FAQ | https://www.cbp.gov/trade/basic-import-export/e-commerce/faqs | L1 | 17-Jul-2026 |
| S6 | CSMS #69183472 Global Guidance Intl Mail | https://content.govdelivery.com/accounts/USDHSCBP/bulletins/41fa7f0 | L1 | 08-Jul-2026 |
| S7 | CBP de minimis suspension factsheet | https://www.cbp.gov/sites/default/files/2025-08/factsheet_suspension_of_duty-free_de_minimis_treatment.pdf | L1 | 18-Aug-2025 |
| S8 | UPU FAQ – US de minimis suspension | https://www.upu.int/getmedia/d79e0dd5-f364-4bff-9476-38a4aba820f8/FAQSdeMinimisUS.pdf | L2 | 30-Aug-2025 / 29-Sep-2025 |
| S9 | FR 2026-00164 (USPS fees incl. $9.35 clearance) | https://www.govinfo.gov/content/pkg/FR-2026-01-08/html/2026-00164.htm | L1 | 08-Jan-2026 |
| S10 | CBP FY2026 customs user fees (MPF) | https://content.govdelivery.com/accounts/USDHSCBP/bulletins/3eb24a9 | L1 | 25-Jul-2025 |
| S11 | HTSUS current (official) | https://hts.usitc.gov/current | L1 | checked 08-Aug-2026 |
| S12 | EY Tax News 2026-1607 | https://taxnews.ey.com/news/2026-1607-ustr-finalizes-section-301-forced-labor-tariffs-on-60-economies | L3 | 24-Jul-2026 |
| S13 | Global Trade Alert final-action overview | https://globaltradealert.org/blog/forced-labour-section-301-final-action | L3 | 24-Jul-2026 |
| S14 | The Hindu (India Post US resumption) | https://www.thehindu.com/news/national/after-two-month-suspension-india-post-restores-us-link-with-new-duty-system/article70162591.ece | L3 | 14-Oct-2025 |
| S15 | Financial Express / PIB (45% exempt) | https://www.financialexpress.com/world-news/us-news/25-us-states-sue-trump-govt-over-new-forced-labour-tariffs-president-does-not-have-the-power/4309871/lite/ | L3 | 04-Aug-2026 |
| S16 | Policy Circle (55% subject; textiles exposed) | https://www.policycircle.org/economy/super-301-us-tariff-india/ | L3 | 03-Aug-2026 |
| S17 | Livingston (Ch 99 application; Ch 98 exception) | https://www.livingstonintl.com/ustr-section-301-forced-labor-duties-take-effect-july-24-2026/ | L3 | 24-Jul-2026 |
| S18 | Alston & Bird (effective date; transition) | https://alstontrade.com/ustr-finalizes-and-imposes-10-to-12-5-percent-section-301-forced-labor-duties/ | L3 | 24-Jul-2026 |
| S19 | Corpus: findings F-H5-a/b; E5.3/E5.4; report §4.4/§11 | `04-synthesis/findings.md`, `03-evidence/supporting/E-H5-*.md` | L1 | 05-Aug-2026 |

**Uncertainty flags (explicit):**
1. ⚠️ Section 301 **Annex II Part A** exemption membership for each of the 8 categories' exact 10-digit lines — **not resolvable from trade press; requires the FRN annex.** Default = subject to +10%.
2. ⚠️ **MPF on ITPS vs EMS** — CBP FAQ exempts postal mail from MPF except Inbound EMS; ITPS classification vs "Inbound Express Mail" must be confirmed per item/service.
3. ⚠️ **USPS clearance fee $9.35** — competitive fee, changes with Notice 123 price actions (next ~Jul-2026+); re-check.
4. ⚠️ **Section 301 litigation** (25-state CIT suit, filed 03-Aug-2026) could end or alter the 10% basis; no injunction as of 08-Aug-2026.
5. ⚠️ 45% vs 55% vs 70% "coverage" figures are press estimates of India export-value shares, not per-line legal exemptions.
