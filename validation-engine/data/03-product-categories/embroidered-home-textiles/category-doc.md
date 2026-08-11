# Category Doc — Embroidered Home Textiles

**DNK export-enablement · SIH260113 · prepared 2026-08-08**
**Scope:** hand-embroidered **bed linen** (bedsheets, pillow covers, bedspreads, duvet covers), **table linen** (runners, tablecloths, napkins), **kitchen/toilet linen** (towels), **furnishing** (cushion covers, curtains, wall hangings) — cotton/silk/wool, made-to-order artisan goods.
**Confidence legend:** 🟢 High 80-95% · 🟡 Moderate 60-80% · 🔴 Low 40-60% · ⚠️ Flagged/verify at build.
**Build rule (report §4.3):** every duty/VAT/postage figure is a **snapshot** → land as config flags with source + timestamp, never hard-coded.

---

## 1. HS / CTH Classification

### 6-digit HS candidates

| 6-digit | Description | Use for |
|---|---|---|
| **6302** | Bed linen, table linen, toilet linen & kitchen linen | 🟢 bedsheets, pillow covers, duvet covers, tablecloths, runners, napkins, towels |
| **6303** | Curtains (incl. drapes) & interior blinds; curtain/bed valances | 🟡 embroidered curtains/drapes |
| **6304** | Other furnishing articles (excl. 9404) — bedspreads, cushion covers, wall hangings | 🟢 cushion covers, bedspreads, wall hangings, runners that read as "furnishing" |

**Line-drawing that matters:**
- **Bed linen** (sheets/pillowcases/duvets) → **6302**; **bedspreads & cushion covers** → **6304**; **curtains** → **6303**. An embroidered **bedspread is 6304, not 6302** (report §5.2 note "excluding those of heading 9404"; US rulings classify duvet covers in 6302.31 and pillow shams in 6304.92 — e.g. CBP N070728, NY H84988). 🟢
- **Embroidered towels** → **6302.60** (terry) — bathroom towel linen. 🟢
- Embroidered **tablecloth/runner** → **6302.51** (table linen, cotton). 🟢
- If the article is a **set for retail sale** (bed-in-a-bag), classify by the component giving essential character (usually the bedsheet → 6302). 🟡

### Likely 8-digit ITC-HS India codes

| ITC-HS 8-digit | Description | Confidence |
|---|---|---|
| **6304 19 40** | Bed sheets and bed covers, of cotton, **handloom** | 🟢 HEPC-attested — preferred for handloom bedspreads |
| 6304 19 10 | Bedsheets and bedcovers, of cotton (general) | 🟡 (ecer.com India schedule) |
| 6304 19 90 | other bedspreads | 🟡 |
| **6304 92 11 / 21 / 31 / 41 / 81 / 91** | Counterpanes / napkins / pillow cases & slips / table cloth & covers (×2) / other furnishing — **of handloom** | 🟢 HEPC-attested handloom furnishing lines — **preferred for embroidered cushion covers, runners, pillow slips** |
| **6304 99 91** | Furnishing articles of silk, **handloom** | 🟢 silk cushion covers/embellishments |
| **6304 99 92** | Furnishing articles of wool, **handloom** | 🟢 wool throws/wall hangings |
| 6304 99 10 | Silk cushion covers (general) | 🟡 |
| **6302 21 10** | Other bed linen, printed, of cotton — **handloom** | 🟢 printed-embroidered bedsheets |
| **6302 51 10** | Table linen, of cotton — **handloom** | 🟢 embroidered runners/tablecloths |
| **6302 60 10** | Toilet/kitchen linen, terry cotton — **handloom** | 🟢 embroidered towels |
| **6302 91 10** | Other bed/table/toilet/kitchen linen, of cotton — **handloom** | 🟢 catch-all cotton home-textile linen |
| 6303 99 xx | Curtains of other textile materials | 🟡 8-digit split for embroidered curtains — verify |
| **6307 10 30** | Floor cloths etc. of cotton — handloom | 🟡 only if kitchen dusters/cleaning cloths |

**Which variant fits made-to-order artisan goods:** HEPC gives India a **handloom 8-digit line for almost every home-textile article** (6302/6304 above) — use the handloom line when the base fabric is handloom, and pair it with Handloom Mark. For **embroidered (not printed) cotton bedsheets**, prefer 6302 91 10 (other cotton handloom) over 6302 21 10 (printed). 🟡 Verify all 8-digit codes on trade.gov.in / ICEGATE before filing.

---

## 2. PBE Declaration (prd_desc) Guidance

**Do:** `hand-embroidered cotton cushion cover, 100% cotton handloom base, kantha embroidery, 45x45 cm, zip closure`
**Don't:** `cushion`, `pillow cover`, `home linen`, `bed sheet`.

Template:
```
hand-embroidered {article: bedsheet | pillow cover | duvet cover | bedspread | cushion cover | table runner | tablecloth | towel | curtain | wall hanging}, {material: 100% cotton | silk | wool} {handloom|powerloom} base, {stitch: kantha | phulkari | chikankari | zardozi | mirror-work}, size {W x L} cm/{single|double|queen|king}, {closures: zip | buttons | open}
```

Tips:
- **Name the article precisely** — bedsheet (6302) vs bedspread (6304) vs cushion cover (6304.92) vs runner (6302.51). The word you choose drives the heading.
- **Name the embroidery** (kantha, phulkari, chikankari, zardozi, mirror-work) — selling attribute + GI/marketing claim.
- **Size + closure** (zip/buttons) aid classification and clear value/weight validation.
- Sets: describe as a set and list component piece counts; keep Σ values/weights coherent (report §2.3).

---

## 3. Destination Notes (duty / VAT)

| Market | Duty (base) | VAT/GST | Notes |
|---|---|---|---|
| **USA** | Cushion covers/bedspreads/furnishing (6304.92.00.00 not-knitted cotton, 6304.19.30 other bedspreads): **6.3%** 🟢 (MFN; TariffLens + wove). Bed linen other cotton (6302.91.00): **9.2%** 🟡 (TariffLens; credlix shows 10%). Embroidered printed bed linen (6302.21.30, embroidery/lace/braid): **11.9%** 🟡. Curtains (6303.x): **~8-11%** 🟡. **Plus Section 301 10% on India (24-Jul-2026)** ⚠️ | State sales tax; usually not postal-collected | De minimis suspended — every parcel dutiable 🟢. **Cushion/bedspread (6.3%) is cheaper than bed linen (9.2-11.9%)** — the article word matters for duty too |
| **UK** | Duty-free ≤ **£135** 🟢; UKGT MFN on 6304 = **12%** 🟢 (trade-tariff.service.gov.uk shows 12.00% across 6304); 6302 similar ~12% 🟡 | **20% VAT on all** 🟢 | Below £135 most single cushion/runner parcels escape duty; VAT always due |
| **UAE** | Duty de minimis **AED 1,000** (duty-only) 🟢; **5% on CIF** above 🟢 | **5% VAT on all** 🟢 | AED 1,000 exempts duty, not VAT (report §4.4) |
| **Australia** | Duty-free ≤ **AUD 1,000** 🟢; home-textile lines generally **Free under ECTA** 🟢 (smallworld: textiles 0-5%) | **10% GST on all** 🟢 | GST is the only real landed-cost line for small parcels |

---

## 4. Certifications & Document Needs

| Need | Required? | Detail |
|---|---|---|
| **IEC** | ✅ Mandatory for PBE (report §5.1) | free under FTP 2023 |
| **GSTIN** | 🟡 not hard-required for booking; **needed for IGST-refund rail** | GSTIN-less artisan can ship; refunds need ICEGATE + AD code + bank |
| **Handloom Mark (HLM)** | 🟢 Voluntary — **recommended** for handloom-base home textiles | certification trademark via Textiles Committee (hlm.gov.in), post onsite verification; authenticates the handloom 8-digit line; 22k+ users. Not a customs NOC. |
| **Handloom Origin Certificate** | 🟢 Voluntary — **valuable for US/EU/AU duty concessions** | Textiles Committee issues under India's bilateral textile agreements (USA, EU, Switzerland, Australia); enables importer duty-concession claims. |
| **GI tag** | 🟡 only for GI-listed crafts | e.g., **Kantha** (WB), **Phulkari** (Punjab), **Chikankari** (UP), **Kutch/Kashmir** embroidery (GI) — brand asset, not customs NOC |
| **AYUSH / NOC** | ❌ Not needed | no herbal/ayurvedic content |
| **Wood / plant material** | ⚠️ **Watch trims & frames** | Wall hangings with **wooden/bamboo rods or frames** hit the per-destination wood/plant restriction (report §5.2; Ireland bans outright). Pure-fabric home textile = clean. |
| **Natural dyes / flame-retardant** | ⚠️ Monitor | EU/UK REACH azo limits on dyed textiles; **US CPSC flammability** (CPSIA) can apply to certain textile articles — bed linen is generally exempt from the general-wearing-apparel standard but verify curtains. Not a DNK NOC. |

⚠️ **Flagged:** **curtains with wooden/bamboo rods** and **wall hangings with wooden frames** are the two cases in this category that can actually block a lane (wood restriction). If the artisan sells those, treat them as wood-bearing goods, not pure textiles, on the DNK route (report §5.2).

---

## 5. Shipping Lane Fit (ITPS vs EMS)

**Typical parcel weight:** cushion cover 150-300 g; table runner 200-400 g; tablecloth 400-800 g; embroidered towel 250-500 g; bedspread (double) 1.2-2.0 kg; bedsheet set 1.5-2.5 kg; curtain panel 500-1,200 g.

**Single article → ≤2 kg → ITPS** 🟢 for cushion covers, runners, towels, most bedspreads. **Heavier bed-linen sets (>2 kg) → EMS** (250-g slabs, volumetric risk — report §4.3).

| Destination | 300 g | 500 g | 1,000 g | 1,500 g | 2,000 g | Lane verdict |
|---|---|---|---|---|---|---|
| **USA** | ₹575 | ₹715 | ₹1,065 | ₹1,415 | ₹1,765 | ITPS ≤2 kg |
| **UK** | ₹325 | ₹425 | ₹675 | ₹925 | ₹1,175 | ITPS ≤2 kg |
| **UAE** | ₹260 | ₹320 | ₹470 | ₹620 | ₹770 | ITPS ≤2 kg |
| **Australia** | ₹620 | ₹800 | ₹1,250 | ₹1,700 | ₹2,150 | ITPS ≤2 kg |

(ITPS first-50g/additional-50g per report §4.1: USA ₹400+₹35, UK ₹200+₹25, UAE ₹185+₹15, Australia ₹395+₹45.)

**Above 2 kg:** EMS first-250g/additional-250g (e.g., US/UK ₹865 + ₹100/250g, report §4.2) — compute volumetric on EMS legs only (÷4000/5000/6000 config), steer ≤2 kg to ITPS.

⚠️ **Flagged:** US ITPS cap **2 kg** per S.O. 659(E) vs **5 kg** per Jan-2026 DoP OM — resolve at build (report O10); bulky-light home textiles (quilts, wall hangings) are exactly the volumetric-margin-killer case in report §4.3.

---

## 6. Sources

1. HEPC handloom HS list (6302 21 10, 6302 51 10, 6302 60 10, 6302 91 10, 6304 19 40, 6304 92 11-91, 6304 99 91/92): https://hepcindia.com/membership/page/hscodes
2. India ITC-HS Chapter 63 (DGCIS PDF, 8-digit lines incl. 6304 19 10, 6304 99 10): https://www.dgciskol.gov.in/Writereaddata/Downloads/CHP_63.pdf ; ecer.com India 63 lookup: https://scm-en.ecer.com/hscode/india/63.html
3. EximGuru 6304 ITC-HS: https://www.eximguru.com/hs-codes/6304-other-furnishing-articles-excluding-those.aspx
4. US HTS 6304.92.00.00 = 6.3% (TariffLens): https://www.tarifflens.ai/hts/6304.92.00.00 ; wove (MFN 6.3%, eff. from China 23.8%): https://tariffs.wove.com/us/tariff/6304.92.00.00
5. US HTS 6302.91.00 = 9.2% (TariffLens): https://www.tarifflens.ai/hts/6302.91.00 ; 6302.21.30 embroidered = 11.9%: https://www.tarifflens.ai/hts/6302.21.30 ; credlix 6302 (10%): https://www.credlix.com/hts-code/6302
6. CBP rulings for home-textile classification: N070728 (duvet 6302.31.9050, sham 6304.92.0000): https://open-gov.usebase.io/rulings/N070728 ; HQ 084323 (cushion slipcovers 6304.92 = 7.2% at the time): https://www.customsmobile.com/rulings/docview?doc_id=HQ+084323 ; NY H84988 (wall hanging 6304.92 = 6.6% at the time): https://www.customsmobile.com/rulings/docview?doc_id=NY+H84988
7. UK Integrated Online Tariff, heading 6304 (12% MFN, 20% VAT): https://trade-tariff.service.gov.uk/headings/6304
8. Australia: ECTA guide (textiles 0-5%): https://www.dfat.gov.au/sites/default/files/using-ecta-do-business-india.pdf ; smallworld ECTA table: https://smallworldindia.com/blog/import-duties-india-to-australia-2026 ; GST 10%: https://www.abf.gov.au/importing-exporting-and-manufacturing/importing/cost-of-importing-goods/gst-and-other-taxes
9. UAE: Dubai Customs FAQ (5% CIF): https://www.dubaicustoms.gov.ae/en/mobile/pages/faq.aspx ; report §4.4 (AED 1,000 duty de minimis, 5% VAT on all)
10. Handloom Mark: https://textilescommittee.gov.in/handloom-mark-scheme/ ; Handloom Origin Certificate: https://textilescommittee.nic.in/certification-0
11. US CPSC flammability/CPSIA guidance: https://www.cpsc.gov/Regulations-Laws--Standards
12. ITPS rates (S.O. 659(E) Feb-2026 + DoP OM Jan-2026): report §4.1; https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html

**Confidence flags recap:** 6303 curtains 8-digit & US rate 🟡 · US 6302.91 (9.2 vs 10) 🟡 · US S.301 per item ⚠️ · US ITPS cap 2 vs 5 kg ⚠️ · wood/bamboo trims per destination ⚠️ · CPSC flammability for curtains ⚠️.
