# USA — State Sales / Use Tax Rates & Economic Nexus (Cross-Border E-Commerce Parcels)

**File:** `data/01-countries/USA/state-sales-tax-table.md`
**Snapshot date:** 2026-08-08 (rates as of 01-Jul-2026 midyear; nexus as of Jun-2026)
**Scope:** All 50 US states + Washington DC: state-level sales tax rate, typical local add-ons, and the economic-nexus (Wayfair 2018) thresholds that would oblige a **foreign (India) remote seller** delivering parcels to that state to register, collect and remit sales/use tax. Fed-level duties/fees live in [`duties-taxes.md`](./duties-taxes.md).

> **⚠️ The three big cross-cutting facts for a DNK seller:**
> 1. **The US has no federal VAT/GST.** Sales/use tax is **state-level** and applies to *use/consumption* of goods in a state — for an international parcel, the recipient's state's **use tax** is technically due even though CBP does not collect it at the border.
> 2. **45 states (49 + DC minus OR/NH/MT/DE) enforce economic nexus** — once a seller's sales into a state exceed that state's threshold (mostly **$100,000** and/or **200 transactions**), the **foreign seller** becomes liable to register & collect. Marketplace-facilitated sales (Amazon/Etsy etc.) count toward thresholds in most states.
> 3. **For a low-volume DNK artisan** (< ~$100k/yr per state), nexus is *not* triggered; the buyer owes use tax on self-assessed returns (almost never enforced for small consumer parcels). **This table exists so the landed-cost engine can (a) price the destination-state tax where relevant, and (b) flag the moment a seller crosses a threshold.**
> 4. Five states have **no state sales tax** (OR, NH, MT, AK, DE) — but MT has local option taxes in resort towns and AK has strong local taxes (see rows).

---

## A. The master table

Columns: **State** | **State rate** | **Typical combined range** | **Economic nexus threshold (2026)** | **Notes** (local add-ons, marketplace rules, quirks)

Rates source: **Tax Foundation, "State and Local Sales Tax Rates, Midyear 2026" (06-Jul-2026)** — state rate + avg local + max local, population-weighted, as of 01-Jul-2026. Combined range shown as *state rate → state + max local* where a range is meaningful; "flat" states show a single figure.
Nexus source: **Eightx "Economic Nexus Thresholds by State 2026" (10-Jun-2026)**, cross-checked with Avalara / Sales Tax Institute / Wolters Kluwer and Commenda (Jul-2026). "OR"/"AND" = logic of the dollar & transaction tests.

| # | State | State rate | Typical combined range | Economic nexus threshold | Notes |
|---|---|---|---|---|---|
| 1 | **Alabama** (AL) | 4.00% | 4.00–12.00% (avg combined **9.46%**, max local 8.00%) | **$250,000** sales only, no transaction test (previous calendar year; marketplace sales excluded) | Highest avg local rate in the US (5.46%). Local rates vary enormously by city/county. Groceries taxed at reduced rate; some counties reach ~11–12%. |
| 2 | **Alaska** (AK) | **0.00%** (no state tax) | 0.00–7.85% local only | Local-level economic nexus via **Alaska Remote Seller Sales Tax Commission**: $100,000 sales only (200-tx test removed 01-Jan-2025) | No state sales tax, but ~110+ local jurisdictions tax; resort/tourism areas up to 7.85%. Not a DNK concern until local nexus. |
| 3 | **Arizona** (AZ) | 5.60% | 5.60–10.90% (avg **8.54%**, max local 5.30%) | $100,000 sales only (marketplace excluded) | TPT (transaction privilege tax) — technically a gross receipts-style tax on sellers. High local add-ons in Phoenix area. |
| 4 | **Arkansas** (AR) | 6.50% | 6.50–12.63% (avg **9.48%**, max local 6.13%) | $100,000 **OR** 200 transactions | 4th-highest avg combined. High local rates (Tontitown area ~11.5%). |
| 5 | **California** (CA) | **7.25%** (highest state rate; incl. mandatory 1.25% state-local add-on) | 7.25–12.50% (avg **9.03%**, max local 5.25% on top of the 7.25% base) | **$500,000** sales only (marketplace sales COUNT toward threshold) | Biggest US market. Base 7.25% = 6.00% state + 1.25% mandatory local (state-collected). LA/SF areas ~9.5–10.25%; rare district add-ons can push toward 12.5%. Marketplace (Amazon) sales count per CDTFA. |
| 6 | **Colorado** (CO) | 2.90% (lowest non-zero state rate) | 2.90–12.00% (avg **7.89%**, max local 9.10%) | $100,000 sales only | Home-rule cities (Denver 8.81%) drive high combined. Broad nexus reachback. |
| 7 | **Connecticut** (CT) | 6.35% | 6.35% (flat — no local option tax) | **$100,000 AND 200 transactions** (both required; measured 12 mo ending Sep-30) — one of only 2 true AND tests | Flat state rate, no local sales tax. |
| 8 | **Delaware** (DE) | **0.00%** | **None** | **No economic nexus / no state sales tax** | True sales-tax-free state (gross receipts tax on businesses instead). DNK-friendly. |
| 9 | **District of Columbia** (DC) | 6.00% | 6.00% (flat) | $100,000 **OR** 200 transactions | Flat; treated as a state for nexus purposes. |
| 10 | **Florida** (FL) | 6.00% | 6.00–8.00% (avg **6.98%**, max local 2.00%) | $100,000 sales only (previous calendar year) | No local sales tax on most counties' base; discretionary surtaxes in some counties (Miami-Dade 1%+). |
| 11 | **Georgia** (GA) | 4.00% | 4.00–9.00% (avg **7.56%**, max local 5.00%) | $100,000 **OR** 200 transactions | Local option sales taxes pushed many counties up by up to 1pt (2026). |
| 12 | **Hawaii** (HI) | 4.00% | 4.00–4.50% (avg **4.50%**, max local 0.50%) | $100,000 **OR** 200 transactions | GET (general excise tax) — very broad base, taxed on B2B too. Low rates. |
| 13 | **Idaho** (ID) | 6.00% | 6.00–9.00% (avg **6.03%**, max local 3.00%) | $100,000 sales only | Local option up to 3% in some cities. |
| 14 | **Illinois** (IL) | 6.25% | 6.25–11.00% (avg **8.98%**, max local 4.75%) | $100,000 sales only (200-tx test **repealed 01-Jan-2026**; preceding 12 months) | Chicago ~10.25%. IL eliminated its 1% food tax Jan-2026 but locals added their own. |
| 15 | **Indiana** (IN) | 7.00% | 7.00% (flat) | $100,000 sales only (tx test repealed 01-Jan-2024) | Flat 7%, no local. |
| 16 | **Iowa** (IA) | 6.00% | 6.00–7.00% (avg **6.94%**, max local 1.00%) | $100,000 sales only (previous calendar year) | Local option tax up to 1% statewide-cap. |
| 17 | **Kansas** (KS) | 6.50% | 6.50–10.75% (avg **8.71%**, max local 4.25%) | $100,000 sales only | High local rates (some counties +3%). |
| 18 | **Kentucky** (KY) | 6.00% | 6.00% (flat) | $100,000 **OR** 200 transactions (tx test **repeals 01-Aug-2026**) | Flat state rate, no local. |
| 19 | **Louisiana** (LA) | 5.00% | 5.00–11.45%+ (avg **10.13%** — HIGHEST avg combined in US, max local 7.00%) | $100,000 sales only (marketplace excluded) | Worst combined in the country; parish/city add-ons are extreme (New Orleans ~9.75–10%). Raised state rate to 5% Jan-2025. |
| 20 | **Maine** (ME) | 5.50% | 5.50% (flat) | $100,000 sales only (previous calendar year; marketplace excluded) | Flat, no local. |
| 21 | **Maryland** (MD) | 6.00% | 6.00% (flat) | $100,000 **OR** 200 transactions | Flat state rate. |
| 22 | **Massachusetts** (MA) | 6.25% | 6.25% (flat) | $100,000 sales only (tx test repealed 01-Oct-2019; previous calendar year; marketplace excluded) | Flat. |
| 23 | **Michigan** (MI) | 6.00% | 6.00% (flat) | $100,000 **OR** 200 transactions | Flat state rate. |
| 24 | **Minnesota** (MN) | 6.88% | 6.88–9.88% (avg **8.14%**, max local 3.00%) | $100,000 **OR** 200 transactions (preceding 12 months) | Minneapolis/St. Paul +1–1.5%. |
| 25 | **Mississippi** (MS) | 7.00% | 7.00–8.00% (avg **7.06%**, max local 1.00%) | **$250,000** sales only (prior 12 months; marketplace excluded) | High state rate. |
| 26 | **Missouri** (MO) | 4.23% | 4.23–10.85% (avg **8.44%**, max local 6.25%) | $100,000 sales only (current or previous year; marketplace counts) | High local rates (St. Louis/KC ~9–10%). |
| 27 | **Montana** (MT) | **0.00%** | 0.00% (no general local sales tax; limited resort-town local option) | **No state economic nexus** | No state sales tax. A few resort areas (e.g. Big Sky/Whitefish) levy local option taxes of ~3% on lodging/retail. DNK-friendly. |
| 28 | **Nebraska** (NE) | 5.50% | 5.50–7.50% (avg **6.98%**, max local 2.00%) | $100,000 **OR** 200 transactions | |
| 29 | **Nevada** (NV) | 6.85% | 6.85–8.38% (avg **8.24%**, max local 1.53%) | $100,000 **OR** 200 transactions | Las Vegas ~8.38%. |
| 30 | **New Hampshire** (NH) | **0.00%** | **None** | **No economic nexus / no state sales tax** | No sales or use tax (highest property/income substitutes). DNK-friendly. |
| 31 | **New Jersey** (NJ) | 6.63% | 6.63–9.94% (avg **6.60%**; Salem Co. local 3.3125% under UEZ) | $100,000 **OR** 200 transactions | UEZ zones halve the rate to 3.3125%. |
| 32 | **New Mexico** (NM) | 4.88% | 4.88–9.44% (avg **7.68%**, max local 4.56%) | $100,000 sales only | Gross-receipts tax (broad, incl. services); some local +1.5–4%. |
| 33 | **New York** (NY) | 4.00% | 4.00–8.88% (avg **8.54%**, max local 4.88%) | **$500,000 AND >100 transactions** (both required; preceding 4 tax quarters) — one of only 2 true AND tests | NYC adds 4.5% city+state surcharge → 8.875%. Huge market, high threshold. |
| 34 | **North Carolina** (NC) | 4.75% | 4.75–8.25% (avg **7.10%**, max local 3.50%) | $100,000 sales only | Local 2–2.75% (2026 changes). |
| 35 | **North Dakota** (ND) | 5.00% | 5.00–8.75% (avg **7.09%**, max local 3.75%) | $100,000 sales only (tx test repealed 31-Dec-2018) | |
| 36 | **Ohio** (OH) | 5.75% | 5.75–8.00% (avg **7.29%**, max local 2.25%) | $100,000 **OR** 200 transactions (previous calendar year) | Cuyahoga/Summit county add-ons. |
| 37 | **Oklahoma** (OK) | 4.50% | 4.50–11.50% (avg **9.06%**, max local 7.00%) | $100,000 sales only (marketplace excluded) | 6th-highest avg combined; high county/city add-ons. |
| 38 | **Oregon** (OR) | **0.00%** | **None** | **No economic nexus / no state sales tax** | Only state with no sales tax AND no local retail sales tax. DNK-friendly. |
| 39 | **Pennsylvania** (PA) | 6.00% | 6.00–8.00% (avg **6.34%**, max local 2.00%) | $100,000 sales only (previous calendar year) | Philly adds 2% local → 8%. |
| 40 | **Rhode Island** (RI) | 7.00% | 7.00% (flat) | $100,000 **OR** 200 transactions (previous calendar year) | Flat. |
| 41 | **South Carolina** (SC) | 6.00% | 6.00–9.00% (avg **7.49%**, max local 3.00%) | $100,000 sales only | |
| 42 | **South Dakota** (SD) | 4.20% | 4.20–8.70% (avg **6.11%**, max local 4.50%) | $100,000 sales only | The *Wayfair plaintiff* state. State cut to 4.2% in 2023 (sunsets to 4.5%? no — 4.2% until Jun-2027). Broad base incl. services. |
| 43 | **Tennessee** (TN) | **7.00%** | 7.00–9.75% (avg **9.61%** — 2nd highest avg combined, max local 2.75%) | $100,000 sales only (lowered from $500,000 eff. 01-Oct-2020; preceding 12 months) | High state rate + heavy local. |
| 44 | **Texas** (TX) | 6.25% | 6.25–8.25% (avg **8.20%**, max local 2.00%) | **$500,000** sales only (preceding 12 months) | Huge market, high threshold; most localities at max 2%. |
| 45 | **Utah** (UT) | 6.10% | 6.10–10.80% (avg **7.42%**, max local 4.70%) | $100,000 sales only (tx test repealed 01-Jul-2025) | High local add-ons in some areas. |
| 46 | **Vermont** (VT) | 6.00% | 6.00–7.00% (avg **6.43%**, max local 1.00%) | $100,000 **OR** 200 transactions (preceding 12 months) | |
| 47 | **Virginia** (VA) | 5.30% | 5.30–8.00% (avg **5.77%**, max local 2.70%) | $100,000 **OR** 200 transactions | 1% mandatory local included in state rate. |
| 48 | **Washington** (WA) | 6.50% | 6.50–10.70% (avg **9.57%** — 3rd highest avg combined, max local 4.20%) | $100,000 sales only | Seattle ~10.25%; heavy local sales taxes. |
| 49 | **West Virginia** (WV) | 6.00% | 6.00–7.40% (avg **6.60%**, max local 1.40%) | $100,000 **OR** 200 transactions | |
| 50 | **Wisconsin** (WI) | 5.00% | 5.00–7.90% (avg **5.72%**, max local 2.90%) | $100,000 sales only | Milwaukee Co. +0.5–1%. |
| 51 | **Wyoming** (WY) | 4.00% | 4.00–7.00% (avg **5.39%**, max local 3.00%) | $100,000 sales only | Only state with a *decrease* in 2026 (local rate cuts Feb/Jul-2026). |

---

## B. Cross-cutting answers (the questions that matter for a foreign seller)

### B.1 Does a state's sales/use tax apply to an international parcel from India?

- **Technically yes — as *use tax* on the recipient.** Every state with a sales tax also levies a complementary **use tax** (same rate) on tangible personal property purchased out of state and used/consumed in the state. A DNK parcel to a consumer is, in law, subject to the recipient's state use tax.
- **BUT the collection responsibility splits by seller size:**
  - **Below nexus threshold** (e.g. < $100k/yr into that state): the *seller* has **no obligation** to register/collect; the *buyer* owes use tax on their own return (rarely paid/enforced for small consumer parcels; most states have no mechanism at the postal counter — **CBP does not collect state use tax on mail**).
  - **At/above nexus threshold:** the *remote seller* must register in that state, collect its rate at checkout, and remit. **This applies to foreign sellers identically** — state statutes do not carve out non-US sellers (Wayfair applied to all remote sellers; e.g. CA CDTFA and NY DTF guidance cover foreign sellers with in-state sales; the 45 enforcing jurisdictions measure gross sales regardless of seller location).
- **Practical rule for the landed-cost engine:** treat state tax as a **checkout-time collection** line item *only once* a seller crosses a state's nexus threshold; before that, state tax is a buyer-side liability and is NOT part of DNK landed cost. This is the conservative, industry-standard reading (Avalara/TaxJar).

### B.2 The five no-state-tax states and what they tax instead

| State | State sales tax | Local sales tax | What they tax instead |
|---|---|---|---|
| **Alaska** | None | **Yes** (~110+ boroughs/cities; up to 7.85%; e.g. Anchorage 0%, Juneau 5%) | No state income tax either; funded by oil/PFD + local sales taxes. Local nexus via Remote Seller Commission. |
| **Delaware** | None | None | **Gross receipts tax** on businesses (not retail); one of the lowest business-tax states. |
| **Montana** | None | Limited (resort-town local option ~3%, lodging) | No general sales tax; income tax + property; resort-area local option taxes only. |
| **New Hampshire** | None | None | No sales/use tax; high property tax + business profits tax (8.5% BPT/7.5% BET) + interest/dividends tax (repealed). |
| **Oregon** | None | **None** (only state with neither state nor local retail sales tax) | Highest income tax reliance; no sales tax at all. |

### B.3 Any state-rate changes 2025–2026?

- **Louisiana** raised state rate 4.45% → **5.00%** (Jan-2025) — the most recent state-level increase (Tax Foundation Midyear-2026).
- **No state-wide rate change between Jan-2026 and Jul-2026** (Tax Foundation Midyear-2026). Only *local* adjustments: NC combined up (rank −4), GA up (Floating Local Option Sales Tax), WA/CA/VT slightly up, **WY down**.
- **Illinois** eliminated its 1% state food tax (01-Jan-2026); some locals added their own.
- **South Dakota** state rate 4.2% (cut 2023) is scheduled to **sunset to 4.5% in June 2027** unless extended.
- **New Mexico** GRT rate (4.875%) reverts to **5.125% on the next 01-Jul** if a fiscal-year revenue floor (<95% of prior yr) is breached between 2026–2029.

---

## C. Economic nexus logic detail (for the config flag)

- **45 jurisdictions enforce** (49 states + DC, minus OR/NH/MT/DE which have no sales tax). Alaska enforces **locally** via its Remote Seller Sales Tax Commission (46th if counted).
- **Threshold distribution (2026):** 41 jurisdictions at **$100,000**; **CA/TX/NY at $500,000**; **AL/MS at $250,000**.
- **18 jurisdictions still run a 200-transaction test** (OR logic, so 200 orders triggers nexus regardless of revenue): AR, CT, DC, GA, HI, MD, MI, MN, NE, NV, NJ, NY, OH, RI, VT, VA, WV (KY's 200-tx test repeals 01-Aug-2026 → 17 active thereafter).
- **True AND tests (both conditions required):** NY ($500k AND >100 tx) and CT ($100k AND 200 tx). Everywhere else with two prongs is OR.
- **Marketplace-facilitated sales** (Amazon/Etsy/Walmart) count toward the seller's threshold in **most** states (incl. CA, TX, NY, WA, IL, GA, KS); a minority exclude them (AZ, AL, LA, ME, MA, MS, OK). Flag: treat as "count unless excluded".
- **Measurement period** varies: current-or-previous calendar year (most), previous-year-only (AL, FL, IA, PA, RI), preceding-12-months (IL, MN, MS, TN, TX, VT), Sep-30-rolling (CT), 4-prior-quarters (NY).
- **For the DNK build:** because thresholds are per-state and mostly $100k OR 200 orders, a small artisan seller is **nowhere near** nexus in any state. The table is a **warning system**, not a pricing input, at current scale.

---

## D. What a US recipient actually pays at the door (state tax angle)

- **Nothing extra at customs/USPS for state tax** — CBP collects federal duty/fees only on mail; state use tax is not collected at the postal counter. (Contrast: some states require marketplace facilitators to collect; postal imports themselves are not intercepted for use tax.)
- The consumer *may* owe use tax on their state return, but **enforcement for sub-threshold small parcels is essentially nil** in practice across all 50 states (Tax Foundation; multi-state compliance guides).
- **Therefore:** for DNK landed-cost quotes, state sales/use tax should be shown as **"0% collected at delivery"** plus a footnote of the destination-state rate for information, unless the seller has registered in that state.

---

## E. Sources

| Source | URL | Level | Date |
|---|---|---|---|
| Tax Foundation — State & Local Sales Tax Rates, Midyear 2026 | https://taxfoundation.org/data/all/state/2026-sales-tax-rates-midyear/ | L1-ish (authoritative aggregator) | 06-Jul-2026 |
| Tax Foundation — Sales Tax Rates 2026 (Jan) | https://taxfoundation.org/data/all/state/sales-tax-rates/ | same | 20-Jan-2026 |
| Eightx — Economic Nexus Thresholds by State 2026 | https://eightx.co/blog/economic-nexus-thresholds-2026 | L3 | 10-Jun-2026 |
| Avalara — State-by-State Guide to Economic Nexus Laws | https://www.avalara.com/us/en/learn/guides/state-by-state-guide-economic-nexus-laws.html | L3 | 2026 |
| Sales Tax Institute — Economic Nexus State by State Chart | https://www.salestaxinstitute.com/resources/economic-nexus-state-guide | L3 | 2026 |
| Wolters Kluwer — state-by-state economic nexus thresholds | https://www.wolterskluwer.com/en/expert-insights/state-by-state-economic-nexus-thresholds-under-state-sales-tax-laws | L3 | 2026 |
| Commenda — Economic Nexus: thresholds by state (verified vs DOR) | https://www.commenda.io/blog/economic-nexus-sales-tax | L3 | 07-Jul-2026 |
| TaxCloud — 2026 Sales Tax Nexus Thresholds PDF | https://taxcloud.com/wp-content/uploads/2026/03/2026_Sales_Tax_Nexus_Thresholds_TaxCloud.pdf | L3 | 05-Mar-2026 |
| Wipfli — Economic Nexus Chart (Jan-2026) | https://www.wipfli.com/-/media/wipfli/collateral/wipfli-economic-nexus-chart_final_jan26.pdf | L3 | Jan-2026 |
| World Population Review / CheckoutReceipt / LevyIO (secondary mirrors of Tax Foundation) | cross-checked | L4 | 2026 |

**Uncertainty flags:**
1. ⚠️ Exact **local combined ceiling** per ZIP varies — "typical combined range" is a population-weighted generalisation (Tax Foundation); a specific destination ZIP needs a rate-lookup API (Avalara/TaxJar) for exact checkout math.
2. ⚠️ **Marketplace-inclusion** is the least consistent field across sources; confirmed borderline states against state DOR before relying on it.
3. ⚠️ AK/MT local taxes are not captured by the "no state tax" column — check local jurisdiction for those destinations.
4. ⚠️ State statutes can change mid-year (IL food-tax repeal 2026; KY tx-test repeal 01-Aug-2026) — re-check at build time.
