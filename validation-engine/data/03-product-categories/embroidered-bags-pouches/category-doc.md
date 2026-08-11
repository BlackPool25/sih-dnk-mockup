# Category Doc — Embroidered Bags & Pouches

**DNK export-enablement · SIH260113 · prepared 2026-08-08**
**Scope:** hand-embroidered handbags, totes, clutches, drawstring pouches, cosmetic/jewellery pouches, wallets/purses, saree-bags (textile outer surface), made-to-order artisan goods.
**Confidence legend:** 🟢 High 80-95% · 🟡 Moderate 60-80% · 🔴 Low 40-60% · ⚠️ Flagged/verify at build.
**Build rule (report §4.3):** every duty/VAT/postage figure is a **snapshot** → land as config flags with source + timestamp, never hard-coded.

---

## 1. HS / CTH Classification

### 6-digit HS candidates

| 6-digit | Description | Use for |
|---|---|---|
| **4202** (with 4202.22) | Handbags with outer surface of **textile materials** | 🟢 embroidered fabric handbags/totes/clutches |
| **4202.32** | Articles of a kind normally **carried in pocket or handbag** (wallets, purses, pouches) with outer surface of textile | 🟢 embroidered wallets/coin purses/cosmetic pouches |
| **4202.92** | Other containers with outer surface of textile (drawstring bags, utility pouches) | 🟡 larger multi-purpose pouches |
| **6307.90** | Other made-up textile articles (catch-all) | 🟡 **unstructured** drawstring/gift pouches, saree bags, potli-style bags that don't read as "handbag/container" — US ruling practice often places simple textile pouches here |

**The 4202 vs 6307.90 boundary is the single biggest classification risk in this category.** 🟢
- **Structured, container-like** bag (gusset, handle, closure, "holds contents like a bag") → **4202.22**.
- **Simple sewn pouch** (drawstring, no structure) → **6307.90** in US practice (wove.com: "if unstructured pouch style… lacks container structure for Chapter 42").
- Declaring an unstructured pouch as 4202 (or vice-versa) is exactly the kind of error that triggers holds/refunds (report §5.1).

### Likely 8-digit ITC-HS India codes

| ITC-HS 8-digit | Description | Confidence |
|---|---|---|
| **4202 22 20** | Hand-bags and shopping bags, of cotton (outer surface textile) | 🟢 confirmed by EximGuru/Ximpex/Seair export data |
| 4202 22 40 | handbags of jute/other vegetable fibre | 🟡 |
| 4202 22 90 | other textile handbags | 🟡 (verify exact split — e.g. silk/man-made) |
| **4202 32 10 / 4202 32 20 / 4202 32 90** | pocket/handbag articles with textile surface (cotton / other) | 🟡 8-digit split varies — verify |
| 4202 92 90 | other textile bags (drawstring/carry) | 🟡 |
| **6307 90 90** | other made-up textile articles (pouches, saree bags, potli) | 🟢 catch-all confirmed structure (EximGuru/ITC-HS 63) |
| 6307 90 20 / 6307 90 30 | specific made-up textile articles | 🟡 verify against ITC-HS 63 |

**Which variant fits made-to-order artisan goods:**
- Embroidered **tote/handbag/clutch** (structured) → **4202 22 20** (cotton) or 4202 22 90 (silk/mix). 🟢
- Embroidered **wallet/coin-purse/cosmetic pouch** → **4202 32 xx**. 🟡
- Embroidered **drawstring/potli/saree pouch** (unstructured) → **6307 90 90**. 🟢
- Flag: if the bag uses a **leather** outer surface, it moves to 4202.21 (leather) — higher duty in some markets; most DNK artisans ship textile.

---

## 2. PBE Declaration (prd_desc) Guidance

**Do:** `embroidered cotton tote bag, hand-embroidered, 100% cotton twill outer, cotton lining, 30x30 cm, with fabric handles`
**Don't:** `bag`, `purse`, `pouch`, `handmade bag`.

Template:
```
hand-embroidered {article: tote bag | handbag | clutch | wallet | cosmetic pouch | drawstring pouch | potli}, {material: 100% cotton | silk | velvet | jute} outer, {stitch: phulkari | kantha | chikankari | zardozi | mirror-work}, {lining: cotton | none}, size {W x H} cm, {structured|unstructured}
```

Tips:
- **Name the embroidery style** (phulkari, kantha, chikankari, zardozi, mirror/abla) — it's the selling attribute and supports a GI/marketing claim.
- **"Structured vs unstructured" matters** for HS (4202 vs 6307.90) — your description should make the construction obvious ("with fabric handles + gusset" vs "drawstring pouch").
- If the pouch has **wooden/glass/mirror beads**, declare the trim material — beads can trip wood/glass restrictions on some lanes (report §5.2).
- Keep Σ values/weights coherent (report §2.3).

---

## 3. Destination Notes (duty / VAT)

| Market | Duty (base) | VAT/GST | Notes |
|---|---|---|---|
| **USA** | Textile handbags: **4202.22.45 (cotton) = 6.3%** 🟢; **4202.22.81/89 (man-made/other) = 17.6%** 🟢; silk ≥85% 4202.22.70 = **7%** 🟡. Pocket/wallet: **4202.32.40 (cotton) = 6.3%** 🟢; 4202.32.80 other = **5.7%** 🟢. Simple pouches: **6307.90.98 = 7%** 🟢. **Plus Section 301 10% on India (24-Jul-2026)** ⚠️ | State sales tax; usually not postal-collected | De minimis suspended — every parcel dutiable 🟢. **Cotton outer = 6.3%; man-made outer = 17.6%** — the material choice moves duty 3× |
| **UK** | Duty-free ≤ **£135** 🟢; UKGT MFN on textile bags/pouches (4202.22.90 / 4202.32.90) = **2%** 🟢 (trade-tariff.service.gov.uk shows 2.00% both "hand-made" and "other"); 6307.90 ≈ 12% 🟡 | **20% VAT on all** 🟢 | Below £135 most pouches escape duty; VAT always due |
| **UAE** | Duty de minimis **AED 1,000** (duty-only) 🟢; **5% on CIF** above 🟢 (landed-cost calculator: bags & luggage 5%) | **5% VAT on all** 🟢 | AED 1,000 exempts duty, not VAT (report §4.4) |
| **Australia** | Duty-free ≤ **AUD 1,000** 🟢; 4202/6307 generally **Free under ECTA** 🟢 | **10% GST on all** 🟢 | GST is the only real landed-cost line for small parcels |

---

## 4. Certifications & Document Needs

| Need | Required? | Detail |
|---|---|---|
| **IEC** | ✅ Mandatory for PBE (report §5.1) | free under FTP 2023 |
| **GSTIN** | 🟡 not hard-required for booking; **needed for IGST-refund rail** | GSTIN-less artisan can ship; refunds need ICEGATE + AD code + bank |
| **Handloom Mark (HLM)** | 🟢 Voluntary — useful if the fabric base is handloom | certification trademark via Textiles Committee (hlm.gov.in). Bags are usually the **embroidery** product, not the loom product — HLM applies to the base fabric, not the stitching. |
| **Handloom Origin Certificate** | 🟡 only if base fabric qualifies as handloom | Textiles Committee bilateral agreements (US/EU/AU/Switzerland) duty concessions |
| **GI tag** | 🟡 only for GI-listed crafts | e.g., **Phulkari** (Punjab, GI), **Kantha** (West Bengal, GI applied), **Chikankari** (UP), **Zardozi** (GI) — brand asset, not customs NOC |
| **AYUSH / NOC** | ❌ Not needed | no herbal/ayurvedic content |
| **Wood / plant material** | ⚠️ **Watch trims** | Bags with **wooden beads/handles, bamboo rings, cane frames** hit the per-destination wood/plant restriction in report §5.2 (Ireland bans outright; CITES species need permits). Pure-textile bag = clean. |
| **Natural dyes / sequins** | ⚠️ Monitor | EU/UK REACH azo limits on dyed textiles; **glass/mirror beads** are fine but declare trim material. |

⚠️ **Flagged:** **zardozi/metal-thread** embroidery contains metal wire (often copper/zinc); purely decorative → fine, but if it reads as bullion, some markets apply scrutiny. And **mirror-work** bags add fragile trims — declare glass to avoid damage-related disputes. Neither blocks export.

---

## 5. Shipping Lane Fit (ITPS vs EMS)

**Typical parcel weight:** single pouch 40-150 g; clutch/wallet 150-300 g; tote/handbag 200-500 g; pouch set (3 pc) 300-600 g. → **≤2 kg → ITPS** 🟢.

| Destination | 100 g | 300 g | 500 g | 700 g | Lane verdict |
|---|---|---|---|---|---|
| **USA** | ₹435 | ₹575 | ₹715 | ₹855 | ITPS ✅ |
| **UK** | ₹225 | ₹325 | ₹425 | ₹525 | ITPS ✅ |
| **UAE** | ₹200 | ₹260 | ₹320 | ₹380 | ITPS ✅ |
| **Australia** | ₹440 | ₹620 | ₹800 | ₹980 | ITPS ✅ |

(ITPS first-50g/additional-50g per report §4.1: USA ₹400+₹35, UK ₹200+₹25, UAE ₹185+₹15, Australia ₹395+₹45.)

**EMS fallback:** only for multi-bag/wholesale runs > 2 kg; EMS bills 250-g slabs + possible volumetric — steer ≤2 kg to ITPS (report §4.3).

⚠️ **Flagged:** US ITPS cap **2 kg** per S.O. 659(E) vs **5 kg** per Jan-2026 DoP OM — resolve at build (report O10).

---

## 6. Sources

1. EximGuru ITC-HS 42022220 (hand-bags of cotton): https://www.eximguru.com/hs-codes/42022220-hand-bags-and-shopping-bags.aspx ; Ximpex 4202: https://ximpex.in/hs-codes/42022220/
2. US HTS 4202.22 duty map (cotton 6.3%, man-made 17.6%, silk 7%): https://open-gov.usebase.io/tariffs/us/42/4202.22 ; 4202.32.40 cotton = 6.3%: https://open-gov.usebase.io/tariffs/us/42/4202.32.40.00
3. US HTS 6307.90.98 = 7% (UNIS): https://www.unisco.com/hts/63079098 ; pouch-classification guidance: https://tariffs.wove.com/us/tariff/6307.90.98/cotton-drawstring-pouch
4. UK Integrated Online Tariff, heading 4202 (textile bags 2%): https://trade-tariff.service.gov.uk/headings/4202 ; subheading 4202329000 (2%): http://www.trade-tariff.service.gov.uk/subheadings/4202329000-80
5. UAE landed-cost / duty guide (bags & luggage 5%, VAT 5%): https://landed-cost-calculator.com/import-duty-calculator/uae/ ; Dubai Customs FAQ: https://www.dubaicustoms.gov.ae/en/mobile/pages/faq.aspx
6. Australia: ECTA guide (textiles 0-5%): https://www.dfat.gov.au/sites/default/files/using-ecta-do-business-india.pdf ; GST 10%: https://www.abf.gov.au/importing-exporting-and-manufacturing/importing/cost-of-importing-goods/gst-and-other-taxes
7. Handloom Mark: https://textilescommittee.gov.in/handloom-mark-scheme/ ; Handloom Origin Certificate: https://textilescommittee.nic.in/certification-0
8. GI registry (Phulkari/Kantha/Chikankari/Zardozi): GI Registry India (search per craft)
9. ITPS rates (S.O. 659(E) Feb-2026 + DoP OM Jan-2026): report §4.1; https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html

**Confidence flags recap:** 4202.22/4202.32 exact 8-digit split 🟡 verify on trade.gov.in · US 4202.22.70 silk / 6307.90 UK rate 🟡 · US S.301 per item ⚠️ · US ITPS cap 2 vs 5 kg ⚠️ · wood/glass trims per destination ⚠️.
