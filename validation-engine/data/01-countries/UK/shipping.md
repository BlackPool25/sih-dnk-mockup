# UK — Shipping Lanes & Costs from India (India Post DNK: ITPS / EMS)

**Country:** United Kingdom · **Snapshot date:** 2026-08-08 · **CURRENT DATE reference:** Aug 2026
**Scope:** India Post international lanes bookable through DNK / booking post offices (EMS, ITPS; foreign parcel is out of scope for ≤2 kg craft goods)
**Confidence language:** High 80–95% · Moderate 60–80% · Low 40–60% · Speculative <40%

---

## 1. TL;DR

| Lane | UK rate basis | 100 g | 500 g | 1,000 g (1 kg) | 2,000 g (2 kg) | Volumetric billing? | Transit (typical) |
|---|---|---|---|---|---|---|---|
| **ITPS** (International Tracked Packet Service) — **the default lane** | ₹200 first 50 g + ₹25/every additional 50 g (actual weight) | **₹225** | **₹425** | **₹675** | **₹1,175** | **No — actual weight only** | ~16–25 days (est.; ~2× EMS) |
| **EMS** (International Speed Post) | ~₹865 first 250 g + ₹100/250 g *(L5, conflict — see §3)* | ~₹865 | ~₹1,165 | ~₹1,665 | ~₹2,665 | Possibly (÷4000/5000/6000 — no official divisor) | **4–14 days** (EMS is the fast lane) |
| **Private couriers** (DHL/FedEx/UPS express) | ~₹1,900–₹2,400 at 0.5–2 kg (3–5 days) | — | ₹1,900+ | ₹2,150–₹2,750 | ₹2,400–₹4,730 | Yes (typically ÷5000) | 2–5 days |

**Steer-to-ITPS rule (corpus §9.2 F4):** for ≤2 kg dense or bulky-light craft goods, ITPS is 20–40% cheaper than EMS on this route and never bills volumetric weight — **use ITPS unless the buyer needs speed (then EMS) or <5-day delivery (then courier)**.

---

## 2. ITPS to the UK — the L1-verified low-cost lane

### 2.1 Rates (L1 — S.O. 659(E) gazette)

**Current legal basis:** *Post Office (Amendment) Regulations 2026*, **S.O. 659(E), published 6-Feb-2026**, substituting **Table VIII (Schedule III)** of the Post Office Regulations 2024 — the complete ITPS postage table for **135 countries**, billed on **first 50 g + every additional 50 g**, effective 6-Feb-2026. (Confirmed structurally by Gazette Tracker / teamleaseregtech / Advocate Gandhi legal overview, all 2026.)

**UK row (from parent corpus §4.1, extracted from the same gazette, L1):**

| ITPS UK | Rate (₹) |
|---|---|
| First 50 g (or part) | **200** |
| Every additional 50 g (or part) | **25** |

**Computed examples (direct arithmetic, corpus §4.1):**

| Weight | 100 g | 500 g | 1,000 g | 2,000 g |
|---|---|---|---|---|
| **ITPS UK cost** | **₹225** | **₹425** | **₹675** | **₹1,175** |

(Check: 100 g = 200 + 25 = 225 ✓ · 500 g = 200 + 9×25 = 425 ✓ · 1,000 g = 200 + 19×25 = 675 ✓ · 2,000 g = 200 + 39×25 = 1,175 ✓)

**Sources:**
- Parent corpus `report.md` §4.1 (S.O. 659(E), 6-Feb-2026; UK ₹200/₹25; computed ₹225/₹425/₹675/₹1,175)
- S.O. 659(E) structural confirmations: https://www.teamleaseregtech.com/updates/article/52530/post-office-amendment-regulations-2026/ · https://advocategandhi.com/recalibrating-international-postal-charges-a-legal-overview-of-the-post-office-amendment-regulations-2026/ (both 2026, describing Table VIII, 135 countries, 50-g slabs)
- Context: prior ITPS extensions (85 countries via S.O. 4907(E) 28-Oct-2025; +50 to 135 via S.O. 6154(E) 31-Dec-2025) — the 6-Feb-2026 table is the current consolidated authority: https://www.potoolsblog.in/2025/10/itps-rates-2025-dop-om-nocf-71172025-cf.html

### 2.2 Weight caps

| Destination | ITPS max weight |
|---|---|
| USA | 5 kg (raised from 2 kg — Shiprocket update, 21-Jan-2026; corpus Ctx-5 flags "US cap may have risen to 5 kg", now confirmed by Shiprocket) |
| Australia, Canada | 2 kg (corpus C17) |
| **UK** | **Per Table VIII of S.O. 659(E) — not individually verified in this pass.** Most countries in the 2025–26 ITPS tables carry **2 kg** caps; a subset carry 5 kg. **Flag: read the UK row off the gazette PDF at build time** (corpus C17 resolved per-destination). |
| ~29 other destinations | 5 kg |

**Sources:** Shiprocket, *What is India Post and What's New in 2026?* (21-Jan-2026) — https://www.shiprocket.in/blog/what-is-india-post-csb-iv-updates/ ("ITPS weight limit for shipments to the USA increased from 2 kg to 5 kg"); corpus report §4.1 + C17.

### 2.3 Volumetric: ITPS is actual-weight only

- **ITPS never bills volumetric weight** — volume is free on this lane (corpus §4.1; F-H5-c). This is the single biggest structural advantage for bulky-light handicrafts (lampshades, big cushions, framed art).
- Bulky-light item worked example (corpus §4.3, confidence 45% Low): a 50×50×30 cm boxed lampshade, actual 1.5 kg, would bill as **12.5–15 kg volumetric on EMS** (÷4000–6000) but as only ~1.5 kg on ITPS — a 7–8× price blow-up avoided by routing to ITPS.
- **Build rule (corpus §9.2 F3):** compute volumetric on EMS/Air-Parcel legs only; ITPS = actual weight; keep the divisor (÷4000/5000/6000) as a configurable parameter.

---

## 3. EMS (International Speed Post) to the UK — fast lane, rate conflict flagged

### 3.1 Rates — ⚠️ THREE conflicting published values, NO authoritative Schedule I public (corpus contradiction C11)

| Source | UK first 250 g | UK additional 250 g | Date |
|---|---|---|---|
| **Parent corpus (report §4.2, L5)** + indiapost.org | **₹865** | **₹100** | corpus 2026-08-05; indiapost.org 2026-06-08 |
| findpincode.net / indianphilately.net (older mirror) | ₹955 | ₹105 | mirror of an older tariff |
| clickpost.ai blog | ₹1,965 | ₹90 | 01-Jul-2026 |

- The corpus treats EMS rates as **estimates (L5), contradiction C11 — "authoritative Schedule I is not reproduced in any fetched source"**.
- The clickpost figure (₹1,965/₹90) is newer but its table contains obvious data errors (USA column shows `$150.00`), so it is **not authoritative** — however it raises the possibility that EMS rates have risen since the ₹865 table. **The divergence ₹865 vs ₹1,965 (~2.3×) must be resolved by reading the current EMS tariff at build time** (official India Post calculate-postage or FPO counter tariff sheet).
- **Presented here as: "~₹865 first 250 g + ~₹100/250 g (L5 estimate; conflict with ₹955 and ₹1,965 — verify at build)".** Do NOT ship ₹865 as fact.

**Sources:**
- Corpus report §4.2 (US/UK ₹865 + ₹100/250 g, L5, C11)
- indiapost.org, *International Speed Post (EMS) 2026: Rates, Countries & Tracking* (08-Jun-2026) — https://indiapost.org/international-speed-post-ems
- clickpost.ai, *India Post Charges 2026* (01-Jul-2026) — https://www.clickpost.ai/blog/india-post-courier-charges
- findpincode.net, *Speed Post International Charges Calculator* (UK ₹955/₹105) — https://www.findpincode.net/speedpost/international-parcel-charges-calculator
- indianphilately.net, *Current Postal Rates — International Speed Post* (UK ₹955/₹105) — http://www.indianphilately.net/intlspeedpostrates.html

### 3.2 EMS weight slabs & coverage

- EMS bills in **250 g slabs**: first-250 g rate + per-additional-250 g rate (corpus §4.2).
- Coverage **~97–108 countries**; no authoritative Schedule I public (C11). UK is served.
- Weight cap for EMS to UK: not individually verified here; general EMS cap cited as 20–35 kg depending on destination (corpus C16: 20 kg general; destination governs).

### 3.3 EMS volumetric risk

- EMS is where the **volumetric divisor bites**: Post Office Regulations 2024 clause (r) define "weight" as **gross or volumetric whichever is higher** (L1), but **no official international divisor exists** — aggregators conflict at ÷4000/÷5000/÷6000 (corpus F-H5-c, 82%). Domestic Speed Post >2 kg is officially ÷5000 (DoP OM 11-Dec-2025).
- Counter application to bulky crafts is **unverified (60% Moderate)**; one aggregator (ClickPost) claims EMS bills purely actual weight at counters — a counter-text that would collapse the risk if true.
- **Practical build rule:** assume EMS may bill volumetrically for bulky items; route bulky-light to ITPS; make ÷4000/5000/6000 a config flag (corpus §9.2 F3).

---

## 4. Transit times (L5, wide spreads — set buyer expectations with ranges, never a single number)

| Lane | UK transit (typical) | Corpus/note |
|---|---|---|
| **EMS** | **4–14 days** (corpus §6.2). Component sources: official escalation matrix "International EMS articles 4–10 days" (pli.indiapost.gov.in); aggregators: US/UK/EU 7–14 working days (indiapost.org); UK/Europe 5–10 business days (indiaposttrackings); UK 7–14 days (trackmyspeedpost) | corpus: 4–14 days |
| **ITPS** | **~16–25 days** (trackmyspeedpost); corpus rule "ITPS is roughly 2× slower than EMS" → ~2× EMS ≈ 8–28 days | estimate (L5) |
| Private express couriers | 2–5 days | L4–L5 |

- Customs clearance at the destination (for >£135 parcels and any item examined) adds **unpredictable extra days** — UK import processing is handled by Royal Mail/Parcelforce, which contacts the recipient when fees are due (see duties-taxes.md §3.2). For ≤£135 seller-VAT parcels, clearance is frictionless at the border.
- The EMC→EMD "quiet period" (departure from India ↔ arrival in UK) is normal; track via the **S10 article number** on Royal Mail + India Post (follow-ups §5).

**Sources:**
- India Post escalation matrix (EMS intl 4–10 days) — https://pli.indiapost.gov.in/CustomerPortal/EscalationMatrix.action
- indiapost.org EMS guide (US/UK/EU 7–14 working days) — https://indiapost.org/international-speed-post-ems
- indiaposttrackings.com — https://indiaposttrackings.com/delivery-time-by-service/ and https://indiaposttrackings.com/ems-international-tracking/ (UK/EU 5–10 business days)
- trackmyspeedpost.com *Delivery Time by Service* (ITPS UK 16–25; EMS UK 7–14) — https://trackmyspeedpost.com/delivery-time-by-service
- Corpus report §6.2 (EMS 4–14 days to UK; ITPS ~2× slower)

---

## 5. Private courier comparison (India → UK) — for context, not the DNK path

| Service | Weight | Indicative cost | Transit | Source / date |
|---|---|---|---|---|
| Express (DHL/FedEx IP/UPS) | <500 g | **~₹1,900** | 3–5 days | clickpost, 04-Jun-2026 |
| Express | 500 g–1 kg | **~₹2,150** | 3–5 days | clickpost, 04-Jun-2026 |
| Express | 1–2 kg | **~₹2,400** | 3–5 days | clickpost, 04-Jun-2026 |
| Economy | 0.5 kg | ~₹1,450 | 6–10 days | clickpost, 04-Jun-2026 |
| Economy | 1–2 kg | ~₹1,950–2,250 | 6–10 days | clickpost, 04-Jun-2026 |
| FedEx International Priority | ~1 kg | ~₹2,750 | 2–3 days | clickpost FedEx guide, 2025 |
| Mixed carriers, 1 kg from Delhi | 1 kg | **₹1,777–₹3,716** | varies | couriervia, updated Aug-2026 |
| CourierBook standard/express (500 g docs) | 0.5 kg | ₹1,200–1,800 / ₹2,200–3,200 | 8–15 / 3–5 days | courierbook, 14-Jan-2026 |

**Reading:**
- India Post is **substantially cheaper**: ITPS 500 g = **₹425** vs courier express ₹1,900+ (≈ **4.5× cheaper**); ITPS 1 kg = **₹675** vs ₹2,150–2,750 (≈ **3–4× cheaper**). Even courier *economy* (₹1,450–2,250) is 2–3× ITPS.
- The 20–40% postal-cheaper claim in the parent corpus (F4-b, 68% Moderate) is confirmed on the UK lane with an even larger gap.
- **Trade-offs:** couriers give 2–5-day delivery + door-to-door with built-in clearance, at 3–4× the price and with volumetric billing (÷5000 typical) — mostly irrelevant for artisan economics except for urgent/high-value orders.

**Sources:**
- clickpost.ai, *Courier Charges for UK from India Per Kg (2026)* (04-Jun-2026) — https://www.clickpost.ai/blog/courier-charges-for-uk
- couriervia.com, *Courier Charges to UK from Delhi* (updated Aug-2026) — https://www.couriervia.com/courier-from-delhi-india-to-united-kingdom
- courierbook.in, *Express vs Standard International Shipping* (14-Jan-2026) — https://www.courierbook.in/blog/express-vs-standard-international/
- clickpost.ai, *FedEx Domestic and International Courier Charges* (19-May-2025) — https://www.clickpost.ai/blog/fedex-courier-charges

---

## 6. Lane decision matrix (DNK booking guidance)

| Order scenario | Weight | Lane | Why |
|---|---|---|---|
| Bulky-light craft (cushion, lampshade, framed textile) | ≤2 kg | **ITPS** | Volume-free (actual weight only); 20–40% cheaper than EMS |
| Dense small craft (jewellery, brass, wood toys, scarves) | ≤2 kg | **ITPS** | Cheapest; tracked |
| Buyer needs speed (≤2 weeks) | ≤2 kg | **EMS** | 4–14 days vs ITPS ~16–25 |
| Heavy >2 kg | >2 kg | EMS / foreign parcel (20 kg general cap) | ITPS cap binds; volumetric risk on bulky items |
| Urgent (<5 days) / high-value | any | DHL/FedEx/UPS | 2–5 days at 3–4× cost; volumetric applies |
| Bulk-light (framed art) | >2 kg | Air parcel? | **Warn:** EMS/parcel volumetric blow-up (÷4000–6000) — check at counter; consider ITPS only ≤2 kg |

**Destination-duty interplay (from duties-taxes.md):** UK ≤£135 → seller charges 20% VAT at point of sale, recipient pays nothing at delivery (no Royal Mail handling fee). >£135 → recipient pays import VAT + duty + £8/£12 handling fee. For typical ≤£135 artisan parcels via ITPS, **the buyer-side surprise at the door is zero** — this is the cleanest of the major markets for seller-paid compliance.

---

## 7. Source register (with dates)

| # | Source | URL | Date |
|---|---|---|---|
| S1 | S.O. 659(E) — Post Office (Amendment) Regulations 2026, Table VIII (135-country ITPS table) | (gazette; structure per teamleaseregtech + advocategandhi mirrors) | 6-Feb-2026 |
| S2 | Corpus report §4.1 (UK ₹200/₹25; ₹225/₹425/₹675/₹1,175) + §4.2 (EMS ₹865/₹100) | — | 5-Aug-2026 |
| S3 | Potoolsblog — ITPS Rates 2025 (S.O. 4907(E), context 45→85→135 countries) | https://www.potoolsblog.in/2025/10/itps-rates-2025-dop-om-nocf-71172025-cf.html | 29-Oct-2025 |
| S4 | Shiprocket — US ITPS cap 2→5 kg | https://www.shiprocket.in/blog/what-is-india-post-csb-iv-updates/ | 21-Jan-2026 |
| S5 | indiapost.org — EMS rates/transit | https://indiapost.org/international-speed-post-ems | 08-Jun-2026 |
| S6 | clickpost.ai — EMS UK ₹1,965/₹90 (conflict) | https://www.clickpost.ai/blog/india-post-courier-charges | 01-Jul-2026 |
| S7 | findpincode / indianphilately — EMS UK ₹955/₹105 (older mirror) | https://www.findpincode.net/speedpost/international-parcel-charges-calculator · http://www.indianphilately.net/intlspeedpostrates.html | n.d. |
| S8 | India Post escalation matrix (EMS intl 4–10 days) | https://pli.indiapost.gov.in/CustomerPortal/EscalationMatrix.action | fetched 2026-08-08 |
| S9 | trackmyspeedpost — ITPS UK 16–25 days | https://trackmyspeedpost.com/delivery-time-by-service | 2026 |
| S10 | clickpost — UK courier charges | https://www.clickpost.ai/blog/courier-charges-for-uk | 04-Jun-2026 |
| S11 | couriervia — Delhi→UK 1 kg ₹1,777–3,716 | https://www.couriervia.com/courier-from-delhi-india-to-united-kingdom | Aug-2026 |

Corpus anchors: `report.md` §4.1–4.3, §6.2; `04-synthesis/findings.md` F-H5-c/d, Ctx-5; `follow-ups/01-order-to-delivery-flow/findings.md` §3 M3.

---

## 8. Confidence flags (honesty summary)

- **ITPS UK rates (₹200/₹25; ₹225/₹425/₹675/₹1,175): High (92%)** — L1 gazette via corpus; arithmetic re-verified.
- **ITPS actual-weight-only billing: High (85–92%)** — corpus; structural, lane-wide.
- **EMS UK rate: LOW (40–60%)** — three conflicting published values (₹865/₹955/₹1,965), no authoritative Schedule I (C11). **Re-verify at build.**
- **Transit times: Low (40–60%)** — L5 aggregators with wide spreads; ranges only.
- **UK ITPS weight cap: unverified in this pass** — read UK row from S.O. 659(E) Table VIII at build (corpus C17).
- **EMS volumetric application at counters: Moderate (60%)** — legal definition exists (L1), counter practice unverified (F-H5-c).
- **Courier prices: Low (40–60%)** — L4/L5 aggregator quotes, volatile; indicative only.

*End of file. All figures cited with URL + access date; every estimate flagged.*
