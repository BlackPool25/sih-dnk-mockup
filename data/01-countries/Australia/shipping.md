# Australia — Shipping: ITPS / EMS / Private Couriers (India → Australia)

**Country:** Australia · **Data file:** `01-countries/Australia/shipping.md`
**Snapshot date:** 2026-08-08 · **Parent research:** dnk-export-enablement (SIH260113)
**Corpus anchors:** `report.md` §4.1–§4.4 (ITPS/EMS tables, AU row), §6.2 (AU transit) · `04-synthesis/findings.md` Ctx-5, F-H5-c · `follow-ups/01-order-to-delivery-flow/findings.md` §4–§5

> **Rule for the build:** all postage numbers are **config flags** (report §4.4 / §9.2-F3). ITPS rates are L1-gazette-verified for the snapshot; **EMS Schedule I has never been reproduced authoritatively (corpus C11)** — the ₹630/₹155 figure is statutory-rules-corroborated but must be re-verified at the counter. Rates change with gazettes/OMs (e.g. ITPS AU first-50g: ₹330 → ₹370 → ₹395 across 2025–26 revisions).

---

## 0. Executive summary (the numbers that matter)

| Metric | Value | Status |
|---|---|---|
| **ITPS rate (AU)** | **₹395 first 50 g + ₹45 per additional 50 g** (actual weight; 100 g ₹440 · 500 g ₹800 · 1 kg ₹1,250 · 2 kg ₹2,150) | ✅ L1 (S.O. 659(E), 6-Feb-2026) |
| **ITPS weight cap (AU)** | **2 kg** | ✅ L1 (gazette + Post Office Rules §50E) |
| **EMS rate (AU)** | **₹630 first 250 g + ₹155 per additional 250 g** | ⚠️ statutory-verified, corpus C11 unverified |
| **EMS can beat ITPS on AU** | **Yes** — crossover ≈ 450 g; EMS cheaper above (e.g. 1 kg: EMS ₹1,095 vs ITPS ₹1,250) | ✅ arithmetic on verified rates |
| **EMS transit (AU)** | **5–14 days** (7–14 working days commonly cited) | ⚠️ L5 wide spread |
| **ITPS transit (AU)** | **~18–28 days** (≈ 2× EMS) | ⚠️ L5 estimate |
| **Volumetric** | **ITPS = actual weight only (volume-free, L1)**; EMS/Air-Parcel legs may bill volumetric — divisor conflict ÷4000/5000/6000, no official international figure | ⚠️ corpus H5-c |

---

## 1. ITPS — International Tracked Packet Service (the default lane)

### 1.1 Rates (L1, Gazette S.O. 659(E) 6-Feb-2026 — substituted Table VIII, Schedule III, Post Office Regulations 2024)

- **Structure:** billed on **actual-weight slabs — first 50 g + every additional 50 g**; **volume is never billed on ITPS** (report §4.1).
- **Australia rate:** **₹395 first 50 g + ₹45 per additional 50 g** (report §4.1 table; S.O. 659(E) L1 gazette).
- **Rate history (flag at build):** AU first-50g/additional-50g was **₹330/45** (Odisha Post page, stale), **₹370/40** (potoolsblog 01-Apr-2025 revision), then **₹395/45** (S.O. 659(E), Feb-2026). The gazette supersedes all earlier numbers. ([potoolsblog — revised ITPS tariff 01-Apr-2025](https://www.potoolsblog.in/2025/03/revised-itps-international-tracked.html); [teamleaseregtech — Post Office (Amendment) Regulations 2026, S.O. 659(E)](https://www.teamleaseregtech.com/updates/article/52530/post-office-amendment-regulations-2026/))

### 1.2 Computed costs (direct arithmetic from Table VIII, L1)

| Weight | ITPS cost (AU) |
|---|---|
| 50 g | ₹395 |
| 100 g | ₹440 |
| 250 g | ₹575 |
| 500 g | **₹800** |
| 750 g | ₹1,025 |
| 1,000 g | **₹1,250** |
| 1,500 g | ₹1,700 |
| **2,000 g (cap)** | **₹2,150** |

These four anchor points are cross-checked in the corpus (report §4.1: 100 g ₹440 · 500 g ₹800 · 1 kg ₹1,250 · 2 kg ₹2,150).

### 1.3 Weight cap and size limits (AU)

- **Maximum weight on ITPS to Australia: 2 kg** (per-destination table; corpus contradiction C17 resolved). ([potoolsblog ITPS tables 2025](https://www.potoolsblog.in/2025/10/itps-rates-2025-dop-om-nocf-71172025-cf.html); report §4.1/§6.1)
- **General ITPS limits (Post Office Rules §50E):** max weight 2 kg; max **90 cm for the sum of length+width+depth**; **largest dimension ≤ 60 cm**. ([Indian Kanoon — §50E Post Office Rules 1933](http://indiankanoon.org/doc/59692720/))
- **Compensation:** restricted to **₹1,000** or actual declared value of contents, whichever is less (Odisha Post ITPS page — L3).
- **USA note (not AU):** US cap was raised 2 → 5 kg (DoP OM 01-Jan-2026) — **Australia remains 2 kg**. ([potoolsblog — 01-Jan-2026 OM](https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html))

---

## 2. EMS — International Speed Post (the AU-lane exception)

### 2.1 Rates (⚠️ statutory-verified, corpus-flagged C11)

- **Structure:** **250 g slabs — first 250 g + per-additional-250 g** (report §4.2).
- **Australia rate:** **₹630 first 250 g + ₹155 per additional 250 g**.
  - Corroborated by: **Indian Post Office Rules §225** (EMS schedule: Australia 630 / 155) ([Indian Kanoon](https://indiankanoon.org/doc/124001496/)); [taxguru 2013 notification](https://taxguru.in/finance/government-notifies-revised-rates-international-posts.html); [indiapost.org EMS 2026](https://indiapost.org/international-speed-post-ems); [wareiq 2026](https://wareiq.com/resources/blogs/india-post-courier-charges/).
  - **Conflict to flag:** one 2026 aggregator (ClickPost) lists AU EMS at ₹1,125/₹230 ([clickpost.ai](https://www.clickpost.ai/blog/india-post-courier-charges)) — inconsistent with the statutory/2026 sources and with the "EMS beats ITPS" corpus note. **Treat ₹630/₹155 as the working figure; re-verify at the counter before shipping.** (corpus C11: no authoritative Schedule I reproduced anywhere)

### 2.2 Computed costs

| Weight | EMS cost (AU) | ITPS cost (AU) | Cheaper lane |
|---|---|---|---|
| 250 g | ₹630 | ₹575 | **ITPS** (₹55) |
| 400 g | ₹630 | ₹710 | **EMS** (₹80) |
| 500 g | ₹785 | ₹800 | **EMS** (₹15) |
| 750 g | ₹940 | ₹1,025 | **EMS** (₹85) |
| 1,000 g | ₹1,095 | ₹1,250 | **EMS** (₹155) |
| 1,500 g | ₹1,405 | ₹1,700 | **EMS** (₹295) |
| 2,000 g | ₹1,715 | ₹2,150 | **EMS** (₹435) |

**Crossover:** ITPS ≈ EMS at **~450 g**; above that **EMS is cheaper on the Australia lane — the exception** (report §4.2: "Australia is the exception where EMS can beat ITPS"). Below 450 g, ITPS wins.

**Build rule (report §4.3 / F4):** for ≤2 kg bulky-light items, prefer **ITPS** (volume-free) — but on AU, for **dense items > ~450 g**, **EMS wins on pure postage**; still apply the volumetric check to EMS legs.

### 2.3 EMS weight cap (AU) — unverified

- EMS generally accepts heavier articles than ITPS, but **no authoritative Schedule I / per-destination cap for Australia was reproduced in the corpus** (corpus C11). Air Parcel general cap is 20 kg (corpus C16 resolved). **Flag: verify EMS weight ceiling for AU at booking.**

### 2.4 Delay compensation (EMS only)

- EMS carries official end-to-end standards with delay compensation ≈ **5% of postage** if delivery is late by >5 days (customs time excluded) — [follow-ups findings §5.1](findings.md). ITPS has no such compensation.

---

## 3. Transit times (set expectations with ranges, never a single number)

| Service | India → Australia (working days) | Source |
|---|---|---|
| **EMS** | **5–14** (commonly "7–14") | corpus report §6.2 (5–14); [indiapost.org 2026](https://indiapost.org/international-speed-post-ems) (7–14); [trackmyspeedpost](https://trackmyspeedpost.com/delivery-time-by-service) (7–14) |
| **ITPS** | **~18–28** (≈ 2× EMS) | corpus §6.2 ("ITPS is roughly 2× slower"); [trackmyspeedpost](https://trackmyspeedpost.com/delivery-time-by-service) (18–28) |
| **Private couriers** | **3–8** | §5 table below |

- **Postal caveat:** EMS/ITPS windows cover **postal transit only**; **destination customs clearance adds unpredictable time** (esp. for commercial goods) ([trackmyspeedpost](https://trackmyspeedpost.com/delivery-time-by-service)). Biosecurity-inspected items (wood/jute) can add days at AU entry.
- **Final mile:** hand-off to **Australia Post** for AU delivery; the **S10 number** is the only tracking key that survives DNK → FPO → customs → AU (follow-ups §5.3). Outbound tracking typically stops at "Dispatched to foreign country"; use third-party S10 trackers (AfterShip/17TRACK) for the joined timeline (follow-ups §5.5).

---

## 4. Volumetric weight notes (the silent margin-killer)

- **ITPS: never volumetric** — bills actual weight only (L1, corpus Ctx-5). This is the single biggest protection for bulky-light handicrafts.
- **EMS / Air Parcel legs: can bill volumetric** — Post Office Regulations 2024 define "weight" as **gross-or-volumetric whichever is higher** (L1). No official **international** divisor exists; aggregators conflict at **÷4000 / ÷5000 / ÷6000** (corpus F-H5-c). Domestic Speed Post >2 kg is officially ÷5000 (DoP OM 11-Dec-2025).
- **Worked example (not measurement, 45% Low — corpus H5-d):** a boxed lamp shade 50×50×30 cm, actual 1.5 kg → 12.5–15 kg volumetric on EMS at ÷4000–6000 → 7–8× price blow-up vs ITPS actual-weight ₹1,700.
- **Build rule (report §4.3):** compute volumetric on **EMS/Air-Parcel legs only**; treat the divisor as a **configurable parameter (÷4000/5000/6000)**; steer bulky-light ≤2 kg items to ITPS. Whether AU-destined counters actually apply volumetric to hand-carried crafts is **unverified (60% Moderate)**.
- **Note:** Australia Post inbound assessment is weight-based; AU does not add its own volumetric surcharge at the parcel-assessment layer for postal items (L5 — flag).

---

## 5. Private courier comparison (India → Australia)

**All figures are L5 aggregator/vendor estimates — wide variance, flag as estimates and re-quote at build.** Postage is roughly comparable to or above EMS/ITPS, but **3–8 day transit + door pickup** is the value proposition; the corpus H4-b finding (India Post 20–40% cheaper than private couriers) holds on AU.

| Carrier / service | India → Australia (approx, 500 g–1 kg) | Transit | Source (accessed 2026-08-08) |
|---|---|---|---|
| **DHL Express** | ₹1,400–2,000 | 3–5 days | [CourierBook (Oct-2025)](https://www.courierbook.in/blog/cross-border-ecommerce-shipping-guide/); DHL 1 kg ≈ ₹3,600 in [Goodseva (Nov-2025)](https://www.goodseva.com/blog/courier-charges-in-india-per-kg/) |
| **FedEx Priority** | ₹1,400–2,000 | 3–5 days | [CourierBook (Oct-2025)](https://www.courierbook.in/blog/cross-border-ecommerce-shipping-guide/) |
| **FedEx Economy** | ₹1,100–1,500 | 5–8 days | [CourierBook (Oct-2025)](https://www.courierbook.in/blog/cross-border-ecommerce-shipping-guide/) |
| **Aramex Premium** | ₹1,000–1,400 | 5–8 days | [CourierBook (Oct-2025)](https://www.courierbook.in/blog/cross-border-ecommerce-shipping-guide/) |
| **UPS Express** | from ₹1,278/kg (aggregator), 1 kg ≈ ₹3,600 retail (DHL-zone) | 5–6 working days | [cargocharges (Jun-2026)](https://cargocharges.com/send-courier-to-australia-from-india.html); [Goodseva (Nov-2025)](https://www.goodseva.com/blog/courier-charges-in-india-per-kg/) |
| **India Post EMS** | ₹630–1,095 (250 g–1 kg) | 5–14 days | §2 |
| **India Post ITPS** | ₹440–1,250 (100 g–1 kg) | 18–28 days | §1 |

- Aggregators (Shiprocket X, etc.) run the same DHL/UPS/FedEx lanes **40–70% below retail counter rates** ([cargocharges](https://cargocharges.com/send-courier-to-australia-from-india.html) — L5).
- **When a courier makes sense:** buyer needs delivery in <1 week, high declared value (>A$1,000 where a courier brokerage/formal entry is expected anyway), or doorstep pickup needed (no village pickup on the postal lane — follow-ups §4.2).
- **Duties/taxes on courier lanes:** couriers typically **clear and collect GST/duty on delivery (DAP)** or let you prepay (DDP); AU-side costs identical to §1–2 of `duties-taxes.md` (≤A$1,000 vendor-GST; >A$1,000 border GST + duty + IPC).

---

## 6. Config flags for the shipping engine

| Flag | Value | Source | Last verified |
|---|---|---|---|
| `au_itps_first_50g` | **₹395** | S.O. 659(E) 6-Feb-2026 (Table VIII) via report §4.1 | 2026-08-08 |
| `au_itps_addl_50g` | **₹45** | S.O. 659(E) | 2026-08-08 |
| `au_itps_max_weight_kg` | **2** | gazette per-destination + PO Rules §50E | 2026-08-08 |
| `au_itps_volumetric` | **false** (actual weight only) | L1 gazette / corpus Ctx-5 | 2026-08-08 |
| `au_ems_first_250g` | **₹630** (⚠️ re-verify at counter; C11) | PO Rules §225 / indiapost.org 2026 | 2026-08-08 |
| `au_ems_addl_250g` | **₹155** (⚠️ re-verify; C11) | PO Rules §225 / indiapost.org 2026 | 2026-08-08 |
| `au_ems_volumetric` | **true** (gross-or-volumetric, higher applies) | Post Office Regulations 2024 (L1) | 2026-08-08 |
| `au_ems_volumetric_divisor` | **÷4000 / ÷5000 / ÷6000 (config, no official figure)** | corpus F-H5-c | 2026-08-08 |
| `au_ems_max_weight_kg` | **unknown (C11)** — Air Parcel general 20 kg | corpus C16 | 2026-08-08 |
| `au_ems_transit_days` | **5–14** (range) | report §6.2 / indiapost.org | 2026-08-08 |
| `au_itps_transit_days` | **18–28** (range, ~2× EMS) | report §6.2 / trackmyspeedpost | 2026-08-08 |
| `au_ems_delay_compensation` | **~5% of postage if >5 days late** (customs excluded) | follow-ups §5.1 | 2026-08-08 |
| `au_lane_rule` | **≤ ~450 g → ITPS; > ~450 g (dense) → EMS; bulky-light ≤2 kg → ITPS** | arithmetic on §1/§2 rates | 2026-08-08 |

---

## 7. Open items / confidence

| Item | Confidence | Note |
|---|---|---|
| ITPS rates + 2 kg cap + volume-free | **High (92%)** — L1 gazette + PO Rules | Corpus Ctx-5; US-only cap change to 5 kg does not affect AU |
| EMS rates (₹630/₹155) | **Moderate (65%)** — statutory + 3 independent 2026 sources, but no reproduced Schedule I (C11) | One conflicting L5 source (ClickPost ₹1,125/₹230); re-verify at counter |
| EMS weight cap AU | **Low/Speculative** — not published in corpus | C11 open |
| Transit times | **Low–Moderate (50%)** — L5 wide spread | EMS 5–14, ITPS ~18–28; customs adds unknown time |
| Volumetric application at AU counters | **Moderate (60%)** — legal definition L1, counter practice unverified | Corpus H5-c/d |
| Private courier rates | **Low (40%)** — L5 aggregator estimates, volatile | Re-quote at build |

---

## 8. Sources (key, accessed 2026-08-08)

- S.O. 659(E) 6-Feb-2026 — Post Office (Amendment) Regulations 2026, substituted Table VIII (ITPS): via [teamleaseregtech](https://www.teamleaseregtech.com/updates/article/52530/post-office-amendment-regulations-2026/) and corpus report §4.1 (L1)
- DoP OM 01-Jan-2026 (ITPS tariff amendment + US 2→5 kg): https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html
- DoP OM 01-Apr-2025 (revised ITPS tariff incl. AU ₹370/40, 2 kg): https://www.potoolsblog.in/2025/03/revised-itps-international-tracked.html
- DoP OM 28-Oct-2025 (ITPS extended to 85 countries, S.O. 4907(E)): https://www.potoolsblog.in/2025/10/itps-rates-2025-dop-om-nocf-71172025-cf.html
- Post Office Rules 1933 §50E (ITPS 2 kg / 90 cm / 60 cm): http://indiankanoon.org/doc/59692720/
- Post Office Rules 1933 §225 (EMS AU ₹630/₹155): https://indiankanoon.org/doc/124001496/
- indiapost.org — International Speed Post 2026 (rates + 7–14 day AU transit): https://indiapost.org/international-speed-post-ems
- trackmyspeedpost — delivery time by service (ITPS AU 18–28): https://trackmyspeedpost.com/delivery-time-by-service
- ClickPost — India Post charges 2026 (conflicting EMS AU figure): https://www.clickpost.ai/blog/india-post-courier-charges
- CourierBook — cross-border seller guide (DHL/FedEx/Aramex AU ranges): https://www.courierbook.in/blog/cross-border-ecommerce-shipping-guide/
- cargocharges — cheapest courier to Australia (UPS from ₹1,278/kg): https://cargocharges.com/send-courier-to-australia-from-india.html
- Goodseva — courier charges per kg (DHL AU 1 kg ≈ ₹3,600): https://www.goodseva.com/blog/courier-charges-in-india-per-kg/
- Corpus: `report.md` §4.1–§4.4, §6.2 · `04-synthesis/findings.md` Ctx-5, F-H5-c/d · `follow-ups/01-order-to-delivery-flow/findings.md` §4–§5
