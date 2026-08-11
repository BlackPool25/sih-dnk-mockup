# Export Incentives — IGST Refund · e-BRC · Duty Drawback · RoDTEP/RoSCTL

**Project:** SIH260113 · **Research area:** dnk-export-enablement · **Date:** 2026-08-08
**Persona this is judged against:** the modal artisan — ~₹7,000/month, <7% beyond primary education, woman-dominated, 97% household-based, zero-inventory made-to-order, **legally GSTIN-less** (90% High) [report §3.1; findings F-H2-a].
**Honesty header.** (1) **RoDTEP and RoSCTL are NOT cash** — they are **e-scrips** (transferable credits usable against Basic Customs Duty on imports) that realise at a **discount** for non-importing exporters; never present them as cash refunds. (2) All claim timelines below are **labelled estimates** — no public per-artisan realised amount or timeline has ever been published (findings F-H1-c); the flagship product feature (FR-013 realization tracker) exists precisely because this flow is the least realised. (3) Every figure is a config flag with source + last-updated timestamp (FR-001). (4) All four schemes are behind the IEC + ICEGATE + AD-code + E-Sanchit stack — **entitlement ≠ cash-in-hand** (H1 CORROBORATED, 82% High) [findings F-H1-a].

---

## 0. The four schemes at a glance

| # | Scheme | Since (electronic) | Payout form | Mechanism | Claimable docs (from the PBE-2026 declaration clusters) |
|---|---|---|---|---|---|
| 1 | **IGST refund** (zero-rated export) | **Live 17-Sep-2024** | **Cash** (DBT via PFMS → bank) | DNK → ICES → PFMS → bank DBT; needs GSTIN quoted + matched on ICES | GSTR-1 (Table 6A) + GSTR-3B + shipping bill/PBE; ICEGATE + AD code + linked bank |
| 2 | **e-BRC** (bank realisation proof) | **Live 17-Sep-2024** | Certificate (not a payment) | DNK → RBI EDPMS → AD bank issues automatically; self-serve on DGFT e-BRC portal | None beyond AD bank + linked account; FIRC→invoice mapping on aggregator rails |
| 3 | **Duty Drawback** | **Electronic 15-Jan-2026** | **Cash** (DBT via PFMS → bank) | PBE → Post-EGM → ICES → scroll → SB → PFMS → DBT | **DBK serial No.** + drawback quantity + 4 Drawback sub-declarations on the PBE; E-Sanchit uploads |
| 4 | **RoDTEP / RoSCTL** | **Electronic 15-Jan-2026** | **e-scrips (NOT cash)** on ICEGATE | PBE → Post-EGM → ICES → final scroll → SB on ICEGATE → scrip generation | **RITC/ITC-HS code + scheme code** + 3 RoDTEP / 3 RoSCTL sub-declarations; E-Sanchit uploads; EPCH RCMC for handicraft FTP benefits |

Source: report §2.4 (all L1); Circular 01/2026-Customs (local copy); PIB PRID 2055743 (17-Sep-2024).

**Prerequisite for every electronic claim** (Circular 01/2026 §4.vi.a/e): **ICEGATE registration** + **bank account linked to the DNK site code on ICEGATE** + **AD-code registration** + **per-claim E-Sanchit document uploads**. No public API exists on this path — a demo must mock it and label the mock (FR-003) [report §2.4; findings Ctx-2].

---

## 1. Realization reality first (the H1 gap — read this before claiming anything)

- **Entitlement ≠ cash.** Aggregate incentive capture is narrow even among formal exporters: RoDTEP benefits were availed by **"nearly 2% of exports"** (Rajya Sabha reply, L3); **₹15,756 Cr disbursed to ~1.11 lakh exporters** vs ~1.5 Cr registered MSMEs (L3); "average exporter claims one refund scheme when entitled to two" (L3). [findings F-H1-b; report §7 #8]
- **No published artisan-realization instance.** Since the electronic unlocks (IGST/e-BRC 17-Sep-2024; Drawback/RoDTEP/RoSCTL 15-Jan-2026), **no L1/L2 instance of an individual artisan realizing an electronic incentive has been published** — the <5% rate is unmeasured/Speculative; the *direction* (narrow realization) is the best-supported claim in the programme [findings F-H1-c; report §7 #8].
- **Why the stack is the barrier (82% High):** IEC + GSTIN (contested) + ICEGATE + AD code + E-Sanchit exceeds a low-literacy solo artisan's unaided capability; CBIC itself acknowledged AD-code/bank-approval delays, and the IGST auto-refund is brittle to a single wrong digit in a document number [findings F-H1-a].
- **Design consequence:** the realization tracker (FR-013) must show "eligible → filed → expected refund" with the timeline labelled **अनुमानित / estimate**, never a live ICEGATE status (FR-003).

---

## 2. IGST Refund (zero-rated export) — cash refund

### 2.1 What it is
A refund of the **Integrated GST paid on inputs** of exported goods — zero-rated supply under **section 16, IGST Act 2017**. On the postal lane it became **automated on 17-Sep-2024**: the DNK portal now exchanges data with **ICEGATE, ICES, PFMS and RBI EDPMS**, so the IGST refund flows **DNK → ICES → PFMS → direct credit to the exporter's linked bank account**. [PIB PRID 2055743, 17-Sep-2024, https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2055743; report §2.4]

### 2.2 Eligibility & the GSTIN key
- **GSTIN is the gateway.** Under the general IGST-refund machinery, the refund flows **only when the GSTIN is quoted and matches GSTN data** (ICES Advisory 012/2017) [findings F-H2-c]. The modal artisan is **legally GSTIN-less** (90% High) — whether the *postal* automation provides a GSTIN-less IGST-refund path is **unverified** [findings F-H2-c]. **Build rule:** never promise IGST refund to a GSTIN-less filer; surface the dependency honestly (FR-061).
- The PBE's zero-rating declaration (declaration 1, "intend to zero rate our exports under section 16 of IGST Act") is the claim entry point; the **Drawback declaration is mutually exclusive** with IGST refund on the same goods (drawback sub-declaration 3(b): "no refund of Integrated Goods and Service Tax paid on export goods shall be claimed") [Notification 07/2026-Customs, local copy].

### 2.3 Claim mechanism (electronic, postal)
1. **Register on ICEGATE**; add bank account details **corresponding to the DNK site**; register **AD code** (Circular 01/2026 §4.vi.a) [document-stack.md §2.3–2.4].
2. File the **PBE-III/IV** on the DNK portal with the zero-rating declaration.
3. Ship; customs clears at the FPO (**LEO**) → **Post EGM** filed in the DNK portal → data pushed to **ICES** (Kolkata Customs PN 08/2026) [follow-up §1.2].
4. **File GSTR-1** with export details in **Table 6A** and **GSTR-3B** for the period — the GST portal transmits eligible export invoices to ICEGATE only when IGST paid in 3.1(b) ≥ export IGST; **ICES matches** and, on success, **credits the IGST to the exporter's bank account** via PFMS. [Jawahar Customs "Guide on IGST Refunds in ICES", http://www.jawaharcustoms.gov.in/pdf/GST_REFUND.pdf; GST Portal tutorial, https://tutorial.gst.gov.in/userguide/refund/Track_Refund_Status_for_IGST_paid_on_account_of_Export_of_Goods.htm; Rule 96, CGST Rules 2017]

### 2.4 Claimable documentation
- PBE (deemed application for refund, Rule 96 CGST Rules 2017) + **Post EGM** (proof of export) + **GSTR-1 (Table 6A)** + **GSTR-3B** + ICEGATE **bank-account/AD-code** linkage + GSTN-matched **GSTIN**.

### 2.5 Expected timeline — **estimate**
- No public postal-IGST timeline exists. General export-IGST refunds are cited in practice as **7–15+ days after matching** (GST tutorial, no fixed statutory limit in the corpus); the automated postal rail is designed to remove manual processing but its realised cadence is **unmeasured** (H1-c). **Label any number "अनुमानित / estimate"** (FR-002).

### 2.6 Failure modes
- Wrong GSTIN / GSTN mismatch → no refund (ICES Advisory 012/2017) [findings F-H2-c].
- GSTR-3B IGST paid < export IGST declared in 6A → ledger balance negative, invoice not transmitted [GST tutorial].
- Single wrong digit in a shipping-bill/PBE number stops the automatic process (L4 guides) [findings F-H1-a].
- AD-code/bank-account approval delays — officially acknowledged by CBIC [findings F-H1-a].

---

## 3. e-BRC (electronic Bank Realisation Certificate) — proof, not payment

### 3.1 What it is
The **e-BRC is proof of realisation of export proceeds** — generated from **RBI EDPMS** data via the AD bank's **Inward Remittance Messages (IRMs)**. Since **17-Sep-2024**, the DNK→EDPMS integration means **AD banks issue e-BRCs automatically** for postal exports. **It is a prerequisite for all FTP benefits and many refund/incentive claims** — you can't get Drawback/RoDTEP/FTP rewards without demonstrating realisation. [PIB PRID 2055743; RBI Notification, https://rbi.org.in/Scripts/NotificationUser.aspx?Id=11119; report §2.4]

### 3.2 Mechanism
- Buyer pays via a rail (payment-rails.md) → funds credit your bank / aggregator → AD bank updates **EDPMS "as and when realised"** → since **16-Oct-2017 e-BRCs are generated only from EDPMS data** [RBI Notification Id=11119] → on the postal lane the DNK→EDPMS integration triggers **automatic e-BRC issuance**.
- **Self-serve alternative:** DGFT's e-BRC portal lets exporters **self-generate e-BRC from bank IRMs** (IEC login → Services → eBRC → Generate e-BRC) [DGFT, https://www.dgft.gov.in/CP/?opt=eBRC].

### 3.3 What the artisan must do
- Keep the **AD bank + linked bank account** correct; ensure the received payment actually routes through the AD bank / an aggregator whose partner bank reports to EDPMS. **No form** beyond that.
- **On aggregator rails the FIRC lists the partner bank as sender** → the CA must map FIRC→invoice or **e-BRC mapping fails** (FR-043) [payment-rails.md §6].

### 3.4 Timeline — **estimate**
- e-BRC issuance follows realisation + EDPMS update; "automatic since 17-Sep-2024" but the **realised cadence for postal exporters is unmeasured** [findings F-H1-c].

---

## 4. Duty Drawback — cash refund (electronic since 15-Jan-2026)

### 4.1 What it is
Drawback under **section 75, Customs Act 1962** reimburses duties/taxes borne on inputs used in the exported product. For postal exports it became **claimable electronically on 15-Jan-2026** via the PBE. [Circular 01/2026 §4.vi.b; report §2.4]

### 4.2 Eligibility
- The product must be covered by the **Drawback Schedule** (an All Industry Rate / brand rate entry with a **DBK serial number**).
- **Mutual exclusivity:** drawback cannot be claimed on goods where **IGST refund** was claimed or **Input Tax Credit** was availed on the same inputs — the PBE's 4 Drawback sub-declarations enforce this [Notification 07/2026-Customs, declarations 3(a)–3(d)].
- Electronic claims follow **Rule 13 & 14, Customs and Central Excise Duties Drawback Rules 2017**; non-electronic claims keep Rule 12 [Circular 01/2026 §4.vi.b/c].

### 4.3 Claim mechanism (electronic, postal)
1. **ICEGATE registration + bank account linked to DNK site + AD code** (Circular 01/2026 §4.vi.a) + **E-Sanchit uploads** per PBE (§4.vi.e).
2. File **PBE-III/IV** on the DNK portal; in the **"Additional details of parcel"** table enter **RITC/ITC-HS code, DBK serial No., drawback quantity, IGST payment status, end-use, scheme code (Drawback), add-freight, nature of contract**; tick the **4 Drawback sub-declarations** [Notification 07/2026-Customs; pbe-iii-iv-fields.md §3–4].
3. Ship → customs clears (**LEO**) → **Post EGM** → data to ICES → **temporary scroll → final scroll** → **Shipping Bill (SB) on ICEGATE** → **PFMS → DBT** to the linked bank account. [report §2.4; follow-up §3 M4; Kolkata Customs PN 08/2026]

### 4.4 Claimable documentation
- PBE with **DBK serial no.** + drawback quantity + scheme code; Post EGM (proof of export); E-Sanchit-uploaded **invoice, packing list, any licences/NOCs**; ICEGATE-linked bank account for the DBT.

### 4.5 Expected timeline — **estimate**
- Post scroll → PFMS DBT is typically quoted as **a few working days after the final scroll** in practice; **no official postal-drawback timeline is published** — label any number "अनुमानित" [findings F-H1-c].

### 4.6 Failure modes
- Wrong **DBK serial** or HS/CTH → claim killed ("one wrong digit" brittleness applies) [findings F-H1-a].
- IGST refund + drawback double-claim on same goods → rejection (mutual-exclusivity sub-declarations).
- E-Sanchit export-side capability is **unverified** (C14) — a potential hidden blocker [contradictions-map C14].
- Missing ICEGATE bank linkage → no DBT.

---

## 5. RoDTEP & RoSCTL — e-scrips, NOT cash

### 5.1 What they are (and are not)
- **RoDTEP (Remission of Duties and Taxes on Exported Products)** reimburses duties/taxes/levies not refunded under any other mechanism. **RoSCTL (Rebate of State and Central Taxes and Levies)** rebates state/central/local taxes on exports.
- **⚠️ NOT cash:** both are granted as **e-scrips** on ICEGATE — transferable credits that can only be used to pay **Basic Customs Duty** on imports (or sold to another IEC holder). A **non-importing exporter realises value by selling the scrip, typically at a discount to face value**; it cannot be encashed directly. [DGFT RoDTEP, https://www.dgft.gov.in/CP/?opt=RODTEPARR; USA India CFO, 2026-07-17, https://usaindiacfo.com/rodtep-scheme/; ICEGATE e-scrip advisory, https://www.icegate.gov.in/guidelines/advisory-e-scrip-avail-export-incentive-schemes-rosctl-rodtep]

### 5.2 How the discount bites (realization reality)
- The secondary market for RoDTEP e-scrips is informal; typical prices are **92–97% of face value** (a **3–8% discount**), depending on demand — a ₹1,00,000-face-value scrip may sell for ₹92,000–97,000. [All Frontier, 2026-06-20, https://allfrontierglobal.com/gdocs/doc106-faq-rodtep-scheme/] — **estimate, label it** (FR-002).
- Aggregate RoDTEP utilisation is narrow: **"nearly 2% of exports availed benefits"** (Rajya Sabha reply) [findings F-H1-b].

### 5.3 Eligibility & the handicraft path (EPCH RCMC)
- RoDTEP rates are product × ITC-HS based. **For handicrafts, EPCH publishes the RoDTEP schedule** (e.g., Notification 32/2024-25, 30-Sep-2024, w.e.f. 10-Oct-2024, rates as % of FOB with a cap per UQC). [EPCH RoDTEP circular, https://epch.in/sites/default/files/policies/RoDTEP_Circular.pdf]
- **EPCH RCMC** (Registration-cum-Membership Certificate, 5 financial years, via DGFT e-RCMC/ANF 2C) is the handicrafts-council registration needed for **FTP scheme benefits**; for a manufacturer exporter it requires the **MSME UDYAM** certificate first. It is **external to DNK** — not required to file a PBE or to claim via the PBE tables, but required for FTP benefits pursued separately. [document-stack.md §2.6–2.7; EPCH FAQ, https://www.epch.in/faqs; DGFT e-RCMC, https://www.dgft.gov.in/CP/?opt=e-rcmc]

### 5.4 Claim mechanism (electronic, postal)
1. **ICEGATE registration + bank account linked to DNK site + AD code + E-Sanchit uploads** (Circular 01/2026 §4.vi.a/e) — same stack as Drawback.
2. File **PBE-III/IV**; in "Additional details of parcel" enter **RITC/ITC-HS code + scheme code (RoDTEP / RoSCTL)**; tick the **3 RoDTEP** or **3 RoSCTL sub-declarations** (undertaking to abide by scheme provisions; no claim on duties already exempted/remitted outside the scheme; preserve audit documents per Customs Audit Regulations 2018) [Notification 07/2026-Customs; Circular 01/2026 §4.vi.d references Notification 24/2023-Customs (N.T.) 01.04.2023 for RoDTEP and 25/2023-Customs (N.T.) 01.04.2023 for RoSCTL].
3. Ship → LEO → **Post EGM** → ICES → final scroll → **SB available on ICEGATE** → **e-scrip generated** in the exporter's ICEGATE ledger. [report §2.4; follow-up §3 M4]

### 5.5 Claimable documentation
- PBE with **RITC/ITC-HS code + scheme code**; Post EGM; E-Sanchit-uploaded invoice/packing list; (for FTP benefits beyond the PBE channel) **EPCH RCMC + UDYAM**.

### 5.6 Expected timeline — **estimate**
- Scrip generation follows the final scroll on ICEGATE; **no official postal scrip-generation timeline is published** — label "अनुमानित". The scrip *value* (not cash) only realises when sold or used against import duty — which is itself a non-cash, discount-bearing step for a non-importing artisan.

### 5.7 Failure modes
- Wrong **RITC/ITC-HS** or missing scheme code → no scrip.
- **RoDTEP as cash** is a category error — the artisan gets a scrip, not rupees; anyone promising "RoDTEP refund to bank" is wrong.
- Product not in the RoDTEP schedule → no entitlement (narrow aggregate realisation partly reflects this) [findings F-H1-b].
- E-Sanchit export-side capability unverified (C14).

---

## 6. Claim prerequisites (shared stack, per scheme)

| Requirement | Where | Applies to |
|---|---|---|
| **IEC** (10-char, DGFT-validated) | DNK profile; PBE header | All schemes (mandatory to export, Reg 2 Ntf 104/2022) |
| **ICEGATE registration** | icegate.gov.in | Every electronic claim (Circular 01/2026 §4.vi.a) |
| **Bank account linked to DNK site code** | ICEGATE | Every electronic claim — the DBT/scrip destination |
| **AD Code** (14-char) | ICEGATE + DNK profile | IGST refund, e-BRC, Drawback, RoDTEP/RoSCTL |
| **E-Sanchit uploads** | ICEGATE e-Sanchit (per PBE) | Drawback/RoDTEP/RoSCTL electronic claims (Circular 01/2026 §4.vi.e) |
| **GSTIN matched on GSTN** | GSTN + ICES | IGST refund (ICES Advisory 012/2017) — contested for the postal GSTIN-less path |
| **EPCH RCMC (+ UDYAM)** | DGFT e-RCMC / EPCH | FTP benefits beyond the PBE channel (handicrafts) |
| **LUT/bond** | DNK profile / GST | IGST zero-rated exports for GST-registered exporters |

Source: Circular 01/2026-Customs (local copy); document-stack.md §2; report §2.4.

---

## 7. Failure-mode roll-up (the #1 documented error classes)

1. **Documentation errors** (wrong HS/CTH/DBK-serial, invoice↔packing-list mismatch, spelling) — the dominant documented failure mode; a single shipping-bill/PBE error has killed a refund and forced litigation (Gujarat HC IGST-refund denial) [report §3.3/#7; findings F-H1-a].
2. **GSTN mismatch** on the IGST rail → no refund [ICES Advisory 012/2017; findings F-H2-c].
3. **Double-claim** (IGST + Drawback on same goods) → rejection [Ntf 07/2026 sub-declarations].
4. **AD-code/bank-approval delay** — officially acknowledged [findings F-H1-a].
5. **E-Sanchit export-side capability unverified** (C14) [contradictions-map C14].
6. **FIRC sender-mismatch** breaking e-BRC mapping on aggregator rails [payment-rails.md §6; FR-043].
7. **RoDTEP scrip realisation at a discount** for non-importing exporters — value erosion before cash [§5.2].

---

## 8. Sources & flags

**Key sources (accessed 2026-08-08 unless dated):**
- PIB PRID 2055743 (17-Sep-2024, DNK↔ICEGATE/ICES/PFMS/EDPMS; automated IGST refund + e-BRC) — https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2055743
- Circular 01/2026-Customs (15-Jan-2026, electronic Drawback/RoDTEP/RoSCTL; ICEGATE + bank + E-Sanchit mandates) — local copy `data/06-legal-sources/circular-01-2026-customs.txt`
- Notification 07/2026-Customs (N.T.) 15-Jan-2026 (substituted PBE forms; RITC/DBK/RoDTEP/RoSCTL/FEMA declarations) — local copy `data/06-legal-sources/notification-07-2026-customs.txt`
- Kolkata Customs PN 08/2026 (11-Feb-2026; LEO + Post EGM → ICES) — https://kolkatacustoms.gov.in/storage/uploads/custom_notice_order/20260211153259.pdf
- Jawahar Customs IGST-refund guides (Rule 96 CGST Rules; GSTR-1 6A/GSTR-3B matching; ICES credit) — http://www.jawaharcustoms.gov.in/pdf/GST_REFUND.pdf; https://jawaharcustoms.gov.in/pdf/IGST_REFUND_FAQ.pdf
- GST Portal refund tutorials (ledger approach, Table 6A / 3.1(b)) — https://tutorial.gst.gov.in/userguide/refund/Refund_on_Account_of_Export_of_Goods_(With_Payment_of_Tax).htm; Track_Refund_Status page
- RBI EDPMS/eBRC notification (MD 16/2015-16; as-and-when-realised; eBRC from EDPMS since 16-Oct-2017) — https://rbi.org.in/Scripts/NotificationUser.aspx?Id=11119
- DGFT e-BRC portal — https://www.dgft.gov.in/CP/?opt=eBRC
- DGFT RoDTEP — https://www.dgft.gov.in/CP/?opt=RODTEPARR
- ICEGATE e-scrip advisory (RoDTEP/RoSCTL) — https://www.icegate.gov.in/guidelines/advisory-e-scrip-avail-export-incentive-schemes-rosctl-rodtep
- USA India CFO RoDTEP economics (scrip discount for non-importers, 2026-07-17) — https://usaindiacfo.com/rodtep-scheme/
- All Frontier RoDTEP FAQ (secondary-market 92–97% of face value, 2026-06-20) — https://allfrontierglobal.com/gdocs/doc106-faq-rodtep-scheme/
- EPCH RoDTEP handicraft circular (Ntf 32/2024-25, 30-Sep-2024) — https://epch.in/sites/default/files/policies/RoDTEP_Circular.pdf
- EPCH FAQ / apply-new-membership (RCMC pre-condition; UDYAM for manufacturer exporters) — https://www.epch.in/faqs; https://www.epch.in/apply-new-membership
- Corpus anchors: report §2.4, §5.1, §7 #8, §9.2 (F2); findings F-H1-a/b/c, F-H2-c; contradictions-map C14; functional-requirements Module A (FR-010…016) + Module H (FR-082); follow-up 01-order-to-delivery-flow §3 M4; document-stack.md §2.3–2.7; pbe-iii-iv-fields.md §3–4

**Flags (do not re-assert as fact):** (1) RoDTEP/RoSCTL = **e-scrips, not cash**; scrip discount 92–97% is a market estimate, label it; (2) no public postal-IGST/drawback/scrip realisation timeline exists — any number is estimate (FR-002); (3) no published individual-artisan realization instance since Jan-2026 (H1-c); (4) GSTIN-less postal IGST path unverified (H2-c); (5) E-Sanchit export-side capability unverified (C14); (6) EPCH RCMC fee unverified (council-set); (7) IGST refund vs Drawback mutual exclusivity is enforced by the PBE sub-declarations, so claiming both on one consignment fails.
