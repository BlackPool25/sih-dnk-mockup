# Australia — Import Duties & Taxes (DNK / India Post lane)

**Country:** Australia · **Data file:** `01-countries/Australia/duties-taxes.md`
**Snapshot date:** 2026-08-08 · **Parent research:** dnk-export-enablement (SIH260113)
**Corpus anchors:** `report.md` §4.4 (AU row), §5.2 (product restrictions) · `04-synthesis/findings.md` F-H5 · `follow-ups/01-order-to-delivery-flow/findings.md` §3 M3 (AU row)

> **Rule for the build:** every figure below is a **config flag with source URL + last-updated date, never a hard-coded number** (report §4.4 / §9.2-F3). Australia's regime is the *least* volatile of the big markets (GST 10% and the A$1,000 threshold have been stable since 2018), but tariffs, biosecurity BICON cases and the LVIG review are all capable of moving. Re-verify flags at build time.

---

## 0. Executive summary (the five numbers that matter)

| # | Fact | Value | Status |
|---|---|---|---|
| 1 | **Duty-free threshold (de minimis)** | **A$1,000** customs value (goods ≤A$1,000 = non-taxable importation, item 26 by-law; excl. alcohol & tobacco) | ✅ L1 verified |
| 2 | **GST rate** | **10%** (= 1/11 of the price charged); applies to **all** consumer imports, low-value or not | ✅ L1 verified |
| 3 | **Vendor collection** | Since **1 Jul 2018** (LVIG regime): non-resident sellers charge GST at **point of sale** on goods ≤A$1,000 | ✅ L1 verified |
| 4 | **Who pays on the DNK lane** | ≤A$1,000 → seller collects GST (LVIG), recipient pays **nothing at delivery**; >A$1,000 → **recipient/importer** pays GST + duty + IPC at the border | ✅ L1 verified |
| 5 | **ECTA preferential rate** | In force 29-Dec-2022; **0% duty** on ~96.4% of Indian exports (incl. textiles 50–63, jewellery, wood, brass) — **needs a Certificate of Origin** | ✅ L1 verified |

**Biosecurity warning (real blocker, do not ignore):** wood articles and jute/plant-fibre products are subject to **Department of Agriculture (DAFF) biosecurity conditions via BICON** — not a customs-duty matter. Small woodware and jute categories need documented compliance (see §4).

---

## 1. The low-value import regime (LVIG — Low Value Imported Goods)

### 1.1 GST on low value imported goods (since 1 Jul 2018)

- **Legal basis:** *Treasury Laws Amendment (GST Low Value Goods) Act 2017* (No. 77, 2017), effective **1 July 2018** — extends GST to offshore supplies of low-value goods bought by Australian consumers. ([legislation.gov.au](https://www.legislation.gov.au/Details/C2017A00077); ATO GSTR 2003/15 para 19A)
- **"Low value" = customs value ≤ A$1,000** (excluding tobacco, tobacco products and alcoholic beverages). ([ATO — GST on low value imported goods](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/gst-on-low-value-imported-goods))
- **Collection point:** the **non-resident seller** collects GST from the Australian customer **at point of sale** and remits it to the ATO. If an electronic distribution platform (marketplace such as Etsy) or redeliverer is involved, it is treated as the supplier ("deemed supplier") and collects instead. ([ATO — how to charge GST](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/how-to-charge-gst); [ATO — non-resident businesses making online sales](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/non-resident-businesses-making-online-sales-to-australia))
- **GST arithmetic:** GST is 10%, i.e. **1/11 of the total amount charged** for the supply. ([ATO](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/non-resident-businesses-making-online-sales-to-australia))
- **Registration threshold for non-resident sellers:** mandatory Australian GST registration once **Australian GST turnover ≥ A$75,000** (A$150,000 for non-profits). **Simplified GST registration** is available for non-residents selling LVIG/services — **no ABN required**. ([ATO — how Australian GST works](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/how-australian-gst-works); [ATO — simplified GST registration](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/gst-registration-for-non-resident-businesses/simplified-gst-registration))
- **Practical consequence for the persona (micro-exporter below A$75,000):** registration is **not mandatory** below the threshold; if not registered and selling via a marketplace, the **marketplace (deemed supplier) collects the GST**. Direct-to-consumer sales below the threshold may proceed without GST collection; this is a compliance grey-zone on the ATO side (audit risk only if turnover crosses the threshold) — **flag as advisory, not legal advice.**

### 1.2 What the recipient pays (the DNK-relevant split)

| Consignment value | Customs duty at border | GST | Border charges |
|---|---|---|---|
| **≤ A$1,000** (single low-value item or multiple items totalling ≤A$1,000) | **None** — non-taxable importation (item 26 by-law; excl. alcohol/tobacco) | **Collected at POS by non-resident seller** (LVIG); *not* collected at border | **None** (no Import Processing Charge below A$1,000) |
| **> A$1,000** (incl. multiple low-value goods shipped as one consignment totalling >A$1,000) | **Payable at border** (see §2 rates) | **Payable at border** by importer/recipient | **Import Processing Charge (IPC)** A$50 (>A$1,000–<A$10,000), A$152 (≥A$10,000) |
| **Alcohol / tobacco** (any value) | Always applicable | Always applicable | Always applicable |

Sources: [ATO — GST and imported goods](https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/rules-for-specific-transactions/international-transactions/gst-and-imported-goods) ("goods with a value at or below $1,000 … non-taxable importations (item 26)"); [ATO — GST and Australian businesses](https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/rules-for-specific-transactions/international-transactions/australian-business-importing-goods-and-services); [ABF — importing by post or mail](https://www.abf.gov.au/buying-online/importing-by-post-or-mail); [Import Processing Charges Act 2001](https://www.legislation.gov.au/C2004A00857/2016-07-01/2016-07-01/text/original/epub/OEBPS/document_1/document_1.html) (A$50 < A$10,000 / A$152 ≥ A$10,000); [Australia Post — international post guide](https://auspost.com.au/sending/parcels-overseas/international-post-guide/results/australia) ("import duties charged when … value over AUD1000 … From 1 July 2018 low value goods may attract GST at the point of sale").

**Who pays on the DNK lane (corpus M3):** "Australia: ≤A$1,000: **seller charges GST at point of sale** (non-resident); >A$1,000: recipient/importer pays | LVIG regime" — [follow-ups/01-order-to-delivery-flow/findings.md](findings.md) §3 M3 (src: ATO LVIG).

### 1.3 Form / label implications

- Value ≤ ~300 SDR (≈A$750–800 at 2026 SDR/AUD rates — **approximate, flag**) → **CN 22**; above → **CN 23 + commercial invoice** (report §5.1). SDR is auto-computed by the DNK portal.
- The commercial invoice must show the **correct customs value in AUD-equivalent**; Australia Post/ABF assesses on arrival ([ABF — importing by post](https://www.abf.gov.au/buying-online/importing-by-post-or-mail)).
- **Recommendation for sellers:** price **GST-inclusive** for ≤A$1,000 consumer orders (LVIG compliance) and keep records; on >A$1,000 orders, quote **ex-duty** and let the buyer pay at the border, or ship DDP if using courier.

---

## 2. Customs duty rates for the 8 target categories (AU HS codes)

Australia's *Customs Tariff Act 1995* Schedule 3 sets the **general (MFN) rate**. Under the **India–Australia ECTA**, originating goods get **Free (0%)** unless the FTA schedule says otherwise (ABF chapter footnotes: *"Unless indicated in the relevant Schedule, rates for originating goods under a free trade agreement are Free"*). **Note:** most of these rates only bite on **>A$1,000** consignments; ≤A$1,000 postal parcels are duty-free regardless (item 26).

| Target category | AU HS code (probable) | General (MFN) rate | ECTA rate | Source (accessed 2026-08-08) |
|---|---|---|---|---|
| **Block-printed textiles** (cotton fabric) | **5208** (woven, ≤200 g/m²) / **5209** (>200 g/m²) | **0% / 5%** | **Free** | [StarShipper AU Ch52 (2026)](https://www.starshipper.io/tariffs/au/chapter/52/cotton) |
| **Embroidered bags & pouches** (textile handbags) | **4202.22** (handbags, textile outer surface); some 4202 subheadings **Free** (4202.19/229/239/232.90) | **5%** (4202.22); Free for others | **Free** | [ABF Ch42 (1-Jul-2026)](https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-viii/chapter-42) |
| **Embroidered home textiles** (bedlinen/furnishing/tapestries) | **6302** (bedlinen), **6304** (furnishing), **5805** (hand-woven tapestries) | **0%** (6302/6304), **Free** (5805) | **Free** | [StarShipper AU Ch63 (2026)](https://www.starshipper.io/tariffs/au/chapter/63/up-textile-articles); [ABF Ch58](https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-xi/chapter-58) |
| **Handloom scarves & stoles** | **6214** (shawls, scarves, mufflers, veils) | **Free** (all 6214.10–6214.90) | **Free** | [ABF Ch62 (1-Jul-2026)](https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-xi/chapter-62); [Customs Tariff Act 1995](https://www.legislation.gov.au/C2004A04997/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_4/document_4.html) |
| **Imitation artisan jewellery** | **7117** (imitation jewellery) | **5%** (all subheadings) | **Free** | [ABF Ch71 (1-Jul-2026)](https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-xiv/chapter-71) |
| **Jute products** (fabric / sacks) | **5310** (woven jute fabric), **5307** (jute yarn), **6305.10** (jute sacks) | **0%** (5310), **5%** (5307), 6305 0% | **Free** | [StarShipper AU Ch53 (2026)](https://www.starshipper.io/tariffs/au/chapter/53/vegetable-textile-fibres); [StarShipper Ch63](https://www.starshipper.io/tariffs/au/chapter/63/up-textile-articles) |
| **Small brass/metalware** | **7418.10** (table/kitchen/household copper & brass), **7419** (other copper articles) | **5%** | **Free** | [Customs Tariff Act 1995 — Ch74](https://www.legislation.gov.au/C2004A04997/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_5/document_5.html); [ABF Ch74 (1-Jul-2026)](https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-xv/chapter-74) |
| **Small woodware** (carved items, boxes, ornaments) | **4420** (wood marquetry, caskets/jewellery boxes, statuettes/ornaments); **4421** (other articles of wood) | **5%** (4420), **0%** (4421) | **Free** | [StarShipper AU Ch44 (2026)](https://www.starshipper.io/tariffs/au/chapter/44/wood-articles-wood); [ABF Ch44](https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-ix/chapter-44) |

**Bottom line for duty:** at the **≤A$1,000 parcel scale**, duty is effectively **0% for every one of the 8 categories** (item 26 exemption). Above A$1,000, general-rate duty is **0–5%** by category, and **ECTA drops all of it to 0%** with a valid CoO.

**Tariff-concession note:** Australia maintains Tariff Concession Orders (TCOs) that can zero out duty where no local equivalent is made — relevant for jewellery/woodware/metalware, but unnecessary under ECTA for Indian goods ([ABF current tariff pages](https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff)).

---

## 3. India–Australia ECTA (Economic Cooperation and Trade Agreement)

### 3.1 Status

- **Signed** 2-Apr-2022 · **In force 29-Dec-2022** (live since then, no suspension — verified current as of 2026-08-08). ([DFAT — ECTA](https://www.dfat.gov.au/trade/agreements/in-force/australia-india-ecta/australia-india-ecta-official-text); [India Briefing](https://www.india-briefing.com/doing-business-guide/india/trade-relationships/india-australia-ecta-in-force-from-december-29-2022-key-benefits))
- **Australia's side:** **96.4% of India's exports by value (98.3% of tariff lines) enter duty-free immediately**; the remainder phases to zero within 5 years. Textiles & apparel (**HS 50–63**), jewellery, leather, footwear, furniture, sports goods, selected pharma — **zero duty from day one**. ([Hindu BusinessLine](https://www.thehindubusinessline.com/blexplainer/all-about-india-australia-economic-co-operation-and-trade-agreement/article65288995.ece); [DFAT guide PDF](https://www.dfat.gov.au/sites/default/files/using-ecta-do-business-india.pdf); [Citi India](https://citiindia.org/india-australia-economic-cooperation-and-trade-agreement-ecta-reg/))
- **India's side:** 85% of Australian exports duty-free at entry, rising to 90% in 6 years. ([DFAT guide PDF](https://www.dfat.gov.au/sites/default/files/using-ecta-do-business-india.pdf))
- **Market context (corpus §3.4):** Australia = **4.03% of Indian handicraft exports** — the 4th largest destination after USA (59.79%), Germany (5.95%), UK (4.25%). Handloom/stole categories have a *duty advantage* over Vietnam/Indonesia competitors post-ECTA ([The Hindu](https://www.thehindu.com/business/india-australia-fta-to-help-increase-apparel-exports-aepc/article66310886.ece)).

### 3.2 Certificate of Origin (CoO) — required to claim the 0%

- **Rule:** preferential treatment is granted only **on the basis of a Certificate of Origin** — ECTA Chapter 4 (Rules of Origin), Art. 4.15 + Annex 4A (minimum information format). ([DFAT — Ch4 Rules of Origin](https://www.dfat.gov.au/trade/agreements/in-force/australia-india-ecta/australia-india-ecta-official-text/chapter-4-rules-origin); [DFAT — Annex 4A](https://www.dfat.gov.au/trade/agreements/in-force/australia-india-ecta/australia-india-ecta-official-text/annex-4a-minimum-information-requirements))
- **How the Indian exporter gets it:** e-COO issued electronically on the **DGFT Common Digital Platform** — `coo.dgft.gov.in` (migrated to the **eCoO 2.0 / trade.gov.in** portal from 17-Jan-2025). India–Australia ECTA e-COO issuance has been live **since 29-Dec-2022** (DGFT Trade Notice 23, 22-Dec-2022). ([DGFT CoO portal](https://coo.dgft.gov.in/); [DGFT Trade Notice 23 PDF](https://apeda.gov.in/hindi/sites/default/files/dgft_trade_notice/Trade%20Notice%2023%20-%20eCoO%20-%20India%20Australia%20ECTA%2022Dec2022_signed%20%281%29_0.pdf))
- **Verification:** QR code on the e-COO is verifiable via the DGFT "Verify Certificate" link; the importer keys the CoO reference into the bill of entry. ([DGFT Trade Notice 23 PDF](https://apeda.gov.in/hindi/sites/default/files/dgft_trade_notice/Trade%20Notice%2023%20-%20eCoO%20-%20India%20Australia%20ECTA%2022Dec2022_signed%20%281%29_0.pdf); [Grant Thornton alert](https://www.grantthornton.in/globalassets/1.-member-firms/india/assets/pdfs/alerts/cbic-issues-clarifications-with-respect-to-implementation-of-origin-procedures-under-the-india-australia-economic-cooperation-and-trade-agreement.pdf))
- **Origin rules:** goods must be wholly obtained in India **or** substantially transformed (per Chapter 4 / Annex 4B product-specific rules; RVC/CTC criteria apply). *Handicraft conversion (dyeing, printing, embroidery, assembly, carving) generally satisfies RVC — verify per product.* ([DFAT — Ch4](https://www.dfat.gov.au/trade/agreements/in-force/australia-india-ecta/australia-india-ecta-official-text/chapter-4-rules-origin); [ABF ECTA rules of origin](https://www.abf.gov.au/free-trade-agreements/files/ECTA-rules-of-origin.pdf))
- **Practical note for postal lanes:** for **≤A$1,000** parcels the duty is 0% anyway (no CoO needed at the border); the CoO matters when the **consignment value exceeds A$1,000** and the buyer/importer wants the ECTA 0% instead of 0–5% general.

---

## 4. Biosecurity — Department of Agriculture (DAFF / BICON) — REAL BLOCKER

> Biosecurity sits **outside customs duty**. Wood, plant fibres (jute) and any plant material are regulated by **BICON (Biosecurity Import Conditions)**. This is the **highest-risk compliance area for the small-woodware and jute categories** (corpus §5.2: wood needs per-destination permission; plants need phytosanitary).

### 4.1 Wood & wooden articles (small-woodware)

- **ALL imported timber, wooden articles, bamboo and related products** — commercial or personal — must comply with conditions in **BICON**. ([DAFF — Importing timber, wooden articles, bamboo](https://www.agriculture.gov.au/biosecurity-trade/import/goods/timber))
- **BICON case: "Timber and timber products"** — covers sawn timber + **manufactured wooden articles** (furniture, household wooden items, stationery, musical instruments, sporting equipment) **where at least one dimension ≤ 200 mm** (typical for small handicrafts). Conditions include demonstrating pest-risk mitigation via **manufacturing process or approved treatment**; DAFF verifies via documentation. (BICON case 826576, version effective 21-Apr-2026–14-May-2026 — [BICON case overview](https://bicon.agriculture.gov.au/BiconWeb4.0/ImportConditions/Questions/EvaluateCase?elementID=0000875666&elementVersionID=333); [DAFF timber page](https://www.agriculture.gov.au/biosecurity-trade/import/goods/timber))
- **Other cases that can apply:**
  - **All dimensions > 200 mm** → BICON case **"Logs, log cabins and oversize timber"** ([BICON](https://bicon.agriculture.gov.au/BiconWeb4.0/ImportConditions/Questions/EvaluateCase?elementID=0000068003&elementVersionID=335)).
  - **Bark retained as a design feature** (rustic bowls, bark-textured frames) → BICON case **"Wooden manufactured articles containing bark"** — stricter conditions ([BICON](https://bicon.agriculture.gov.au/BiconWeb4.0/ImportConditions/Questions/EvaluateCase?elementID=0000451431&elementVersionID=220)).
- **Import permit?** Some wood scenarios require a **biosecurity import permit** obtained **before arrival**; BICON defines whether the scenario is a permit case. "Approved arrangement Class 19.2" lists manufactured wooden articles that generally **do not require an import permit** (subject to inspection on arrival). ([DAFF — BICON permits](https://www.agriculture.gov.au/biosecurity-trade/import/online-services/bicon/bicon-permit); [DAFF — Approved arrangement 19.2](https://www.agriculture.gov.au/biosecurity-trade/import/arrival/arrangements/requirements/approved-commodities-class-19-2))
- **Practical guidance for small woodware:** declare honestly; wood should be **kiln-dried / manufactured, bark-free, pest- and soil-free**; attach supporting evidence to the shipment documentation if available (treatment/drying certificates). **Verify the exact scenario live in BICON before every new product line** — conditions change (the timber case has an active alert at snapshot date).
- **CITES note:** rare/endangered species in wood (e.g., certain rosewoods) require CITES permits — beyond scope of standard DNK artisan categories but check for exotic woods.

### 4.2 Jute & plant-fibre products

- **BICON case: "Permitted plant fibres"** — covers the **majority of articles made from plant fibres** (jute, cotton, coir…) for all uses except animal food/fertiliser/landscaping/growing. (BICON case, version effective 16-Feb-2026–20-Mar-2026 — [BICON](https://bicon.agriculture.gov.au/BiconWeb4.0/ImportConditions/Questions/EvaluateCase?elementID=0000068178&elementVersionID=287))
- **BICON case: "Plant based fabric, textiles or yarn"** — for **highly processed flexible fabrics** (woven/knitted/crocheted/bonded natural-fibre textiles) — the relevant case for jute fabric, cotton textiles, and most embroidered textile categories. (BICON case, version effective 16-Feb-2026–20-Mar-2026 — [BICON](https://bicon.agriculture.gov.au/BiconWeb4.0/ImportConditions/Questions/EvaluateCase?elementID=0000112169&elementVersionID=132))
- **BICON case: "Plant fibre products and seed handicrafts"** — dried cotton pods, cholla wood, luffa; seed handicrafts from specific genera. (BICON, version 16-Sep-2024–25-Oct-2024 — [BICON](https://bicon.agriculture.gov.au/BiconWeb4.0/ImportConditions/Questions/EvaluateCase?elementID=0000116391&elementVersionID=225))
- **Practical guidance for jute products:** finished woven jute goods (fabric, sacks, table runners) are usually **permitted without an import permit but subject to inspection/conditions** — keep the fibre **clean and free of soil, seeds and live insects**, and confirm the scenario in BICON.

### 4.3 The India-Post side

- India Post's per-country restricted list is the scanned `Country_List.pdf` (corpus Ctx-4); the DNK portal validates service/restrictions per destination at booking. Wood/plant items may need **documentation at induction**; attach physical copies for destination customs (report §2.3 step 6).

---

## 5. Config flags for the landed-cost engine (F3)

| Flag | Value | Source URL | Last verified |
|---|---|---|---|
| `au_gst_rate` | **10%** (GST = 1/11 of price) | [ATO](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/non-resident-businesses-making-online-sales-to-australia) | 2026-08-08 |
| `au_duty_threshold_aud` | **1,000** (item 26 non-taxable importation; excl. alcohol/tobacco) | [ATO](https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/rules-for-specific-transactions/international-transactions/gst-and-imported-goods) | 2026-08-08 |
| `au_lvig_vendor_collection` | **true** (since 1-Jul-2018, ≤A$1,000 at POS) | [ATO — LVIG](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/gst-on-low-value-imported-goods) | 2026-08-08 |
| `au_gst_registration_threshold_aud` | **75,000** (turnover; 150,000 non-profit) | [ATO](https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/how-australian-gst-works) | 2026-08-08 |
| `au_ipc_fee_1k_10k` | **A$50** (>A$1,000–<A$10,000, formal declaration) | [Import Processing Charges Act 2001](https://www.legislation.gov.au/C2004A00857/2016-07-01/2016-07-01/text/original/epub/OEBPS/document_1/document_1.html) | 2026-08-08 |
| `au_ipc_fee_10k_plus` | **A$152** (≥A$10,000) | [Import Processing Charges Act 2001](https://www.legislation.gov.au/C2004A00857/2016-07-01/2016-07-01/text/original/epub/OEBPS/document_1/document_1.html) | 2026-08-08 |
| `au_ecta_preferential` | **true** (0% duty with CoO for all 8 categories) | [DFAT](https://www.dfat.gov.au/trade/agreements/in-force/australia-india-ecta/australia-india-ecta-official-text) | 2026-08-08 |
| `au_ecta_coo_required` | **true** (e-COO via DGFT platform, QR-verifiable) | [DGFT CoO](https://coo.dgft.gov.in/) | 2026-08-08 |
| `au_biosecurity_wood` | **required** — BICON "Timber and timber products" (+bark/oversize cases); permit scenario-dependent | [DAFF timber](https://www.agriculture.gov.au/biosecurity-trade/import/goods/timber); [BICON](https://bicon.agriculture.gov.au/) | 2026-08-08 |
| `au_biosecurity_jute` | **required** — BICON "Permitted plant fibres" / "Plant based fabric, textiles or yarn" | [BICON](https://bicon.agriculture.gov.au/) | 2026-08-08 |
| `au_landed_cost_who_pays` | ≤A$1,000: **seller** (GST at POS) · >A$1,000: **recipient** at border | [follow-ups findings M3](findings.md) / [ATO](https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/rules-for-specific-transactions/international-transactions/australian-consumers-importing-goods-and-services) | 2026-08-08 |

---

## 6. Open items / confidence

| Item | Confidence | Note |
|---|---|---|
| GST 10%, A$1,000 threshold, LVIG vendor collection | **High (90%)** — L1 ATO + Act 2017 | Stable since 2018; Board of Taxation review exists but no change through 2026 snapshot |
| Category duty rates (0–5% general; ECTA Free) | **High (85%)** — L1 ABF tariff/legislation + L3 StarShipper | Per-HS subheading; verify at build |
| IPC amounts (A$50 / A$152) | **Moderate (70%)** — L1 Act but thresholds in regs | Re-verify with current regulations |
| Biosecurity BICON scenarios | **Moderate (65%)** — L1 DAFF/BICON but case conditions versioned & permit-dependency scenario-specific | **Must be checked live in BICON per product** |
| CoO / e-COO mechanics | **High (85%)** — L1 DFAT + DGFT | Portal migrated to trade.gov.in Jan-2025 |

---

## 7. Sources (key, accessed 2026-08-08)

- ATO — *GST on low value imported goods*: https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/gst-on-low-value-imported-goods
- ATO — *GST and imported goods* (item 26 / non-taxable importation): https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/rules-for-specific-transactions/international-transactions/gst-and-imported-goods
- ATO — *How Australian GST works / simplified registration*: https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses/how-australian-gst-works
- Treasury Laws Amendment (GST Low Value Goods) Act 2017 (No. 77, 2017): https://www.legislation.gov.au/Details/C2017A00077
- ABF — *Importing by post or mail*: https://www.abf.gov.au/buying-online/importing-by-post-or-mail
- ABF — current tariff chapters 42/44/53/58/62/63/71/74: https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff
- Customs Tariff Act 1995 (consolidated 1-Jul-2026): https://www.legislation.gov.au/C2004A04997/2026-07-01
- Import Processing Charges Act 2001: https://www.legislation.gov.au/C2004A00857/2016-07-01
- DFAT — ECTA official text / Chapter 4 Rules of Origin / Annex 4A: https://www.dfat.gov.au/trade/agreements/in-force/australia-india-ecta/
- DGFT Common Digital Platform for CoO (eCoO 2.0): https://coo.dgft.gov.in/
- DGFT Trade Notice 23/2022 (e-CoO India–Australia ECTA): https://apeda.gov.in/hindi/sites/default/files/dgft_trade_notice/Trade%20Notice%2023%20-%20eCoO%20-%20India%20Australia%20ECTA%2022Dec2022_signed%20%281%29_0.pdf
- DAFF — *Importing timber, wooden articles, bamboo*: https://www.agriculture.gov.au/biosecurity-trade/import/goods/timber
- BICON (all cases): https://bicon.agriculture.gov.au/
- India Briefing — *ECTA in force 29-Dec-2022*: https://www.india-briefing.com/doing-business-guide/india/trade-relationships/india-australia-ecta-in-force-from-december-29-2022-key-benefits
- StarShipper Australian Tariff (2026, L3 rate aggregator): https://www.starshipper.io/tariffs/au/
- Corpus: `report.md` §4.4 & §5.2 · `04-synthesis/findings.md` F-H5 · `follow-ups/01-order-to-delivery-flow/findings.md` §3 M3
