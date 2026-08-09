# Category Doc — Small Woodware (wooden toys, boxes, statuettes, marquetry, lamp shades, kitchenware)

**Project:** SIH260113 — DNK Export Enablement · **Doc date:** 2026-08-08
**Confidence convention (corpus-wide):** High 80–95% · Moderate 60–80% · Low 40–60% · Speculative <40%. Items marked ⚑ are flags the build must re-verify at ship-time (US duty basis changes ~every 6–14 months; see corpus H5-a, O11).
**Warning banner (do not strip):** this is the highest-compliance category of the four. Wood = plant material, and *destination-side* rules (Lacey Act, AU biosecurity, EU/Ireland restrictions, CITES species) are the real export blockers — not India-side paperwork. Every wood consignment must be species-clean, source-legal, bark-free, and pest-free.

---

## 1. HS / CTH classification

The relevant 6-digit headings for small woodware (Chapter 44 "Wood and articles of wood"):

| 6-digit HS | Description (WCO) | Typical in-scope goods | India 8-digit ITC-HS (likely) | Confidence |
|---|---|---|---|---|
| **4419** | Tableware and kitchenware, of wood | wooden spoons, chopping boards, bowls, ladles | 4419 00 10 / 4419 00 90 ⚑ (2012 Indian schedule has 4419 00 10 / 00 90; **verify against current ITC-HS/ICEGATE** — low-precision) | Low |
| **4420** | Wood marquetry & inlaid wood; caskets & cases for jewellery/cutlery; statuettes & other ornaments of wood | jewellery boxes, caskets, inlaid panels, carved figurines, table ornaments | **4420 11 00** (statuettes/ornaments of tropical wood), **4420 19 00** (other statuettes/ornaments), **4420 90 10** (wood marquetry & inlaid wood), **4420 90 90** (other) | High for the 8-digit set |
| **4421** | Other articles of wood (residual) | wooden toys, candle stands, lacquerware, carved decorative items, hangers, lamp bases | **4421 90 90** (other articles of wood — handicrafts/decorative) — corroborated by DGFT ITC-HS Export Schedule 2 (sandalwood line lists "4421 90 60, 4421 90 90") and handicraft guides | Moderate–High |

Key classification rules:
- **Do not use Chapter 94** (furniture/luminaires). Wooden lampshade *frames* are 4421/4419; a complete lighting fitting is Ch 94. Flag to the user in the PBE assist if "lamp shade" is declared.
- **Do not use Chapter 95** (toys) if the item is a *decorative* toy-like object sold as ornament — CBP/UK note 1(p) Ch 44 excludes toys; but Indian ITC-HS 4421 is routinely used for "wooden toys" in export data. Practical split: functional plaything → 9503; decorative craft item → 4421. (Moderate confidence on the practical guidance.)
- **Frames for pictures/photos → 4414**, not 4421. **Baskets/wicker of Chapter 46** are NOT this category (they sit with jute/vegetable plaiting).
- Casket/jewellery-box line (4420 90 in India, "jewelry boxes… of wood" in US 4420.90) — the *specific* line for wooden jewellery boxes.

Sources: DGCIS Chapter 44 PDF (4420 8-digit structure) · EPCH HS-code list (4420 11 00 / 4420 19 00 / 4420 90 10 / 4420 90 90) · DGFT ITC-HS Export Schedule 2, Table B Ch 44 (sandalwood handicraft line "4414/4415/4419/4420/4421 90 60, 4421 90 90") · impexkit "HSN Code for Wooden Handicraft" (44219090). ⚑ India's 8-digit detail for 4419 is inconsistent across sources — resolve at build from the current ITC-HS or an ICEGATE lookup.

---

## 2. PBE declaration description guidance (what to type on PBE-III/IV + CN 22/23)

The DNK SOP requires a **specific, non-vague description** per piece with an HS code. For woodware:

- **Mandatory elements:** material(s) in plain terms, finish, product type, and — critically — **wood species** where known. Correct: `Wooden jewellery box (mango wood, lacquer finish)` → HS 44209090. Bad: `wooden handicraft`, `wood items`, `decoration`.
- **Species matters, not just for duty:** APHIS Lacey declarations and AU BICON ask for the **scientific name (genus + species)** of plant material. Where the artisan does not know the species (e.g., mixed waste-wood carvings), declare honestly (`mixed hardwood, species unknown`) — a false declaration is the Lacey violation that gets parcels seized, not an honest "unknown".
- **Finish drives biosecurity risk:** say whether sealed/painted/lacquered (lower biosecurity risk) vs raw/unfinished wood (higher; may need treatment/certificate for AU).
- **Bark:** declare if bark is present (e.g., "rustic wall art with bark edge") — AU has a *separate* BICON case for bark-featured items; misdeclared bark = hold/destroy.
- **Value/weight discipline:** Σ piece values ≤ parcel value; gross weight ≤ 110% of net (SOP validation rules). Lamp shades must be weighed **boxed** — see §5.
- **CITES species:** if the wood is rosewood/sandalwood/red sanders (see §4), the description must be exact because the CITES/Comparable-Certificate route is species-specific.

---

## 3. Destination duty & VAT notes (2026-08-08 snapshot)

Overlay these on the corpus landed-cost rule: postage (ITPS 50-g slabs / EMS 250-g slabs) + destination duty + destination VAT/GST + handling. **Every figure below is a config flag with source + last-updated timestamp, never a hard-coded number.**

| Destination | Duty | Tax | Category-specific notes |
|---|---|---|---|
| **USA** | MFN 3.2% (4420, 4421; 4419.90 ≈3.2%) **+ Section 301 10% on India** (24-Jul-2026; net-of-MFN; ~45% of exports exempt — check whether wood is on the exemption list ⚑). **De minimis suspended** (29-Aug-2025) → every parcel dutiable. | State sales tax varies; none at federal customs | Lacey Act declaration applies at **formal entry only** (see §4). Section 301 basis has changed 4× in 14 months — never quote it as fixed. |
| **UK** | **Duty-free ≤ £135** (postal). UKGT rate on 4421 = **0.00%**; 4420 also 0% on the same chapter schedule. | **20% VAT on all consignments, always** | The £135 de minimis, not the UKGT rate, governs small parcels. |
| **UAE** | Duty-free ≤ **AED 1,000** (duty-only exemption) | **5% VAT on all commercial imports** | AED 1,000 exempts duty, not VAT. |
| **Australia** | Duty-free ≤ **AUD 1,000** | **GST 10% on all** (vendor-collected) | **Biosecurity is the real gate**: BICON "Timber and timber products" case applies to all wooden articles (see §4). |

Sources: US — hts.usitc.gov / open-gov HTS 4420 (3.2%), tariffstool 4421 (3.2–3.3%), TariffLens 4420.19 (3.2% + IEEPA/S.122/S.301 notes), corpus F-H5-a/b (S.301 10% 24-Jul-2026; de minimis suspension factsheet); UK — trade-tariff.service.gov.uk/headings/4421 (fetched 8-Aug-2026, all 4421 subheadings 0.00% duty, 20% VAT), corpus §4.4; UAE — corpus F-H5-e (5% VAT on all; AED 1,000 duty-only); AU — corpus §4.4, DAFF timber import pages.

---

## 4. Certifications & restrictions — CRITICAL (this section decides whether the parcel flies)

### 4.1 India-side (export control)
- **Export policy is "Free"** for finished wood handicrafts, including sandalwood finished products (DGFT ITC-HS Schedule 2 Table B, entry 149: sandalwood finished handicrafts under 4414/4415/4419/4420/4421 90 60 /4421 90 90 are Free). Raw timber/logs/sandalwood in un-finished forms are restricted/prohibited — do not ship raw wood.
- **CITES export paperwork (only for CITES-listed species):**
  - **Indian rosewood / shisham (*Dalbergia sissoo*) and East-Indian rosewood (*Dalbergia latifolia*)** are CITES **Appendix II** (since 2017), but **India lodged a reservation** (26-Jan-2017) and exports finished products under a **CITES Comparable Certificate** issued by MoEFCC — **excluding logs, timber, stumps, roots, bark, chips, powder, flakes, dust, charcoal**. CoP19 (Nov-2022) explicitly relaxed finished shisham furniture/handicrafts. Practical rule: *finished, decorated handicraft of sissoo/rosewood = exportable with a Comparable Certificate; raw wood = not.* ⚑ For DNK postal volumes, verify whether the comparable-certificate route is practical for single parcels or reserved for bulk consignees.
  - **Red sanders (*Pterocarpus santalinus*)** — Appendix II **plus a national zero-quota/suspension since 31-May-1999** (exports only of seized stock, under licence). **Effectively a dead-end for artisans — do not ship red sanders.**
  - **Sandalwood (*Santalum album*)** — not CITES-listed; finished sandalwood handicrafts export Free (DGFT), but sandalwood is state-controlled in India (legal-provenance documentation expected). Ship only finished, carved/decorative items with invoice showing legal purchase.
  - **Teak (*Tectona grandis*)** — not CITES-listed, but Indian Forest Act + legality documentation; finished handicrafts are routinely exported.
- **India Post prohibitions:** per-corpus Ctx-4, wood/wood articles are **per-destination permission**; India Post's `Country_List.pdf` per-country tables are scanned/non-machine-readable. Ireland is the known outright ban (below).

### 4.2 Destination-side (the real blockers)
- **USA — Lacey Act plant declaration.** Required when a shipment (1) contains plant material, (2) is in an APHIS-listed HTS code, **and (3) enters as a formal entry** (entry types 01/02/03/06/07; formal entries generally ≥ US$2,500 value and bonded). **Informal entries, personal importations, and mail "unless subject to formal entry" do not require the declaration** (APHIS enforcement notice, 2020 Federal Register). Consequence for DNK: a typical ₹2,000–5,000 woodware parcel is an **informal/mail entry → Lacey declaration generally NOT required**. **But:** (a) with de minimis suspended, higher-value wood parcels may route into formal postal entry (19 CFR Part 145; Entry Type 13 per corpus F-H5-b) — if so, Lacey applies; (b) **"due care" applies regardless of declaration** — the importer must be able to show the wood was legally harvested; (c) CITES species are always regulated. **Do not over-warn (it is not a flat requirement for small parcels) and do not under-warn (it IS a flat requirement for formal entries).** ⚑ Re-check whether the current US postal-entry treatment pushes small wood parcels to formal entry.
- **Australia — BICON biosecurity (mandatory, applies to every parcel regardless of duty).** Wooden articles fall under the DAFF **"Timber and timber products"** BICON case: manufactured wooden articles where **at least one dimension ≤ 200 mm** (bigger pieces → "logs, log cabins and oversize timber" case). Conditions: **bark-free** (bark-featured items = separate case), **pest-free**, and compliance demonstrated via **manufacturing process or approved treatment** verified by documentation/declaration. Finished/sealed pieces are low-risk; raw/unfinished wood may require treatment (e.g., ISPM-15) or, if standard conditions can't be met, a **non-standard import permit** (the old "wooden article permit" pathway was removed; permit route remains for non-standard goods). The buyer/importer must check BICON and have documentation ready.
- **EU / Ireland — outright wood ban.** Corpus Ctx-4 + India Post `Country_List_Ireland.pdf`: **Ireland bans wood/plant products outright via the postal channel**. This is a hard destination-level block — do not route wood to Ireland. Other EU destinations: EU postal lane is open via PDDP (corpus H6), but plant-material restrictions vary per country — always check the per-country postal list (scanned PDF, curate top-N).
- **Phytosanitary certificates:** generally **not** required for finished/sealed wood handicrafts to US/UK/UAE/AU **unless the item is raw or contains seeds/bark/soil** (soil is strictly banned everywhere). If in doubt → ship finished/sealed pieces only.

### 4.3 What the exporter should physically carry
Commercial invoice (species + finish stated) · packing list · source/legal-purchase proof for any controlled species · CITES Comparable Certificate if sissoo/rosewood · BICON-ready declarations (AU) · copy of the DNK PBE/CN22 · EPCH RCMC (for FTP incentives, not for clearance).

---

## 5. Shipping lane notes

- **Weight profile:** mixed. Carved statuettes and boxes are **dense-heavy** (good for postal); **marquetry panels, lamp shades and light frames are bulky-light** — the dangerous profile.
- **Volumetric risk (the worked example, corpus F-H5-c/d):** boxed lamp shade 50×50×30 cm at 1.5 kg actual bills as **12.5–15 kg volumetric** on EMS (÷4000–6000), a **7–8× price blow-up** vs ITPS actual-weight (≈₹715 @1 kg). **Steer all ≤2 kg woodware to ITPS (volume-free, 135 countries, 50-g slabs, 2 kg cap on US/AU/CA).** If >2 kg and bulky → EMS volumetric divisor is a *configurable* flag (÷4000/5000/6000), never hard-coded.
- **Indicative ITPS postage** (gazette Table VIII, corpus §4.1): 500 g → USA ₹715, UK ₹425, UAE ₹320, AU ₹800; 1 kg → USA ₹1,065, UK ₹675, UAE ₹470, AU ₹1,250.
- **Packing:** use foam/padding to keep box small (volumetric). For AU: **no straw, no second-hand bags/sacks, no soil** in packaging (destroyed + charges). For US: no bark.
- **Cap check:** ITPS US/Australia/Canada = **2 kg**; a woodware parcel over 2 kg to these markets must go EMS/Air-Parcel (with volumetric flag).

---

## 6. Sources
- DGCIS Chapter 44 ITC-HS: `https://www.dgciskol.gov.in/Writereaddata/Downloads/2012/CHP_44.pdf`
- EPCH HS-code list for handicrafts: `https://www.epch.in/sites/default/files/policies/hscode.pdf`
- DGFT ITC-HS Export Schedule 2, Table B, Ch 44 (sandalwood handicrafts line): `https://www.eximguru.com/exim/dgft/itc-hs-export-schedule-2/table-b-chapter-44-...aspx`; DGFT Export Policy Schedule 2: `https://content.dgft.gov.in/Website/dgftprod/254a0ac9-bbe8-4d7a-918a-4cd33d96aad5/Export%20Policy.pdf`
- US HTS: `https://hts.usitc.gov`; open-gov 4420 `https://open-gov.usebase.io/tariffs/us/44/4420`; tariffstool 4421 `https://www.tariffstool.com/hts/other-wood-articles-4421`
- US de minimis suspension factsheet: `https://www.cbp.gov/sites/default/files/2025-08/factsheet_suspension_of_duty-free_de_minimis_treatment.pdf` (corpus copy in `data/06-legal-sources/`)
- APHIS Lacey Act requirements: `https://www.aphis.usda.gov/plant-imports/file-lacey-act-declaration/requirements`; entry-type table `https://www.aphis.usda.gov/plant-imports/file-lacey-act-declaration/lacey-act-requirements-entry-type-code`; enforcement notice `https://www.govinfo.gov/content/pkg/FR-2020-03-02/pdf/2020-04165.pdf`; 7 CFR §357.3 `https://www.law.cornell.edu/cfr/text/7/357.3`
- Australia DAFF timber imports: `https://www.agriculture.gov.au/biosecurity-trade/import/goods/timber` and types page; BICON: `https://bicon.agriculture.gov.au` (search "wooden manufactured articles", "wooden manufactured articles containing bark")
- CITES: India reservation & comparable certificate `https://moef.gov.in/uploads/2018/03/CITES%20comparable%20document.pdf`; Kew "CITES and Timber" (red sanders zero quota) `https://www.kew.org/sites/default/files/2019-02/CITES%20and%20Timber_Second%20Edition.pdf`; CoP19 shisham relaxation `https://www.downtoearth.org.in/wildlife-biodiversity/cop19-cites-relaxes-restrictions-on-export-of-indian-shisham-products-86169`
- UK Integrated Online Tariff 4421: `https://www.trade-tariff.service.gov.uk/headings/4421` (fetched 2026-08-08)
- India Post Ireland country list: `https://www.indiapost.gov.in/VAS/ProhibitedItemsDocuments/Country_List_Ireland.pdf` (JS-rendered copy in corpus)
- Corpus anchors: report.md §4.3/§5.2, findings.md Ctx-4/F-H5

**Flags (⚑) to resolve at build:** current US S.301 exemption list for Ch 44 · whether US postal entry for de minimis-suspended parcels is formal (→Lacey) or informal · India 8-digit detail for 4419 · Ireland's exact wood sub-categories (scanned PDF not parseable).
