# Document Stack — What an Artisan Needs to Export via DNK

**Project:** SIH260113 · **Research area:** dnk-export-enablement · **Date:** 2026-08-08
**Persona this stack is judged against:** the modal artisan — ~₹7,000/month earnings, <7% beyond primary education, woman-dominated, 97% household-based, zero-inventory made-to-order, **legally GSTIN-less** (90% High, findings F-H2-a) [report §3.1, findings.md].
**Reading note.** "Mandatory / Optional / Conditional" below is the *legal-and-documented* status, not the perceived one. The single most important research finding is that the **stack itself is the barrier**: IEC + ICEGATE + AD-code + E-Sanchit (and the contested GSTIN) exceed what a low-literacy solo artisan can clear unaided — H1 corroborated at 82% [findings F-H1-a]. Every electronic incentive claim (IGST refund, e-BRC, Drawback, RoDTEP, RoSCTL) sits behind this stack, and **no published instance exists of an individual artisan realizing an electronic incentive since the Jan-2026 unlock** [findings F-H1-c].
**Honesty header.** No public API exists on the DNK/ICEGATE/EDPMS path; all figures below are from L1/L2 documents, official portals, and secondary mirrors cross-checked against the corpus — never fabricated fees, never invented portal steps [report §10; review-data-tech §0].

---

## 1. The stack at a glance

| # | Document | Purpose | Status (law/docs) | Indicative cost | Indicative time | Friction for the persona |
|---|---|---|---|---|---|---|
| 1 | **IEC** (DGFT, 10-char) | Legal precondition to file any PBE (Reg 2, Ntf 104/2022); validated live against DGFT | **MANDATORY** | ₹500 application fee (DGFT help file); IEC itself described as free under FTP 2023 | Auto-generated on submission — same day | Needs firm PAN + firm-name bank account + Aadhaar e-Sign/DSC; portal literacy; booking disabled if IEC suspended/blacklisted |
| 2 | **GSTIN** | Profile field; keys the IGST-refund rail (ICES Advisory 012/2017) | **LEGALLY OPTIONAL** for the persona; CONTESTED on the portal (see §3) | Free to obtain; carries compliance burden | — | Perceived-mandatory; whether migrated portal hard-blocks IEC-only users is **untested** |
| 3 | **AD Code** (14-char) | Registers the export bank account with Customs; gateway for IGST refund, e-BRC, electronic incentives | **Optional** in DNK profile; **REQUIRED on ICEGATE** for electronic claims | Bank-set issuance fee (no public fixed figure) | Days (approval delays acknowledged by CBIC) | Bank letter + passbook upload via e-Sanchit; approval status tracking |
| 4 | **ICEGATE registration + bank account linked to DNK site code** | **Mandatory for every electronic incentive claim** (Circular 01/2026 para 4.vi.a) | **MANDATORY** (conditional on claiming electronically) | Free | Same-day to a few days | Class-3 DSC required; CLK-role bank-account approval |
| 5 | **E-Sanchit uploads** | Per-claim supporting-document upload for electronic PBE claims | **Conditional** (electronic claims only) | Free | Per-claim, minutes | Login-gated; export-side capability **unverified** (C14) — potential hidden blocker |
| 6 | **UDYAM** (MSME) | MSME identity; **required for EPCH manufacturer-exporter RCMC** | **Optional** for DNK; conditional for FTP/MSME benefits | **Zero** (official) | Minutes–same day | Aadhaar-linked mobile OTP only; fraud-portal warning |
| 7 | **EPCH RCMC** | Handicrafts council registration for FTP schemes | **Conditional** (FTP benefits only) | Council-set (not a public fixed figure) | Days–weeks | Needs UDYAM first (manufacturer exporter); DGFT login; council processing |
| 8 | **Commercial invoice + packing list** | Destination customs + value declaration; **#1 documented failure mode** | **MANDATORY** for commercial parcels | Free (portal auto-generates invoice from entered data) | At booking | Mismatch invoice↔packing list = holds; artisans rarely invoice |
| 9 | **HS/CTH code per piece** | PBE declaration; wrong code = claim killed | **MANDATORY** per piece | Free (in-portal description→HS lookup) | At booking | "HS codes and export details are confusing" (L5, corroborated L4) |
| 10 | **CN 22 / CN 23** | Customs declaration on the parcel; CN22 ≤ 300 SDR, CN23 > 300 SDR | **MANDATORY** per parcel; auto-generated with the label set | Included in postage | At booking | Fields must be right; SDR auto-computed by portal |
| 11 | **Certificate of Origin** | Trade-agreement duty preference at destination | **Conditional** (agreement + origin criteria) | eCoO fees vary by issuing agency (not fixed) | Online, fast | Needs FTA in force + RoO compliance; buyer-driven |
| 12 | **Product-specific NOCs** (AYUSH / Spice Board / Tea Board / phytosanitary / wood) | Prohibited/restricted product clearance | **Conditional** (product × destination) | Authority-set (not fixed) | Days–weeks | Hard to source alone; per-country truth table is a scanned PDF |
| 13 | *(Supporting)* **e-BRC / EDPMS** | Proof of realisation; generated automatically by DNK→EDPMS→AD bank | **Auto-generated** (no artisan action beyond AD bank + account) | Free | Automatic since 17-Sep-2024 | FIRC sender-mapping trap on aggregator payment rails |

*Sources for the table: §2 detail sections below (each row carries its own citations).*

---

## 2. Per-document detail

### 2.1 IEC — Importer–Exporter Code (MANDATORY)

- **What.** A 10-character alphanumeric code issued by DGFT. It is PAN-based — for proprietary firms the IEC is effectively keyed off the firm's PAN, and DGFT states the IEC is issued on the same PAN basis while still issuing a separate IEC [dgft.gov.in IEC Profile Management, https://www.dgft.gov.in/CP/?opt=iec-profile-management, accessed 2026-08-08].
- **Why needed.** Reg 2 of the Postal Export (Electronic Declaration and Processing) Regulations 2022 (Notification 104/2022-Customs, 09-Dec-2022) limits the PBE system to **any person holding a valid IEC**, in furtherance of business. The DNK portal validates the IEC **live against DGFT** and disables booking if the IEC is suspended/blacklisted/cancelled [report §2.3; DNK SOP v1.3, local copy `data/06-legal-sources/dnk-sop-wayback.txt`].
- **Status.** **MANDATORY** — no IEC, no PBE, no DNK export.
- **How to obtain.** Online application on the DGFT portal, form **ANF-2A** (revised: ANF-1A was merged into ANF-2A by DGFT Public Notice 32/2025-26 dated 20-Nov-2025, making ANF-1A obsolete) [taxguru.in/dgft/dgft-merges-anf-1a-anf-2a-streamline-iec-applications.html, 2025-11-20]. Prerequisites per the official IEC Manual v2.0 / module help file:
  - active **firm PAN** (validated online with the Income Tax department);
  - **bank account in the name of the firm** + proof (cancelled cheque / bank certificate) — used for online fee payment;
  - active **DSC or Aadhaar of a firm member** for e-signing the application;
  - valid address (may be **physically verified** by DGFT on issuance).
  - **GSTIN is NOT required** — the manual reads "GSTIN … if applicable"; IEC is obtainable without GSTIN [DGFT IEC Manual v2.0, https://content.dgft.gov.in/Website/IEC_Manual_V2.0_Updated.pdf, accessed 2026-08-08; findings F-H2-a].
  - Application flow: file ANF-2A online at `https://dgft.gov.in` with applicable fee → **IEC auto-generated**, applicant informed by e-mail/SMS → e-IEC downloadable from dashboard → Regional Authorities do **post-verification** [HBP 2023 Chapter 2 para 2.08, https://content.dgft.gov.in/Website/dgftprod/6978673f-9c59-4aac-a612-084df7b47e39/HBP2023_Chapter02.pdf, accessed 2026-08-08].
- **Cost.** **₹500 application fee** paid via Bharatkosh payment gateway; **₹200** for modification — per the official IEC Module User Help File and IEC Manual v2.0 ["The Application of IEC Fee is Rs 500", https://content.dgft.gov.in/Website/DGFT%20-%20IEC%20Module%20User%20Help%20File.pdf; https://content.dgft.gov.in/Website/IEC_Manual_V2.0_Updated.pdf, accessed 2026-08-08]. ⚠️ **Flag:** the corpus (report §5.1) describes IEC as "free under FTP 2023"; the official help file charges ₹500 for the *online application*. The reconciliation is that FTP/HBP provide IEC issuance on the portal "with applicable fee"; the ₹500 is the portal processing fee, not a licence fee. **Do not quote "free" or "₹500" alone — both appear in official sources.**
- **Time.** Auto-generated on submission (same-day); post-verification by RA afterwards [HBP Ch-2 §2.08]. The follow-up corpus notes an aggregator (Weavehand, L4) advertising "free IEC in 5 days" — self-reported, treat as estimate [follow-up 01-order-to-delivery-flow §2.4].
- **Friction for the persona.** (a) requires a **firm-name bank account** (see §2.2 / onboarding Step 2) and **firm PAN** — the household artisan may hold only a personal account; (b) **Aadhaar e-Sign** needs an Aadhaar-linked mobile and matching PAN details; a DSC costs extra (vendor-priced, no fixed public fee); (c) DGFT portal is English-first and form-heavy; (d) address physical verification can delay. **Who can help:** Dak Niryat Sahayaks explicitly provide "generation of Import-Export Code" assistance [New Indian Express 19-Mar-2023, https://www.newindianexpress.com/nation/2023/Mar/19/india-post-turbocharges-small-businesses-export-game-in-up-2557565.html; ThePrint, https://theprint.in/india/india-post-turbocharges-small-businesses-export-game-in-up/1455312/].

### 2.2 Firm-name bank account (precondition, not itself a DNK document)

- **What.** A bank account (ideally a current account) in the name of the firm that holds the IEC.
- **Why needed.** It is (a) an **IEC prerequisite** (proof of firm's bank account + fee payment), (b) the account that receives the **AD Code** and the destination for **DBT refunds** (IGST refund, Drawback via PFMS), and (c) what you link to the **DNK site code on ICEGATE** for electronic claims [DGFT IEC Manual v2.0; Circular 01/2026; Kolkata Customs PN 08/2026].
- **Status.** De-facto **MANDATORY** for the full incentive path (a postal export can be filed with a savings-account-backed IEC, but electronic claims need a bank account linked on ICEGATE).
- **How.** Any scheduled commercial bank; ask the branch to issue the **AD Code letter** (see 2.3). No DNK-specific step here.
- **Cost/time.** Bank-dependent; no public fixed figure for opening. **Friction:** the modal artisan's household runs cash-first and rarely holds a firm account (UP: 0.1% of establishments keep accounts) [report §3.1] — this is a silent precondition sitting behind the IEC.

### 2.3 AD Code — Authorised Dealer Code (14 chars; required on ICEGATE)

- **What.** A **14-digit Authorised Dealer (AD) Code** issued by the **RBI-authorised bank** where the exporter holds its account. It links the business's import/export transactions to that bank's foreign-exchange services [skydo.com/blog/ad-code-registration, 2026-07-25; ICEGATE advisory].
- **Why needed.** Registers the bank with Customs against the IEC; on the DNK path it is a gateway for **IGST refund, e-BRC, and the electronic incentive claims** [report §5.1; PIB PRID 2055743]. ICEGATE has a dedicated **"AD Code Bank Account Registration Advisory"** and the bank-account management manual covers both **Refund/Incentive Account** and **Foreign Remittance Account (Authorized Dealer Code)** [https://www.icegate.gov.in/guidelines/ad-code-bank-account-registration-advisory; https://www.icegate.gov.in/sites/default/files/2024-11/User%20Manual-Bank%20Account%20Management%20v1.0.pdf, accessed 2026-08-08].
- **Status.** **Optional** in the DNK business-profile form (SOP field says "AD Code: 14 characters — Optional"); **REQUIRED on ICEGATE** for every electronic incentive claim — "exporter has to also register for AD Code on ICEGATE" [Kolkata Customs PN 08/2026, https://kolkatacustoms.gov.in/storage/uploads/custom_notice_order/20260211153259.pdf, 11-Feb-2026; DNK SOP v1.3].
- **How to obtain.** (1) Ask your bank for the **AD Code letter** (the bank issues the 14-digit code on its letterhead); (2) log in to ICEGATE → "AD Code / Bank Account Registration" → select the port of registration; (3) upload the **bank authorisation letter + passbook/cancelled cheque/IEC/PAN/Class-3 DSC** via **e-Sanchit**; (4) customs approves (statuses: System Pending → Customs Approved / Rejected, tracked on the ICEGATE dashboard) [taxguru.in/custom-duty/online-registration-authorised-dealer-ad-code-bank-accounts-icegate.html, 2023-08-30; Mumbai Customs Zone-III PN 40/2025, https://mumbaicustomszone3.gov.in/Content/writereaddata/Portal/Document/1003_1_1_Public-NoticeNo-40-2025.pdf]. Once registered at any one port, the AD Code works at **all customs locations** [Kolkata PN 08/2026].
- **Cost.** Bank-set issuance fee (no public fixed figure — flag); ICEGATE registration itself is free.
- **Time.** Days — and **delays in AD-code/bank-account approval are officially acknowledged** by CBIC [findings F-H1-a, E1.4].
- **Friction.** Needs the firm bank account + bank letter + DSC; approval tracking on a second portal (ICEGATE) beyond the DNK one.

### 2.4 ICEGATE registration + bank account linked to DNK site code (MANDATORY for every electronic claim)

- **What.** ICEGATE (icegate.gov.in) is the customs e-filing gateway. Circular 01/2026-Customs para 4.vi.a makes it the precondition for postal electronic incentives: *"All exporters who intend to claim export incentives viz. Drawback, RoDTEP and RoSCTL, electronically through postal route, must get registered on ICEGATE. Such exporters must add their bank account details on ICEGATE portal corresponding to the DNK site."* [Circular 01/2026-Customs, 15-Jan-2026, local copy `data/06-legal-sources/circular-01-2026-customs.txt`].
- **Why needed.** The whole electronic incentive machinery (Drawback/RoDTEP/RoSCTL via Post-EGM→ICES→PFMS/scrip, automated IGST refund, e-BRC) routes through ICEGATE-verified identity and bank details. Same requirement applies to the **automated IGST refund** launched 17-Sep-2024 (ICEGATE registration + AD code + bank details) [PIB PRID 2055743, https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2055743].
- **Status.** **MANDATORY** for every electronic incentive claim; not required to merely book a parcel.
- **How.** Register at icegate.gov.in → "Register Now" → **Fresh Registration** (or continue with a Reference ID) → enter **IEC and GSTIN** (validated live against DGFT/GSTN), PAN, contact details, **Class-3 DSC**, active bank account [cleartax.in/s/icegate-registration, 2025-02-14; eximpe.com/blog/b2b/icegate-meaning-registration-troubleshooting-benefits, 2026-07-10]. Then add the **bank account for the DNK site code**; a customs officer approves it in ICES (CLK role); if the IEC+account are **already approved for any site, a newly added account is auto-approved at end of day** [Kolkata PN 08/2026]. Also register the **AD Code** (§2.3).
- **Cost.** Free.
- **Time.** Registration immediate; bank-account approval same-day/next-day (with acknowledged exceptions — see H1-a).
- **Friction.** Class-3 DSC (vendor-priced, not a public fixed fee — **flag as unverified**); a second/third portal to learn; the person is now maintaining IEC (DGFT), ICEGATE (customs), and DNK (DoP) logins.

### 2.5 E-Sanchit (per-claim uploads; CONDITIONAL)

- **What.** **E-Sanchit** ("e-Storage and Computerized Handling of Indirect Tax documents") is ICEGATE's document-upload service — exporters upload the supporting documents for each claim. Circular 01/2026 para 4.vi.e: *"for each Postal Bill of Export where the claim is made electronically, the supporting documents must be uploaded to the E-Sanchit/ICEGATE portal."* [local copy of Circular 01/2026].
- **Why needed.** Mandatory condition of the electronic claim; documents are visible to Indian Customs (a parallel DNK portal upload covers the parcel-specific docs).
- **Status.** **CONDITIONAL** — only when claiming electronically (Drawback/RoDTEP/RoSCTL). ⚠️ **C14, unresolved:** the requirement is documented but the **export-side capability is undocumented** — ICEGATE's FAQ and e-Sanchit material are historically importer/BoE-focused, so export-side usability is a potential hidden blocker [contradictions-map C14; findings F-H1-a].
- **How.** Log in to ICEGATE → click the **e-Sanchit** link → Upload Documents → select document type → submit (digital-signature validation applies). Only ICEGATE-registered users can use it [eSANCHIT_FAQs, https://www.icegate.gov.in/sites/default/files/2022-02/eSANCHIT_FAQs.pdf; https://www.icegate.gov.in/guidelines/esanchit-advisory; portal https://foservices.icegate.gov.in/]. Upload specs (from the Jawahar Customs step-by-step): ≥200 dpi B/W, ≤1 MB per PDF, no folds/skew — an artisanal scanner-grade document often fails these [jawaharcustoms.gov.in eSANCHIT procedure, https://www.jawaharcustoms.gov.in/pdf/PN-2017/eSANCHIT_Step_by_Step_Procedure_updated.pdf].
- **Cost.** Free. **Time.** Per claim, minutes once documents are digitised.
- **Friction.** Login-gated; importer-oriented FAQ; scan-quality specs; low-literacy upload errors. **Who can help:** Dak Niryat Sahayak / DNK staff at the counter.

### 2.6 UDYAM registration (MSME; OPTIONAL for DNK, needed for EPCH RCMC)

- **What.** Official MSME registration certificate issued by the Ministry of MSME's Udyam portal.
- **Why needed.** **Not required by the DNK portal** at all — it is an *external* registration. It is required for the **EPCH manufacturer-exporter RCMC** (EPCH FAQ: the Udyam/IEM certificate is *essential* to register as a manufacturer exporter) and generally unlocks MSME/FTP benefits [review-policy §4, §6; EPCH FAQ, https://www.epch.in/faqs, accessed 2026-08-08].
- **Status.** **OPTIONAL** for the DNK path; **conditional** (needed if claiming FTP/MSME-linked benefits or getting the manufacturer-exporter RCMC).
- **How.** `https://udyamregistration.gov.in` — **Aadhaar number + OTP to Aadhaar-linked mobile** → self-declaration of enterprise details → e-certificate issued. **No documents or proofs to upload**; fully free. Official portal warns that any other site/portal/app charging fees is fraudulent [udyamregistration.gov.in, accessed 2026-08-08].
- **Cost.** **Zero.** **Time.** Minutes — same day.
- **Friction.** Needs Aadhaar + linked mobile; GSTIN field appears for non-proprietary forms but a proprietor needs only Aadhaar. Very low friction — this is the easiest document in the stack.

### 2.7 EPCH RCMC (handicrafts council registration; CONDITIONAL)

- **What.** Registration-cum-Membership Certificate from the **Export Promotion Council for Handicrafts (EPCH)**, the Registering Authority for handicraft exporters. RCMC is issued for **5 financial years** [DGFT e-RCMC, https://www.dgft.gov.in/CP/?opt=e-rcmc, accessed 2026-08-08].
- **Why needed.** Membership is a **pre-condition for registration** at EPCH, and the RCMC is the ticket to **FTP scheme benefits** for handicraft exporters (status certificates, some scheme windows). On the postal route it is **not** required to file a PBE or to claim IGST/Drawback/RoDTEP via the PBE tables — it matters for FTP benefits pursued separately [review-policy §4 "Explicitly NOT part of DNK"; DGFT e-RCMC; EPCH].
- **Status.** **CONDITIONAL** — only if claiming FTP benefits beyond the PBE-channel incentives.
- **How.** New membership applications go **through the DGFT portal** using DGFT login credentials; the form used is **ANF 2C** via DGFT's **e-RCMC** module [EPCH membership procedure, https://epchonlineportal.in/addapplicants/; review-policy §6]. A **manufacturer exporter must furnish the MSME UDYAM certificate** + a self-declaration of the handicraft product type (per NIC code); a merchant exporter furnishes GSTIN and other docs [https://www.epch.in/apply-new-membership, accessed 2026-08-08]. RCMC issuance is mandatory through the DGFT e-RCMC platform (DGFT Trade Notice 35/2021-22, 24-Feb-2022) [https://epch.in/trade-notice-no-35-2021-22-dated-24022022-dgft-regarding-mandatiry-issuance-e-rcmc-through-dgft].
- **Cost.** Council-set membership/registration fee — **no public fixed figure in the corpus; flag for EPCH query**.
- **Time.** Days–weeks (council processing).
- **Friction.** Requires UDYAM first (for manufacturer exporters), DGFT login, council paperwork and fee — a chain of external steps, and the exact burden is unmeasured for the persona.

### 2.8 Commercial invoice + packing list (MANDATORY; the #1 failure mode)

- **What.** **Commercial invoice**: seller (IEC) and buyer details, per-line product description, **HS/CTH code**, quantity + unit, unit price, **FOB value**, currency and exchange rate, invoice number/date. **Packing list**: per-box contents, gross/net weights, dimensions (relevant for EMS volumetric risk).
- **Why needed.** Destination customs + the value declaration; the portal validates **FOB ≤ invoice value** and Σ piece values ≤ parcel value against it. The **invoice↔packing-list mismatch is the single most documented failure mode** — wrong HS codes, invoice mismatches and spelling errors cause customs holds; a single shipping-bill error can kill a refund and force litigation (Gujarat HC IGST-refund denial) [report §3.3/#7; findings F-H1-a].
- **Status.** **MANDATORY** for commercial export parcels (PBE is a customs declaration over these underlying values).
- **How.** The DNK portal **auto-generates an invoice from the data you enter** at booking (and the bulk template carries `invoiceno`, `prd_inv_date`, `tax_inv_date`, `tax_inv_sno`, `tax_inv_val` columns). Print via Forms Download [DNK SOP v1.3].
- **Cost.** Free (self-generated). **Friction.** Error here = claim killed; the persona rarely issues invoices at all — assisted generation is the entire point of the P0 document-pack feature [gap-feature-map F1/F7].

### 2.9 HS/CTH code per piece (MANDATORY)

- **What.** The **Harmonized System (HS) code** (6 digits, international) / **Customs Tariff Heading (CTH)** / **ITC-HS 8-digit** (India's tariff) for every distinct item.
- **Why needed.** PBE piece details require it — the SOP explicitly rejects vague descriptions ("Don't mention vague as 'clothes'") and enforces a description↔HS match. A wrong code kills the claim and can trigger restriction checks ("ITCH code not applicable for restricted policy") [DNK SOP v1.3].
- **Status.** **MANDATORY** per piece type.
- **How.** The portal provides an **in-portal search by product description** (enter 4 chars → pick product → system supplies the HS code); DGFT ITC-HS and EPCH's "Know your HS Code" are external aids [DNK SOP v1.3; review-data-tech §1.1]. The PBE declarations then reference the code in `hscode` and RITC/ITC-HS fields (see `pbe-iii-iv-fields.md`).
- **Cost.** Free. **Friction.** "Errors in documentation are common; HS codes and export details are confusing" (L5, corroborated L4) [report §5.1]. The P0 HS-assist (seed top-50) is the mitigation.

### 2.10 CN 22 / CN 23 (MANDATORY per parcel; auto-generated)

- **What.** Universal Postal Union (UPU) customs-declaration forms affixed to the parcel. **CN 22** for items up to **300 SDR**; **CN 23** (fuller form, usually with the commercial invoice) for items **over 300 SDR** — the 300-SDR ceiling is a UPU standard used by all member countries [UPU Acts/Circular 100-2022, https://www.upu.int/UPU/media/upu/files/aboutUpu/acts/05-actsRegulationsConventionAndPostalPayment/actsCircular100-2022En.pdf; India Post CN22 form guidance: "If the value of the contents is more than 300 SDR, you must use a CN 23 form"]. CN22 also covers the <2 kg + <300 SDR case; heavier/higher-value/restricted items go CN23 [UN IMTS Guide §3.7; dutiable.io, 2026-04-11].
- **Why needed.** The customs declaration on the physical parcel — destination customs assesses duty/VAT from it; it must reconcile with the PBE and invoice.
- **Status.** **MANDATORY** per parcel. **Auto-generated by the DNK portal with the label set** — CN22/23 + harmonised label + address label + invoice print together after booking. The **SDR value is auto-computed by the portal** ("Customer need not to enter anything"); the 300-SDR figure only decides which label the portal prints [follow-up 01-order-to-delivery-flow §1.1; DNK SOP v1.3].
- **Cost.** Included in postage. **Friction.** Fields must reconcile with invoice/PBE; printing needs a printer or counter assistance.

### 2.11 Certificate of Origin (CONDITIONAL)

- **What.** Proof of Indian origin used to claim **preferential duty** under a trade agreement at destination. For the **India–UK Comprehensive Economic and Trade Agreement (CETA)** (in force 15-Jul-2026), DGFT Trade Notice 11/2026-27 (13-Jul-2026) enabled **fully electronic issuance of Preferential Certificates of Origin (eCoO) through the Trade Connect ePlatform** (`www.trade.gov.in`) — issued either by **self-declaration** or through an **authorised agency**; the common digital platform for all agreements is `coo.dgft.gov.in` [taxguru.in/dgft/dgft-enables-india-uk-ceta-ecoo-issuance-trade-connect-portal.html, 2026-07-14; knnindia, 2026-07-16; https://www.trade.gov.in/pages/certificate-of-origin; https://coo.dgft.gov.in/].
- **Why needed.** Only if the buyer will claim the agreement preference (e.g., zero/lower UK duty under CETA); many small-consignment handicraft buyers never ask for it.
- **Status.** **CONDITIONAL** — product + agreement + origin-criteria (RoO) dependent; "not always needed" [report §5.1].
- **How.** Trade Connect "Certificate of Origin" service → eCoO (self-declaration or authorised agency). UK importers may also self-certify under the "importer's knowledge" route [NSEZ RoO FAQs, https://nsez.gov.in/Resources/Trade/FAQs%20ROO.pdf].
- **Cost.** eCoO service fees vary by issuing agency — **no public fixed figure; flag**.
- **Friction.** Low for self-declaration once the origin criteria are met; the artisan typically can't map HS-level RoO rules unaided. **Build note:** the Trade Connect integration is referenced, not fought [gap-feature-map F5].

### 2.12 Product-specific NOCs and certificates (CONDITIONAL; prohibitions/restrictions)

SOP v1.3 is explicit that certificates here mean **No Objection Certificates** from competent authorities, and requires the exporter to *count and upload* them at booking: "Suppose you have put spices, drugs & Tea in one consignment… you need 3 NOC, one from Spice Board of India, second from ADC and third from Tea Board of India" [DNK SOP v1.3, local copy]. Uploaded docs are visible to **Indian Customs only** — **physical copies must be attached to the parcel** for destination customs [DNK SOP v1.3; report §2.3].

| Product | Certificate / NOC | Competent authority | Source |
|---|---|---|---|
| **Ayurvedic / herbal / homeopathic** | AYUSH certification or specific NOC; craft-adjacent herbal soaps/balms must be **classified as cosmetics, not medicines** | AYUSH Ministry / Assistant Drugs Controller (ADC) | [findings Ctx-4; DNK SOP v1.3] |
| **Spices** | NOC | **Spice Board of India** | [DNK SOP v1.3] |
| **Tea** | NOC | **Tea Board of India** | [DNK SOP v1.3] |
| **Drugs/medicines** | NOC + manufacturing licence | Assistant Drugs Controller (ADC) | [DNK SOP v1.3] |
| **Plants, seeds, flowers, plant material** | **Phytosanitary certificate**; soil strictly banned | Plant quarantine / destination requirement | [findings Ctx-4] |
| **Wood & wood articles** | Per-destination permission; several countries (e.g., **Ireland**) ban wood/plant products outright; CITES species need permits | Destination + CITES authorities | [findings Ctx-4; report §5.2] |
| **Liquids/oils/perfume, magnets (Class 9), lithium batteries, cosmetics, currency, explosives, narcotics, perishables** | Restricted/prohibited categories; many are outright barred | — | [findings Ctx-4; report §5.2] |

- **How.** From the competent authority; uploaded via the portal's **Document Upload** against the Article ID, with the count entered at booking. The per-country truth table is India Post's **scanned, non-machine-readable `Country_List.pdf`** — the build must curate a top-N-country matrix with per-row confidence, not pretend to encode the whole thing (85% High) [findings Ctx-4; report §5.2].
- **Status.** **CONDITIONAL** — product × destination. **Friction.** The single highest-cost error class; an artisan cannot self-serve a per-country prohibition lookup.

### 2.13 Supporting: e-BRC / EDPMS (auto-generated)

- **What.** e-BRC (electronic Bank Realisation Certificate) = proof of receipt of export proceeds, generated from **RBI EDPMS** data via the AD bank's Inward Remittance Messages; the DNK↔EDPMS integration has generated e-BRCs automatically for postal exports since **17-Sep-2024** [PIB PRID 2055743; RBI Master Direction 16/2015-16, https://www.rbi.org.in/scripts/NotificationUser.aspx?Id=12561].
- **Why needed.** Prerequisite for FTP benefits and many refund claims; exporters can self-generate on DGFT's eBRC portal [https://www.dgft.gov.in/CP/?opt=eBRC].
- **Status.** **AUTO-GENERATED** — no artisan action beyond keeping the AD bank + linked bank account correct. **Friction.** On aggregator payment rails the FIRC lists the partner bank as the sender, so a CA must map FIRC→invoice or the e-BRC mapping fails [review-data-tech §2.1; follow-up §3 M1].

---

## 3. The contested field: GSTIN — do not build on "GSTIN blocks artisans"

- **Legally optional for the persona (90% High).** The modal weaver/artisan turns over far below GST thresholds (₹20L goods / ₹40L goods service-mix), and handicraft inter-State supply carries a GST-registration exemption (Notifications 08/2017-IGST and 03/2018-IGST); DGFT issues IEC without GSTIN ("GSTIN … if applicable") [findings F-H2-a; E2.1/E2.2/E2.7].
- **On paper, no hard-block (70% Moderate).** The DNK SOP's business-details table marks GSTIN "Mandatory", but its **KYC Note-1 enables booking after uploading at least one of IEC or GSTIN**, and every PBE form reads **"GSTIN or as applicable"**; the KYC dropdown includes IEC/AD-code/GSTIN/**Others** [DNK SOP v1.3; findings F-H2-b; contradictions-map C2].
- **The caveat (why it is contested, H2).** All of the above is *on-paper*. Whether the **migrated portal** (`app.indiapost.gov.in/customer-selfservice`) actually honours the KYC escape hatch is **untested** — if it diverges, the hard-block branch is restored. And GSTIN **keys the IGST-refund machinery** (ICES Advisory 012/2017: refund credit flows only when GSTIN is quoted and matches GSTN) — so a GSTIN-less exporter may be able to *ship* but not *realise the IGST refund*; how the postal automation handles that is unverified [findings F-H2-b/c].
- **Design consequence.** The product must offer **dual IEC-only / GSTIN onboarding** (GSTIN as an optional enhanced identifier), never a "GSTIN blocks artisans" story [gap-feature-map F8; section 4 of gap-feature-map].

---

## 4. Sources (key, with access dates 2026-08-08)

- **DNK Customer Portal SOP v1.3** (CEPT; pre-migration URL `https://dnk.cept.gov.in/customers.web/static/SOP.pdf`) — local copy `data/06-legal-sources/dnk-sop-wayback.txt`.
- **Circular 01/2026-Customs** (15-Jan-2026) — local copy `data/06-legal-sources/circular-01-2026-customs.txt`; mirror commentary taxguru.in/custom-duty/postal-exporters-claim-drawback-incentives-online-cbic.html.
- **Kolkata Customs PN 08/2026** (11-Feb-2026) — kolkatacustoms.gov.in/storage/uploads/custom_notice_order/20260211153259.pdf.
- **DGFT IEC Profile Management + IEC Manual v2.0 + IEC Module User Help File + HBP 2023 Ch-2** — dgft.gov.in/CP/?opt=iec-profile-management; content.dgft.gov.in/Website/IEC_Manual_V2.0_Updated.pdf; content.dgft.gov.in/Website/DGFT%20-%20IEC%20Module%20User%20Help%20File.pdf; content.dgft.gov.in/Website/dgftprod/…/HBP2023_Chapter02.pdf.
- **ICEGATE** — icegate.gov.in/guidelines/ad-code-bank-account-registration-advisory; User Manual-Bank Account Management v1.0; foservices.icegate.gov.in; icegate.gov.in/guidelines/esanchit-advisory.
- **Mumbai Customs Zone-III PN 40/2025** (Bank Account & AD Code Dashboard) — mumbaicustomszone3.gov.in/Content/writereaddata/Portal/Document/1003_1_1_Public-NoticeNo-40-2025.pdf.
- **UDYAM** — udyamregistration.gov.in (official).
- **EPCH** — epch.in/apply-new-membership; epch.in/faqs; DGFT e-RCMC dgft.gov.in/CP/?opt=e-rcmc.
- **Trade Connect eCoO / India-UK CETA** — trade.gov.in/pages/certificate-of-origin; coo.dgft.gov.in; taxguru.in/dgft/dgft-enables-india-uk-ceta-ecoo-issuance-trade-connect-portal.html (Trade Notice 11/2026-27, 13-Jul-2026).
- **UPU CN22/CN23** — upu.int Acts Circular 100-2022; India Post CN22 guidance.
- **PIB PRID 2055743** (IGST refund + e-BRC live 17-Sep-2024).
- **Corpus anchors** — report.md §2.2–2.5, §5.1–5.2, §9.2; findings.md F-H1, F-H2, F-H3, Ctx-1/4; gap-feature-map F1/F7/F8; review-policy.md §4/§6; review-data-tech.md §1–2; follow-ups/01-order-to-delivery-flow/findings.md.

**Flags (do not re-assert as fact):** IEC fee "free vs ₹500" (both appear in official sources); AD-code issuance fee and EPCH RCMC fee (council/bank-set, unverified); Class-3 DSC price (vendor-set); e-Sanchit export-side capability (C14); GSTIN hard-block on the migrated portal (untested, H2); Trade Connect usefulness for a solo artisan (unmeasured).
