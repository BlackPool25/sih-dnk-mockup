# ITPS Lane — International Tracked Packet Service (India → 135 Countries)

**Lane:** International Tracked Packet Service (ITPS) · **Operator:** Department of Posts (India Post), bookable through Dak Ghar Niryat Kendra (DNK) / booking post offices
**Prepared:** 2026-08-08 · **CURRENT DATE reference:** Aug 2026 · **Corpus anchors:** `report.md §4.1/§6.1`, `04-synthesis/findings.md Ctx-5 (92% High), F-H5-c`, `01-background/review-logistics.md §1–4`, `follow-ups/01-order-to-delivery-flow/findings.md §3/§5`

> **Honesty rule (FR-001):** every rate is a **config flag with source + last-updated timestamp**, never a hard-coded number. ITPS first-50g/additional-50g rates below are **L1 gazette-verified** (S.O. 659(E), 6-Feb-2026). Weight caps and transit times carry lower-confidence flags. Re-check on the India Post postage calculator (`indiapost.gov.in/calculate-postage`) or at a DNK counter before quoting a buyer.

---

## 1. What ITPS is

- **Definition:** ITPS is India Post's **tracked international packet service for lightweight e-commerce/goods** — officially a **letter-post** product. The India Post international-services page lists ITPS inside the letter-post family: *"In the international post, letter post shall include items such as letters, postcards, aerogramme, printed papers … small packets, literature for the blind, M Bag (Bulk Bag), and **International Tracked Packet Service (ITPS)**."* — [indiapost.gov.in/mailproducts/internationalservices](https://www.indiapost.gov.in/mailproducts/internationalservices) (last reviewed 16-Apr-2026; fetched 2026-08-08).
- **Purpose:** *"International Tracked Packet is specially designed to cater to the needs of eCommerce for cross border transactions. However, individuals are also most welcome to use this service. It is the best economical service with visibility to send shipments to Asia Pacific region."* — [Odisha Post (official DoP circle) ITPS page](https://odishapost.gov.in/EN/Itp.aspx) (fetched 2026-08-08, L3). IANS (20-Jan-2026) echoes: ITPS in 135 countries is "a reliable and cost-effective option for cross-border e-commerce shipments" — [ianslive.in](https://ianslive.in/export-benefits-for-msmes-rolled-out-on-postal-channel--20260120181504) (L3).
- **Tracked by design:** the name itself says it — tracking is an inherent product feature, not an add-on. ITPS carries the UPU **S10 article identifier** end-to-end (see §7).
- **Registered Small Packet successor:** Registered Small Packet was **discontinued 1-Jan-2026**; ITPS is the designated replacement for non-document international items [DoP OM CF-71/17/2025-CF-DOP, 01-Jan-2026, via potoolsblog mirror — L5 mirror of L1](https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html). Corroborated by Shiprocket (21-Jan-2026): [shiprocket.in/blog/what-is-india-post-csb-iv-updates](https://www.shiprocket.in/blog/what-is-india-post-csb-iv-updates/).
- **What it is NOT:** not a parcel service (parcels = Air Parcel/SAL/surface parcel); not the fast lane (that is EMS, §2 of ems-lane.md); no signature-required registered service.

---

## 2. Legal basis (L1)

| Item | Detail |
|---|---|
| Gazette | **Post Office (Amendment) Regulations 2026, S.O. 659(E)**, Gazette of India (Extraordinary), **6-Feb-2026**; substitutes **Table VIII** of Schedule III of the Post Office Regulations 2024 |
| File no. | F. No. CF-71/5/2023-CF-DOP |
| Structure | Table VIII = "Postage Structure of International Tracked Packet Service (ITPS)": **First 50 gms or part thereof (₹)** + **For every additional 50 gms (₹)**, country-wise, **135 rows** |
| Origin | Principal regulations: S.O. 5440(E) 16-Dec-2024; last amended S.O. 6154(E) 31-Dec-2025 before this consolidation |
| Verified copy | `data/06-legal-sources/so-659-e-gazette-2026-02-06.txt` (extracted 2026-08-08 from archive.org in.gazette.central.e.2026-02-06.269951); structural confirmations: [teamleaseregtech.com/updates/article/52530](https://www.teamleaseregtech.com/updates/article/52530/post-office-amendment-regulations-2026/) and [advocategandhi.com legal overview](https://advocategandhi.com/recalibrating-international-postal-charges-a-legal-overview-of-the-post-office-amendment-regulations-2026/) (both 2026, L3) |

The gazette text (L1, via corpus) describes ITPS as: *"Dispatch packets internationally with end-to-end tracking … ensure greater transparency, accountability, and security compared to ordinary international mail; track delivery status electronically across participating destination countries"* [advocategandhi legal overview, 08-Feb-2026].

---

## 3. Country coverage — 135 countries (L1)

- **Current:** **135 countries** in Table VIII, S.O. 659(E), 6-Feb-2026 (L1 gazette; corpus Ctx-5, 92% High).
- **Growth timeline** (resolves contradiction C1 — it is a timeline, not a conflict):

| Date | Instrument | ITPS countries |
|---|---|---|
| initial | (service launch) | ~16 (Australia, Bhutan, Cambodia, Hong Kong, Indonesia, Japan, Malaysia, Mongolia, NZ, Philippines, Singapore, South Korea, Sri Lanka, Thailand, Vietnam, USA — per Odisha Post ITPS page) |
| Apr-2025 | DoP OM (revised tariff, w.e.f. 01-Apr-2025) | 45 |
| 28-Oct-2025 | **S.O. 4907(E)** (DoP OM CF-71/17/2025-CF-DOP) | **85** (+40) |
| 31-Dec-2025 | **S.O. 6154(E)** (DoP OM CF-71/17/2025-CF-DOP, 01-Jan-2026) | **135** (+50; also Australia tariff amendment + US cap) |
| 06-Feb-2026 | **S.O. 659(E)** (Post Office (Amendment) Regulations 2026) | **135** (current consolidated table) |

Sources: potoolsblog mirrors of the OMs — [28-Oct-2025](https://www.potoolsblog.in/2025/10/itps-rates-2025-dop-om-nocf-71172025-cf.html), [01-Jan-2026](https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html); press confirmation of the +50 (Mint, 02-Jan-2026: [livemint.com](https://www.livemint.com/economy/india-post-global-network-e-commerce-exports-msme-growth-11767351938231.html); India Seatrade: [indiaseatradenews.com](https://indiaseatradenews.com/india-post-diversifies-e-commerce-export-routes-to-africa-west-asia/) — L3). New 2026 additions include Algeria, Ethiopia, Iran, Iraq, Russia, Papua New Guinea, Zambia.

**Coverage geography:** all of Europe (major), USA/Canada, Japan/Korea/SE Asia, Gulf, Australia/NZ, plus Africa and Central/West Asia. Note: **South Africa, Saudi Arabia, Türkiye, Egypt, Ukraine, Russia** are on the list; countries like **Argentina, Chile, Brazil, Colombia** are on the list. The full 135-country list with per-country rates lives in the companion file `itps-full-rate-table-s0659e.md`.

---

## 4. Rate structure — 50-g actual-weight slabs (L1)

**Formula:** `Postage = First 50 g rate + (additional-50g rate × ceil((W − 50)/50))` for weight `W` g, **billed on ACTUAL weight only**.

- **Volume is free on ITPS — volumetric weight is never billed.** There is no volumetric divisor in any official ITPS text; the gazette slab structure is weight-only (corpus F-H5-c, **82% High**; corpus Ctx-5, 92% High). This is the single most important structural fact for bulky-light handicrafts.
- Slab granularity is **50 g** — every extra 50 g (or part) adds the per-slab rate. Pack to just under a slab boundary (e.g. 500 g instead of 501 g saves one full slab).
- **Registration fee:** none extra for ITPS (it is tracked by design; the ₹150 letter-post registration charge applies to letters/small packets/postcards, not to ITPS as an auto-tracked product — the ₹150 fee is for *adding* registration to untracked letter-post items [indiapost.gov.in internationalservices]).
- **Portal-induction discount:** **2% off postage** for ITPS booked via portal induction (POS v5.2, 16-Feb-2025, potoolsblog — L3). EMS portal induction is 1%.
- **Volume discount (advance-deposit customers):** calendar-month revenue up to ₹1,00,000 → nil; ₹1,00,000–2,00,000 → **5%**; above ₹2,00,000 → **10%** [Odisha Post ITPS page, L3].

### 4.1 Full rate table for major markets (L1, S.O. 659(E) Table VIII)

| Destination | First 50 g (₹) | Each addl 50 g (₹) | 100 g | 500 g | 1,000 g | 2,000 g |
|---|---|---|---|---|---|---|
| **USA** | 400 | 35 | ₹435 | ₹715 | ₹1,065 | ₹1,765 |
| **UK (Great Britain)** | 200 | 25 | ₹225 | ₹425 | ₹675 | ₹1,175 |
| **UAE** | 185 | 15 | ₹200 | ₹320 | ₹470 | ₹770 |
| **Australia** | 395 | 45 | ₹440 | ₹800 | ₹1,250 | ₹2,150 |
| **Canada** | 340 | 40 | ₹380 | ₹700 | ₹1,100 | ₹1,900 |
| **Germany** | 245 | 25 | ₹270 | ₹470 | ₹720 | ₹1,220 |
| **Japan** | 310 | 20 | ₹330 | ₹490 | ₹690 | ₹1,090 |
| **Singapore** | 185 | 15 | ₹200 | ₹320 | ₹470 | ₹770 |

Computed values are **direct arithmetic** from the L1 gazette rows (report.md §4.1 test vectors: USA 100g ₹435 / 500g ₹715 / 1kg ₹1,065 / 2kg ₹1,765; UK ₹225/₹425/₹675/₹1,175; UAE ₹200/₹320/₹470/₹770; AU ₹440/₹800/₹1,250/₹2,150 — all re-verified). The full 135-country table is in `itps-full-rate-table-s0659e.md`.

**Rate-stability note:** the Feb-2026 gazette is the current authority. ITPS rates moved during 2025–26 (e.g. Australia first-50g: ₹330 → ₹370 → ₹395 across 2025–26 revisions; USA stayed ₹400/₹35 through the Jan-2026 OM). Treat any pre-6-Feb-2026 table as stale.

---

## 5. Weight caps per destination (flag O10)

| Destination | ITPS cap | Source / status |
|---|---|---|
| **USA** | **2 kg (gazette extraction) — O10 OPEN: likely raised to 5 kg** | Corpus S.O. 659(E) extraction (2 kg); **DoP OM CF-71/17/2025-CF-DOP 01-Jan-2026 raised USA 2 kg → 5 kg** ("maximum permissible weight limit for the United States of America under the ITPS mail category has also been increased from 2 kg to 5 kg", potoolsblog mirror); Shiprocket 21-Jan-2026 corroborates 5 kg. **Treat current US cap as 5 kg, verify at build (O10 / data README 2026-08-08)** |
| Australia | **2 kg** | L1 (gazette + Post Office Rules 1933 §50E); the US-only cap change does NOT apply to AU |
| Canada | **2 kg** | L1 (gazette per-destination); corpus C17 |
| ~29 other destinations | **5 kg** | DoP OM 01-Apr-2025 ("weight limit raised to 5 kg for 29 destinations", Council for Leather Exports page — L3) + potoolsblog tables |
| Remainder of 135-country list | **2 kg** (per-table) | S.O. 659(E) / potoolsblog Oct-2025 OM (the +40-country table lists **2 kg for all 40**) |

**General size limits (Post Office Rules 1933 §50E, via [indiankanoon.org/doc/59692720](http://indiankanoon.org/doc/59692720/)):** max weight 2 kg; max **90 cm** for length+width+depth combined; **largest dimension ≤ 60 cm** (tolerance 2 mm); roll form: length + 2×diameter ≤ 1,040 mm. Min surface 90×140 mm. *(Note: the 90 cm / 2 kg rule is the letter-post general rule; the per-destination cap table is the operative cap — verify both at build.)*

---

## 6. Transit times (L5 — ranges only, never a single number)

| Destination | ITPS transit (typical) | Basis |
|---|---|---|
| **USA** | **18–28 days** | corpus report §6.2; trackmyspeedpost.com "India Post Delivery Time by Service 2026" (18–28) |
| UK / EU | ~16–25 days (est., ~2× EMS) | trackmyspeedpost; corpus rule "ITPS is roughly 2× slower than EMS" |
| Gulf / Asia (UAE, SE Asia) | ~14–21 days | trackmyspeedpost (Gulf/Asia 14–21) |
| Australia | ~18–28 days (≈2× EMS) | corpus §6.2; trackmyspeedpost |

- **ITPS ≈ 2× EMS transit** across routes (corpus §6.2). EMS = 5–14 days to USA; ITPS = 18–28.
- **Delay events:** India Post issued a public notice for delays on USA-bound mail (~Feb-2026) — periodic US gateway/customs backlogs are a known factor [indiapost.gov.in document listing, via USA shipping.md §1.4].
- **No official lane standard** for ITPS is published; figures are aggregator estimates (L5).
- Destination customs clearance adds unpredictable days on top (excluded from all postal standards).

---

## 7. Tracking (S10 article number, EMSEVT) — the only key that survives end-to-end

- **The tracking key is the S10 article number**, not the PBE number. S10 = 13-char UPU format `LL NNNNNNNN C CC`; outbound India articles end `IN`; the last two letters encode the destination country; the first two encode the service class. The PBE number is a separate exporter-side customs document number (postal authorities write the tracking number onto the PBE, not vice versa) [follow-ups/01-order-to-delivery-flow/findings.md §5.3].
- **ITPS is tracked by design** (International *Tracked* Packet Service) — S10 events from posting to final delivery.
- **Event codes (UPU EMSEVT V3):** `EMA` (posting) → `EMB` (arrival at outward OE) → `EMC` (departure from origin) → `EMD` (arrival at inward OE) → `EDB` (presented to import customs) → `EME` (held by customs) → `EDC` (returned from customs) → `EMF` (departure from inward OE) → `EMH` (failed delivery) → `EMI` (final delivery). The EMC→EMD gap is the normal international "quiet period". [follow-ups findings §5.4; UPU EMSEVT V3]
- **India-side statuses:** Article Booked → Item Received → Bagged/Dispatched ("Bag Despatched to X RMS") → Received at sorting → In Transit → Arrived at Destination Office → Out for Delivery → Delivered; exceptions (Attempted/Addressee absent/Held/RTS). Outbound typically **stops at "Dispatched to foreign country"** on the India side.
- **Public data sources (origin/India):** India Post Track Consignment (`app.indiapost.gov.in`) + IPS Web Tracking (`ipsweb.ptcmysore.gov.in`). **Destination leg:** the destination operator's tracker, joined by the same S10.
- **Integration reality (no public API):** official partner channel = Parcel Directorate E-Commerce API Integration SOP (ECE-5778), not self-serve; practical path = third-party APIs (AfterShip `india-post-int`, 17TRACK, ClickPost, Track123) or scraping the two public trackers. PBE/LEO/EGM customs state is **not public** — do not promise buyers "customs cleared (export)" visibility. [follow-ups findings §5.5]

---

## 8. Documents needed per lane

| Document | ITPS requirement | Source / note |
|---|---|---|
| **CN 22** | For items with contents **up to 300 SDR** (~₹30,000; 1 SDR = ₹109.4194 in 2024 ⇒ 300 SDR ≈ ₹32,800) — small green customs label | postalstudy (2022): "CN-22 for a letter post item with contents up to the 300 SDR"; corpus report §5.1 |
| **CN 23** | For each item with content value **exceeding 300 SDR**; **CN23 + commercial invoice for commercial exports** | postalstudy; indiapost.org EMS guide (CN23 + invoice for commercial > USD 2,500); corpus report §5.1 |
| **Commercial invoice (+ packing list)** | Required for commercial/e-commerce goods; attach a copy to the outside where the form allows | India Post CN23 guidance (CN_23_en.pdf); follow-ups findings §1.1 |
| **PBE-III / PBE-IV** | Export filing via DNK portal: **PBE-III** for e-commerce exports (electronic payment), **PBE-IV** for all other postal exports; gives Article ID + PBE number; auto-generates CN22/23 + harmonised label + invoice | DNK SOP v1.3; Notification 104/2022; Notification 07/2026-Customs |
| **HS/CTH code** per piece | Mandatory on PBE piece details (no vague descriptions) — wrong code kills incentive claims | report §5.1; SOP validation rules |
| **Physical copies for destination customs** | Documents uploaded on the portal are visible to Indian customs only — **physical copies must be attached to the parcel for destination customs** | follow-ups findings §1.1/§1.2 |
| **KYC / ID proof** | Photo ID needed at counter for higher-value parcels (ClickPost cites > ₹25,000 declared value for EMS; the same logic applies to ITPS commercial items) | ClickPost EMS guide 2026 (L5) |

**General rule:** accurate declaration is the #1 documented failure mode. Σ piece values ≤ parcel value; gross ≤ 110% of net; FOB ≤ invoice value (portal validation rules).

---

## 9. Who pays destination duty/VAT (per market — same for ITPS & EMS postal lanes)

Source: `follow-ups/01-order-to-delivery-flow/findings.md §3 M3` (the decisive who-pays finding). **On the DNK postal lane the sender is the default payer only where the service is DDP/PDDP; otherwise the recipient pays at delivery.**

| Market | Who pays | Mechanics |
|---|---|---|
| **USA** | **Recipient at delivery** (DAP-style) unless DDP used | De minimis $800 suspended since 29-Aug-2025 — every US parcel dutiable (90% High); current duty basis: Section 301 10% net-of-MFN (24-Jul-2026, changed 4×/14 months — re-verify, O11); USPS DDP lets the sender prepay |
| **UK** | ≤ £135: **seller charges 20% UK VAT at point of sale**; > £135: recipient pays import VAT + duty + handling to delivery co | Overseas seller must charge/register |
| **EU (27)** | **SENDER pays** — PDDP since 14-Jul-2026: duties/taxes **collected from sender at booking**, remitted via settlement; DDP recommended; €3 flat duty on ≤ €150 from 1-Jul-2026 | DoP OM DA-22/2/2026-IR-DOP (Jul-2026, L1) |
| **UAE** | **Recipient at pickup** — 5% VAT (always, on commercial imports) + 5% duty above AED 1,000; Emirates Post collects & remits to FTA | UAE FTA E-Commerce VAT Guide (L1); Gulf Today 05-Aug-2026 |
| **Australia** | ≤ A$1,000: **seller charges 10% GST at point of sale** (non-resident); > A$1,000: recipient/importer pays | LVIG regime |
| **Canada** | **Recipient pays** at delivery (> CAD 20 threshold; CBSA E14 attached) + Canada Post handling fee | Postal Imports Remission Order |
| **Japan** | **Recipient pays** (total tax ≥ ¥10,000 via Notice of Assessment); below threshold waived | Japan Customs |
| **Singapore** | **Recipient pays** before delivery (CIF > S$400; 9% GST; SingPost app/SAM) | Singapore Customs |

**Build implication:** landed-cost must be a per-market config flag with source link + timestamp (FR-001); the sender-pays EU leg reframes postage as a seller-side cash-advance problem.

---

## 10. Compensation & claims

- **ITPS loss/damage compensation:** restricted to **₹1,000 or the actual declared value of the contents damaged/lost, whichever is less** (sender's declaration final) — [Odisha Post ITPS page, L3](https://odishapost.gov.in/EN/Itp.aspx).
- **Registered international letter-post comparison:** value of contents or **30 SDR** (≈ ₹3,300), whichever is less, **plus postage paid**; partial loss/damage limited to value of lost content — [indiapost.gov.in internationalservices](https://www.indiapost.gov.in/mailproducts/internationalservices).
- **Claims processing:** under the DoP SOP for international-mail compensation (Apr-2025), **ITPS claims settle in ~7 working days** [potoolsblog SOP, Apr-2025, L3 mirror].
- **No delay compensation** on ITPS (unlike EMS, which pays ~5% of postage for >5-day delay). ITPS is a low-price, no-guarantee lane.

---

## 11. Typical use cases (the DNK persona)

- **Sub-2 kg lightweight handicrafts** — block-printed textiles, scarves/stoles, embroidered bags, jute products, imitation jewellery, small woodware/metalware (the 8 `03-product-categories/` SKUs). ITPS is the L1-verified cheapest tracked lane for these (corpus §4.1, Ctx-5).
- **Bulky-light items** (lamp shades, wall hangings, big cushions, framed art): ITPS wins decisively because it **never bills volumetric weight** — see the worked example in `lane-comparison.md` §3.
- **Cross-border e-commerce parcels** (the official design purpose) — tracked, economical, portal-inductable with a 2% discount.
- **Not for:** items > 2 kg (cap; AU/CA stay 2 kg, US ~5 kg), urgent orders needing < 2-week delivery (that's EMS), documents needing registered/signature service, high-value items needing insurance (ITPS loss cap ₹1,000 — use EMS insurance instead).

---

## 12. Booking & payment

- Book at any DNK / booking post office or via the DNK customer portal (`app.indiapost.gov.in/customer-selfservice`, migrated from `dnk.cept.gov.in` per Circular 01/2026).
- **Prepayment is mandatory** (Rule 9, PO Regulations 2024): cash at counter (default), UPI/card at APT 2.0 counters, online card/netbanking via GCIF, advance-deposit account (all products). **BNPL is EMS-only** — not on ITPS [follow-ups findings §3 M2].
- Portal booking → print CN22/23 + harmonised label + invoice → induct at DNK/booking PO → faceless customs at FPO → LEO → dispatch.

---

## 13. Source register (URL + date)

| # | Source | Establishes | Level | Date |
|---|---|---|---|---|
| S1 | **S.O. 659(E), Post Office (Amendment) Regulations 2026**, 6-Feb-2026 gazette (archive.org in.gazette.central.e.2026-02-06.269951; local copy `so-659-e-gazette-2026-02-06.txt`) | Table VIII ITPS: 135 countries, 50-g slabs, per-country rates | **L1** | 2026-08-08 (fetched) |
| S2 | India Post international services page — [indiapost.gov.in/mailproducts/internationalservices](https://www.indiapost.gov.in/mailproducts/internationalservices) | ITPS is letter-post; 219 letter-post destinations; registration ₹150; 30 SDR compensation; size limits; 1 SDR = ₹109.4194 | L1/L3 | 2026-08-08 (fetched; local copy `indiapost-international-services.html`) |
| S3 | Odisha Post ITPS page — [odishapost.gov.in/EN/Itp.aspx](https://odishapost.gov.in/EN/Itp.aspx) | eCommerce purpose; 2 kg packets; compensation ₹1,000/declared value; volume discounts 5–10%; original 16 countries | L3 | 2026-08-08 (fetched) |
| S4 | DoP OM CF-71/17/2025-CF-DOP 28-Oct-2025 — [potoolsblog](https://www.potoolsblog.in/2025/10/itps-rates-2025-dop-om-nocf-71172025-cf.html) | S.O. 4907(E): 45→85 countries; per-country 2-kg weight limits | L5 mirror of L1 | 2025-10-29 |
| S5 | DoP OM CF-71/17/2025-CF-DOP 01-Jan-2026 — [potoolsblog](https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html) | S.O. 6154(E): 85→135 countries; AU tariff amendment; **USA cap 2→5 kg**; Registered Small Packet discontinued | L5 mirror of L1 | 2026-01-02 |
| S6 | Shiprocket — [what-is-india-post-csb-iv-updates](https://www.shiprocket.in/blog/what-is-india-post-csb-iv-updates/) | USA ITPS cap 5 kg; 50 new countries | L4 | 2026-01-21 |
| S7 | IANS — [ianslive.in](https://ianslive.in/export-benefits-for-msmes-rolled-out-on-postal-channel--20260120181504) | ITPS 135 countries, e-comm positioning | L3 | 2026-01-20 |
| S8 | trackmyspeedpost — [delivery-time-by-service](https://trackmyspeedpost.com/delivery-time-by-service) | ITPS transit 18–28 days USA; 14–21 Gulf/Asia; 16–25 UK | L5 | 2026 |
| S9 | DoP SOP for compensation (international mail) — [potoolsblog](https://www.potoolsblog.in/2025/04/standard-operating-procedure-sop-for.html) | ITPS claims ~7 working days; standardized claim SOP | L3 | 2025-04-11 |
| S10 | Post Office Rules 1933 §50E — [indiankanoon.org/doc/59692720](http://indiankanoon.org/doc/59692720/) | ITPS 2 kg / 90 cm / 60 cm size limits | L1 | n.d. |
| S11 | India Post customs declaration guidance — [indiapost.gov.in/documents/reports/customs-declaration](https://www.indiapost.gov.in/documents/reports/customs-declaration) + CN23 PDF | CN22/CN23 rules | L1/L3 | n.d. |
| S12 | postalstudy — [instructions-on-kyc-for-foreign](https://www.postalstudy.in/2022/03/instructions-on-kyc-for-foreign.html) | CN-22 ≤ 300 SDR; CN-23 for parcels/EMS/letter-post > 300 SDR | L3 | 2022-03 |
| S13 | Corpus: `report.md §4.1/§6.1`, `04-synthesis/findings.md Ctx-5/F-H5-c`, `follow-ups/01-order-to-delivery-flow/findings.md §3/§5` | Rate anchors, volumetric-free, tracking/EMSEVT, who-pays duties | — | 2026-08-05/08 |

---

## 14. Confidence & open items

| Item | Confidence | Note |
|---|---|---|
| ITPS rates (135-country Table VIII) | **L1 (92% High)** | S.O. 659(E) gazette; computed examples are deterministic arithmetic |
| Actual-weight-only billing (volume-free) | **82–92% High** | gazette structure; no counter-evidence found |
| 135-country coverage | **L1 / 92% High** | gazette Table VIII |
| US weight cap **2 vs 5 kg** | **O10 OPEN** | corpus extraction says 2 kg; DoP OM 01-Jan-2026 + Shiprocket say 5 kg. **Use 5 kg for USA, verify at build** |
| AU / CA weight caps (2 kg) | **L1 / High** | gazette + PO Rules; not changed by Jan-2026 OM |
| Transit times (18–28 d US; ~2× EMS) | **L5 (40–60%)** | aggregators only; ranges, never points |
| ITPS compensation (₹1,000 / declared value) | **L3 / Moderate** | Odisha Post circle page; counter-check at counter |
| Who pays destination duty | **L1–L3** | per-market table; US basis volatile (O11 — re-verify) |
| Volumetric application at counters | **n/a for ITPS** | ITPS never bills volume (L1) — the divergence from EMS is the product story |

**Re-check at build time:** (1) live portal/calculator rate for each destination; (2) US cap (O10); (3) whether the DNK portal applies the 2% portal-induction discount automatically; (4) any 2026 amendments after S.O. 659(E).

*End of file. All figures cited with URL + date; every estimate flagged. Companion files: `itps-full-rate-table-s0659e.md` (135-country table), `ems-lane.md`, `lane-comparison.md`.*
