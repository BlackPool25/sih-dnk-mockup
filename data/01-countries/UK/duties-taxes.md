# UK — Duties & Taxes for Low-Value Parcels from India (DNK / ITPS / EMS)

**Country:** United Kingdom (Great Britain; Northern Ireland has separate rules — see §9)
**Author:** DNK Export Enablement research (SIH260113)
**Snapshot date:** 2026-08-08 · **CURRENT DATE reference:** Aug 2026
**Applies to:** Exports from India via India Post DNK lanes — ITPS (≤2 kg typical) and EMS/International Speed Post
**Confidence language:** High 80–95% · Moderate 60–80% · Low 40–60% · Speculative <40% (inherited from parent corpus)

---

## 1. TL;DR — the two rules you must never get wrong

| Rule | Value | Applies to |
|---|---|---|
| **1. Customs Duty is duty-free ≤£135** | **No Customs Duty** on non-excise consignments worth **£135 or less** (value of goods, not including postage/duty). Above £135 the MFN/agreement rate applies to value **+ postage, packaging and insurance**. | All parcels |
| **2. VAT (20%) applies to ALL commercial imports — there is NO threshold.** | Every commercial consignment from outside the UK to Great Britain is subject to **20% import VAT**, regardless of value. The only true VAT exemption is **gifts worth ≤£39**. | All commercial parcels |
| **Who collects VAT ≤£135** | **The overseas (Indian) seller** must charge 20% **UK supply VAT at the point of sale** ("Overseas Seller VAT") and account for it to HMRC. The recipient pays no import VAT or handling fee at delivery for these. | ≤£135 consignments |
| **Who collects VAT >£135** | **Import VAT at the border** — the **recipient pays the delivery company** (Royal Mail/Parcelforce/courier) before delivery, plus a handling fee. | >£135 consignments |
| **India-UK CETA** | **IN FORCE since 15-Jul-2026** (full Comprehensive Economic and Trade Agreement, not a limited interim deal). Preferential **0% duty** on essentially all handicraft tariff lines with a valid Certificate of Origin / origin declaration. | Commercial (mainly >£135) |

> **⚠️ Honesty rule (corpus §4.4):** "VAT always due even below threshold." Never claim "UK is duty-free" without the ≤£135 condition; never claim the parcel "pays no UK tax" — commercial goods always attract 20% VAT, the only question is **who collects it** (seller at point of sale vs recipient at delivery).

---

## 2. The two-rule regime in detail

### 2.1 Customs Duty — the £135 threshold (Great Britain)

Per GOV.UK *Tax and customs for goods sent from abroad: Tax and duty* (fetched 2026-08-08, url below):

| Type and value of goods | Customs Duty |
|---|---|
| Non-excise goods worth **£135 or less** | **No charge** |
| Goods above £135 | Rate depends on type of goods and origin — use the [UK Trade Tariff service](https://www.gov.uk/trade-tariff) |
| Excise goods (alcohol/tobacco) | Charged at any value |

- The threshold is **per consignment**, not per item: "The £135 limit applies to the value of a total consignment that is imported, not the separate value of individual items in a consignment." (GOV.UK *VAT and overseas goods sold directly to customers in the UK*).
- If Customs Duty applies, it is charged on **the price paid for the goods + postage, packaging and insurance** (GOV.UK, ibid).
- Gift relief: goods sent as gifts worth **£135–£630** attract a reduced duty of **2.5%** (lower for some goods) instead of the full rate; gifts above £630 pay the full rate (GOV.UK *Check if you can pay a reduced amount of Customs Duty*; Wise UK import-duty guide, L4, corroborating).

**Sources:**
- GOV.UK, *Tax and customs for goods sent from abroad: Tax and duty* — https://www.gov.uk/goods-sent-from-abroad/tax-and-duty (fetched 2026-08-08; content continuously maintained)
- GOV.UK, *Check if you can pay a reduced amount of Customs Duty* — https://www.gov.uk/guidance/check-if-you-can-pay-a-reduced-rate-of-customs-duty (gift relief, low-value relief)
- Wise, *Import Duty from India to the UK* — https://wise.com/gb/import-duty/from-india (L4; gifts £135–£630 = 2.5%, "lower for some goods")

### 2.2 VAT — always applies (no threshold for commercial goods)

GOV.UK *Tax and customs for goods sent from abroad*:

> "VAT is charged on all goods (except for gifts worth £39 or less) sent from outside the UK to Great Britain."

- VAT is charged at the rate applying to the goods (**20% standard rate for all 8 target craft categories** — verified per-commodity on the UK Trade Tariff, §5).
- **VAT is calculated on the total package value including: value of goods + postage, packaging and insurance + any duty you owe** (GOV.UK, ibid). This matters for landed-cost modelling: the 20% is not just 20% of the goods price.
- **VAT exemptions are minimal:** only gifts ≤£39 escape VAT. Documents are not the issue here (merchandise). There is **no de-minimis VAT relief** for commercial consignments — the old Low-Value Consignment Relief (goods ≤£15) was **abolished** (GOV.UK *VAT and overseas goods sold directly to customers in the UK*, 2020; HMRC BIRDS handbook).

**Sources:**
- GOV.UK, *Tax and customs for goods sent from abroad: Tax and duty* — https://www.gov.uk/goods-sent-from-abroad/tax-and-duty
- GOV.UK, *VAT and overseas goods sold directly to customers in the UK* — https://www.gov.uk/guidance/vat-and-overseas-goods-sold-directly-to-customers-in-the-uk (Low Value Consignment Relief removed; point-of-sale VAT rule)
- HMRC, *Bulk Import Reduced Data Set (BIRDS) — Overview of VAT on Low-Value Imports* — https://www.gov.uk/guidance/technical-handbook-on-bulk-import-reduced-data-set-birds/overview-of-vat-on-low-value-imports ("goods … are now subject to VAT regardless of their value")

---

## 3. Who pays / collects — the decisive mechanics (corpus M3, verified)

| Consignment value | Customs Duty | VAT | Who collects VAT | Handling fee at delivery |
|---|---|---|---|---|
| **≤£135** (commercial, B2C) | None | **20%** | **Indian seller at point of sale** (must register for UK VAT) | **None** (VAT already collected — delivery company has nothing to bill) |
| **≤£135** (B2B, buyer gives valid UK VAT number) | None | **20%** — reverse-charged by the **UK buyer** | UK buyer accounts for it | None |
| **>£135** (any) | MFN or CETA rate on goods+postage+insurance | **20%** | **Recipient** pays import VAT to the delivery company (Royal Mail/Parcelforce/courier) before delivery | **Yes** — Royal Mail £8 / Parcelforce £12 (see §4) |
| **Gifts ≤£39** | None | **None** | — | None |
| **Gifts £39–£135** | None | **20%** | **Recipient** (import VAT) | Yes |
| **Gifts £135–£630** | **2.5%** (reduced rate) | **20%** | **Recipient** | Yes |

### 3.1 Overseas Seller VAT (≤£135) — the key rule for Indian D2C sellers

- **Legal basis:** Section 7 VAT Act 1994 — goods sent to the UK in consignments ≤£135, which would normally be supplied outside the UK, are treated as **supplied in the UK**: domestic supply VAT applies and **import VAT is not chargeable** (HMRC VATREG37210).
- **Consequence:** the overseas seller **must charge UK VAT at the point of sale and register for UK VAT** — there is **no registration threshold** for non-established (non-UK) sellers selling direct to UK consumers (HMRC VATREG37210; GOV.UK *Charging VAT on goods sold direct to customers in the UK*).
- **B2B carve-out:** the seller need **not** register if it only sells to **UK VAT-registered businesses** that give their UK VAT number — the UK buyer reverse-charges (GOV.UK *Charging VAT on goods sold direct to customers in the UK*).
- **Practical implication for a solo artisan:** a GSTIN-less Indian artisan selling direct B2C to UK must (a) register for UK VAT, or (b) price VAT-inclusive and let the marketplace be the deemed supplier — online marketplaces (e.g., Amazon Global, Etsy, eBay) collect/remit UK VAT on ≤£135 sales on behalf of sellers, shifting the liability to the marketplace. This is a **real compliance gate** to flag in the assisted-docs build (corpus M3 confirms "Overseas seller must charge/register").

**Sources:**
- HMRC internal manual VATREG37210 (Section 7 VAT Act 1994; £135 rule; mandatory registration) — https://www.gov.uk/hmrc-internal-manuals/vat-registration-manual/vatreg37210
- GOV.UK, *Charging VAT on goods sold direct to customers in the UK* — https://www.gov.uk/guidance/charging-vat-on-goods-sold-direct-to-customers-in-the-uk (2023-03-08)
- GOV.UK, *VAT and overseas goods sold directly to customers in the UK* — https://www.gov.uk/guidance/vat-and-overseas-goods-sold-directly-to-customers-in-the-uk (2020-11-20, continuously updated)
- Tolley/LexisNexis commentary, *Consignments with a value of £135 or less* (2026-06-05) — https://www.lexisnexis.co.uk/tolley/tax/commentary/eu-and-global-vat/55-united-kingdom/consignments-with-a-value-of-135-or-less-united-kingdom

### 3.2 >£135 — recipient pays the delivery company

- GOV.UK: "Goods worth more than £135 in total: You will have to pay VAT to the delivery company either before the goods are delivered or when you collect them."
- The delivery company (Royal Mail/Parcelforce/courier) contacts the recipient with a bill stating which fees are due, and **holds the parcel ~3 weeks** before returning to sender if unpaid (GOV.UK, ibid).
- Note the recipient-side cash friction is therefore real for any >£135 shipment — but most single-artisan craft parcels are ≤£135, where this does not apply.

**Source:** GOV.UK, *Tax and customs for goods sent from abroad: Tax and duty* — https://www.gov.uk/goods-sent-from-abroad/tax-and-duty

---

## 4. Customs handling fees (Royal Mail / Parcelforce)

When **Royal Mail or Parcelforce has to collect VAT/duty from the recipient** (i.e., >£135, or gifts >£39, or excise), it levies a handling fee on top of the tax itself:

| Operator | Handling fee | When |
|---|---|---|
| **Royal Mail products** | **£8** | Dutiable/taxable items delivered by Royal Mail where fees are payable |
| **Parcelforce products** | **£12** | Parcelforce items; also EMS/express network items |
| **Parcelforce Central Clearance Bureau (CCB)** | **£25** | Goods valued **over £900** (full customs declaration handled in-house) |

Sources:
- Royal Mail Group, *Pay a fee* — https://www.royalmail.com/receiving-mail/pay-a-fee (fetched 2026-08-08: "£8 Royal Mail Products · £12 Parcelforce Products … over £900 … £25 handling fee")
- Parcelforce Worldwide, *Pay a Customs Charge* / *Importing to the UK* — https://www.parcelforce.com/receiving/customs-charge , https://www.parcelforce.com/help-and-advice/sending/importing-to-the-uk (two fee tiers: express/EMS/GLS + >£900 = higher; others = lower)
- GOV.UK refund form BOR 286 for Royal Mail/Parcelforce-delivered items (overcharge/return) — https://www.gov.uk/goods-sent-from-abroad/tax-and-duty

> **Key practical point:** for a ≤£135 commercial consignment where the seller has charged UK VAT at the point of sale, **no import VAT is due and no Royal Mail handling fee should be charged to the recipient** — the £8/£12 fee only arises when the delivery company must collect the tax.

---

## 5. Customs Duty rates — the 8 target craft categories (UK Global Tariff)

Verified 2026-08-08 directly against the **UK Integrated Online Tariff** (`trade-tariff.service.gov.uk`) using the commodity lookup with `country = India`. "MFN" = UK Global Tariff (third-country) rate; "CETA (India)" = preferential rate available with a valid Certificate of Origin under the India-UK CETA, in force 15-Jul-2026 (legal base **S.I. 2026 No. 36**, *The Customs (Tariff and Miscellaneous Amendments) Regulations 2026*). All standard **VAT 20%**.

| # | Category (project folder) | Suggested commodity code | Description (as on UK tariff) | MFN duty | CETA (India) duty | VAT |
|---|---|---|---|---|---|---|
| 1 | **block-printed-textiles** | `5208520011` / `5208520091` (Ch. 52) | Cotton woven fabric, plain weave >100 g/m², **hand-printed** ("batik") | **8.0%** | **0%** | 20% |
| 2 | **embroidered-bags-pouches** | `4202221000` (Ch. 42) | Handbags, outer surface of textile/sheeting of plastics | **8.0%** | **0%** | 20% |
| 2b | (textile cases/satchels variant) | `4202129910` | Cases of textile materials, hand-made | **2.0%** | **0%** | 20% |
| 3 | **embroidered-home-textiles** | `6304990099` (Ch. 63) | Furnishing articles (cushion covers/throws), not knitted, other textile materials | **12.0%** | **0%** | 20% |
| 3b | (embroidered table/bed linen) | `6302999090` (Ch. 63) | Table/bed/kitchen linen of other textile materials | **12.0%** | **0%** | 20% |
| 4 | **handloom-scarves-stoles** | `6214900011` (Ch. 62) | Shawls/scarves/stoles of other textile materials — cotton, **hand-made** | **8.0%** | **0%** | 20% |
| 4b | (silk scarves) | `6214100010` | Shawls/scarves of silk, hand-made | **8.0%** | **0%** | 20% |
| 5 | **imitation-artisan-jewellery** | `7117190010` (Ch. 71) | Imitation jewellery of base metal, **hand-made**, without glass | **4.0%** | **0%** | 20% |
| 6 | **jute-products** | `6305109000` (Ch. 63) | Sacks and bags of a kind used for packing, of jute (other) | **4.0%** | **0%** | 20% |
| 7 | **small-brass-metalware** | `8306290000` (Ch. 83) | Statuettes and other ornaments of base metal (brass), not plated | **0.0%** | **0%** | 20% |
| 8 | **small-woodware** | `4420909990` (Ch. 44) | Wood marquetry/statuettes/ornaments of wood (4420.90) | **0.0%** | **0%** | 20% |
| 8b | (wood tableware) | `4419900000` | Tableware and kitchenware of wood | **0.0%** | **0%** | 20% |
| 8c | (other wood articles) | `4421999999` | Other articles of wood (4421.99) | **0.0%** | **0%** | 20% |

**Reading notes:**
- **Brass ornaments (8306) and wood articles (44) are MFN 0% anyway** — CETA preference changes nothing for them. The CETA win matters for **textiles (8–12% MFN → 0%)** and **imitation jewellery (4% → 0%)**.
- **For ≤£135 consignments the duty rate is irrelevant** — no Customs Duty is charged at all. The tariff only bites on **>£135** shipments.
- These codes are *suggested* starting points; correct classification depends on the exact product (fabric composition, whether knitted, jewellery content). Wrong HS/CTH code is the #1 documented DNK error mode (corpus §5.1).
- Jute **woven fabric** (Ch. 53) also exists for jute-yardage exports (heading `5310`); the leaf rate was not individually resolvable in this pass — **flag: verify at build time**.

**Source:** UK Integrated Online Tariff, commodity lookups with country=IN, fetched 2026-08-08:
- https://www.trade-tariff.service.gov.uk/commodities/6214900011 (hand-made cotton scarves)
- https://www.trade-tariff.service.gov.uk/commodities/5208520011 · `.../6304990099` · `.../7117190010` · `.../6305109000` · `.../8306290000` · `.../4420909990` · `.../4419900000` · `.../4421999999` · `.../4202221000` · `.../4202129910` · `.../6302999090` · `.../6214100010`
- Legal base for India 0% preference: **S.I. 2026 No. 36**, https://www.legislation.gov.uk/uksi/2026/36/contents/made (also listed as `2026 No.36` on tariff pages)

---

## 6. India-UK CETA — status VERIFIED (full agreement in force) + preferential angle

### 6.1 Status: FULL CETA in force since 15-Jul-2026 (NOT a limited/interim deal)

| Fact | Detail | Source |
|---|---|---|
| Name | UK-India **Comprehensive Economic and Trade Agreement (CETA)** — a full FTA | GOV.UK collection |
| Signed | **24-Jul-2025** | GOV.UK news |
| **Entered into force** | **15-Jul-2026** | GOV.UK news (17-Jul-2026); UK Trade Tariff news (13-Jul-2026) |
| UK offer to India | **99% of Indian goods** entering the UK either duty-free or with reduced tariffs | GOV.UK news |
| India offer to UK | removes/reduces tariffs on 90% of tariff lines (64% at entry into force; 85% eligible duty-free after 10-year staging) | GOV.UK, *UK-India CETA Chapter 2: Trade in Goods* |

**Corpus check:** the parent research note — "India-UK CETA eCoO via Trade Connect since 15-Jul-2026 (TN 11/2026-2027)" — is **verified and consistent**: the DGFT eCoO rollout date (15-Jul-2026) equals the CETA entry-into-force date, and Trade Notice 11/2026-2027 exists. The parent corpus itself (2026-08-05) did not yet confirm the agreement was in force; external verification now confirms it is **a full CETA, in force, not a limited deal**.

### 6.2 The Certificate of Origin / preferential angle

- **eCoO mechanism:** from 15-Jul-2026, **Preferential Certificates of Origin under India-UK CETA are issued electronically on the Trade Connect ePlatform (trade.gov.in)** — DGFT Trade Notice **11/2026-2027, dated 13-Jul-2026** ("Electronic filing and Issuance of Preferential Certificate of Origin (CoO) under India-UK CETA with effect from July 15, 2026"). Issued via **self-declaration** or **authorised agencies** (EPCs/chambers).
- **Proof of origin options (CETA Chapter 3):** (1) origin declaration / statement on origin completed by the exporter (with a unique reference number registered/authenticated per Annex 3D framework); (2) **importer's knowledge** — the UK importer can self-claim preference if it has documentation demonstrating origin; (3) eCoO via DGFT. For Indian exports the practical route is the **DGFT eCoO (Trade Connect)** or an origin declaration on the invoice.
- **Rules of origin:** goods must be wholly obtained or substantially transformed in India (CETA Chapter 3 / Annex 3A product-specific rules). **Textiles/apparel rules are the strictest — generally require both a change in tariff classification (CTC) and a regional value content/wholesale value threshold** (NSEZ ROO FAQ). Handloom/block-printed textiles should qualify if wholly woven/finished in India, but the **value-added requirement must be met** — keep records (yarn→fabric→garment chain).
- **Why it matters for DNK parcels:** for ≤£135 consignments, duty is 0 regardless — **CETA changes nothing at the low end**. It matters for (a) **>£135 commercial shipments** (textiles drop 8–12% → 0% with a valid origin proof), and (b) **B2B/wholesale** consignments where the importer claims preference. The landed-cost engine should treat CETA preference as a **config flag "origin proof on file?"** that flips the duty column from MFN to 0% for >£135 shipments.

### 6.3 DCTS (Developing Countries Trading Scheme) note

India was in the **DCTS Standard Preferences** scheme, but the tariff data now shows the standard-preference rows as "**excluding India**" (e.g., 6214 standard = 6.4% but "excluding India") — consistent with India graduating from DCTS-standard to the **CETA preferential track**. The trade-tariff country lookup for India returns the CETA 0% preference, not DCTS. **Build rule:** do not encode DCTS for India — use CETA.

**Sources:**
- GOV.UK news, *Historic UK-India Free Trade Agreement is now in effect* (17-Jul-2026) — https://www.gov.uk/government/news/historic-uk-india-free-trade-agreement-is-now-in-effect
- GOV.UK collection, *Comprehensive Economic and Trade Agreement between the UK and India* (full text + annexes) — https://www.gov.uk/government/collections/comprehensive-economic-and-trade-agreement-between-the-united-kingdom-of-great-britain-and-northern-ireland-and-india
- UK Integrated Online Tariff news, *India Free Trade Agreement (enters into force on 15 July 2026)* (13-Jul-2026) — https://www.trade-tariff.service.gov.uk/news/stories/india-free-trade-agreement-enters-into-force-on-15-july-2026--13-july-2026
- GOV.UK, *UK-India CETA Chapter 2: Trade in Goods* / *Chapter 3: Rules of Origin* / *Annex 3B Origin Declaration Template* / *Annex 3D Authentication Framework* — https://www.gov.uk/government/publications/uk-india-ceta-chapter-2-trade-in-goods , https://www.gov.uk/government/publications/uk-india-ceta-chapter-3-rules-of-origin , https://www.gov.uk/government/publications/uk-india-ceta-origin-declaration
- DGFT Trade Notice **11/2026-2027 (13-Jul-2026)**, full text mirror — https://www.caalley.com/dgft26/TN11.pdf ; registry listing — https://www.dgft.gov.in/CP/?opt=trade-notice
- Taxguru/KNN/ELP Law coverage of TN 11/2026-2027 (14–22-Jul-2026)
- NSEZ, *FAQs on Rules of Origin* (self-certification; importer's knowledge; textiles = CTC + value addition) — https://www.nsez.gov.in/Resources/Trade/FAQs%20ROO.pdf

---

## 7. Landed-cost worked examples (UK, 2026-08-08 snapshot)

Assumptions: single commercial consignment, sold B2C, no origin proof; VAT always 20%; postage = ITPS actual weight (corpus S.O. 659(E)); goods value INR converted at illustrative **£1 = ₹108** (mid-Aug-2026 approximate — **re-derive at build time**; corpus engine must use live FX).

**Case A — small scarf parcel, ≤£135 (the typical artisan order)**
- Goods: 1 handloom cotton scarf, invoice value **£50 (~₹5,400)**
- Postage: ITPS 100 g → **₹225**
- Customs Duty: **£0** (≤£135, non-excise)
- VAT: **20% × £50 = £10** — charged by **seller at point of sale** (Overseas Seller VAT)
- Recipient pays at delivery: **£0 + no Royal Mail handling fee**
- **Landed cost to buyer = £60** (seller must remit £10 to HMRC)

**Case B — brass/wood decorative item >£135, no origin proof**
- Goods: brass statuette, invoice **£200 (~₹21,600)**; postage ITPS 1 kg **₹675** ≈ £6.25
- Customs Duty (MFN 8306 = 0%): **£0** (brass/wood are MFN-0 anyway)
- Import VAT: 20% × (goods £200 + postage/insurance £6.25 + duty £0) = **£41.25** — **recipient** pays Royal Mail/Parcelforce
- Handling fee: **£8** (Royal Mail) or **£12** (Parcelforce)
- **Recipient pays ≈ £49.25 before delivery**

**Case C — textile parcel >£135 (where CETA matters)**
- Goods: embroidered home textiles, invoice **£300**; postage EMS 1 kg ≈ ₹1,165–₹2,275 (see shipping.md)
- Customs Duty: MFN **12% × £300 = £36**; with **CETA origin proof = £0**
- Import VAT: 20% × (goods + postage + duty) ≈ £68–£70 either way (VAT is never preferential)
- **CETA saves the duty £36 but never the VAT** — the invoice origin statement/eCoO is what flips the duty column.

**Build rule (corpus §9.2 F3):** every duty/VAT/threshold must be a **config flag with source link + last-updated timestamp**, never a hard-coded number. Duty and FX are volatile; VAT at 20% and the £135 threshold are structurally stable but still date-stamped.

---

## 8. Product/classification flags for the 8 categories

- **Textiles (all 4 textile categories):** 8–12% MFN, CETA 0%. VAT 20%. Origin rules strictest (CTC + value addition). Watch: knitted vs woven classification; "hand-made" vs "other" sub-codes carry different MFN bases.
- **Imitation jewellery:** 4% MFN, CETA 0%, VAT 20%. If it incorporates natural/cultured pearls, precious/semi-precious stones, or precious-metal plating as more than a minor constituent, it is **not** heading 7117 (reclassify — possibly higher rates). Hand-made-without-glass sub-code used here.
- **Brass metalware:** 0% MFN (8306) — duty-neutral even without CETA. If classified under 7418 (table/kitchen brassware) instead, rate may differ — **verify per-product**. VAT 20%.
- **Wood:** 0% MFN on 4419/4420/4421 — duty-neutral. **CITES/wood-provenance controls** apply at import (Import control — CITES flagged on 4420/4421/4419 tariff pages): tropical/listed woods need CITES paperwork; Ireland-style outright wood bans are destination-specific but the UK still enforces CITES at import. VAT 20%.
- **Jute:** 4% MFN (sacks 6305), CETA 0%. If jute handicraft is classified as basketwork (Ch. 46), rates differ — verify.
- **No target category is VAT-exempt** — all 20% standard.

---

## 9. Northern Ireland carve-out (one line)

Northern Ireland applies different rules: VAT charged on consignments from outside the **UK and EU**, and goods "at risk" of entering the EU can face **EU rate duty / €3 flat duty on ≤£135 non-business parcels** (GOV.UK, ibid). NI is a small share of Indian craft exports; **flag, don't build for it initially.**

---

## 10. Source register (with dates)

| # | Source | URL | Date verified |
|---|---|---|---|
| S1 | GOV.UK — Tax and customs for goods sent from abroad | https://www.gov.uk/goods-sent-from-abroad/tax-and-duty | fetched 2026-08-08 |
| S2 | GOV.UK — VAT and overseas goods sold directly to customers in the UK | https://www.gov.uk/guidance/vat-and-overseas-goods-sold-directly-to-customers-in-the-uk | 2026-08-08 (pub 2020-11-20) |
| S3 | GOV.UK — Charging VAT on goods sold direct to customers in the UK | https://www.gov.uk/guidance/charging-vat-on-goods-sold-direct-to-customers-in-the-uk | 2026-08-08 (pub 2023-03-08) |
| S4 | HMRC VATREG37210 (Section 7 VAT Act 1994) | https://www.gov.uk/hmrc-internal-manuals/vat-registration-manual/vatreg37210 | 2026-08-08 |
| S5 | HMRC BIRDS handbook — Overview of VAT on Low-Value Imports | https://www.gov.uk/guidance/technical-handbook-on-bulk-import-reduced-data-set-birds/overview-of-vat-on-low-value-imports | 2026-08-08 |
| S6 | Royal Mail — Pay a fee (£8/£12/£25) | https://www.royalmail.com/receiving-mail/pay-a-fee | 2026-08-08 |
| S7 | Parcelforce — Pay a Customs Charge / Importing to the UK | https://www.parcelforce.com/receiving/customs-charge | 2026-08-08 |
| S8 | UK Integrated Online Tariff — per-commodity lookups (country=IN) | https://www.trade-tariff.service.gov.uk/commodities/6214900011 (etc.) | fetched 2026-08-08 |
| S9 | S.I. 2026 No. 36 (CETA preferential tariffs legal base) | https://www.legislation.gov.uk/uksi/2026/36/contents/made | 2026-08-08 |
| S10 | GOV.UK — Historic UK-India FTA in effect (CETA, 15-Jul-2026) | https://www.gov.uk/government/news/historic-uk-india-free-trade-agreement-is-now-in-effect | 17-Jul-2026 |
| S11 | GOV.UK — UK-India CETA collection (Ch.2, Ch.3, Annex 3B/3D, origin declaration) | https://www.gov.uk/government/collections/comprehensive-economic-and-trade-agreement-between-the-united-kingdom-of-great-britain-and-northern-ireland-and-india | 2026-08-08 |
| S12 | DGFT Trade Notice 11/2026-2027 (eCoO, 15-Jul-2026) | https://www.caalley.com/dgft26/TN11.pdf | 13-Jul-2026 |
| S13 | NSEZ ROO FAQ (self-certification, textiles rules) | https://www.nsez.gov.in/Resources/Trade/FAQs%20ROO.pdf | 2026-08-08 |
| S14 | Wise — Import Duty from India to the UK (L4 gift rates) | https://wise.com/gb/import-duty/from-india | 2026-08-08 |

Corpus anchors: `report.md` §4.4 (UK row), `04-synthesis/findings.md` F-H5, `follow-ups/01-order-to-delivery-flow/findings.md` §3 M3.

---

## 11. Confidence flags (honesty summary)

- **£135 duty threshold + 20% VAT on all commercial imports + ≤£135 seller-VAT-at-POS + >£135 recipient-import-VAT: High (90%+)** — L1 GOV.UK/HMRC primary sources.
- **Handling fees £8/£12/£25: High (90%)** — Royal Mail/Parcelforce official.
- **Tariff table (MFN + CETA 0% per code): High (90%)** — direct UK Trade Tariff API read, 2026-08-08. The *code assignment* to a specific physical product is the uncertain part (40–60% until a specific product is classified).
- **CETA in force 15-Jul-2026, eCoO via Trade Connect: High (88–95%)** — multiple L1 sources (GOV.UK, DGFT TN, Trade Tariff news).
- **£1→INR conversion: illustrative only** — re-derive at build (no fixed rate; flag).
- **Jute woven fabric (Ch. 53) leaf rate + 7418 brass tableware rate: unverified** — flagged, needs lookup at build.

*End of file. All figures cited with URL + access date; every estimate flagged.*
