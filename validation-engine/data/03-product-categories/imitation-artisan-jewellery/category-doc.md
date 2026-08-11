# Category Doc — Imitation / Artisan Jewellery (imitation jewellery, base-metal & beadwork)

**Project:** SIH260113 — DNK Export Enablement · **Doc date:** 2026-08-08
**Confidence convention (corpus-wide):** High 80–95% · Moderate 60–80% · Low 40–60% · Speculative <40%. Items marked ⚑ must be re-verified at ship-time.
**Warning banner:** two silent margin-killers live in this category — (1) **magnetic clasps = IATA Class 9 dangerous goods** when above threshold (postal rejection risk at scale), and (2) **lead/cadmium content limits** (US CPSIA for children's pieces, EU/UK REACH for everything). Neither blocks a clean, adult, magnet-free parcel — both become hard blockers the moment they are ignored.

---

## 1. HS / CTH classification

**This category is HS 7117 (imitation jewellery) — it is NOT 7113/7114** (jewellery/goldsmiths' wares of precious metal). If a piece contains precious metal beyond plating/minor constituents, or precious/semi-precious stones, it moves out of 7117 (Ch 71 note 11; UK tariff note quoted in sources).

| 6-digit HS | Description (WCO) | Typical in-scope goods | India 8-digit ITC-HS (likely) | Confidence |
|---|---|---|---|---|
| **7117** | Imitation jewellery | beaded necklaces, bracelets, earrings (non-piercing or stud), bangles, brooches, anklets, "junk jewellery", terracotta/brass/kundan-style base-metal pieces, lac bangles | **7117 11 00** (cuff-links & studs), **7117 19 10** (bangles), **7117 19 20**, **7117 19 90** (other, base metal, plated or not), **7117 90 10**, **7117 90 90** (other) | High (set) — common handicraft code **7117 19 90** |
| 7113 / 7114 | Jewellery of precious metal / goldsmiths' wares | silver/gold/platinum pieces | — | **Out of scope** — flag if declared |
| 7117 boundary rule | Ch 71 note 11: 7117 excludes articles with natural/cultured pearls, precious/semi-precious stones, or precious metal other than as **plating or minor constituents** | | | apply strictly |

Notes:
- **Beaded pieces with seed beads / semi-precious beads** stay in 7117 when the beads are not "precious or semi-precious stones" per note 4(C) of Ch 71 (glass, plastic, terracotta, lac, wood, base-metal beads = 7117). If the piece uses genuine gemstones → 7116/7113 territory. (Moderate — verify borderline products.)
- **Hair ornaments/combspins → 9615, buttons → 9606** (excluded from 7117 by note 11).
- India import-tariff schedules (GJEPC PDF) confirm the 8-digit set: 71171100, 71171910 (bangles), 71171990 (other), 71179090 (other). **Export policy Free.**

Sources: GJEPC India import tariff PDF (7117 8-digit set) · eximguru India customs duty 7117 (all lines "Free" import policy shown; export free) · XIMPEX HS 71171910 · UK Integrated Online Tariff heading 7117 (note 11 definition, fetched 2026-08-08).

---

## 2. PBE declaration description guidance

- **Mandatory:** material composition + type. Correct: `Imitation jewellery necklace, glass beads + base-metal clasp (no precious metal)` → 71171990. `Brass-plated imitation bangle set` → 71171910. Avoid `jewellery` / `artificial jewellery` / `metal item` alone (vague description = PBE rejection risk, corpus §7 pain 3).
- **State the metals truthfully:** "brass base, gold-coloured plating" keeps you in 7117; a piece described as "gold jewellery" or "silver necklace" invites 7113 re-classification and (worse) India-side gold-export rules (§4.1).
- **Declare any animal/plant components** (wood beads → cross-reference the woodware doc's Lacey/biosecurity notes; bone/horn/shell beads → destination wildlife/CITES check; seeds → treat like jute/plant material for AU).
- **Magnetic clasp:** disclose in the description and in the CN22 if strong — see §4.2.
- Weight discipline: jewellery is dense-small; Σ piece weights ≤ parcel weight; Σ piece values ≤ parcel value (SOP rules).

---

## 3. Destination duty & VAT notes (2026-08-08 snapshot)

| Destination | Duty | Tax | Category-specific notes |
|---|---|---|---|
| **USA** | **7117.90.90.00 "Other" = 11% MFN** (7117.90.55.00 = 7.2%; base-metal 7117.19.90 ≈ 11%; 7117.11 cuff links ≈ 10.4%) **+ Section 301 10% on India** (24-Jul-2026). **De minimis suspended** → every parcel dutiable. | State taxes vary | ⚑ S.301 basis moved 4× in 14 months (corpus H5-a). Note the subheading choice changes duty: "other" 7117.90.90 = 11% vs toy jewellery lines = Free — classify honestly. |
| **UK** | Duty-free ≤ **£135** (postal). UKGT on 7117 = **4.00%** (7117110000, 7117190010, 7117190090, 7117900000 — official, fetched 8-Aug-2026). | **20% VAT always** | £135 de minimis governs small parcels; VAT always due. |
| **UAE** | Duty-free ≤ **AED 1,000** (duty-only) | **5% VAT on all commercial imports** | Cheap lane; VAT on all. |
| **Australia** | Duty-free ≤ **AUD 1,000** | **GST 10% on all** | No biosecurity issue **unless plant/animal components** (seeds, wood, shell, bone) — then see woodware/jute biosecurity notes. |

Sources: US — open-gov 7117.90 duty table (11% / 7.2% / Free lines), CBP ruling HQ H343827 (7117.19.9000 11.1%, China 25% S.301 note), NY 815436 (7117.11 10.4%, 7117.19.90 11%), corpus F-H5-a/b; UK — trade-tariff.service.gov.uk/headings/7117 (fetched 2026-08-08); UAE/AU — corpus §4.4.

---

## 4. Certifications & restrictions

### 4.1 India-side
- **No NOC required for imitation jewellery as such.** Export policy is Free.
- **Gold/bullion rule applies only to precious-metal content:** postal export of gold (jewellery/coins) above **₹20,000 is banned** (corpus §5.2). Imitation jewellery is fine because precious metal is only plating/minor constituent — but a "gold jewellery" misdescription can trigger this rule. Keep descriptions to imitation jewellery.
- **CITES cross-checks (edge cases):** pieces incorporating animal products (ivory, tortoiseshell, some shells/corals) or protected plant products (e.g., rudraksha/mani-mala seeds may be exempt but verify; sandalwood beads) carry CITES/Wildlife Act restrictions. This is a niche but real blocker — flag in the product rule engine.

### 4.2 Magnets — the category-specific compliance trap (CRITICAL)
- **Magnetic clasps/earring backs are magnetised material = IATA Class 9 dangerous goods (UN 2807, Packing Instruction 953)** when the field exceeds the exempt threshold: **≤ 0.418 A/m (≈0.00525 gauss) at 4.6 m** OR compass deflection **≤ 2° at 4.6 m** from the assembled package. Below that → ships as general cargo; above it → regulated DG with labelling + AWB statement + shipper's declaration (and IATA DGR 2.3 trained shipper), which **postal channels will not accept**.
- Corpus §5.2 flags magnetic-closure boxes as "a compliance trap at scale". For DNK: a parcel of many neodymium-clasp necklaces can easily exceed the threshold. **Build rule:** jewellery with magnetic clasps → (a) test/pack so the assembled parcel is below threshold, or (b) use non-magnetic clasps (hook/spring-ring), or (c) reject magnetic-clasp parcels for postal export. Do not silently ship.
- Sources: radialmagnet "Shipping Magnetized Material UN 2807 / PI 953", FAA PackSafe Magnets (0.00525 gauss at 4.5 m), ICC/PHMSA interpretation 09-0084.

### 4.3 Heavy-metal content limits (destination consumer-safety law — enforced at import/listing, not customs declaration)
- **US — children's jewellery (intended for ≤ 12 yrs):** CPSIA total lead ≤ **100 ppm** in accessible substrate and ≤ **90 ppm** in paint/coating; **cadmium ≤ 75 ppm** per component (CPSC staff guidance; standard ASTM F2923-14). Non-compliant = banned hazardous substance; at scale this triggers CPSC recall/import detention, not just duty.
- **US — adult jewellery:** no federal limit; **California Prop 65** warning/limits apply (lead typically ≤ 500 ppm metal / ≤ 300 ppm for some components — state-specific ⚑).
- **EU REACH Annex XVII:** lead (Entry 63) ≤ **500 mg/kg** in metal parts of jewellery; **cadmium (Entry 23) ≤ 100 mg/kg** (0.01%) — including via skin-contact/licking route; **nickel (Entry 27) release ≤ 0.2 µg/cm²/week** for piercing posts, ≤ 0.5 µg/cm²/week for prolonged skin contact. **UK REACH mirrors EU REACH** (assimilated).
- Practical: base-metal alloy composition in Indian artisan jewellery is variable (brass often contains lead ~1.5–3.5%). **Test-before-scale** for any children's line; for adult lines, prefer certified lead-free/nickel-free findings. US test reports do **not** satisfy EU REACH (separate testing) — cite euverify + ECHA + Business Companion.
- Sources: CPSC total-lead page + 16 CFR 1500.91; QIMA "CPSIA Regulations for Children's Jewelry / ASTM F2923"; ECHA nickel restriction entry 27; EUR-Lex 32011R0494 (cadmium); Business Companion (UK REACH jewellery metal content); euverify REACH jewellery.

### 4.4 Destination customs
- No biosecurity/certificate normally required for metal-and-bead jewellery to US/UK/UAE/AU.
- If seeds/wood/plant parts: apply the relevant jute/woodware notes (AU biosecurity; US Lacey only at formal entry).
- No CoO needed unless claiming a preference (none applies to India for these markets).

---

## 5. Shipping lane notes

- **The best postal category:** small + dense. A typical 100–200 g jewellery parcel is near-minimum ITPS cost — jewellery is the cheapest-to-ship craft category.
- **Indicative ITPS postage** (gazette Table VIII): 100 g → USA ₹435, UK ₹225, UAE ₹200, AU ₹440; 200 g → USA ₹470, UK ₹250, UAE ₹215, AU ₹485 (direct arithmetic on 50-g slabs).
- **No volumetric risk** (dense). EMS only if > 2 kg (rare for jewellery) or to a non-ITPS destination.
- **Protection packaging:** anti-tarnish pouches; keep the outer box small. Strong magnets change the risk class — see §4.2 (a bulky magnetised box can also trip the volumetric divisor on EMS, but the DG rule is the primary issue).
- **Recommendation:** ship jewellery ≤ 500 g on ITPS to all four markets; it is the natural volume lane for the persona.

---

## 6. Sources
- GJEPC India import tariff (8-digit 7117 set): `https://gjepc.org/pdf/India's-Imports-Tariff-Rates-at-HS-Code-8-digit-level-26-06-2025.pdf`
- eximguru India customs duty 7117: `https://www.eximguru.com/indian-customs-duty/7117-imitation-jewellery-of-base.aspx` and 71179090 page
- US HTS: open-gov 7117.90 `https://open-gov.usebase.io/tariffs/us/71/7117.90`; CBP ruling HQ H343827 `https://rulings.cbp.gov/docs/hq/2025/h343827`; NY 815436 (customsmobile.com)
- UK Integrated Online Tariff 7117: `https://www.trade-tariff.service.gov.uk/headings/7117` (fetched 2026-08-08)
- IATA Class 9 magnets: `https://www.faa.gov/hazmat/packsafe/magnets`; `https://radialmagnet.com/shipping-magnetized-material/`; PHMSA interp `https://www.phmsa.dot.gov/regulations/title49/interp/09-0084`
- CPSC lead: `https://www.cpsc.gov/Business--Manufacturing/Business-Education/Lead/Total-Lead-Content`; 16 CFR 1500.91 `https://www.law.cornell.edu/cfr/text/16/1500.91`; QIMA children's jewellery `https://www.qima.com/blog/lab-testing/childrens-jewelry-cpsia-regulations`
- ECHA nickel entry 27: `https://echa.europa.eu/documents/10162/17233/nickel_restriction_prolonged_contact_skin_en.pdf`; EU cadmium Reg 32011R0494 `https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02011R0494-20110610`; Business Companion UK REACH `https://www.businesscompanion.info/en/quick-guides/product-safety/jewellery-safety-metal-content`; euverify `https://euverify.com/resource/reach-compliance-for-jewellery/`
- Corpus anchors: report.md §5.2 (magnets, gold >₹20k), findings.md Ctx-4, F-H5

**Flags (⚑) to resolve at build:** current US S.301 exemption list for 7117 · exact US subheading match for multi-material pieces (7117.90.90 vs 7117.19.x) · CA Prop 65 limits for adult jewellery · whether any seed/animal-component lines in scope need CITES/biosecurity checks.
