# UAE — Shipping (India Post DNK / ITPS / EMS from India)

**Country:** United Arab Emirates (UAE) · **Lane:** India Post DNK (ITPS / EMS via Emirates Post) · **Snapshot date:** 2026-08-08
**Corpus anchors:** report.md §4.1 (ITPS rates, L1 gazette S.O. 659(E) 6-Feb-2026), §4.2 (EMS), §6.2 (transit times); review-logistics findings
**Config-flag rule (corpus):** rates are L1-sourced for ITPS (gazette) but EMS figures are unverified (corpus contradiction C11 — no authoritative Schedule I reproduced). Treat EMS numbers as estimates.

---

## 1. Executive summary

| Item | Value | Source / confidence |
|---|---|---|
| **ITPS to UAE (primary lane)** | **₹185 first 50 g + ₹15 per additional 50 g** — actual-weight, volume-free | L1 (S.O. 659(E), 6-Feb-2026; DoP OM 01-Apr-2025) |
| ITPS weight cap (UAE) | **5 kg** | L1 (DoP OM table) |
| ITPS computed: 100 g / 500 g / 1 kg / 2 kg | **₹200 / ₹320 / ₹470 / ₹770** | L1 arithmetic (report §4.1) |
| EMS to UAE (International Speed Post) | First-250g rate **conflicting across sources** (₹600–₹1,400); per-additional-250g ₹40–₹60 | Unverified — corpus C11; treat as estimate |
| EMS transit | **3–8 days** (corpus); secondary sources 5–9 working days | Moderate (L5 corpus; L4 secondary) |
| ITPS transit | **~14–21 days** (Gulf/Asia) | L4–L5 estimate |
| Volumetric | **ITPS: never** (actual weight only, L1). **EMS: divisor unconfirmed** (÷4000/5000/6000 conflict); couriers ÷5000 | Corpus F-H5-c, C8 |
| Private courier vs ITPS | UAE is a cheap lane; private express ≈ ₹2,400–2,690 for 500 g–1 kg vs ITPS ₹320–470 — ITPS is **~5–7× cheaper** at these weights | L4 (clickpost, courierbook) |

**Bottom line:** UAE is one of the cheapest DNK lanes. Steer ≤2 kg bulky-light craft to **ITPS** (actual-weight, volume-free, ₹185 base). Above 2 kg, EMS or private courier.

---

## 2. ITPS to UAE — L1 rate table (the primary lane)

**Billing basis:** actual weight, slabs of **first 50 g + every additional 50 g**. Volume is never billed on ITPS (no volumetric divisor in any official text) — report §4.1; E-H5 E5.5.

### 2.1 Slab rates (L1 gazette, S.O. 659(E), 6-Feb-2026; DoP OM CF-71/38-2024-CF-DOP, 28-Mar-2025, w.e.f. 01-Apr-2025)

| Destination | First 50 g (₹) | Additional 50 g (₹) | Max weight |
|---|---|---|---|
| **UAE** | **185** | **15** | **5 kg** |
| USA | 400 | 35 | 2 kg |
| UK | 200 | 25 | — |
| Singapore | 185 | 15 | 5 kg |
| Australia | 395/370* | 45/40* | 2 kg |

\* 395/45 per S.O. 659(E) 2026 report table; 370/40 per the 2025 OM — ITPS Australia was revised 01-Jan-2026; flag the movement. UAE has been stable at **185/15** across the 2025 OM and the Feb-2026 gazette.

### 2.2 Computed end-to-end ITPS postage to UAE (L1 arithmetic, report §4.1)

| Weight | First-50g | # additional 50-g slabs | Total (₹) |
|---|---|---|---|
| 100 g | 185 | 1 | **200** |
| 500 g | 185 | 9 | **320** |
| 1,000 g | 185 | 19 | **470** |
| 2,000 g | 185 | 39 | **770** |

Formula: `185 + 15 × ceil((W − 50)/50)` for W ≤ 5,000 g.

### 2.3 ITPS booking notes

- Booked at any DNK/booking PO or via the DNK portal (PBE-III/IV flow); postage collected at counter, cash default (report §2.3; order-to-delivery-flow M2).
- **Portal-induction discount: 2% off postage for ITPS booked via portal induction** (retail & contractual) — POS v5.2, 16-Feb-2025 (potoolsblog). EMS portal induction: 1% discount.
- Trackable end-to-end (International Tracked Packet Service). Tracking via India Post / `ipsweb.ptcmysore.gov.in` (order-to-delivery-flow S29/S30).
- For DNK bulk/full-documentation stack: same PBE-III/IV + CN22/CN23 + invoice requirements as any destination (report §5).

---

## 3. EMS (International Speed Post) to UAE

- **Billing:** 250-g slabs (first 250 g + per-additional-250 g) — corpus §4.2. **Weight cap for UAE EMS: 30 kg** (EMS general cap; corpus C16 — destination governs; report says Air Parcel 20 kg general, EMS 30/35 claims unresolved → flag).
- **Rates to UAE (UNVERIFIED — conflicting L4/L5 sources):**

| Source | First 250 g (₹) | Per additional 250 g (₹) | Date |
|---|---|---|---|
| findpincode / indianphilately (shared table) | 895 | 50 | (older table) |
| indspeedpost.com | 1,240 | 50 | — |
| shiprocket (2024) | 600 | 60 | Jul-2024 |
| clickpost (2026) | 1,400 | 40 | Jul-2026 |

**Corpus honesty rule:** no authoritative Schedule I was reproduced in any fetched source (contradiction C11) — **do not ship these as current**. Use the India Post portal rate at booking; encode EMS as a config flag with a "verify at booking" note. What is consistent across sources: **250-g slab structure**, and EMS is typically **20–40% more expensive than ITPS** below 2 kg on the same route (report §4.2).

- **EMS transit to UAE: 3–8 days** (corpus §6.2, L5 wide-spread); secondary sources say **5–9 working days** (courierbook 18-May-2026; trackmyspeedpost "UAE/Gulf 5–9 days"; indiapost.org "Gulf countries 5–8 working days"). Use ranges, never a single number (corpus rule).

---

## 4. Transit times (India → UAE)

| Service | Corpus | Secondary (L4/L5) | Confidence |
|---|---|---|---|
| **EMS** | **3–8 days** | 5–9 working days (courierbook; trackmyspeedpost; indiapost.org) | Moderate |
| **ITPS** | ~2× slower than EMS (report §6.2) | Gulf/Asia **14–21 days** (trackmyspeedpost) | Low–Moderate (estimate) |
| Private express (DHL/FedEx/Aramex) | — | **2–5 days** door-to-door from Indian metros (courierbook; clickpost) | High (L4) |

Sources: report §6.2; courierbook.in/blog/india-to-uae-courier-complete-guide/ (18-May-2026); trackmyspeedpost.com/delivery-time-by-service; indiapost.org/international-speed-post-ems (08-Jun-2026); clickpost.ai.

---

## 5. Private courier comparison (UAE is a cheap lane)

### 5.1 Indicative door-to-door rates India → UAE (L4, 2026)

| Service | 500 g | 1 kg | 2 kg | Transit | Source |
|---|---|---|---|---|---|
| **ITPS (India Post)** | **₹320** | **₹470** | **₹770** | 14–21 d | §2 above (L1) |
| Private express (DHL/FedEx/UPS/Aramex) | ₹2,400 | ₹2,690 | ₹2,950 | 3–5 d | clickpost 29-May-2026 |
| Private express (DTDC/Aramex) | ₹1,890–1,984 | ₹2,100–2,250 | ₹2,400+ | 3–5 d | clickpost 02-Jul-2026 |
| Economy private | ₹1,800–2,500 (range, per-lane) | — | — | 7–15 d | courierbook 18-May-2026 |

**Read:** at 500 g–1 kg, **ITPS is ~5–7× cheaper** than private express; the express premium buys 2–5-day transit vs ITPS ~2–3 weeks. UAE is among the cheapest private-courier lanes (courierbook: "UAE ₹2,500–3,500 express vs USA ₹4,500–6,000"). For ≤2 kg craft, ITPS wins on price; for time-critical or high-value (>AED 1,000 declared, where CoO/CEPA and duty handling matter), express couriers bundle customs clearance.

---

## 6. Volumetric weight notes

- **ITPS: bills ACTUAL weight only** — no volumetric divisor exists in any official ITPS text (E-H5 E5.5; report §4.1). This is the key steering rule: bulky-light craft (lamp shades, jute bags, woodware) go ITPS ≤2 kg, volume-free.
- **EMS/Air-Parcel: volumetric may apply** — Post Office Regulations 2024 define "weight" as gross-or-volumetric whichever higher (L1), but **no official divisor for international mail** exists: aggregators conflict at ÷4000 / ÷5000 / ÷6000 (corpus F-H5-c, C8). One aggregator (ClickPost) claims EMS bills purely on actual weight (E5.7 counter-text) → counter practice is unverified, field-check required.
- **Private couriers (DHL, FedEx, UPS, Aramex): ÷5000** (IATA standard, India outbound) — courierbook volume-weight table. Shiprocket's India-Post integration bills higher-of-dead-or-volumetric (E5.2).
- **Build rule (corpus):** compute volumetric on EMS/Air-Parcel legs only, divisor configurable (÷4000/5000/6000); steer ≤2 kg bulky-light to ITPS (recommendations §1.3).

---

## 7. UAE-specific shipping watch-outs

1. **Recipient pays duty/VAT at pickup** (Emirates Post collects & remits to FTA) — see `duties-taxes.md` §2.3. The recipient-facing estimate is **5% VAT always + 5% duty above AED 1,000**. A 500-g scarf parcel (CIF AED 300–500) → recipient pays **only 5% VAT** at pickup. Set buyer expectations to avoid surprise.
2. **Declared value on CN22/CN23 must be accurate:** if undeclared, Emirates Post applies a **default value of AED 1,000** — which pushes a cheap parcel into the duty band (EMX page). Undervaluing to dodge VAT is unlawful; accurate declaration is the safety rail.
3. **Prohibited/restricted:** no alcohol, tobacco, e-cig/nicotine (always dutiable + excise), and India Post per-country prohibited matrix applies (report §5.2). Curate per `Country_List.pdf` at build.
4. **ITPS 5 kg cap to UAE** — above 5 kg use EMS (30 kg) or courier.
5. **CN22 vs CN23:** CN22 ≤ SDR 300 (~₹30,000); CN23 + commercial invoice for commercial exports (report §5.1).

---

## 8. Source register (URL + date)

| # | Source | Establishes | Level | Date accessed |
|---|---|---|---|---|
| S1 | **S.O. 659(E), Post Office (Amendment) Regulations 2026** (6-Feb-2026 gazette) — via report §4.1 and potoolsblog mirrors | ITPS Table VIII: UAE ₹185/15, 135 countries, 50-g slabs; computed ₹200/₹320/₹470/₹770 | **L1** | 2026-08-08 (via corpus) |
| S2 | **DoP OM CF-71/38-2024-CF-DOP (28-Mar-2025, w.e.f. 01-Apr-2025)** — reproduced at https://www.potoolsblog.in/2025/03/revised-itps-international-tracked.html | ITPS UAE first-50g ₹185, additional-50g ₹15, **max 5 kg**; full country table | **L1** (via L3 reproduction) | 2026-08-08 |
| S3 | **Potoolsblog** — ITPS Rates 2025 (28-Oct-2025) https://www.potoolsblog.in/2025/10/itps-rates-2025-dop-om-nocf-71172025-cf.html | ITPS revision + country additions; per-country weight limits | L1/L3 | 2026-08-08 |
| S4 | **Advocategandhi** — "Recalibrating International Postal Charges" (08-Feb-2026) https://advocategandhi.com/recalibrating-international-postal-charges-a-legal-overview-of-the-post-office-amendment-regulations-2026/ | First-50g/additional-50g slab structure confirmed | L3 | 2026-08-08 |
| S5 | **ClickPost** — "Courier Charges for Dubai" (29-May-2026) https://www.clickpost.ai/blog/courier-charges-for-dubai | Express courier UAE: ₹2,400/500 g, ₹2,690/1 kg, ₹2,950/1–2 kg; 3–5 d | L4 | 2026-08-08 |
| S6 | **ClickPost** — "International Courier Charges" (02-Jul-2026) https://www.clickpost.ai/blog/international-courier-charges | UAE DTDC/Aramex ₹1,890–1,984 (0.5 kg), ₹2,100–2,250 (1 kg), ₹2,400+ (2 kg) | L4 | 2026-08-08 |
| S7 | **CourierBook** — "India to UAE: Complete Lane Guide" (18-May-2026) https://www.courierbook.in/blog/india-to-uae-courier-complete-guide/ | DHL/FedEx 2–3 d, Aramex 3–5 d, **India Post EMS 5–9 d**; Ramadan/Eid +1–2 d | L4 | 2026-08-08 |
| S8 | **CourierBook** — "International Shipping from India" (18-May-2026) https://www.courierbook.in/blog/international-shipping-from-india/ | UAE express ₹2,500–3,500; economy ₹1,800–2,500 | L4 | 2026-08-08 |
| S9 | **CourierBook** — "Volumetric Weight for International Air Freight" (24-Jan-2026) https://www.courierbook.in/blog/volume-weight-calculations/ | Divisors: DHL/FedEx/UPS/Aramex/India Post EMS ÷5000 (conflicts with ÷6000 sources) | L4 | 2026-08-08 |
| S10 | **TrackMySpeedPost** — "Delivery Time by Service" https://trackmyspeedpost.com/delivery-time-by-service | EMS UAE/Gulf **5–9 days**; ITPS **14–21 days** | L5 | 2026-08-08 |
| S11 | **IndiaPost.org** — "International Speed Post (EMS) 2026" (08-Jun-2026) https://indiapost.org/international-speed-post-ems | EMS 250-g slabs; Gulf 5–8 working days; per-country first-250g examples | L5 | 2026-08-08 |
| S12 | **Shiprocket** — "International Speed Post" (Jul-2024) https://www.shiprocket.in/blog/international-speed-post/ | EMS UAE ₹600/₹60 (older rate; superseded) | L4 | 2026-08-08 |
| S13 | **findpincode** — "Speed Post International Charges Calculator" https://www.findpincode.net/speedpost/international-parcel-charges-calculator | EMS UAE ₹895/₹50 (older table) | L5 | 2026-08-08 |
| S14 | **Potoolsblog** — "POS v5.2 released 16/02/2025" https://www.potoolsblog.in/2025/02/pos-v52-released-on-16022025.html | Portal-induction discounts: 2% ITPS, 1% EMS | L1/L3 | 2026-08-08 |
| S15 | **Corpus E-H5** — evidence file (03-evidence/supporting/E-H5-landed-cost-volatility-and-volumetric.md) | E5.1 divisor conflict; E5.5 ITPS actual-weight L1; E5.7 ClickPost EMS actual-weight counter-text; E5.2 Shiprocket volumetric | — | 2026-08-05 |

---

## 9. Confidence & open items

- **High:** ITPS UAE ₹185/15, 5 kg cap, computed ₹200/₹320/₹470/₹770 (L1 gazette + OM; unchanged across 2025→2026 documents).
- **High:** ITPS is actual-weight only (volume-free).
- **Moderate:** EMS transit 3–8 days (corpus) vs 5–9 working days (secondary) — a range, not a point.
- **Low/Unverified (flag in product):** EMS UAE first-250g rate — sources conflict ₹600–₹1,400 (corpus C11; no Schedule I). Volumetric application at FPO counters (corpus F-H5-d, 45–60%). ITPS transit to UAE (14–21 days, L4/L5 only).
- **Open items to close at build:** (1) India Post portal rate for EMS UAE on booking date; (2) ITPS exact cap re-check (5 kg) and any 2026 amendments; (3) whether DNK portal applies the 2% ITPS discount automatically; (4) UAE-side handling fee on top of VAT/duty (not confirmed — see duties-taxes.md open items).

---

*Prepared 2026-08-08 for the DNK export-enablement data pack. ITPS rates are L1; EMS rates are unverified and must be pulled live from the India Post portal at booking. Steer rule: ≤2 kg bulky-light → ITPS (volume-free); transit expectations as ranges.*
