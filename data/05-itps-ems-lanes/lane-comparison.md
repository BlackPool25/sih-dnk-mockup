# Lane Comparison — ITPS vs EMS vs Air Parcel (Decision Matrix)

**Purpose:** when to use which India Post international lane for the DNK artisan persona (sub-5 kg handicrafts), with volumetric-risk scenarios, a per-destination weight-cap lookup, and a 4-market cost comparison.
**Prepared:** 2026-08-08 · **CURRENT DATE reference:** Aug 2026 · **Corpus anchors:** `report.md §4.1–4.3`, `04-synthesis/findings.md Ctx-5/F-H5-c/d/C16/C17`, `04-synthesis/requirements/functional-requirements.md Module B (FR-022/023) + Module C (FR-030/031/032)`, `data/01-countries/{USA,UK,UAE,Australia}/shipping.md`

> **Honesty header:** ITPS rates are **L1** (gazette). **EMS rates are L5 ESTIMATES** (Schedule I not public — corpus C11) and several sources conflict 2×; every EMS cell below is an estimate on the corpus working figure. The volumetric blow-up is a **worked example (45% Low)** — NOT measurement. Air Parcel 2024-schedule values likely **predate the Apr-2025 −49% tariff cut** (L1-text, L5-current). All figures are config flags with source + date (FR-001).

---

## 1. The three lanes at a glance

| | **ITPS** | **EMS / Intl Speed Post** | **Air Parcel** |
|---|---|---|---|
| Product class | Letter-post tracked packet | Express Mail Service (UPU EMS Cooperative) | Parcel post |
| Billing slab | **First 50 g + per 50 g** | **First 250 g + per 250 g** | **First 250 g + per 250 g** (2024 schedule) |
| Chargeable weight | **ACTUAL weight only — volume-free** (L1) | Gross **or volumetric** whichever higher (PO Regs 2024, L1); divisor ÷4000/5000/6000 **unresolved**; ClickPost says actual-weight at counters | Same volumetric risk as EMS |
| Weight cap | **2 kg (US/AU/CA per gazette; US likely 5 kg — O10); 5 kg ~29 dest** | **20 kg general; 30 kg many; 30–35 kg claims** (C16) | **20 kg general** (C16) |
| Transit (USA ref.) | **18–28 days** (~2× EMS) | **5–14 days** | no published standard; slower than EMS |
| Tracking | Tracked by design (S10) | End-to-end official standards (S10, EM/EA) | Tracked (parcel) |
| Delay compensation | none | **~5% of postage if > 5 days late** (customs excluded) | per parcel policy |
| Insurance | none (loss cap ₹1,000 / declared value) | **yes — Schedule IV fees** (₹10 up to ₹200; +₹6/₹100) | yes (parcel insurance) |
| BNPL | **no** | **yes (EMS only)** | no |
| Docs | CN22/CN23 + invoice + PBE | CN22/CN23 + invoice + PBE | CN22/CN23 + invoice + PBE |
| Rates confidence | **L1 (gazette)** | **L5 ESTIMATE (C11)** | L1-text / L5-current |
| Best for | ≤ 2 kg, bulky-light or dense, price-first | > 2 kg, speed-first, insurance/BNPL needs | > EMS ceiling / destination allows |

---

## 2. Decision matrix — when to use which (build rule FR-030)

| Order scenario | Weight | Lane | Why (evidence anchor) |
|---|---|---|---|
| **Bulky-light** ≤ 2 kg (lamp shade, wall hanging, cushion, framed art, jute bag) | ≤ 2 kg | **ITPS** | **Volume-free (L1)** — EMS/Air-Parcel may bill volumetric up to 7–8× (worked example, 45% Low); ITPS 20–40% cheaper below 2 kg (corpus §4.2) |
| **Dense** small craft (jewellery, brass, wood toys, scarves) | ≤ 2 kg | **ITPS** | Cheapest tracked lane; actual-weight slabs; 92% High on rates |
| Dense but heavy | ~2 kg on the crossover | **Compare per-market** | USA: EMS undercuts ITPS above ~1.3 kg; **AU: EMS beats ITPS above ~450 g** (see §5) |
| Buyer needs speed (< 2 weeks) | ≤ 2 kg | **EMS** | EMS 5–14 days vs ITPS 18–28 (L5); buyer-expectation trade-off |
| **> 2 kg** | 2–20/30 kg | **EMS** | ITPS cap binds (2 kg US/AU/CA; ~5 kg US); EMS is the above-2-kg lane (C16) |
| **> EMS ceiling** or bulky > 2 kg with low volumetric application | > 20 kg | **Air Parcel** | 20 kg general cap; destination governs; slower, cheaper than EMS per-kg on 2024 schedule |
| Urgent < 5 days / high declared value | any | Private courier (FedEx/DHL/UPS) | 2–5 days at **2.5–4× the postal price**; volumetric + brokerage apply — only for time-critical/high-value |
| Volumetric-risky bulky > 2 kg | > 2 kg | **Check at counter** | Whether counters apply volumetric to bulky crafts is **unverified (60%)** — field instrument O4; split the parcel into ≤ 2 kg ITPS units if cheaper |

**The F4/F30 steer rule (corpus, verbatim):** *"≤2 kg bulky-light → ITPS (volume-free); per-destination cap table"*; EMS-vs-ITPS comparison for dense parcels; EMS/Air-Parcel for over-cap; Australia flagged as the exception where EMS beats ITPS (report §9.2 F4; functional-requirements FR-030).

---

## 3. Volumetric-risk worked example (⚠️ 45% Low — worked example, NOT measurement)

**The corpus example (findings F-H5-d; report §4.3):** a boxed lamp shade **50×50×30 cm, actual weight 1.5 kg**.

Volumetric weight = `50 × 50 × 30 ÷ divisor`:

| Divisor | Volumetric weight |
|---|---|
| ÷6000 | 12.5 kg |
| ÷5000 | 15.0 kg |
| ÷4000 | 18.75 kg |

**EMS→USA bill on the L5 working figure (₹865 + ₹100/250g):**

| Scenario | Chargeable weight | EMS bill (₹) | ITPS bill (₹) | Blow-up vs ITPS |
|---|---|---|---|---|
| ÷6000 | 12.5 kg | **₹5,765** | ₹1,415 (1.5 kg actual) / ₹715 (500 g) | **4× (1.5 kg basis) to ~8×** |
| ÷5000 | 15.0 kg | **₹6,765** | ₹1,415 / ₹715 | **4.8× to ~9.5×** |
| ÷4000 | 18.75 kg | **₹8,265** | ₹1,415 / ₹715 | **5.8× to ~11.6×** |

- **Interpretation:** on the US lane, a 1.5-kg actual lamp shade billed volumetrically would cost **₹5,765–8,265 on EMS vs ₹1,415 on ITPS** (actual-weight). Even at the corpus's loose 500-g reference (₹715), the blow-up is **7–8×** — the "7–8× price blow-up vs ITPS actual-weight ₹715" figure used across the corpus.
- **Confidence:** **45% (Low)** on magnitudes — the corpus explicitly labels this a *worked example*, not measurement (F-H5-d). Whether counters actually apply volumetric to bulky handicrafts is **60% Moderate/unverified** (F-H5-c; O4). One aggregator (ClickPost, Jul-2026) claims EMS bills actual weight at India Post counters — a direct counter-text.
- **Build rule (FR-022/FR-032):** compute volumetric on **EMS/Air-Parcel legs only**; divisor = configurable (÷4000/5000/6000) and **displayed per quote**; when dims indicate volumetric ≥ 2× actual on EMS, surface the ITPS alternative prominently (bulky-light segmentation hint, FR-032).

---

## 4. Weight-cap lookup per destination

| Destination | ITPS cap | EMS cap | Air Parcel cap |
|---|---|---|---|
| **USA** | **2 kg per gazette extraction; 5 kg per DoP OM 01-Jan-2026 (O10 — verify)** | "typically 2–30 kg"; legacy table 31.5 kg (STALE) | 20 kg general |
| **UK** | per S.O. 659(E) table — not individually verified in this pass (flag C17) | legacy 30 kg (STALE) | 20 kg |
| **UAE** | **5 kg** (L1) | legacy 30 kg (STALE); EMS cap unverified | 20 kg |
| **Australia** | **2 kg** (L1) | legacy 30 kg (STALE); EMS cap unverified | 20 kg |
| **Canada** | **2 kg** (L1) | legacy 30 kg (STALE) | 20 kg |
| **Germany** | 5 kg or 2 kg per table (verify) | legacy 30 kg (STALE) | 20 kg |
| **Japan** | per table (verify) | legacy 30 kg (STALE) | 20 kg |
| **Singapore** | **5 kg** (L1) | legacy 30 kg (STALE) | 20 kg |
| ~29 other ITPS destinations | **5 kg** (DoP OM 01-Apr-2025) | destination-dependent | 20 kg |
| Remaining ITPS destinations | **2 kg** (S.O. 659(E) / Oct-2025 OM) | destination-dependent | 20 kg |

- Sources: ITPS caps — `itps-lane.md §5` (S.O. 659(E); DoP OMs 01-Apr-2025 & 01-Jan-2026); EMS caps — `ems-lane.md §6` (C16: "20 kg general; destination governs"; legacy 30/31.5 kg table is STALE, coverage-only); Air Parcel — corpus C16 (20 kg general, dest. governs), 1.05 m max length / L + greatest circumference ≤ 2 m (Odisha Post, L3).
- **Size limits that also bind:** letter-post incl. ITPS — L+W+D ≤ 900 mm, greatest ≤ 600 mm (rolls 1,040 mm); min surface 90×140 mm. Air Parcel — max length 1.05 m, L + greatest circumference ≤ 2 m.
- **Lookup rule (FR-031):** block or warn when weight exceeds the ITPS per-country cap, with the cap from live config and a suggested alternative lane (EMS for 2–20/30 kg).

---

## 5. Cost comparison — 4 target markets × 500 g / 1 kg / 2 kg (ITPS vs EMS)

**4 target markets:** the corpus's top handicraft export destinations with usable rate data — **USA (59.79% share), UK (4.25%), UAE (cheap Gulf lane), Australia (4.03%)** (report §6.2; `data/01-countries/*`). Germany is the 5th-largest market (5.95%) — ITPS only shown because no corpus EMS figure exists for DE.

**ITPS = L1 arithmetic (S.O. 659(E)). EMS = L5 estimate on the corpus working figure (C11). Air Parcel = 2024 schedule, likely pre-tariff-cut (L5-current).**

### 5.1 USA (ITPS ₹400+35/50g · EMS ~₹865+100/250g)

| Weight | ITPS (L1) | EMS (L5 est.) | Cheaper | Air Parcel (2024) |
|---|---|---|---|---|
| 500 g | **₹715** | ₹965 | **ITPS (−26%)** | ₹1,130 |
| 1,000 g | **₹1,065** | ₹1,165 | **ITPS (−9%)** | ₹1,480 |
| 2,000 g | ₹1,765 | **₹1,565** | **EMS (−11%)** | ₹2,180 |

**US crossover ≈ 1.3 kg** — ITPS wins ≤ ~1.3 kg; EMS wins 1.3–5 kg (USA shipping.md §2.3).

### 5.2 UK (ITPS ₹200+25/50g · EMS ~₹865+100/250g)

| Weight | ITPS (L1) | EMS (L5 est.) | Cheaper |
|---|---|---|---|
| 500 g | **₹425** | ₹965 | **ITPS (−56%)** |
| 1,000 g | **₹675** | ₹1,165 | **ITPS (−42%)** |
| 2,000 g | **₹1,175** | ₹1,565 | **ITPS (−25%)** |

**UK: ITPS is decisively cheaper at every weight shown** (20–56% below EMS). The widest ITPS-advantage lane in the set.

### 5.3 UAE (ITPS ₹185+15/50g · EMS CONFLICTED ₹600–1,400 first-250g — C11)

| Weight | ITPS (L1) | EMS low (₹600+60) | EMS high (₹1,400+40) | Cheaper |
|---|---|---|---|---|
| 500 g | **₹320** | ₹660 | ₹1,440 | **ITPS** |
| 1,000 g | **₹470** | ₹780 | ₹1,520 | **ITPS** |
| 2,000 g | **₹770** | ₹1,020 | ₹1,680 | **ITPS** |

**UAE: ITPS is the clear winner** — the cheapest lane in the set (₹320 at 500 g). EMS has **no corpus working figure** (sources conflict ₹600–1,400; see ems-lane §4.2) — shown as a range, both ends above ITPS.

### 5.4 Australia (ITPS ₹395+45/50g · EMS ~₹630+155/250g) — the EXCEPTION

| Weight | ITPS (L1) | EMS (L5 est.) | Cheaper |
|---|---|---|---|
| 250 g | **₹575** | ₹630 | **ITPS (₹55)** |
| 500 g | ₹800 | **₹785** | **EMS (−2%)** |
| 1,000 g | ₹1,250 | **₹1,095** | **EMS (−12%)** |
| 2,000 g | ₹2,150 | **₹1,715** | **EMS (−20%)** |

**AU crossover ≈ 450 g** — ITPS wins below ~450 g; **EMS beats ITPS above it** (Australia = the documented exception, corpus §4.2). Apply the volumetric check to EMS legs before choosing EMS for bulky items.

### 5.5 4-market summary table (₹, 500 g / 1 kg / 2 kg)

| Market | ITPS 500g | EMS 500g | ITPS 1kg | EMS 1kg | ITPS 2kg | EMS 2kg | Best ≤ 2 kg dense |
|---|---|---|---|---|---|---|---|
| **USA** | ₹715 | ₹965 | ₹1,065 | ₹1,165 | ₹1,765 | ₹1,565 | **ITPS ≤1.3 kg; EMS above** |
| **UK** | ₹425 | ₹965 | ₹675 | ₹1,165 | ₹1,175 | ₹1,565 | **ITPS** |
| **UAE** | ₹320 | ₹660–1,440 | ₹470 | ₹780–1,520 | ₹770 | ₹1,020–1,680 | **ITPS** |
| **Australia** | ₹800 | ₹785 | ₹1,250 | ₹1,095 | ₹2,150 | ₹1,715 | **EMS above ~450 g** |

*EMS columns are L5 estimates on the corpus working figure — flag in the UI (FR-001/002). Australia EMS ₹ figures are statutory-mirror corroborated (PO Rules §225) but still C11-unverified.*

---

## 6. Transit × cost trade-off (set buyer expectations as ranges)

| Market | ITPS transit | EMS transit | Courier transit | Price ratio (ITPS 500 g vs courier) |
|---|---|---|---|---|
| USA | 18–28 d | 5–14 d | 2–5 d | ~2.5–4× cheaper |
| UK | ~16–25 d | 4–14 d | 2–5 d | ~4.5× cheaper (₹425 vs ₹1,900+) |
| UAE | ~14–21 d | 3–8 d | 2–5 d | ~5–7× cheaper |
| Australia | ~18–28 d | 5–14 d | 3–8 d | postal 2.5–4× cheaper |

Sources: `data/01-countries/*/shipping.md` (L5 transit, L4 courier). **The price gap is the value proposition** — ITPS at 2.5–7× below courier express buys a 2–4-week transit window the persona can tolerate for made-to-order craft goods.

---

## 7. Destination-duty overlay (same for all postal lanes — config flags)

Landed cost = **postage (ITPS 50-g or EMS 250-g slabs) + packaging + destination duty + destination VAT/GST + handling fee**, with every duty/VAT/threshold a config flag (FR-020/021). Per-market duty payer table is in both lane files (§9 ITPS / §13 EMS); the volatile US basis must be re-verified at build (O11).

| Market | Duty/tax snapshot (2026-08-08) |
|---|---|
| USA | De minimis suspended — every parcel dutiable; **S.301 10% net-of-MFN** (24-Jul-2026); recipient at delivery unless DDP |
| UK | Duty-free ≤ £135; **20% VAT always** (seller-charged ≤ £135) |
| UAE | **5% VAT on all** commercial imports; AED 1,000 duty-only exemption; recipient at pickup |
| Australia | Duty-free ≤ AUD 1,000; **10% GST** (seller-charged ≤ AUD 1,000); EMS beats ITPS on postage |

---

## 8. Decision summary (the one-paragraph steer)

1. **≤ 2 kg, bulky-light → ITPS**, always — volume is free, so the EMS volumetric blow-up (up to 7–8×, worked example) never applies; ITPS is 20–40% cheaper below 2 kg (L1 rates).
2. **≤ 2 kg, dense → ITPS by default**, except **Australia above ~450 g (EMS wins)** and **USA above ~1.3 kg (EMS wins)** — run the per-market crossover comparison.
3. **2–20 kg → EMS** (ITPS cap binds; EMS has insurance, delay compensation, BNPL).
4. **> 20 kg or destination requires parcel → Air Parcel** (20 kg general, destination governs).
5. **Urgent/high-value → private courier** at 2.5–7× the postal price.
6. **Never hard-code any number** — ITPS L1 gazette rates, EMS L5 estimates (flag), the ÷4000/5000/6000 divisor (config), weight caps (config), and the volatile US duty basis all come from live config with source + timestamp (FR-001).

---

## 9. Source register (URL + date)

| # | Source | Establishes | Level | Date |
|---|---|---|---|---|
| S1 | S.O. 659(E), Post Office (Amendment) Regulations 2026, 6-Feb-2026 gazette (local copy in `06-legal-sources/`) | ITPS Table VIII rates + 135 countries + 50-g slabs | **L1** | 2026-08-08 |
| S2 | DoP OM CF-71/17/2025-CF-DOP 01-Jan-2026 — [potoolsblog](https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html) | US ITPS cap 2→5 kg (O10); +50 countries | L5 mirror of L1 | 2026-01-02 |
| S3 | DoP OM 01-Apr-2025 — [potoolsblog](https://www.potoolsblog.in/2025/03/revised-itps-international-tracked.html) + leatherindia.org DNK page | ITPS 5 kg for ~29 destinations; 2 kg AU/CA/USA (pre-Jan-2026) | L3/L5 | 2025-04 / n.d. |
| S4 | indiapost.org — [International Speed Post (EMS) 2026](https://indiapost.org/international-speed-post-ems) | EMS 250-g slabs, ₹865/₹100, ₹630/₹155, 97+ countries | L5 | 2026-06-17 |
| S5 | ClickPost — [India Post EMS Guide 2026](https://www.clickpost.ai/blog/international-speed-post) | EMS actual-weight counter-claim; 30 kg; transit | L5 | 2026-07-03 |
| S6 | speedpost.report — [Schedule IV PO Regs 2024](https://www.speedpost.report/2024/12/schedule-iv.html) | EMS insurance fees | **L1** | 2024-12-16 |
| S7 | DoP EMS compensation policy — [cept.gov.in](https://test.cept.gov.in/enterpriseportal/mails/international-mail/international-speedpost) | 130 SDR merch comp; 5% delay > 5 days | **L1** | 2026-08-08 |
| S8 | Post Office Regulations 2024 Schedule III Table VI (Air Parcel) — [speedpost.report](https://www.speedpost.report/2024/12/schedule-iii.html) | Air Parcel USA ₹955+175/250g; 20 kg | L1-text/L5-current | 2024-12 |
| S9 | Odisha Post — [Air Parcel](https://odishapost.gov.in/EN/Airparcel.aspx) | Air Parcel 20 kg, 1.05 m / 2 m dims | L3 | n.d. |
| S10 | Corpus: `report.md §4.1–4.3, §6.1–6.2, §11/12` · `findings.md Ctx-5/F-H5-c/d/C16/C17` · `functional-requirements.md FR-022/023/030/031/032` · `follow-ups/01-order-to-delivery-flow/findings.md §3/§5` | Rate anchors, volumetric worked example, transit, who-pays, tracking | — | 2026-08-05/08 |
| S11 | `data/01-countries/{USA,UK,UAE,Australia}/shipping.md` | Per-market ITPS/EMS/courier tables, crossovers, USPS fees | mixed | 2026-08-08 |

---

## 10. Confidence & open items

| Item | Confidence | Note |
|---|---|---|
| ITPS rates + volume-free | **L1 / 92% High** | gazette |
| EMS rates | **L5 / 40–60% — ESTIMATE** | C11; conflicts 2× |
| Volumetric blow-up magnitudes | **45% Low (worked example)** | F-H5-d; counter application unverified (60%, O4) |
| Weight caps | ITPS L1; EMS Low–Mod (C16) | US ITPS cap O10 open |
| Transit times | **L5 (40–60%)** | ranges only |
| EMS insurance + delay comp | **L1** | Schedule IV / DoP policy |
| US duty basis | **92% High volatile** | S.301 10% (24-Jul-2026); re-verify O11 |

**Re-check at build:** (1) EMS Schedule I (C11); (2) US ITPS cap (O10); (3) volumetric counter application (O4); (4) Air Parcel post-cut tariff; (5) US duty basis (O11); (6) live portal calculator quotes per destination.

*End of file. All figures cited with URL + date; every estimate flagged. Companion files: `itps-lane.md`, `ems-lane.md`, `itps-full-rate-table-s0659e.md`.*
