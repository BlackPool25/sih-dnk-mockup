# Shipping Cost Data — India → USA (India Post DNK lanes + Private Couriers)

**Country:** United States of America
**Scope:** Origin-side postage/freight only — India Post DNK lanes (ITPS, EMS, Air Parcel) vs private couriers (FedEx/DHL/UPS): per-weight-band rates, weight caps, transit times, volumetric-weight treatment, packaging guidance, and USPS destination-side fees.
**Prepared:** 2026-08-08 · **Data snapshot:** rates as cited (per-cell sources); US postage/entry fees as of the 24-Jul-2026 regime.
**Out of scope (different workstream):** US import duty/VAT rates (de minimis suspension, Section 301 basis, sales tax) — referenced only where they trigger the fees in §9. See `dnk-export-enablement/report.md §4.4` and `follow-ups/01-order-to-delivery-flow/findings.md §3` for that side.

> **Confidence tags:** **L1** = statutory/gazette/regulator primary source · **L5** = aggregator/blog/secondary estimate — verify before relying · **Est.** = arithmetic derivation. Anything flagged **L5/Est.** must be re-checked on the India Post official postage calculator (`indiapost.gov.in/calculate-postage`) or at a DNK counter before quoting a buyer.

---

## 0. One-glance table (₹, actual-weight basis, India → USA)

| Weight | **ITPS** (50 g slabs, L1) | **EMS** (250 g slabs, L5/Est.) | **Air Parcel** (250 g slabs, 2024 sched.) | FedEx | DHL | UPS |
|---|---|---|---|---|---|---|
| 100 g | **₹435** | — | — | — | — | — |
| 250 g | ₹540 | ₹865 | ₹955 | — | — | — |
| 500 g | ₹715 | ₹965 | ₹1,130 | ~₹2,400–4,200 | ~₹2,432–3,080 | ~₹3,456+ |
| 1 kg | ₹1,065 | ₹1,165 | ₹1,480 | ~₹3,000–4,500 | ~₹3,482–3,711 | zone-dependent |
| 1.5 kg | ₹1,415 | ₹1,365 | — | ~₹3,500–5,500 | ₹3,999 | — |
| 2 kg | ₹1,765 | ₹1,565 | ₹2,180 | ~₹4,300–6,500 | ₹4,406 | — |
| 2.5 kg | ₹2,115 | ₹1,765 | — | — | ₹5,059 | — |
| 3 kg | ₹2,465 | ₹1,965 | ₹2,880 | — | — | — |
| 5 kg | ₹3,865 | ₹2,765 | ₹4,280 | bulk ≈ ₹1,100/kg | bulk ≈ ₹1,250/kg | — |

**Bottom line:** ITPS is the cheapest tracked option for **sub-1.3 kg** parcels (20–35% below EMS at 500 g); **above ~1.3 kg EMS undercuts ITPS** on the US lane; couriers cost roughly **2.5–4× ITPS/EMS** at sub-2 kg (see §6). FedEx/DHL figures are per-zone aggregates — the exact quote depends on origin city, US ZIP, and chargeable (volumetric) weight.

---

## 1. ITPS — International Tracked Packet Service (the primary DNK lane)

### 1.1 Rate structure (L1, gazette)

- **Billing basis:** actual-weight slabs — **first 50 g ₹400 + every additional 50 g ₹35** to the USA.
- **Source:** S.O. 659(E), *Post Office (Amendment) Regulations 2026*, Gazette of India (Extraordinary), 6-Feb-2026, substituting Table VIII of Schedule III (ITPS Postage Structure) [corpus `report.md §4.1`, `review-logistics §2.1`; gazette substitution confirmed at teamleaseregtech.com, 2026].
- The US rate (₹400/₹35) was **unchanged** by the Jan-2026 amendment (that OM revised only Australia's tariff and added 50 countries) [potoolsblog, OM 01/01/2026].
- **Volume is free:** ITPS bills strictly on actual weight; no volumetric divisor applies (gazette slab structure; corpus `findings F-H5-c`, 82% High) — the single most important fact for bulky-light handicrafts.
- **Registered Small Packet was discontinued 1-Jan-2026**; ITPS is now the designated replacement for non-document items [DoP OM CF-71/17/2025-CF-DOP, 01/01/2026].

### 1.2 Computed cost curve — USA (Est., direct arithmetic from Table VIII)

Formula: `₹400 + ceil((w−50)/50) × ₹35` for weight `w` g.

| Weight | ₹ | Weight | ₹ | Weight | ₹ |
|---|---|---|---|---|---|
| 50 g | 400 | 600 g | 785 | 2,000 g | 1,765 |
| 100 g | **435** | 700 g | 855 | 2,500 g | 2,115 |
| 150 g | 470 | 750 g | 890 | 3,000 g | 2,465 |
| 200 g | 505 | 800 g | 925 | 3,500 g | 2,815 |
| 250 g | 540 | 900 g | 995 | 4,000 g | 3,165 |
| 300 g | 575 | 1,000 g | **1,065** | 4,500 g | 3,515 |
| 400 g | 645 | 1,250 g | 1,240 | 5,000 g | **3,865** |
| 500 g | **715** | 1,500 g | 1,415 | — | — |

*(Corpus-verified anchor points: 100 g ₹435 · 500 g ₹715 · 1 kg ₹1,065 · 2 kg ₹1,765 — `report.md §4.1`.)*

### 1.3 Weight cap — CONFLICT RESOLVED (was open question O10)

| Claim | Cap | Source | Status |
|---|---|---|---|
| Corpus (`report.md §4.1/§6.1`, C17) | **2 kg** USA | S.O. 659(E) Table VIII as extracted Aug-2026; potoolsblog 28/03/2025 table (USA 2 kg) | **Stale** — pre-Jan-2026 value |
| DoP OM CF-71/17/2025-CF-DOP, 01/01/2026 | **5 kg** USA | "maximum permissible weight limit for the United States of America under the ITPS mail category has also been increased from 2 kg to 5 kg" (potoolsblog mirror of OM + S.O. 6154(E)) | **Current (L1)** |
| Shiprocket blog, 21/01/2026 | **5 kg** USA | "ITPS weight limit for shipments to the USA has been increased from 2 kg to 5 kg" | Corroborates |

**Operative cap as of Aug-2026: 5 kg to the USA** — no rollback found in searches. The corpus's 2 kg figure was the pre-amendment value; treat any "2 kg US cap" copy as outdated. Dimension limits still apply (see §8).

### 1.4 Transit time

**18–28 days** to USA (L5, wide spread) [corpus `review-logistics §4`; trackmyspeedpost.com 2026 confirms exactly 18–28]. Roughly **2× slower than EMS**. India Post issued a public notice for delays on USA-bound mail (~Feb-2026) — periodic US gateway/customs backlogs are a known factor [indiapost.gov.in document listing].

### 1.5 Notes

- Tracked end-to-end by design (S10 article number; UPU network).
- ITPS claims processing: **7 working days** under the international-mail compensation SOP [potoolsblog, 04/2025].
- Whole-list ITPS caps: 5 kg for ~29 destinations, 2 kg elsewhere across the 135-country list — the USA is now in the 5 kg set [corpus C17; DoP OM 01/01/2026].

---

## 2. EMS / International Speed Post (the 1–5 kg lane)

### 2.1 Rate structure (L5 — ESTIMATE, flag)

- **Billing basis:** 250 g slabs — **first 250 g ₹865 + ₹100 per additional 250 g** to the USA (documents and merchandise share the structure; merchandise needs a customs declaration).
- **Primary working figure:** ₹865/₹100 — corroborated by indiapost.org (updated 17-Jun-2026, citing ClickPost *International Speed Post Guide 2026*) and the corpus (`report.md §4.2`, L5). Authoritative EMS tariff = **Schedule I** of the Post Office Regulations — **not reproduced in any fetched source** (corpus contradiction C11, still open). **Verify on the official calculator before quoting.**
- **Conflicting L5 figures (do not ignore):** ClickPost blog (May-2025) and ithinklogistics (Oct-2025) quote **USA first-250 g ≈ ₹1,820 + ₹150**. Likely stale/pre-Apr-2025-tariff-cut or mis-copied (DoP cut international postage up to 49% effective Apr-2025, corpus `review-logistics §1`); findpincode's older ₹585/₹165 is clearly legacy. **The ₹865 vs ₹1,820 gap is unresolved at L1 level — flag it.**

### 2.2 Computed cost curve — USA (Est., on the ₹865/₹100 working figure)

| Weight | ₹ | Weight | ₹ |
|---|---|---|---|
| 250 g | 865 | 2,000 g | 1,565 |
| 500 g | **965** | 2,500 g | 1,765 |
| 750 g | 1,065 | 3,000 g | 1,965 |
| 1,000 g | **1,165** | 3,500 g | 2,165 |
| 1,250 g | 1,265 | 4,000 g | 2,365 |
| 1,500 g | 1,365 | 5,000 g | 2,765 |

### 2.3 ITPS vs EMS on the US lane — the crossover nuance

Contrary to the generic corpus claim ("below 2 kg, ITPS is typically 20–40% cheaper"), on **USA specifically** the ITPS advantage shrinks with weight and **flips above ~1.3 kg**:

| Weight | ITPS | EMS | Cheaper |
|---|---|---|---|
| 500 g | ₹715 | ₹965 | ITPS (−26%) |
| 1,000 g | ₹1,065 | ₹1,165 | ITPS (−9%) |
| 1,250 g | ₹1,240 | ₹1,265 | ITPS (−2%) |
| 1,500 g | ₹1,415 | ₹1,365 | EMS (−4%) |
| 2,000 g | ₹1,765 | ₹1,565 | EMS (−11%) |

**Routing rule for the USA:** ≤1.3 kg dense parcels → **ITPS**; 1.3–5 kg → **EMS is usually cheaper than ITPS** (both far below couriers). (Est. on L1 ITPS + L5 EMS rates.)

### 2.4 Weight cap, transit, booking

- **EMS weight cap (USA):** destination-dependent; India Post guidance says international EMS limits "typically from 2 kg up to 30 kg" (indiapost.org, Jun-2026); the captured EMS dataset (~108 countries) includes up-to-30/35 kg claims (corpus `review-logistics §1`). **No authoritative USA-specific EMS ceiling was fetched — confirm at counter.**
- **Transit:** **5–14 working days** to USA (corpus L5); indiapost.org: **7–14 working days**; omnijournal (May-2026): **5–9 business days typical, 12–15 in Diwali/Christmas peaks**. Customs time excluded; official EMS delay compensation ≈5% of postage if >5 days late beyond standard (customs time excluded) [corpus; indiapost.org].
- EMS covers **97+ countries** (indiapost.org, 2026) — consistent with the corpus 97–108 range (C11).
- Booking before **2 pm** on a weekday = same-day dispatch; **no at-door pickup for international EMS** (indiapost.org).

---

## 3. International Air Parcel (above-EMS/above-2-kg lane)

### 3.1 Rate structure (L1 statutory text, but possibly pre-cut)

- **Billing basis:** 250 g slabs — **USA ₹955 first 250 g + ₹175 per additional 250 g**.
- **Source:** Schedule III Table VI "Air Parcel — List of Countries/Territories and Postage", **Post Office Regulations 2024** (reproduced at speedpost.report, Dec-2024). The corpus had flagged Schedule III as "not reproduced in any fetched source"; this reproduction is the first found — **but it predates the Apr-2025 tariff cut (up to −49%), so the 2024 values likely overstate current postage. Treat as L1-text but L5-current: verify at counter.**

### 3.2 Computed cost curve — USA (Est., on the 2024 schedule)

| Weight | ₹ | Weight | ₹ |
|---|---|---|---|
| 250 g | 955 | 2,000 g | 2,180 |
| 500 g | 1,130 | 3,000 g | 2,880 |
| 1,000 g | 1,480 | 5,000 g | 4,280 |

### 3.3 Position on the USA lane

- More expensive than EMS at every comparable weight on the 2024 schedule (1 kg ₹1,480 vs EMS ₹1,165) — on USA, **EMS is the better >1.3 kg postal lane**; Air Parcel is the fallback above EMS's ceiling (or when EMS volumetric billing hurts, §4).
- **Weight cap:** 20 kg general, subject to the destination's lower ceiling (corpus C16 resolved: 20 kg general; destination governs).
- **Dimensions:** max length 1.05 m; length + greatest circumference ≤ 2 m; min surface 90×140 mm (corpus `review-logistics §1`).
- **Transit:** no published standard; L5 estimate: slower than EMS (allow EMS + several days for US-bound).
- Volumetric weight can apply on the parcel leg (see §4).

---

## 4. Volumetric (dimensional) weight

| Aspect | ITPS | EMS / Air Parcel | Source |
|---|---|---|---|
| Actual weight only | ✅ **Volume-free by construction** (50-g slabs on weight) | — | Gazette Table VIII structure; corpus F-H5-c 82% |
| Chargeable = max(actual, L×W×H÷divisor) | — | ✅ **Applies where the counter uses volumetric** | Post Office Regs 2024 clause (r): "weight means gross or volumetric, whichever higher" (L1); Shiprocket VCN: "higher of Dead Weight or Volumetric Weight" on the India Post lane (L4) |
| Divisor (international) | n/a | **CONFLICT, no official figure:** ÷6000 (courierbook Oct-2025; shipmozo; singhxpress) · ÷5000 (clickpost; courierbook Jan-2026 "UPU standard alignment"; costcalculator Jan-2026) · ÷4000 (smartfree) | corpus F-H5-c 82% (unresolved); courierbook's own two pages contradict each other |
| Divisor (domestic reference) | — | Official **÷5000** for domestic Speed Post >2 kg (DoP OM 11-Dec-2025, L1) — sometimes misapplied to international | corpus F5.4 |

**Worked example (Est., NOT measurement — magnitudes Low, 45% confidence per corpus H5-d):** a boxed lamp shade **50×50×30 cm, actual 1.5 kg**:
- Volumetric = 12.5 kg (÷6000) / 15 kg (÷5000) / 18.75 kg (÷4000).
- EMS-US bill (on ₹865/₹100): **₹5,765 (÷6000) / ₹6,765 (÷5000) / ₹8,265 (÷4000)** vs **ITPS actual-weight ₹1,415** (1.5 kg) or ₹715 (corpus's 1 kg reference).
- Blow-up factor vs ITPS: **4–6× (1.5 kg basis), up to ~8–11× (1 kg basis)**.

**Build rule (corpus recommendations F3/F4):** compute volumetric on EMS/Air-Parcel legs only; treat the divisor as a **configurable parameter (÷4000/5000/6000)**; steer ≤5 kg bulky-light items to **ITPS where volume is free**. Field instrument O4 (counter-level measurement at ≥2 DNKs) exists to settle whether counters actually apply volumetric — currently unverified (60%).

---

## 5. Transit times — India → USA

| Service | Transit | Basis | Sources |
|---|---|---|---|
| **EMS** | **5–14 working days** (typical 7–14; 5–9 business days reported; 12–15 in peaks) | L5 (no official lane standard; official EMS standard exists, customs time excluded) | corpus `review-logistics §4`; indiapost.org Jun-2026; omnijournal May-2026; trackmyspeedpost 2026 |
| **ITPS** | **18–28 days** (~2× EMS) | L5 | corpus `review-logistics §4`; trackmyspeedpost 2026 |
| **Air Parcel** | No published standard; slower than EMS | L5 estimate | — |
| FedEx / DHL / UPS | **2–5 days** (Express) | Carrier-standard | CourierBook May-2026; cargocharges Jul-2026 |

**Set buyer expectations with ranges, never a single number.** Destination customs holds add days beyond all figures (explicitly excluded from EMS standards). India Post issued a USA-bound delay notice ~Feb-2026 [indiapost.gov.in document listing].

---

## 6. Private courier comparison (FedEx / DHL / UPS)

### 6.1 India → USA published/aggregated rates (₹, excl. GST / fuel surcharges)

| Carrier | 0.5 kg | 1 kg | 1.5 kg | 2 kg | Transit | Source (date) |
|---|---|---|---|---|---|---|
| **FedEx** | ₹2,400–4,200 (metro→US) | ₹3,000–4,500 | — | ₹4,300–6,500 | 3–5 days | CourierBook lane guide, 17-May-2026 (L5, per-zone) |
| **DHL Express** | ₹2,432–3,080 | ₹3,482–3,711 | ₹3,999 | ₹4,406 | 2–3 days | cargocharges 02-Jul-2026; ClickPost DHL guide (Apr-2026 rates) |
| **UPS** | ₹3,456–5,851 (by zone) | zone-dependent | — | — | 2–5 days | UPS 2026 Tariff Guide — India, eff. 7-Jun-2026 (published rates, excl. GST) |

**Corpus anchor (L5):** FedEx 0.5 kg ≈ **₹2,800**; EMS ≈ **₹1,100–1,800** for a small parcel; postal postage is **₹1,000–1,500 cheaper than FedEx** at sub-1 kg (F4.3 arithmetic) — consistent with the per-zone figures above (1 kg FedEx ~₹3,000–4,500 vs EMS ₹1,165, a ~₹1,800–3,300 gap).

**Sampling of CourierBook metro lanes (17-May-2026, L5):** Mumbai→New York 0.5 kg ₹2,800–4,200 / 1–2 kg ₹4,800–6,500 (DHL/FedEx Express); Delhi→Los Angeles 0.5 kg ₹2,500–3,800 / 1–2 kg ₹4,500–6,200; Bangalore→San Francisco 0.5 kg ₹2,400–3,500 / 1–2 kg ₹4,300–5,800 (FedEx Priority); Chennai→Houston 0.5 kg ₹2,800–4,000 / 1–2 kg ₹4,800–6,500; Jaipur→New York 0.5 kg ₹3,000–4,500 / 1–2 kg ₹5,200–7,000.

### 6.2 What the comparison means for the DNK pitch

- Sub-2 kg, India Post (ITPS ₹435–1,765 / EMS ₹865–1,565) is **2.5–4× cheaper** than courier Express — the price gap that justifies the slower transit for the persona.
- Couriers add door pickup, 2–5-day delivery, and commercial brokerage — trade-offs for urgent/high-value parcels only.
- **Do NOT present "~30% savings" as measured fact** (n=1 exporter quote; corpus §4.5 honesty rule) — quote per-consignment component deltas (postage gap) labelled as estimates.

---

## 7. Packaging guidance (to fit the slab structure)

**The slab structure IS the pricing rule** — pack to the next-lower slab:

- **ITPS (50-g slabs):** every 50 g costs ₹35. A 501 g packet pays the same as a 550 g packet (both ₹750); a 500 g packet pays ₹715. **Pack tight so the declared gross weight stays just under a slab boundary** — 500 g instead of 501 g saves one full slab (₹35).
- **EMS / Air Parcel (250-g slabs):** anything up to 250 g pays the first-250 g rate; 251 g jumps to two slabs. Choose the smallest box that fits — packaging weight of 100–200 g can cost an extra 250-g step.
- **Bulky-light steering:** anything light but voluminous (lamp shades, wall hangings, woven baskets, jute goods) → **ITPS up to 5 kg**, because ITPS ignores volume while EMS/Air Parcel may bill volumetric (up to 4–11× on the §4 worked example). Measure L×W×H at the counter and ask whether volumetric will be applied (open field question O4).
- **Dimensional limits:** letter post incl. ITPS — L+W+D ≤ 900 mm with greatest dimension ≤ 600 mm (rolls: length + 2×diameter ≤ 1,040 mm); Air Parcel — max length 1.05 m, L + greatest circumference ≤ 2 m; min surface 90×140 mm [indiapost.gov.in internationalservices; corpus `review-logistics §1`].
- **Protective packing:** international parcels pass through several handlers and a customs inspection — use a sturdy corrugated box, cushion fragile contents, and pack so the box can be opened and re-sealed by customs [indiapost.org].
- **Addressing:** clear Roman-script address, country in capitals, correct US ZIP; add recipient phone/email where the form allows. Incomplete addresses are a leading cause of delay/return [indiapost.org].
- **Prohibited/restricted watch for handicraft goods:** flammable liquids (perfume/essential oils > small volumes), standalone lithium batteries, magnets (Class 9), perishables, currency, wood/plant material per destination — check India Post's prohibited-items list and the destination country list before packing (corpus `review-logistics §3`).

---

## 8. Weight & size caps summary (USA)

| Lane | Weight cap (USA) | Source / status |
|---|---|---|
| ITPS | **5 kg** (raised from 2 kg) | DoP OM 01/01/2026 (L1); Shiprocket 21/01/2026. Corpus's 2 kg is stale — see §1.3 |
| EMS | Destination-dependent, "typically 2–30 kg"; no USA-specific ceiling fetched | indiapost.org Jun-2026 (L5); **confirm at counter** |
| Air Parcel | **20 kg general** (destination governs) | corpus C16 (resolved) |
| FedEx/DHL/UPS | 68–70 kg typical per-piece; volumetric applies | carrier-standard |

---

## 9. USPS destination-side fees (the USA leg, not duty rates)

Duty/VAT rates are a separate workstream — these are the **US-side handling/entry fees** that add to landed cost when a parcel is dutiable (every US-bound postal parcel is currently dutiable: de minimis suspended indefinitely by EO 14324 + EO 14388, Federal Register 24-Jun-2026).

| Fee | Amount / status | Source (date) |
|---|---|---|
| **USPS customs clearance & delivery fee** (per dutiable item, collected from addressee at delivery) | Amount set in Notice 123 / IMM §712; the **competitive** (courier-side) fee rose to **$9.35** per dutiable item | Federal Register 91:603, 8-Jan-2026 (L1); USPS IMM §712 (pe.usps.com); Notice 123 price list |
| **CBP customs processing fee** on dutiable mail shipments (Form 3419ALT, orange envelope) | Assessed on all dutiable mail shipments; collected with duty | USPS IMM §712 (Jan-2026 archive) |
| **Merchandise Processing Fee (MPF)** | **Exempt for inbound EMS** ("Inbound Express Mail service / Inbound EMS"); other postal items may be subject per CBP rules | CBP E-Commerce FAQ |
| **New postal informal entry process** (from 24-Jul-2026) | Applies to mail-valued ≤ $2,500; CBP amends 19 CFR 145.31(b) — duties, taxes, and fees now collected under the modified postal entry process; the process is generally for informal-entry-eligible items | Federal Register 24-Jun-2026 (FR-2026-06-24); CBP Global Guidance for International Mail, updated 07-Jul-2026 |
| **USPS Delivered Duty Paid (DDP)** | USPS option to prepay import duties/taxes/fees on items to select destinations; fees for facilitating payment exclude the duties themselves | USPS IMM §360; Federal Register 8-Jan-2026 |
| **Inbound Letter-Post letters/flats** | USPS proposed eliminating the customs clearance fee for inbound letter-post letters/flats (Jul-2026 price change) — parcels unaffected | USPS proposed rule 39 CFR 20, Jul-2026 |

**Handling reality on the DNK lane:** for India Post items, US duty collection is via the origin carrier (India Post collects at origin / USPS DDP option) rather than the addressee-only model [corpus `01-order-to-delivery-flow findings §3`, CBP guidance]. Whether the $9.35 or the older ~$5 level applies to a given India Post parcel is not L1-confirmed for the postal-inbound class — **treat as configurable, verify at build time.**

---

## 10. Sources (all cited above with dates)

**India Post / DoP (L1):**
1. S.O. 659(E), Post Office (Amendment) Regulations 2026, Gazette of India (Extraordinary), 6-Feb-2026 — ITPS Table VIII (USA ₹400 + ₹35). Gazetted substitution confirmed: `teamleaseregtech.com/updates/article/52530`.
2. DoP OM CF-71/17/2025-CF-DOP, 1-Jan-2026 — USA ITPS cap 2 kg → 5 kg; +50 countries; Registered Small Packet discontinued. Mirror: `potoolsblog.in/2026/01/amendment-of-international-tracked.html` (also linked from indiapost.gov.in tracking page).
3. Post Office Regulations 2024, Schedule III Table VI (Air Parcel) + clause (r) volumetric definition — reproduced at `speedpost.report/2024/12/schedule-iii.html` (Dec-2024).
4. India Post international services: `indiapost.gov.in/mailproducts/internationalservices` (letter-post/air-parcel dimensions, 219 destinations).
5. DoP OM 11-Dec-2025 (domestic Speed Post >2 kg ÷5000) — via corpus F5.4.
6. potoolsblog, "SOP for Payment of Compensation in case of International Mail", Apr-2025 — ITPS claims 7 working days.

**EMS / secondary (L5 — verify):**
7. indiapost.org, "International Speed Post (EMS) 2026", updated 17-Jun-2026 — USA/UK ₹865 + ₹100/250g; EMS 97+ countries; USA EMS 7–14 working days; EMS weight limits 2–30 kg; 2 pm cut-off; no international pickup. (`indiapost.org/international-speed-post-ems`)
8. ClickPost, "India Post Courier Charges" (May-2025) + ClickPost International Speed Post Guide 2026 — conflicting USA first-250g ₹1,820 + ₹150 (see §2.1).
9. ithinklogistics, "Speed Post Charges 2026" (Oct-2025) — USA/Canada/UK ₹1,820/250g (conflicting).
10. trackmyspeedpost.com, "India Post Delivery Time by Service 2026" — USA EMS 7–14 days, ITPS 18–28 days.
11. omnijournal.blog, "India Post USPS Tracking" 26-May-2026 — EMS India→USA 5–9 business days, 12–15 peaks.

**Couriers (L5 unless noted):**
12. CourierBook, "Courier from India to USA: Complete Lane Guide", 17-May-2026 — FedEx/DHL metro lane rates.
13. cargocharges.com, "DHL Courier Charges to USA from India", 02-Jul-2026 — DHL 0.5 kg ₹3,080 / 1 kg ₹3,482 / 2 kg ₹4,406; 2–3 working days.
14. ClickPost, "DHL Courier Charges in India 2026" (Apr-2026 indicative rates) — DHL India→USA from ₹2,432/0.5 kg, ~₹3,711/kg at 1 kg.
15. UPS, "2026 UPS Tariff Guide — India", effective 7-Jun-2026 (assets.ups.com PDF) — published 0.5 kg zone rates ₹3,456–5,851 excl. GST.

**US side (L1):**
16. Federal Register Vol.91 Issue 5, 8-Jan-2026 (govinfo 2026-00164) — competitive customs clearance & delivery fee → $9.35.
17. USPS International Mail Manual §712 (pe.usps.com/imm) — Postal Service customs clearance fee per dutiable item; CBP Form 3419ALT processing fee.
18. CBP E-Commerce FAQ (cbp.gov) — inbound EMS exempt from MPF; new postal informal entry process 24-Jul-2026.
19. Federal Register 24-Jun-2026 (2026-12669/12668) — indefinite de minimis suspension for postal; new postal informal entry process; 19 CFR 145.31(b).
20. CBP "Updated Global Guidance for International Mail", 07-Jul-2026 (content.govdelivery.com) — postal informal entry ≤ $2,500.
21. USPS proposed rule 39 CFR 20 (Jul-2026) — proposal to eliminate customs clearance fee for inbound letter-post letters/flats.

**Corpus (parent research):** `dnk-export-enablement/report.md` §4, §4.5, §6.1–6.2, §11/12 (O10); `01-background/review-logistics.md` §1–4 (dimensions, EMS/Air-Parcel position, volumetric, transit L5, EMS L5 flag); `04-synthesis/findings.md` F-H5 (volumetric divisor conflict, US fee context, worked example) and F-H4 (30% honesty rule); `follow-ups/01-order-to-delivery-flow/findings.md` §3 (who-pays duties) — all cited per-claim above.

---

## 11. Confidence & flags summary

| Item | Confidence | Note |
|---|---|---|
| ITPS USA rate ₹400/₹35 + cost curve | **L1** | Gazette Table VIII; arithmetic is deterministic |
| ITPS USA cap **5 kg** | **L1** | OM 01/01/2026; resolves corpus O10 — corpus's 2 kg is stale |
| ITPS actual-weight-only (volume free) | **82% High** | Gazette structure; no counter-evidence found |
| EMS USA ₹865/₹100 | **L5 — ESTIMATE** | Conflicting ₹1,820 sources; Schedule I not public (C11) |
| Air Parcel USA ₹955/₹175 | **L1-text / L5-current** | 2024 Regulation; predates Apr-2025 tariff cut |
| Volumetric divisor (EMS/Air Parcel) | **Unresolved** | ÷4000/÷5000/÷6000 all claimed; no official figure |
| Transit EMS 5–14 wd / ITPS 18–28 d | **L5** | Wide spread; ranges only |
| USPS customs fee | **L1 partial** | $9.35 (competitive); postal-inbound class amount unconfirmed |
| FedEx/DHL/UPS rates | **L5** | Per-zone aggregates; quote live |

**Re-check at build time:** (1) EMS Schedule I; (2) Air Parcel post-cut tariff; (3) whether US counters apply volumetric to in-scope handicrafts (O4); (4) US-side fee applicable to postal-inbound items; (5) US duty basis — different workstream, flag-driven.



