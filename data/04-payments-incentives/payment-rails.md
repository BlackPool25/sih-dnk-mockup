# Payment Rails — Buyer → Artisan (Receive-Money Guide)

**Project:** SIH260113 · **Research area:** dnk-export-enablement · **Date:** 2026-08-08
**Persona this guide is judged against:** the modal artisan — ~₹7,000/month earnings, <7% beyond primary education, woman-dominated, 97% household-based, zero-inventory made-to-order, **legally GSTIN-less** (90% High) [report §3.1; findings F-H2-a]. Selling an item to a buyer in another country and wanting the money to land, in INR, in a bank account the artisan controls.
**Honesty header.** No public API exists on the DNK/ICEGATE/EDPMS path [findings Ctx-2]; every payment rail below is a *third-party commercial service* whose fees/currencies/settlement can and do change. Every figure is a **config flag with source link + last-updated timestamp** (FR-001), and fee quotes are vendor-published (L3/L4), not measured. **PA-CB vs PA-CB-E status is called out rail-by-rail**: "full PA-CB" ≠ "in-principle PA-CB-E" — a rail is only *fully authorised* when RBI has granted the final licence, and in-principle approval does not guarantee final authorisation [review-data-tech §2; findings Ctx-3].

---

## 0. The one-page answer (rail selector)

| Rail | RBI PA-CB status | Currencies | Settlement | Cost (vendor-published) | Best for |
|---|---|---|---|---|---|
| **Razorpay International** | **Full PA-CB** (final licence 02-Dec-2025) | 135 currencies, buyers in 180+ countries | **INR, T+2/T+3** to your linked bank account; optional EEFC (foreign-currency) settlement | **Up to 3%** international cards; **1%** international bank transfers; +18% GST on fees; auto eFIRC **included** | Regular MSME / repeat seller; the default first choice (FR-080) |
| **Wise** | Not a PA-CB — operates via its own/partner-bank licences; receives into Wise account details in 8 currencies | 8 account-currency details (USD, GBP, EUR, …) | INR to your verified Indian bank account in 1–2 days | **~1.6–1.7%** conversion (major corridors) + **~US$2–2.50** e-FIRC fee, +18% GST on fees; mid-market rate, no FX markup | Direct-client / invoice payments; lowest FX cost |
| **PayPal India** | **PA-CB-E in-principle only** (28-May-2025; final authorisation unconfirmed) | ~200 markets, but you can't hold foreign currency | **Auto-converts to INR daily + auto-withdraws** to linked bank account | **4.4% + fixed fee + ~3–4% FX markup + 18% GST ≈ 7–8% all-in** at micro volumes | Buyers who only have PayPal; in-principle status is the caveat |
| **Etsy / Payoneer** | Etsy Payments via Payoneer (no PA-CB on Etsy's own name) | **USD only** to Payoneer account | Weekly (Monday) USD deposit → Payoneer → INR bank | **6.5% + 5% + ₹25 + 2.5% conversion + Payoneer ≈ 12–15% total** | Marketplace context only; the most expensive rail |
| **Stripe** | **Not viable** — India accounts invite-only, no PA-CB | — | — | — | Do not build on Stripe |
| **Cross-border UPI** | **NOT an export-receiving rail** — inbound UPI (UPI One World) is retail P2M for foreign visitors in India | — | — | — | Do not use for export receipts |

**The single most important trap** (see §6): on aggregator rails, the **FIRC lists the aggregator's partner bank — not the buyer — as the sender**. A CA must map the FIRC to the invoice, or the **e-BRC mapping fails** (FR-043/FR-082) [follow-up 01-order-to-delivery-flow §3 M1; review-data-tech §2.1].

---

## 1. Razorpay International (full PA-CB — the default recommendation)

### 1.1 Status
Razorpay secured the **Payment Aggregator – Cross-Border (PA-CB)** licence from RBI on **2-Dec-2025**, placing it among the fintechs authorised for both inward and outward cross-border payments. Its international gateway supports **135 currencies from buyers in 180+ countries** (cards, Apple Pay, Google Wallet, ACH/SEPA/FPS/SWIFT bank transfers). *Full PA-CB — not in-principle.* [Razorpay newsroom, 2025-12-02, https://razorpay.com/newsroom/razorpay-secures-rbis-cross-border-license-igniting-its-push-to-redefine-global-payments-from-india/; Razorpay international, accessed 2026-08-08, https://razorpay.com/accept-international-payments/]

### 1.2 What the artisan must do to receive money
1. **Firm identity + KYC**: a business bank account in the exporter's name, PAN, and Razorpay KYC (business proof, bank proof, authorised signatory). The exporter needs a PAN-linked business identity to onboard.
2. **IEC (mandatory to export at all)**: Reg 2, Notification 104/2022-Customs limits the PBE system to IEC holders [pbe-iii-iv-rules.md §1]. An IEC is obtained from DGFT without a GSTIN ("GSTIN … if applicable", IEC Manual v2.0) [document-stack.md §2.1].
3. **AD code + ICEGATE registration (for the incentive rails, not for the payment itself)**: to unlock IGST refund / e-BRC / Drawback / RoDTEP, the artisan must register on ICEGATE, link the bank account to the DNK site code, and register the AD code [Circular 01/2026 §4.vi.a; document-stack.md §2.3–2.4].
4. **Choose settlement account**: INR settlement goes to the linked bank account (current account recommended); a **multi-currency EEFC account** can be used to hold foreign currency instead (see 1.4) [Razorpay docs, accessed 2026-08-08, https://razorpay.com/docs/payments/international-payments/international-bank-transfer/].

### 1.3 How settlement lands
- **INR settlement at T+2 to T+3** (transaction + 2–3 working days) to the linked Indian bank account. [Razorpay blog, 2026-05-25, https://razorpay.com/blog/merchant-of-record-vs-international-payment-gateway-decision-guide/]
- International bank transfers (MoneySaver Export Account): INR settlement to your current account, or **non-INR settlement to an EEFC account** (a facility for exporters who want to hold foreign exchange before conversion). [Razorpay docs, https://razorpay.com/docs/payments/international-payments/international-bank-transfer/]
- **Auto eFIRC**: an automated digital FIRC is generated for **every** transaction and downloadable from the dashboard — "at no additional cost". [Razorpay blog 2026-05-25; https://razorpay.com/international/]

### 1.4 Fees (vendor-published, L3/L4 — config flag)
| Fee | Rate | Source |
|---|---|---|
| International cards (Visa/MC/Amex/Diners/Discover/JCB/UnionPay) | **Up to 3%** per successful transaction | [Razorpay pricing, accessed 2026-08-08, https://razorpay.com/pricing/] |
| GST on platform fee | 18% | same |
| International bank transfers (ACH/SEPA/SWIFT via virtual accounts) | **1%** of transaction value, zero forex markup | [Razorpay, https://razorpay.com/accept-international-payments/; https://razorpay.com/blog/razorpay-payment-gateway-pricing-explained/ (2026-02-13)] |
| FIRC / e-FIRC | **Included, auto-generated** | [https://razorpay.com/pricing/] |

### 1.5 FIRC mechanics
Razorpay issues an **e-FIRC automatically per transaction** (foreign-inward-remittance evidence) — the exporter does not chase the bank for a certificate. The e-FIRC names the partner bank/aggregator channel as the receiving entity, so the CA still maps it to the invoice (see §6).

---

## 2. Wise (mid-market rate, cheapest FX)

### 2.1 Status
Wise (India) lets Indian businesses and freelancers receive money via **account details in 8 currencies**; a client pays in their local currency to those details, Wise **auto-converts to INR at the mid-market rate** and transfers to the verified Indian bank account. **Wise is not a PA-CB licensee in the Razorpay sense** — it operates its cross-border receipt business under its own RBI permissions/partner-bank arrangements, which is why its in-principle status appears differently in the corpus; treat its availability as *live and operating*, not "in-principle pending". [Wise, https://wise.com/in/business/receive-money; https://wise.com/in/blog/how-to-receive-international-payments-in-india; corpus findings Ctx-3]

### 2.2 What the artisan must do
1. **KYC**: PAN + Indian identity + a verified **INR bank account** (Wise verifies it before payout).
2. No IEC needed just to receive money *via Wise* — but **IEC is still mandatory to export via DNK**, and e-BRC realisation still requires the export to be tied to the AD bank's EDPMS records (see §7). Receiving money on a rail without the export paperwork doesn't create a valid export realisation.

### 2.3 How settlement lands
- Money received to your Wise account details → **auto-converted at mid-market rate** (no FX markup) → INR to your Indian bank account **within 1–2 days**. [Wise Help, accessed 2026-08-08, https://wise.com/help/articles/71lNXW0Ls3gEFhUH8PtodV/receiving-payments-for-indian-businesses]

### 2.4 Fees (vendor-published, L3/L4 — config flag)
- **Conversion fee ~1.6–1.7%** of the transfer value for major corridors (varies by currency/amount). [Infinity App review, 2026-02-20, https://www.infinityapp.in/blog/wise-(transferwise)-india-features-benefits-and-alternatives; Winvesta, 2026-03-27, https://www.winvesta.in/blog/businesses/wise-india-review-2026-features-fees-limitations-verdict]
- **e-FIRC fee**: the equivalent of **US$2** in the requested currency per transfer (US$2.50 for USD), for the automatic e-FIRC issuance. [Wise Help, https://wise.com/help/articles/71lNXW0Ls3gEFhUH8PtodV/receiving-payments-for-indian-businesses; Infinity App 2026-02-20]
- **GST 18%** applies on the conversion-fee component. [Winvesta 2026-03-27]
- **Mid-market rate with zero markup** — this is the rail's core advantage over PayPal's FX markup. [Wise, https://wise.com/in/business/receive-money]

### 2.5 FIRC mechanics
- **e-FIRC emailed within 3 working days** of the money being processed — automatic, no request needed. [Wise Help, https://wise.com/help/articles/2655509/...; https://wise.com/in/blog/firc-certificate (2025-03-31)]
- For **INR transfers** the e-FIRC is the evidence. To get a **bank FIRC** (signed by an AD bank) an exporter can request a **No Objection Certificate (NOC)** from Wise and take it to the bank. [Wise Help FIRC article; corpus follow-up §3 M1]

---

## 3. PayPal India (PA-CB-E **in-principle** — the caveat rail)

### 3.1 Status
PayPal Payments Private Limited received **in-principle approval from RBI to operate as a Payment Aggregator – Cross Border – Exports (PA-CB-E)** on **28-May-2025**; RBI's PA-CB list records "In-Principle Authorisation Granted". **Final/full authorisation is unconfirmed** — do not present PayPal as a fully-licensed PA-CB-E. [PayPal newsroom, 2025-05-28, https://newsroom.apac.paypal-corp.com/2025-05-28-...; RBI list of PAs-CB, https://rbi.org.in/scripts/Bs_viewcontent.aspx?Id=4236; corpus findings Ctx-3]

### 3.2 What the artisan must do
- **KYC**: PAN + identity + linked Indian bank account. For India accounts **you cannot hold foreign currency** — incoming foreign funds are **auto-converted to INR at PayPal's daily rate (≈ midnight IST)** and **auto-withdrawn to the linked Indian bank account within about a day**. [Xflow, 2026-07-24, https://www.xflowpay.com/blog/paypal-transaction-fees]
- IEC + export paperwork remain mandatory for the DNK export itself (see §2.2 note).

### 3.3 Fees (vendor-published, L3/L4 — config flag)
- **Cross-border receipts: 4.4% + fixed fee** (e.g., US$0.30) for the transaction, **+ ~3–4% currency-conversion markup**, **+ 18% GST** on charges → **≈ 7–8% all-in at micro volumes**. [PayPal India business fees, https://www.paypal.com/in/business/paypal-business-fees; Xflow, https://www.xflowpay.com/blog/how-much-paypal-charges-for-usd-to-inr; payMyPage]
- **FIRA via Citibank**: a **Weekly Digital FIRA** is available for download (no request needed); bespoke FIRA/Advice is priced **₹100 + 18% GST per transaction** (≤20 transactions) or **₹2,000 + 18% GST** bulk. [PayPal India FIRC page, https://www.paypal.com/in/business/firc-certificate]

### 3.4 Madras HC confirmation (export-proceeds status)
**Afortune Trading Research Lab LLP v. Additional Commissioner, W.P. No. 2849 of 2021 (Madras HC, 16-Feb-2024):** receipts routed through PayPal (which first credits the intermediary's **Citibank** account, then transfers INR to the merchant's account) **count as export proceeds** for FEMA/GST purposes — a GST refund is admissible even though the money arrives in INR via the intermediary. This is the legal anchor for using aggregator rails on an export. [Indian Kanoon, https://indiankanoon.org/doc/147821356/; Taxscan, 2024-03-06; Taxguru, 2024-03-11, https://taxguru.in/goods-and-service-tax/refund-admissible-receiving-export-proceeds-authorized-dealers-paypal-madras-hc.html]

---

## 4. Etsy / Payoneer (marketplace context, USD-only, most expensive)

- **Etsy only deposits in USD** to your **Payoneer Payment Account**, weekly (Monday, 11:30 am ET). Etsy cannot deposit in another currency. [Etsy Help, https://help.etsy.com/hc/en-us/articles/6742925359255-How-to-Accept-Payments-as-a-Seller-in-India]
- **Fee stack (vendor-published)**: 6.5% transaction fee + 5% + ₹25 processing fee + 2.5% conversion fee (if shop currency ≠ USD) + Payoneer withdrawal/conversion fees (typically up to **~3%** of the amount) → **≈ 12–15% total**. [Karbon, 2026-07-26, https://www.karboncard.com/blog/etsy-payouts-india-fees-conversion; Etsy Payments Policy, https://www.etsy.com/legal/etsy-payments/]
- **What the artisan must do**: PAN + government ID, Etsy shop onboarding, a Payoneer account linked to an Indian bank; funds auto-withdraw from Payoneer to the INR bank within ~48 h. [Payoneer India pricing, https://www.payoneer.com/en-in/about/pricing/]
- **Use**: marketplace context (the buyer is on Etsy, not your storefront); the highest-cost rail — steer the demo's standalone-storefront flows to Razorpay/Wise instead.

---

## 5. Non-viable rails (do not build on these)

### 5.1 Stripe — NOT viable for India onboarding
- **India accounts are invite-only**, and export transactions require additional export setup; Stripe India operates as a payment aggregator under RBI KYC Direction, not as a PA-CB for cross-border export receipts. [Niryat Box, 2026-05-03, https://niryatbox.com/blog/stripe-firc-india-service-exporter-guide; Stripe India RBI-guidelines guide, https://stripe.com/in/guides/rbi-guidelines-kyc-direction]
- **Build consequence:** Stripe is excluded from the rail selector (FR-080 marks it explicitly non-viable) [corpus findings Ctx-3; functional-requirements FR-080].

### 5.2 Cross-border UPI — NOT an export-receiving rail
- The RBI/NPCI cross-border UPI framework (incl. **UPI One World** for inbound travellers) is a **retail Person-to-Merchant (P2M)** payment mechanism for foreign visitors *inside India* — it does **not** give an Indian exporter a way to receive export proceeds from an overseas buyer for goods shipped out of India. [NPCI press release, 2026-02-16, https://www.npci.org.in/uploads/...; RBI press release 2022-2023/1765 on UPI for inbound travellers, https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=55263]
- **Build consequence:** cross-border UPI is explicitly **not** an export rail (FR-080) [corpus findings Ctx-3].

---

## 6. The aggregator-FIRC-sender-mismatch trap (design it out)

- **The trap:** on every aggregator rail the FIRC/e-FIRC is issued in the name of the **partner bank or aggregator channel** (PayPal → Citibank; Razorpay/Wise → their banking partners), **not in the name of the overseas buyer** who actually paid. A CA reconciling the export sees a FIRC whose "sender" is a bank, not the invoice party.
- **Consequence if ignored:** the CA can't map the FIRC to the commercial invoice / PBE, and the **e-BRC mapping fails** — the payment is legally realised but the export is never "closed" in EDPMS, killing IGST/Drawback/FTP claims that depend on e-BRC.
- **Mitigation (FR-043/FR-082, P0 features):** keep the buyer's name, order/invoice number and payment-transaction ID against the FIRC reference; surface a guided "match FIRC → invoice" checklist for the CA; treat aggregator FIRCs as *evidence to be mapped*, never as automatically-tied documents. [corpus: follow-up §3 M1; review-data-tech §2.1; functional-requirements FR-043/FR-082]

---

## 7. FEMA: export realisation & repatriation (the legal floor under every rail)

- **The 9-month rule (base):** under FEMA, an exporter must **realise and repatriate the full export value within 9 months from the date of export** (Reg 9, Foreign Exchange Management (Export of Goods and Services) Regulations, 2015, as amended by the **First Amendment Regulations 2026, 5-Jun-2026**, which reverted Reg 9 from 15 back to 9 months). [Taxguru, 2026-06-05, https://taxguru.in/rbi/foreign-exchange-management-export-goods-services-first-amendment-regulations-2026.html]
- **The 15-month relaxation (still in force — flag):** RBI's **Trade Relief Measures press release, 31-Mar-2026**, clarifies that the earlier relaxation extending realisation to **15 months** (Press Release 2025-2026/1510, 14-Nov-2025) **"shall continue to remain in force"**. As of 2026-08-08 the legal text is 9 months with a relaxation to 15 months available — **make this a config flag and re-verify at build** (FR-001). [RBI, https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=62478]
- **EDPMS is the source of truth:** the **Export Data Processing & Monitoring System** (RBI Master Direction 16/2015-16, 01-Jan-2016) tracks each export's realisation; AD Category-I banks update EDPMS **"as and when realised"**, and since **16-Oct-2017 e-BRCs are generated only from EDPMS data**. [RBI Notification, https://rbi.org.in/Scripts/NotificationUser.aspx?Id=11119]
- **e-BRC:** DGFT's enhanced e-BRC system builds the certificate from **electronic Inward Remittance Messages (IRMs)** transmitted directly by banks; exporters can **self-generate e-BRC** on the DGFT portal. [DGFT e-BRC, https://www.dgft.gov.in/CP/?opt=eBRC]
- **DNK integration:** since **17-Sep-2024** the DNK portal exchanges data with EDPMS so **AD banks issue e-BRCs automatically** for postal exports. [PIB PRID 2055743, https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2055743]
- **FEMA undertaking on the PBE:** since the 2026 substituted forms, every PBE carries a **FEMA declaration** — the exporter undertakes to abide by FEMA 1999 **including realisation and repatriation** of foreign exchange [Notification 07/2026-Customs, 15-Jan-2026, local copy `data/06-legal-sources/notification-07-2026-customs.txt`, declaration 6].
- **Artisan implication:** the money landing in a bank account is only *half* the compliance story — the **export must be closed (realised) in EDPMS within the window**, which is why e-BRC guidance is a P0 product feature (FR-044).

---

## 8. Artisan → India Post: postage payment modes (M2)

The artisan also *pays* India Post for postage. **Prepayment is mandatory** (Rule 9, Post Office Regulations 2024), and the default at the counter is **cash**.

| Mode | Applies to | Mechanics | Source |
|---|---|---|---|
| **Cash at counter (default)** | All | "If no contract is mapped, then the payment mode is shown as cash" — standard Retail Customer ID | [DNK SOP v1.3, local copy `data/06-legal-sources/dnk-sop-wayback.txt`] |
| **UPI / QR / debit card at counters** | All | APT 2.0 counter payments | [follow-up §3 M2] |
| **Online card / POSB netbanking** | All | Via GCIF account (India Post's online payment facility) | [follow-up §3 M2] |
| **Advance-payment account (contract)** | **All products** (foreign letters, foreign parcel, EMS, ITPS) | Contractual customer; postage adjusted from advance deposit at induction in PoS | [DNK SOP v1.3: "advance payment facility is available for all products"] |
| **BNPL ("Book Now Pay Later")** | **EMS only** | Contractual customer; BNPL facility is limited to Express Mail Service | [DNK SOP v1.3: "BNPL facility is available only for Express Mail Service (EMS)"] |
| **Aggregator billing** | e-platform / e-marketplace contracts | Addenda with e-commerce platforms | [DoP OM DA-22/2/2026-IR-DOP; follow-up §3 M2] |

**Build consequence:** the demo must not assume online postage is universally available — the **cash-at-counter default** and the contract-gating of advance/BNPL are documented constraints; the portal's advertised "wallet" for online postage is **unverified** (treat as a flag, not a feature) [follow-up §3 M2].

---

## 9. Which rail for which artisan (selector logic, FR-080)

| Seller profile | Recommended rail | Why |
|---|---|---|
| **First-order artisan** (no GSTIN, low volume, INR-only needs) | **Wise** (if buyer can pay by bank transfer to Wise details) or **Razorpay International cards** | Lowest FX cost (Wise mid-market) / auto eFIRC (Razorpay); no GSTIN required to *receive* money (GSTIN is needed for the IGST-refund rail, not for the payment itself) |
| **Regular MSME / repeat seller** (GSTIN-holder, wants incentive rails) | **Razorpay International** | Full PA-CB, 135 currencies, auto eFIRC per transaction, 3%/1% fees, EEFC MoneySaver optional |
| **Buyer insists on PayPal** | **PayPal India** | Works, but in-principle PA-CB-E status + ~7–8% all-in fees; auto-withdraw INR daily |
| **Selling on Etsy** | **Etsy → Payoneer** | Marketplace context; USD-only; 12–15% total |
| **Never** | Stripe, cross-border UPI | Not viable / not an export rail (§5) |

**Build consequence:** the rail selector must display PA-CB status (full vs in-principle) next to each rail and mark every fee "vendor-published, verify at onboarding" (FR-002).

---

## 10. Sources & flags

**Key sources (accessed 2026-08-08 unless dated):**
- Razorpay: newsroom PA-CB (2025-12-02, https://razorpay.com/newsroom/razorpay-secures-rbis-cross-border-license-igniting-its-push-to-redefine-global-payments-from-india/); international (https://razorpay.com/accept-international-payments/); pricing (https://razorpay.com/pricing/); MoR-vs-IPG blog (2026-05-25); pricing-explained blog (2026-02-13); MoneySaver docs (https://razorpay.com/docs/payments/international-payments/international-bank-transfer/)
- Wise: business receive (https://wise.com/in/business/receive-money); India help article (https://wise.com/help/articles/71lNXW0Ls3gEFhUH8PtodV/receiving-payments-for-indian-businesses); FIRC help (https://wise.com/help/articles/2655509/...); firc-certificate blog (2025-03-31); Infinity App review (2026-02-20); Winvesta review (2026-03-27); Skydo compare (https://www.skydo.com/compare/wise-alternatives)
- PayPal: newsroom PA-CB-E (2025-05-28); RBI PA-CB list (https://rbi.org.in/scripts/Bs_viewcontent.aspx?Id=4236); merchant fees (https://www.paypal.com/in/business/paypal-business-fees; merchant-fees PDF 28-Mar-2024); FIRC/FIRA page (https://www.paypal.com/in/business/firc-certificate); Xflow transaction-fees (2026-07-24) & USD-INR (https://www.xflowpay.com/blog/how-much-paypal-charges-for-usd-to-inr); Madras HC Afortune Trading case (Indian Kanoon https://indiankanoon.org/doc/147821356/; Taxscan 2024-03-06; Taxguru 2024-03-11)
- Etsy/Payoneer: Etsy India help (https://help.etsy.com/hc/en-us/articles/6742925359255); Etsy Payments Policy (https://www.etsy.com/legal/etsy-payments/); Karbon fee-stack blog (2026-07-26); Payoneer India pricing (https://www.payoneer.com/en-in/about/pricing/)
- Stripe/UPI: Niryat Box Stripe-FIRC guide (2026-05-03); Stripe RBI-guidelines (https://stripe.com/in/guides/rbi-guidelines-kyc-direction); NPCI UPI One World (2026-02-16); RBI PPI/UPI inbound (https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=55263)
- FEMA/EDPMS/e-BRC: Taxguru First Amendment Regs 2026 (2026-06-05); RBI press release 2025-2026/2362 (31-Mar-2026, https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=62478); RBI EDPMS/eBRC notification (https://rbi.org.in/Scripts/NotificationUser.aspx?Id=11119); DGFT e-BRC (https://www.dgft.gov.in/CP/?opt=eBRC); PIB PRID 2055743 (17-Sep-2024)
- Corpus anchors: report §2.4, §5.1, §9.2; findings Ctx-3, F-H1; functional-requirements FR-080/081/082; follow-up 01-order-to-delivery-flow §3 M1/M2/M4; document-stack.md §2.1–2.4; DNK SOP v1.3 (local copy); Circular 01/2026-Customs (local copy); Notification 07/2026-Customs (local copy); Post Office Regulations 2024 (Rule 9)

**Flags (do not re-assert as fact):** (1) PayPal final PA-CB-E authorisation — unconfirmed, in-principle only; (2) Wise's RBI status wording — operates cross-border receipts under its own permissions, not labelled PA-CB in vendor docs; (3) all fee percentages are vendor-published (L3/L4), not measured — re-verify at onboarding; (4) Wise e-FIRC fee is US$2 (USD corridor US$2.50) per the Help Centre vs US$2 flat in some reviews — treat as configurable; (5) the 9-month vs 15-month FEMA realisation window is a live policy tension (9-month base text vs 15-month relaxation "continues in force" per 31-Mar-2026) — config flag, re-verify at build; (6) Etsy 12–15% total is a composite estimate from vendor fees (FR-002: label estimate); (7) portal wallet for online postage — unverified.
