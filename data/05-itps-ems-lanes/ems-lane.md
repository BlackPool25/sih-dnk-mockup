# EMS Lane — International Speed Post / Express Mail Service (India → ~97–108 Countries)

**Lane:** EMS / International Speed Post · **Operator:** Department of Posts (India Post), member of the **UPU EMS Cooperative**; bookable through DNK / booking post offices (650+ Speed Post centres)
**Prepared:** 2026-08-08 · **CURRENT DATE reference:** Aug 2026 · **Corpus anchors:** `report.md §4.2`, `04-synthesis/findings.md C11, F-H5-c/d, C16`, `01-background/review-logistics.md §1–4`, `follow-ups/01-order-to-delivery-flow/findings.md §3/§5`

> **⚠️ THE C-11 WARNING (must stay in every EMS quote):** the authoritative EMS tariff — **Schedule I of the Post Office Regulations** — **has never been reproduced in any fetched source** (corpus contradiction C11, still open). All EMS rates below are **L5 ESTIMATES** from aggregators/statutory mirrors, and several sources **conflict by 2×**. **Do NOT ship any EMS rate as fact; pull the live rate from the India Post postage calculator / FPO tariff sheet at booking.** The EMS country list is similarly not authoritatively public.

---

## 1. What EMS is

- **Definition:** *"Express Mail Service (EMS) shall be the fastest service for sending documents and merchandise worldwide."* — [indiapost.gov.in/mailproducts/internationalservices](https://www.indiapost.gov.in/mailproducts/internationalservices) (fetched 2026-08-08).
- **Mechanism:** EMS is the premium international tier of the **UPU EMS Cooperative** network — "the express tier" — giving priority handling at origin, in transit, and at destination customs/network, with **end-to-end tracking and delivery signature** [ClickPost EMS Guide 2026](https://www.clickpost.ai/blog/international-speed-post), L5.
- **Two product categories:** **EMS Documents** (lighter tariff; usually no customs declaration) vs **EMS Merchandise** (parcels/goods; customs declaration + country-specific weight limits) [indiapost.org EMS guide 2026](https://indiapost.org/international-speed-post-ems), L5.
- **Who it serves:** documents (certificates, contracts, visas) and merchandise (gifts, samples, small commercial consignments) — the **above-2-kg lane** for the DNK persona.

---

## 2. Legal basis & the Schedule I problem (C11)

| Item | Detail |
|---|---|
| Governing law | Post Office Act 2023 (s.13) + **Post Office Regulations 2024** (Schedules I–V); EMS tariff lives in **Schedule I** |
| **Schedule I** | **NOT publicly reproduced in any corpus source** (corpus contradiction C11, OPEN). The India Post EMS catalog on data.gov.in is **stale since Dec-2021 — never ship as current** (report §10 build-data map) |
| Weight definition | Post Office Regulations 2024 clause (r): *"weight means gross weight or volumetric weight, whichever is higher"* — **L1 legal definition** (via corpus F-H5-c / thc.nic.in) |
| Volumetric divisor | **NO official international divisor published** — aggregators conflict at ÷4000 / ÷5000 / ÷6000 (corpus F-H5-c, 82% High). Domestic Speed Post > 2 kg is officially ÷5000 (DoP OM 11-Dec-2025, L1) |
| Related instruments | DoP OM DA-22/2/2026-IR-DOP (Jul-2026): EU resumption via PDDP — EMS to EU resumed 14-Jul-2026 (corpus H6 FALSIFIED, 90%) |

**Build rule (FR-022):** treat the EMS divisor as a **configurable parameter (÷4000/5000/6000)**; compute volumetric on EMS/Air-Parcel legs **only**; ITPS is actual-weight-only. Never hard-code a divisor.

---

## 3. Country coverage — ~97–108 (NOT authoritatively public — flag C11)

- **Working figure:** **97+ countries** (UPU EMS Cooperative member count; indiapost.org EMS 2026: "as of 2026, EMS covers more than 97 countries"; ClickPost: "97+ countries through the UPU EMS Cooperative"; corpus range **~97–108**, contradiction C11).
- **Why the count is fuzzy:** the corpus shows **~97 vs ~106–108** (contradiction C11) and **no authoritative Schedule I** was reproduced. The stale Dec-2021 data.gov.in EMS catalog is the only "list" and is 5 years old.
- **Confirmed coverage (multiple 2026 sources):** USA, UK, Canada, Australia, Germany, France, Japan, UAE, Singapore, Saudi Arabia, Sri Lanka, Nepal, Bangladesh, China, South Korea [indiapost.org/ClickPost 2026].
- **Legacy official mirror (Indian Philately/DoP table, ~2011 — L1-text but STALE):** ~99 EMS destinations incl. all of the above, most European states, Russia, Brazil, South Africa, Egypt, etc. **Use only as a coverage-sanity list, never for rates.**

---

## 4. Rate structure — 250-g slabs (first-250g + additional-250g)

**Formula:** `Postage = First-250g rate + (additional-250g rate × ceil((W − 250)/250))` for weight `W` g.

- **Slab structure is the one thing every source agrees on:** EMS bills in **250-g slabs** (corpus §4.2; indiapost.org 2026; findpincode; costcalculator). Per-slab rate varies by destination/zone.
- **Zone structure (L5, ClickPost 2026, indicative):** Zone A (SAARC: Nepal, Bangladesh, Sri Lanka, Pakistan, Bhutan, Maldives, Afghanistan); Zone B (Asia-Pacific: China, Japan, Korea, Singapore, Malaysia, UAE, Saudi, Hong Kong, Thailand, Australia, NZ); Zone C (Europe & Americas); Zone D (rest).
- **Portal-induction discount:** **1%** off EMS postage for portal induction (POS v5.2, 16-Feb-2025, potoolsblog — L3). ITPS portal induction is 2%.
- **Bulk discount (L1, cept.gov.in enterprise portal / Odisha Post EMS page):** monthly International EMS revenue ₹2,00,000–10,00,000 → **5%**; ₹10,00,001–50,00,000 → **10%**; above ₹50,00,000 → **15%** (all EMS destinations).

### 4.1 Rate examples — **L5 ESTIMATES, flag everything** (C11)

| Destination | First 250 g (₹) | Each addl 250 g (₹) | 500 g | 1,000 g | 2,000 g | Primary source |
|---|---|---|---|---|---|---|
| **USA** | **865** | **100** | ₹965 | ₹1,165 | ₹1,565 | corpus §4.2 (L5); indiapost.org 2026; ClickPost Guide 2026 |
| **UK** | **865** | **100** | ₹965 | ₹1,165 | ₹1,565 | corpus §4.2 (L5); indiapost.org 2026 |
| **Australia** | **630** | **155** | ₹785 | ₹1,095 | ₹1,715 | corpus §4.2 (L5); PO Rules §225 (statutory mirror); indiapost.org 2026 |
| Bangladesh (context) | 485 | 35 | ₹520 | ₹590 | ₹730 | indiapost.org 2026 (L5) |
| **UAE** | **CONFLICT — ₹600–1,400** | 40–60 | — | — | — | see §4.2 conflict table |
| Canada | 930 | 165 | — | — | — | legacy indianphilately table (STALE — coverage only) |
| Germany | 865–1,053 | 100 | — | — | — | legacy table (STALE — coverage only) |
| Japan | 420–540 | 90 | — | — | — | legacy table (STALE — coverage only) |
| Singapore | 430–670 | 60 | — | — | — | legacy table (STALE — coverage only) |

*(Computed 500g/1kg/2kg are direct arithmetic on the L5 working figures, NOT L1 — label as estimates.)*

### 4.2 The conflicting EMS figures you will hit (C11 in the wild)

| Source | USA first-250g | UK first-250g | AU first-250g | UAE first-250g | Date |
|---|---|---|---|---|---|
| Corpus §4.2 + indiapost.org + PO Rules §225 | ₹865 | ₹865 | ₹630 | — | 2026-08 (working figure) |
| ClickPost *India Post Charges 2026* | ₹1,820 | ₹1,965 | ₹1,125 | ₹1,400 | 01-Jul-2026 |
| findpincode / indianphilately (legacy) | ₹585 | ₹955 | ₹630 | ₹895 | n.d. (stale) |
| Shiprocket (2024) | — | — | — | ₹600 | Jul-2024 |
| indiaposttracking.net zone table | USA/Canada up to 250g ₹800 | Europe ₹730 | AU/NZ ₹750 | — | 2026-03-10 |

- **Reading:** the ClickPost 2026 numbers (₹1,820–1,965) are newer but contain obvious data errors (e.g. USA column shows `$150.00`), so they are **not authoritative** — yet they raise the possibility EMS rates rose after the ₹865 table. **The ₹865 vs ₹1,965 divergence (~2.3×) must be resolved at the counter/calculator at build time.** Do NOT ship ₹865 as fact.

---

## 5. Volumetric weight — the divisor conflict (flag, never hard-code)

| Aspect | EMS / Air Parcel | ITPS |
|---|---|---|
| Chargeable weight = max(actual, L×W×H÷divisor) | **Applies where the counter uses volumetric** — legal basis: PO Regs 2024 clause (r) "gross or volumetric, whichever higher" (L1); Shiprocket VCN: "higher of Dead Weight or Volumetric Weight" on the India Post lane (L4) | **Never** — actual weight only (L1 gazette) |
| Divisor (international) | **CONFLICT — no official figure:** ÷6000 (courierbook Oct-2025; shipmozo; singhxpress) · ÷5000 (clickpost; courierbook Jan-2026 "UPU standard alignment"; costcalculator Jan-2026) · ÷4000 (smartfree) | n/a |
| Divisor (domestic reference) | ÷5000 for domestic Speed Post > 2 kg (DoP OM 11-Dec-2025, L1) — sometimes misapplied to international | n/a |
| Counter-text | **ClickPost (Jul-2026): "India Post EMS charges on actual weight only … volumetric weight rules do not apply at India Post unlike private couriers"** — a direct contradiction of the legal definition; if true at counters, the EMS blow-up never materialises (corpus F-H5-c, E5.7) | — |
| Counter application to bulky crafts | **UNVERIFIED** (corpus 60% Moderate) — field instrument O4 settles it | — |

**Worked example (Est., NOT measurement — 45% Low per corpus H5-d):** see `lane-comparison.md §3`. 50×50×30 cm, actual 1.5 kg → 12.5–15 kg volumetric (÷6000–5000) → EMS-US bill ₹5,765–6,765 vs ITPS actual-weight ₹715–1,415.

**Practical build rule:** *assume* EMS may bill volumetric for bulky items; steer bulky-light ≤ 2 kg to ITPS; keep the divisor a config flag.

---

## 6. Weight caps — 30–35 kg claims vs 20 kg general (C16)

| Claim | Cap | Source / status |
|---|---|---|
| EMS "typically 2 kg up to 30 kg" | 30 kg max | indiapost.org 2026 (L5); ClickPost ("up to 30 kg") |
| Legacy official EMS table weight limits | 30 kg majority; **20 kg for some** (Bahrain, Belarus, Iceland, Iran, Israel, Mexico, Mongolia, Nauru, Pakistan, Poland, Spain, Taiwan, Thailand, Tunisia, Ukraine, Yemen); 31.5 kg for a few (Barbados, Kenya, Macao, Nepal, Romania, USA, Vietnam) | indianphilately legacy DoP table (L1-text, STALE — coverage/caps sanity only) |
| Corpus resolution C16 | **Air Parcel 20 kg general (destination governs); EMS 30/35 claims unresolved** | corpus contradictions-map C16 — "RESOLVED (20 kg general; destination governs)" |
| ClickPost comparative table | EMS max weight **30 kg** (vs international airmail 2 kg) | ClickPost 2026 (L5) |

**Operative guidance:** destination-dependent; general reference **20 kg** with many destinations accepting up to **30 kg**. **Confirm the destination ceiling at the counter before packing** — a 25-kg parcel accepted by one country may be refused by another.

---

## 7. Transit times (L5 wide spreads — ranges only, never a single number)

| Destination | EMS transit | Sources |
|---|---|---|
| **USA** | **5–14 working days** (typical 7–14; 5–9 business days reported; 12–15 in peaks) | corpus report §6.2 (L5); indiapost.org 2026 (7–14); omnijournal May-2026 (5–9); ClickPost (7–12) |
| **UK** | **4–14 days** | corpus §6.2; indiapost.org (7–14); ClickPost (6–10) |
| **UAE / Gulf** | **3–8 days** (5–8 working days commonly cited) | corpus §6.2; indiapost.org (Gulf 5–8); ClickPost (UAE 5–7); courierbook (5–9) |
| **Australia** | **5–14 days** (6–10 per ClickPost; 7–14 commonly cited) | corpus §6.2; indiapost.org; ClickPost (6–10, biosecurity adds days) |
| **Canada** | **7–16 days** (8–14 per ClickPost) | corpus §6.2; ClickPost (8–14) |
| **EU / Germany** | **6–14 days** (Germany 7–10 per ClickPost) | corpus §6.2; ClickPost |
| **Japan** | **3–7 days** (5–7 per ClickPost) | corpus §6.2; ClickPost |
| **SE Asia** | **3–10 days** (SG 4–6; 5–10 region) | corpus §6.2; indiapost.org; ClickPost |
| SAARC (Nepal/Bangladesh/Sri Lanka) | 3–6 days | ClickPost 2026 (L5) |

- **Official escalation-matrix anchor:** "International EMS articles 4–10 days" — [pli.indiapost.gov.in Escalation Matrix](https://pli.indiapost.gov.in/CustomerPortal/EscalationMatrix.action) (L1, fetched 2026-08-08).
- **Customs time is excluded** from EMS standards; destination customs holds add unpredictable days. **No money-back guarantee** on EMS transit (ClickPost: "EMS carries no guaranteed delivery date" — unlike DHL/FedEx SLA-backed express).
- **USA-bound delay notice** ~Feb-2026 issued by India Post (periodic gateway/customs backlogs) — [via USA shipping.md §5].

---

## 8. Tracking (end-to-end official standards, EMSEVT)

- **Tracking number:** 13-char UPU **S10**; EMS items begin with **E** (e.g. `EM` / `EA` prefixes; example `EX123456789IN`); ends `IN` for India outbound [indiapost.org 2026; ClickPost 2026; follow-ups findings §5.3].
- **EMS has official end-to-end tracking standards** (unlike ITPS which is tracked "by design" but without a published lane standard) [follow-ups findings §5.1].
- **Event codes (UPU EMSEVT V3):** `EMA` posting → `EMB` arrival at outward OE → `EMC` departure → `EMD` arrival at inward OE → `EDB` presented to import customs → `EME` held by customs → `EDC` returned from customs → `EMF` departure from inward OE → `EMH` failed delivery → `EMI` final delivery. The EMC→EMD gap is the normal "quiet period" — a few days at the border is not a lost parcel [follow-ups findings §5.4; UPU EMSEVT].
- **Where to track:** India Post Track Consignment + IPS Web Tracking (`ipsweb.ptcmysore.gov.in`) for the Indian leg; the **destination operator's tracker** for the final leg (USPS / Royal Mail / Australia Post / Japan Post / Emirates Post track the same S10); third-party joiners (AfterShip `india-post-int`, 17TRACK, ClickPost). **No public API** — official partner channel is Parcel Directorate ECE-5778 (not self-serve); PBE/LEO/EGM customs state is NOT public [follow-ups findings §5.5].
- **India-side statuses:** Item Booked → Bag Closed → Dispatched from Sorting Hub → Despatched from Exchange Office (cleared Indian customs) → Arrived at Exchange Office (destination) → Customs Clearance → In Transit to Delivery PO → Out for Delivery → Delivered (signature obtained) [ClickPost 2026, L5].
- **Complaint trigger:** no update for >10 business days after "Despatched from Exchange Office" → file a mail complaint at the originating Speed Post centre or online; international complaints typically within 6 months of booking [ClickPost 2026, L5].

---

## 9. Delay compensation & compensation policy (L1, DoP)

From the DoP International EMS compensation policy (reproduced at [cept.gov.in enterprise portal](https://test.cept.gov.in/enterpriseportal/mails/international-mail/international-speedpost) and [Odisha Post EMS page](https://odishapost.gov.in/EN/EMS.aspx), L1/L3):

| Case | Compensation |
|---|---|
| **Loss / total damage / total theft — EMS Merchandise** | **Value of contents or 130 SDR, whichever is less, PLUS postage paid** |
| Loss / damage — EMS Document | **Postage paid** |
| **Delay in delivery** | **5% of the postage charges for delay of MORE than 5 days** (excluding holidays) from the published norms; **customs time excluded** |
| Registered international letter-post (comparison) | value or 30 SDR (≈ ₹3,300) whichever less + postage |

- **Delay rule in plain terms:** if delivery exceeds the declared standard by > 5 days (holidays excluded), the customer gets ~5% of postage. Customs-hold time does not count toward the delay.
- **Policy document:** "Revised compensation policy for international articles (Registered, Parcels, EMS and ITPS)" — [postalstudy 2022](https://www.postalstudy.in/2022/04/revised-compensation-policy-for.html) confirms the 5%-of-postage delay rule (L3).
- **Claims SOP:** international-mail compensation SOP (Apr-2025) standardises complaint→settlement with financial powers delegated to Incharge/Head FPO [potoolsblog, Apr-2025].

---

## 10. EMS-specific payments & booking

- **BNPL (Buy Now Pay Later) is available on EMS only** — not on ITPS (advance-payment/credit facility for contract customers; ₹10,000/month Speed Post business qualifies) [follow-ups findings §3 M2].
- **Payment modes (all postal products):** cash at counter (default), UPI/card at APT 2.0 counters, online card/POSB-netbanking via GCIF, advance-payment account. Prepayment is mandatory (Rule 9, PO Regulations 2024).
- **Booking rules (L5, indiapost.org/ClickPost 2026):** book **before 2 pm on weekdays** for same-day dispatch; **no at-door pickup for international EMS**; bookable at 650+ Speed Post centres / designated HPOs and at DNKs/booking POs via the DNK portal (PBE-III/IV).

---

## 11. Insurance options (L1 — Post Office Regulations 2024, Schedule IV)

**EMS insurance is a real, fee-based value-added service** (Schedule IV, Table VII(c) — "Insurance Fee (International)", via [speedpost.report/2024/12/schedule-iv.html](https://www.speedpost.report/2024/12/schedule-iv.html), L1 reproduction of PO Regs 2024):

| Service | Insurance fee |
|---|---|
| **EMS / International Speed Post** | (i) value insured up to ₹200 → **₹10**; (ii) every additional ₹100 or part above ₹200 → **₹6** |
| International Letter Post | up to ₹500 → ₹210; every additional ₹500 → ₹10 |
| International Parcel | up to ₹500 → ₹10; every additional ₹500 → ₹10 |
| Registration of international items | ₹150 (letters/small packets/etc.), M Bag ₹750 |
| Advice of delivery | ₹10 (Bhutan/Nepal), ₹20 (other countries) |

- **Why it matters:** the standard UPU liability limit (~SDR 30 ≈ ₹3,300) is "woefully insufficient for electronics or jewellery — purchase additional shipping insurance at the counter for valuable parcels" [ClickPost 2026, L5; UPU liability].
- **In practice:** insurance is bought at the counter at booking; coverage is up to the insured/declared value subject to the item being permitted [trackparcel.in blog, Jan-2026, L5 — premium ~₹1–2 per ₹100 for postal insurance]. Treat the fee table as L1 (Schedule IV) and counter availability as the practical gate.

---

## 12. Documents needed (per lane — EMS)

| Document | EMS requirement | Source / note |
|---|---|---|
| **CN 22** | Items valued below **300 SDR** (~₹30,000–32,800) — small green label affixed to the parcel | postalstudy 2022 (L3): "CN-22 for letter post item with contents up to 300 SDR"; indiapost.org |
| **CN 23** | Items of value **300 SDR or above**, **each EMS parcel**, and **commercial shipments** — detailed customs declaration, two copies; CN23 + commercial invoice for commercial exports (> USD 2,500 per indiapost.org; > USD 300 per ClickPost — use the higher-value rule to be safe) | postalstudy; cept.gov.in EMS page ("CN22: below SDR 300; CN23: SDR 300 or above"); indiapost.org |
| **Commercial invoice (3 copies) + packing list** | Required for commercial/e-commerce goods | ClickPost 2026 (L5); CN23 guidance |
| **PBE-III / PBE-IV** | DNK export filing (PBE-III = e-commerce w/ electronic payment; PBE-IV = other); auto-generates labels + customs forms | DNK SOP v1.3; Notification 104/2022; Ntf 07/2026 |
| **HS/CTH code** per piece | Mandatory on PBE piece details | report §5.1 |
| **KYC / photo ID** | Photo ID at counter for parcels > ₹25,000 declared value | ClickPost 2026 (L5) |
| **Physical copies** | Uploads on the portal are visible to Indian customs only — attach physical copies to the parcel for destination customs | follow-ups findings §1.2 |

**Accuracy rule:** under-declaring commercial goods as "Gift" is customs fraud in both India and the destination (seizure, fines, criminal liability) [ClickPost 2026; CBIC].

---

## 13. Who pays destination duty (per market — same postal mechanics as ITPS)

Source: `follow-ups/01-order-to-delivery-flow/findings.md §3 M3`.

| Market | Who pays | Mechanics |
|---|---|---|
| **USA** | **Recipient at delivery** (DAP-style) unless DDP used | De minimis suspended 29-Aug-2025 — every parcel dutiable; S.301 10% net-of-MFN (24-Jul-2026, volatile — O11); USPS DDP lets sender prepay |
| **UK** | ≤ £135: **seller charges 20% VAT**; > £135: recipient pays import VAT + duty + handling | Overseas seller registers/charges |
| **EU (27)** | **SENDER pays** — PDDP duties-at-booking since 14-Jul-2026; €3 flat duty ≤ €150 from 1-Jul-2026 | DoP OM Jul-2026 (L1); Council Reg (EU) 2026/382 |
| **UAE** | **Recipient at pickup** — 5% VAT always + 5% duty above AED 1,000; Emirates Post collects/remits | UAE FTA guide (L1) |
| **Australia** | ≤ A$1,000: **seller charges 10% GST**; > A$1,000: recipient/importer | LVIG |
| **Canada** | **Recipient** (> CAD 20) + Canada Post handling fee | Postal Imports Remission Order |
| **Japan** | **Recipient** (≥ ¥10,000 total tax) | Japan Customs |
| **Singapore** | **Recipient** before delivery (CIF > S$400; 9% GST) | SingPost/Singapore Customs |

---

## 14. Prohibited / restricted (EMS-specific, L5 + corpus Ctx-4)

- **Absolute prohibitions:** currency/coins, explosives & flammable materials, standalone lithium batteries, perishables, narcotics, weapons/ammunition, radioactive material, obscene material, counterfeit goods, live animals, human remains [indiapost.org 2026; ClickPost 2026].
- **Conditionally restricted:** food items (AU/NZ/US biosecurity — must be commercially sealed & declared), medicines (prescription + quantity limits), electronics with lithium batteries (IATA: state of charge < 30%, declared), seeds/plants (phytosanitary certificate), currency/bearer instruments (FEMA limits).
- **Craft-relevant watch-outs:** magnets (IATA Class 9 dangerous goods — magnetic-closure boxes are a trap), liquids/oils/perfume (small-volume limits), wood & plant articles (per-destination; Ireland bans outright), ayurvedic/herbal (AYUSH/NOC), cosmetics (Drugs & Cosmetics Act). The authoritative per-country matrix is India Post's scanned `Country_List.pdf` — not machine-readable; curate a top-N table with confidence flags (corpus Ctx-4).

---

## 15. ITPS vs EMS on the same route (the reason the persona should default to ITPS)

- **Below 2 kg, ITPS is typically 20–40% cheaper than EMS** on the same route (corpus §4.2) — **Australia is the exception** (EMS beats ITPS above ~450 g; see `lane-comparison.md` §5).
- **EMS wins on:** weight (> 2 kg), speed (5–14 days vs 18–28), delay compensation, BNPL, insurance availability, and 30 kg capacity.
- **EMS loses on:** price at sub-2 kg, volumetric risk on bulky items, and the total absence of an authoritative public rate table (C11).

---

## 16. Source register (URL + date)

| # | Source | Establishes | Level | Date |
|---|---|---|---|---|
| S1 | DoP International EMS compensation policy — [test.cept.gov.in/enterpriseportal/mails/international-mail/international-speedpost](https://test.cept.gov.in/enterpriseportal/mails/international-mail/international-speedpost) + [odishapost.gov.in/EN/EMS.aspx](https://odishapost.gov.in/EN/EMS.aspx) | 130 SDR merchandise comp; postage-only for docs; **5% delay comp > 5 days**; CN22/CN23 rule; bulk discounts 5–15% | **L1/L3** | 2026-08-08 |
| S2 | Post Office Regulations 2024 Schedule IV — [speedpost.report/2024/12/schedule-iv.html](https://www.speedpost.report/2024/12/schedule-iv.html) | **EMS insurance fees** (₹10 up to ₹200; ₹6 per ₹100 above); registration/advice-of-delivery fees | **L1** (reproduction) | 2024-12-16 |
| S3 | Post Office Regulations 2024 clause (r) — "gross or volumetric whichever higher" | Volumetric legal definition | **L1** | 2024 |
| S4 | indiapost.org — [International Speed Post (EMS) 2026](https://indiapost.org/international-speed-post-ems) | 97+ countries; 250-g slabs; USA/UK ₹865+100, AU ₹630+155, BD ₹485+35; transit; CN22/CN23; compensation; EM/EA tracking | L5 | 2026-06-17 |
| S5 | ClickPost — [India Post EMS Guide 2026](https://www.clickpost.ai/blog/international-speed-post) | 97+ countries; zone rates; EMS actual-weight counter-claim; 30 kg; CN22/CN23 (USD 300); transit by country; prohibited list; insurance tip | L5 | 2026-07-03 |
| S6 | ClickPost — [India Post Charges 2026](https://www.clickpost.ai/blog/india-post-courier-charges) | **Conflicting** EMS figures (USA ₹1,820, UK ₹1,965) — C11 evidence | L5 | 2026-07-01 |
| S7 | indianphilately.net — [International Speed Post Rates](http://www.indianphilately.net/intlspeedpostrates.html) | Legacy ~99-country EMS table with per-country weight caps (20/30/31.5 kg) — STALE, coverage-only | L1-text/STALE | n.d. (c.2011) |
| S8 | postalstudy — [Revised compensation policy (Registered, Parcels, EMS, ITPS)](https://www.postalstudy.in/2022/04/revised-compensation-policy-for.html) | 5% delay comp; 130 SDR merchandise | L3 | 2022-04 |
| S9 | pli.indiapost.gov.in Escalation Matrix | "International EMS articles 4–10 days" | L1 | 2026-08-08 |
| S10 | corpus `report.md §4.2/§6.2`, `04-synthesis/findings.md C11/F-H5-c/C16`, `follow-ups/01-order-to-delivery-flow/findings.md §3/§5` | EMS 250-g slabs, ~97–108 countries, transit ranges, BNPL, S10/EMSEVT, who-pays | — | 2026-08-05/08 |

---

## 17. Confidence & open items

| Item | Confidence | Note |
|---|---|---|
| EMS rate structure (250-g slabs) | **High** (all sources agree) | first-250g + additional-250g |
| **EMS rate LEVELS (₹865/₹100, ₹630/₹155)** | **L5 / 40–60% — ESTIMATE, flag** | Schedule I not public (C11); conflicting ₹1,820–1,965 sources |
| EMS country count (~97–108) | **Low–Moderate** | C11; UPU EMS Cooperative ~97+; no authoritative list public |
| Weight caps (20–30 kg general) | **Low–Moderate** | C16 resolved as "20 kg general; destination governs"; 30/35 claims unverified |
| Volumetric divisor | **Unresolved (82% High no-official-figure)** | ÷4000/÷5000/÷6000; ClickPost counter-text says actual-weight at India Post |
| Transit times | **L5 (40–60%)** | wide spreads; ranges only; customs excluded |
| Delay compensation (5% > 5 days) | **L1** | DoP policy; customs time excluded |
| Insurance fees | **L1** | Schedule IV, PO Regs 2024 |
| BNPL availability (EMS only) | **L3** | follow-ups §3 M2 |

**Re-check at build time:** (1) **EMS Schedule I** (the C11 gap — the single most important data fix); (2) live calculator rate per destination; (3) EMS ceiling per destination; (4) whether counters apply volumetric (field instrument O4); (5) US duty basis (O11).

*End of file. All figures cited with URL + date; every rate flagged. Companion files: `itps-lane.md`, `lane-comparison.md`, `itps-full-rate-table-s0659e.md`.*
