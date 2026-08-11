# UAE — Duties & Taxes (import regime for postal parcels from India)

**Country:** United Arab Emirates (UAE) · **Lane:** India Post DNK (ITPS/EMS via Emirates Post) · **Snapshot date:** 2026-08-08
**Corpus anchors:** report.md §4.4 (UAE row), §6.2 · findings.md F-H5-e (85% High) · order-to-delivery-flow findings.md §3 M3 · sources.md S20 (Dubai Customs Notice 05/2022)
**Config-flag rule (corpus):** every figure below is a config flag with a source + last-updated timestamp — never a hard-coded number. Re-verify at build time.

---

## 1. Executive summary (what a landed-cost engine must encode)

| Flag | Value | Confidence | Source |
|---|---|---|---|
| VAT rate (all commercial imports) | **5%**, applies to ALL parcels regardless of value | High (L1) | UAE FTA E-Commerce VAT Guide (tax.gov.ae, 09-Aug-2020); EMX Emirates Post VAT page (24-May-2023) |
| Customs duty rate (above threshold) | **5% of CIF** (GCC Common External Tariff standard) | High (L1) | Dubai Customs Customer Guide Booklet; WTO tariff profile |
| Duty de minimis (duty-ONLY exemption) | **AED 1,000** (≈ ₹23,000) — exempts customs **duty**, NOT VAT | High (85% corpus; L3 current) | Gulf Today 05-Aug-2026; EY 2023; SamVertex 29-May-2026; EMX page |
| Who pays | **Recipient at pickup** — Emirates Post collects and remits VAT to FTA | Moderate–High | The National 14-May-2018; EMX; RAK Customs |
| Collector | **Emirates Post** (inbound postal), couriers for courier lane | High | EMX VAT page; Dubai Customs Customer Guide |
| Default valuation | If no value declared: **AED 1,000 default** applied (FTA Article on VAT) | High (L1 operator) | EMX VAT page |
| CEPA preferential duty | **0%** on ~97% of UAE tariff lines incl. most craft categories; needs CoO | High (agreement L1); per-line unverified | India-UAE CEPA text; TPCI analysis; NSEZ CoO guidance |

**The one-liner:** AED 1,000 exempts **duty only**. **5% VAT applies to every commercial import** — below and above the threshold. A recipient with no TRN pays both at pickup. Do NOT quote "under AED 1,000 = tax-free" (corpus contradiction C9, resolved F-H5-e).

---

## 2. The import regime — two separate charges, two separate rules

### 2.1 Customs duty: AED 1,000 de minimis (duty-only)

- **Standard GCC Common External Tariff (CET) = 5% of CIF** on foreign goods imported from outside the GCC Customs Union (Dubai Customs Customer Guide Booklet; ~87.6% of UAE tariff lines at 5%, 11.2% duty-free — Arab Trade Financing Program/WTO 2021).
- **Below AED 1,000 → duty exempt.** This is the GCC-standard threshold (SAR 1,000) and is the current operative figure (SamVertex 29-May-2026; EY; Khaleej Times).
- **Threshold history (reconciles the AED 300 vs AED 1,000 conflict in the corpus):**

| Period | Threshold | Legal basis | Source |
|---|---|---|---|
| Pre-1-Jan-2023 | AED 1,000 (GCC SAR 1,000) | GCC Unified Guide for Customs Procedure | EY alert 12-Jan-2023 |
| 1-Jan-2023 → 1-Mar-2023 | **AED 300** | **Dubai Customs Notice 05/2022** (parcels up to 70 kg via courier) | EY alert 12-Jan-2023; Gulf News 04-Jan-2023; vatupdate |
| **1-Mar-2023 → present** | **AED 1,000** (reinstated "until further notice") | Notice 05/2022 art. 2(a) **suspended** | Khaleej Times 03-Mar-2023; EY 03-Mar-2023 |
| 3-Aug-2026 announcement | AED 1,000 **re-affirmed/amended for e-commerce** (Dubai Customs Notice 16/2026) | Cross-border e-commerce exemption ≤ AED 1,000 | Gulf Today 05-Aug-2026; LinkedIn/Dubai Customs |

**Reconciliation (corpus follow-up M3 said ">AED 300"):** the AED 300 figure was a **short-lived 2022 rule** (effective only Jan–Mar 2023), then suspended. The current duty threshold is **AED 1,000**. The M3 "AED 300" line reflects the historical Notice 05/2022 source (S20) and must be updated to AED 1,000.

- **Above AED 1,000 → 5% duty applies to the WHOLE CIF value**, not just the amount over the line (SamVertex 29-May-2026).
- **Always dutiable regardless of value:** tobacco, e-cigarettes/nicotine liquids, alcohol and alcohol-containing food (Gulf Today 05-Aug-2026; SamVertex).
- **Applies to parcels up to 70 kg via courier; ordinary mail/cards/printed matter outside the scope** (EY 12-Jan-2023; SamVertex).

### 2.2 VAT: 5% on ALL imports (no threshold)

- **Import VAT = 5%** on goods imported into the UAE, unless zero-rated or exempt (UAE FTA E-Commerce VAT Guide, 09-Aug-2020 — L1).
- **Applies to all commercial imports, regardless of value** — there is NO VAT de minimis. A parcel under AED 1,000 is duty-free but NOT VAT-free (SamVertex 29-May-2026; E-H5 evidence E5.6; findings F-H5-e).
- **VAT base:** CIF + any customs duty + excise (air-fashion/industry; FTA VAT Importers Guide — VAT computed on value inclusive of duty).
- **Non-registered recipients pay import VAT at the point of import** (Article 49, Federal Decree-Law No. 8/2017 on VAT — The National 14-May-2018). VAT-registered businesses self-account via reverse charge (nets to zero).

### 2.3 Who pays & who collects (the DNK postal lane)

- **Recipient pays at pickup.** Emirates Post collects import VAT (and duty when applicable) and **remits to the Federal Tax Authority** (The National 14-May-2018: "It has fallen to delivery companies and the post office to collect this VAT and remit it to the Federal Tax Authority").
- **Emirates Post inbound postal rules** (EMX page, last updated 24-May-2023):
  - All inbound non-document items subject to **5% duty (items valued over AED 1,000)**;
  - All inbound non-document items require a declared value;
  - **No value declared → default value of AED 1,000 applied** (FTA Article on VAT).
- **Postal clearance mechanics:** Customs selects postal parcels for declaration; recipients directed to the Customs Office at the post office; online declaration not available for postal cargo — counter-based (Dubai Customs Customer Guide).
- **This is a recipient-side charge, unlike EU PDDP (sender) and unlike UK ≤£135 (seller).** For the DNK lane, the seller's landed-cost quote must therefore be "postage + handling, **plus recipient-facing estimate** of 5% VAT (+5% duty above AED 1,000)" — the recipient pays in-country, and surprise VAT at pickup is a buyer-experience risk (order-to-delivery-flow findings M3).

---

## 3. Duty rates for the 8 target craft categories (UAE Customs Tariff / HS)

**Key structural fact:** under the GCC CET, **almost all craft categories sit at the standard 5%** (87.6% of lines at 5%; only tobacco/alcohol exceed 5% — Arab Trade Financing Program; Dubai Customs Customer Guide). Duty applies only when CIF > AED 1,000. **Under India–UAE CEPA most of these lines are 0%** (see §4) — the operative rate depends on CoO.

HS codes below are the standard 6-digit WCO/Indian RITC-ITC-HS codes for each category. The UAE has moved to a **12-digit Integrated GCC Tariff** (first 6 digits WCO HS 2022, next 2 GCC regional, last 4 national) — effective for declarations from Jan-2025 (Kayrouz; Kuehne+Nagel 25-Nov-2025). The 6-digit level is sufficient for the config-flag; the build should confirm the 8/12-digit line at booking.

| # | Category (product folder) | HS 6-digit (ITC-HS) | MFN/GCC CET duty | CEPA note (India) | Source |
|---|---|---|---|---|---|
| 1 | Handloom scarves / stoles | **6214** (6214.10 silk, 6214.20 wool, 6214.90 other) | 5% (standard line) | Textiles ch. 50–63 zero-duty CEPA access; origin tolerance: non-originating material <7% of weight or 10% FOB | XIMPEX 6214/621490; CEPA PSR; TPCI |
| 2 | Block-printed textiles (fabric) | **5208/5209** (woven cotton, ≤200g/m² / >200g/m²); silk alternative **5007** | 5% | ch. 50–63 CEPA; cotton ch. 52 on day-1 elimination for most lines | CEPA PSR Annexure-B (WO for 5202–5204); TPCI; tariff-finder NZ schedule |
| 3 | Embroidered bags / pouches | **4202** (textile-surface bags e.g. 4202.22.40 cotton, 4202.22.81 man-made) | 5% | Ch. 42 preferential (often 0% under CEPA if RoO met) | air-fashion UAE table; TPCI |
| 4 | Embroidered home textiles | **6304** (furnishing articles, e.g. 6304.91); bed linen alt **6302** | 5% | ch. 50–63 CEPA | air-fashion; dutiable.io (Ch. 61/62 at 5%) |
| 5 | Imitation artisan jewellery | **7117** (7117.11/7117.19 base-metal, 7117.90 other) | 5% | **0% under CEPA** — jewellery is flagship zero-duty sector (e.g. HS 7113.19 example 5%→0%); 7117 line-specific confirm at build | NSEZ CoO guidance (71131910 5%→0%); The Hindu; XIMPEX 711790 |
| 6 | Jute products | **5310** (woven jute fabrics) / **6305** (sacks & bags of jute) | 5% | ch. 50–63 CEPA | Dubai Customs tariff; PSR |
| 7 | Small brass / metalware | **7418** (brass table/kitchen/household), **7419**; decorative **8306** | 5% | Ch. 74/83 CEPA preferential (line-dependent) | netyex (5% + 5% VAT); air-fashion |
| 8 | Small woodware | **4420** (wood marquetry/inlaid wood), **4419** (table/kitchen woodware), **4421** | 5% | Ch. 44 CEPA (labour-intensive sector covered) | netyex (wooden wall decor 4420, 5% duty); TPCI |

**Worked landed-cost examples (recipient-side, at pickup; flags = estimates):**

| Parcel CIF | Duty (5%, if >AED 1,000) | VAT (5% on CIF+duty) | Total at pickup |
|---|---|---|---|
| AED 800 (< threshold) | **AED 0** (duty-exempt) | AED 40 | **AED 40 (VAT only)** |
| AED 1,000 (= threshold) | AED 0 (not exceeding) | AED 50 | **AED 50** |
| AED 2,000 (> threshold) | AED 100 (5% of full 2,000) | AED 105 (5% of 2,100) | **AED 205** |

*Worked arithmetic from the rules above; not a government table.*

---

## 4. India–UAE CEPA (Comprehensive Economic Partnership Agreement)

### 4.1 Status & coverage

- **In force 1-May-2022** (signed 18-Feb-2022). India customs rules notified as *Customs Tariff (Determination of Origin of Goods under CEPA between India and UAE) Rules, 2022*, effective 1-May-2022 (Taxmann; CBIC Notification 39/2022-Customs (N.T.)).
- **UAE commitment:** eliminates duties on **97% of its tariff lines = 99% of imports from India**; ~90% of India's exports by value duty-free **immediately** (TPCI analysis; Deloitte). Schedules: UAE Annex 2B.
- **India-side benefit structure (UAE schedule):** Immediate Elimination (Day 1, ~80%+ of lines), 5-yr phased (by 2027), 7-yr, 10-yr (by 2032), Tariff Reduction (TR), Exclusion list (~187 lines). Legallands analysis gives UAE-side split: immediate 80.3% (6,090 lines), phased-5yr 4.4%, phased-10yr 2.4%, TR 0.5%, excluded 2.4%.
- **Craft-relevant coverage:** UAE's immediate zero-duty offer to India covers labour-intensive sectors — gems & jewellery, textiles, leather, footwear, wood products, engineering, plastics (TPCI). The Hindu/Commerce Secretary: jewellery zero-duty access (5% → 0%) confirmed.

### 4.2 Certificate of Origin (CoO) requirement

- **Proof of origin required** for preferential (0%) treatment — via a **preferential CoO** (paper or e-Certificate) issued by a competent authority, an origin declaration by an approved exporter, or a fully digitised e-CoO exchanged via the mutual system (CEPA Art. 3.14; Grant Thornton).
- **Issuance:** DGFT authorised agencies under FTP Appendix 2B; **e-CoO filing on the DGFT CoO e-platform since 1-May-2022** (Trade Notice 29/2022-23). Handicraft CoOs: **Development Commissioner (Handicrafts) & regional offices** authorised (DGFT amendment 29-Apr-2022, taxguru/taxtmi).
- **Origin criteria (Rules 2022):** wholly-obtained (WO) or Product Specific Rules (PSR) — change-in-tariff-classification (CTC/CTH/CTSH), value addition, or specific operations. For **textiles & clothing (HS ch. 50–63): de minimis tolerance = non-originating material < 7% of total weight OR 10% of FOB/Ex-Works** (CEPA PSR; Taxguru; webtel notification text).
- **Practical implication for the DNK lane:** a solo artisan exporting a scarf/jute/bag parcel will normally be **below AED 1,000**, where duty is already 0 under de minimis — **CoO is unnecessary for duty**. CoO matters when CIF > AED 1,000 (duty would otherwise be 5%) or when the buyer/re-exporter needs preferential proof. The landed-cost engine should gate "CoO needed?" on CIF > AED 1,000 AND category in CEPA zero lines.

### 4.3 Build-time open item

- Per-line CEPA rate (0% vs 5%) for **each 8/12-digit HS line in the 8 categories** must be verified against the UAE Annex 2B schedule at build time (this file gives 6-digit standard rates + the structural claim that craft lines are covered). Flag per-line, never hard-code.

---

## 5. Source register (with URL + date)

| # | Source | Establishes | Level | Date accessed |
|---|---|---|---|---|
| D1 | UAE FTA **E-Commerce VAT Guide** — tax.gov.ae `E_Commerce_VAT_Guide_EN_09_08_2020_EN.pdf` | Import VAT 5% on all imported goods unless zero-rated/exempt; e-commerce import rules | **L1** | 2026-08-08 |
| D2 | **Emirates Post / EMX — "VAT"** page — https://www.emx.ae/vat (updated 24-May-2023) | 5% duty on inbound non-doc > AED 1,000; default value AED 1,000 if undeclared; 5% VAT on services; TRN of Emirates Post | **L1 (operator)** | 2026-08-08 |
| D3 | **The National** — "VAT Q&A: Why am I charged tax to pick up a parcel from the post office?" — https://www.thenationalnews.com/business/money/vat-q-a-why-am-i-charged-tax-to-pick-up-a-parcel-from-the-post-office-1.730293 (14-May-2018) | Article 49 Decree-Law 8/2017: non-registered pay import VAT; post office/delivery companies collect & remit to FTA | L2 | 2026-08-08 |
| D4 | **EY Tax Alert** — "Dubai reduces threshold for imposing customs duties on imports of consignments" — https://www.ey.com/en_gl/technical/tax-alerts/dubai-reduces-threshold-for-imposing-customs-duties-on-imports-o (12-Jan-2023) | **Dubai Customs Notice 05/2022**: AED 300 threshold from 1-Jan-2023; prior SAR 1,000≈AED 970; ≤70 kg courier parcels; mail/printed matter excluded | L2 (of L1 notice) | 2026-08-08 |
| D5 | **EY Tax Alert** — "Dubai reinstates former import value threshold" — https://www.ey.com/en_gl/technical/tax-alerts/dubai-reinstates-former-import-value-threshold-of-consignments (Mar-2023) | Notice 05/2022 art. 2(a) suspended; SAR 1,000 ≈ AED 980 reinstated from 1-Mar-2023 | L2 (of L1 notice) | 2026-08-08 |
| D6 | **Khaleej Times** — "Dubai suspends new customs duty on international goods above Dh300" — https://www.khaleejtimes.com/life-and-living/dubai-suspends-new-customs-duty-on-international-goods-above-dh300 (03-Mar-2023) | Suspension of AED 300 exemption; AED 1,000 re-established 01-Mar-2023 "until further notice" | L2 | 2026-08-08 |
| D7 | **Gulf Today** — "Dubai Customs exempts e-commerce shipments up to Dhs1,000 from customs duties" — https://www.gulftoday.ae/news/2026/08/05/dubai-customs-exempts-e-commerce-shipments-up-to-dhs1000-from-customs-duties (05-Aug-2026) | Goods ≤ AED 1,000 exempt from customs duties (cross-border e-commerce amendment; effective 3-Aug-2026); tobacco/e-cig/alcohol always dutiable | **L3** (press) | 2026-08-08 |
| D8 | **SamVertex** — "UAE Customs De Minimis in 2026" — https://samvertex.com/blog/uae-customs-de-minimis-2026/ (29-May-2026) | Reconciles AED 300 (2022, 2-month rule) vs AED 1,000 (current GCC); 5% duty on whole CIF above threshold; VAT not exempted by de minimis; 70 kg courier regime | L4 | 2026-08-08 |
| D9 | **Dubai Customs Customer Guide Booklet** — https://www.dubaicustoms.gov.ae/en/OpenData/Publications/Customer_Guide_Booklet_EN.pdf | GCC CET 5% on CIF; postal clearance at post office counters; courier declarations | **L1** | 2026-08-08 |
| D10 | **Arab Trade Financing Program** — UAE Tariffs — https://atfp.org.ae/english/countries/emirates/Tariffs.htm | 87.6% of tariff lines at 5%; 11.2% duty-free; only tobacco/alcohol >5% | L3 (WTO-derived) | 2026-08-08 |
| D11 | **WTO tariff profile AE** — https://www.wto.org/english/res_e/statis_e/daily_update_e/tariff_profiles/ae_e.pdf | Applied tariff ~5% simple average | L1 | 2026-08-08 |
| D12 | **India–UAE CEPA full text** — MOEAT https://www.moet.gov.ae/documents/20121/1347101/Final+Agreement_UAE+India+CEPA.pdf | Annex 2B UAE schedule; Art. 3.14 CoO; elimination mechanics | **L1** | 2026-08-08 |
| D13 | **Customs Tariff (Determination of Origin of Goods under CEPA) Rules, 2022** — Notification 39/2022 (Taxmann; taxguru full text) | Origin rules, PSR Annexure-B, textiles 7%/10% tolerance, de minimis | **L1** | 2026-08-08 |
| D14 | **DGFT Trade Notice 29/2022-23** (apeda) — e-CoO for India-UAE CEPA w.e.f. 01-May-2022 | e-CoO platform issuance | **L1** | 2026-08-08 |
| D15 | **DGFT Appendix 2B amendment** (taxguru, 29-Apr-2022) | Handicraft CoO → Development Commissioner (Handicrafts) & regional offices | **L1** | 2026-08-08 |
| D16 | **TPCI** — "India-UAE CEPA Key Insights" — https://www.tpci.in/wp-content/uploads/2022/09/India-UAE-CEPA_Key-Insights-R2.pdf | UAE eliminates duties on 97% of tariff lines / 99% of imports from India; labour-intensive sectors covered | L3 | 2026-08-08 |
| D17 | **NSEZ CoO guidance (UAE)** — https://www.nsez.gov.in/Resources/Trade/Documents%20for%20COO%20issuance%20UAE.pdf | Example: HS 71131910 duty 5% → **0% under CEPA**; value-addition & RoO mechanics | L3 (gov) | 2026-08-08 |
| D18 | **The Hindu** — "Duty-free access for jewellery sector..." (19-Feb-2022) — https://www.thehindu.com/business/...article65065699.ece | Jewellery 5%→0% zero-duty CEPA access | L2 | 2026-08-08 |
| D19 | **XIMPEX** — HS 6214/621490, 711790 India→UAE pages — https://ximpex.in/hs-codes/621490/united-arab-emirates/ etc. | Standard HS descriptions; CEPA preference noted; UAE = India's #2 export destination | L4 | 2026-08-08 |
| D20 | **air-fashion.com UAE customs table** — https://www.air-fashion.com/index.php?cod=2509116156&lang=1&way=customs | HS 4202 handbags 5% MFN / 0–5% India-CEPA; VAT on CIF+duty | L4 | 2026-08-08 |
| D21 | **netyex** — "How to Import Wall Decor Items from India to UAE" (27-May-2026) — https://netyex.com/how-to-import-wall-decor-items-from-india-to-uae/ | Wooden wall decor HS 4420, metal decorative 8306; 5% import duty + 5% VAT | L4 | 2026-08-08 |
| D22 | **Kuehne+Nagel** — "UAE 12-digit Integrated Customs Tariff" (25-Nov-2025) — https://www.kuehne-nagel.com/market-insights/customs-clearance/uae-12-digit-integrated-customs-tarif | 12-digit GCC tariff structure (6+2+4) effective from 2025 | L4 | 2026-08-08 |
| D23 | **RAK Customs Common Inquiries** — https://rakcustoms.rak.ae/home/common-inquiries/ | Duty base = CIF; express companies/buyer liability | L1/L2 | 2026-08-08 |
| D24 | **Gulf News** — "New Dubai Customs duty charges..." (04-Jan-2023) — https://gulfnews.com/living-in-uae/ask-us/...1.1672841121866 | >AED 300 → 5% duty + 5% VAT breakdown (historical regime) | L2 | 2026-08-08 |

**Levels (corpus convention):** L1 = official/legal · L2 = credible secondary · L3 = practitioner/official-adjacent · L4 = vendor/marketing · L5 = anecdote.

---

## 6. Confidence & open items

- **High (85%, corpus F-H5-e):** AED 1,000 = duty-only exemption; 5% VAT on ALL commercial imports. Overturn condition: an L1 UAE statute change, or a zero-rating category for handicrafts (not observed).
- **High:** 5% GCC CET on craft lines above threshold; VAT 5% base = CIF+duty.
- **Moderate:** the operative duty figure of AED 1,000 is L3/L4-sourced for the Aug-2026 amendment (Gulf Today press; no L1 Dubai Customs notice text fetched). SamVertex caveat: "the exact dirham figure on any given day is worth a five-minute check."
- **Open items:**
  - 8/12-digit per-line UAE duty + CEPA 0% status for each of the 8 categories' lines (Annex 2B).
  - Whether the cross-border e-commerce AED 1,000 exemption (Notice 16/2026, effective 3-Aug-2026) applies to **postal** (Emirates Post) parcels or only to registered e-commerce operators' courier traffic — Gulf Today implies the e-commerce platform route; the GCC postal de minimis is the same AED 1,000 figure (SamVertex; goodsacrossborders). Verify at build.
  - Handling/facilitation fee on UAE side (if any) charged by Emirates Post for duty/VAT collection — not separately confirmed in fetched sources (flag as estimate).
  - UAE-side admin fee (Gulfbuzz mentions AED 65 admin fee in the historical AED 300 regime) — not current, flag as estimate.

---

## 7. Source notes (fetched texts)

- **Gulf Today (05-Aug-2026):** "goods and products whose value does not exceed Dhs1,000 would be exempt from customs duties... Exemption would not apply to tobacco and derivatives, electronic smoking devices, nicotine liquids, alcoholic beverages and food preparations containing alcohol... announcement takes effect from August 3, 2026."
- **EMX/Emirates Post (24-May-2023):** "All inbound non document items are subject to 5% Duty (for items valued over AED 1000). All inbound non document items require a declared value. If an inbound non document is received with no value declared, a default value of AED 1000 will be applied as per the FTA Article on VAT."
- **EY (12-Jan-2023):** "Dubai Customs will impose customs duties on consignments imported to Dubai with a value exceeding AED 300 starting 1 January 2023 under Customs Notice 05/2022. This threshold was formerly set at SAR 1,000, i.e., approximately AED 970... applies to parcels or shipments up to 70 kg transported via courier companies. Consignments of cards, mail, visually impaired leaflets, and print materials are out of scope."
- **EY (Mar-2023):** "the application of the relevant provision of Customs Notice 05/2022 relating to exemption of consignments has been suspended, and the threshold in accordance with the GCC Unified Guide for Customs Procedure was reinstated effective 1 March 2023."
- **UAE FTA E-Commerce VAT Guide (09-Aug-2020):** "Where goods are imported into the UAE from overseas, the goods will be subject to import VAT at 5%, unless the goods would be either zero-rated or exempt if supplied in the UAE."
- **The National (14-May-2018):** "Article 49 of the Decree Law states that a person not registered for tax shall pay due tax on import of concerned goods from outside the implementing states on the date of import... It has fallen to delivery companies and the post office to collect this VAT and remit it to the Federal Tax Authority."

---

*Prepared 2026-08-08 for the DNK export-enablement data pack. All duty/VAT figures are config flags with source links; the AED 1,000 figure and the 12-digit tariff per-line rates must be re-verified at build time. Never claim AED 1,000 exempts VAT.*
