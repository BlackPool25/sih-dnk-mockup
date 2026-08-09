# PBE-III / PBE-IV — Field-by-Field Form Structure

**Project:** SIH260113 · **Research area:** dnk-export-enablement · **Date:** 2026-08-08
**Purpose:** the exact electronic Postal Bill of Export (PBE) structure a document-pack generator must emit, plus the portal's bulk-upload schema, validation rules, and submission flow.
**Honesty header.** The field lists below are assembled from the corpus: Notification 104/2022-Customs (Reg 5/7/9), the substituted PBE-III/PBE-IV forms in **Notification 07/2026-Customs (N.T.) dated 15-Jan-2026** (as described in corpus, not reproduced verbatim), Circular 01/2026-Customs, Circular 25/2022-Customs, the DNK SOP v1.3 (local copy), and the follow-up analysis. Where a sub-declaration's *exact wording* is not reproduced in any fetched source, it is flagged below rather than invented.

---

## 0. Which form when (the only branching decision)

| Form | Use for | Route |
|---|---|---|
| **PBE-III** | **E-commerce** exports — order received through an **e-marketplace** with **payment through electronic means** per RBI guidelines | Electronic (DNK portal) |
| **PBE-IV** | **All other** postal exports (order not via e-marketplace) | Electronic (DNK portal) |
| PBE-I / PBE-II | Manual legacy equivalents (e-commerce / other), filed at APSO under Exports by Posts Regs 2018 | Manual (non-electronic) |

Source: Reg 5 + Reg 3 (definition of e-commerce), Ntf 104/2022; SOP v1.3 ("In this scenario, exporter has to choose PBE-III… If the exporter get order by other mode… he has to choose PBE-IV") [DNK SOP v1.3; review-policy §2].
**Selection rule in the SOP:** the exporter opts PBE-III or PBE-IV at the Consignment Details step; the distinction is whether the order came through an e-marketplace with electronic payment (PBE-III captures the marketplace's Order ID / Payment ID).

---

## 1. Header block (form-level fields)

| Field | Type / format | Source |
|---|---|---|
| **Bill of Export No.** | System-generated on submission (Article ID + PBE number pop-up) | [SOP v1.3; follow-up §1.1] |
| **FPO code** | Code of the Board-appointed Foreign Post Office mapped to the booking post office | [follow-up §1.1; Reg 6] |
| **Exporter name / address** | Auto-populated from DGFT IEC validation (name, address, city, pincode, PAN) | [SOP v1.3 — "IEC prefill"] |
| **IEC** | 10-char alphanumeric, **mandatory**, validated live against DGFT; booking disabled if suspended/blacklisted | [SOP v1.3] |
| **State code** | Exporter's state | [follow-up §1.1] |
| **GSTIN-or-as-applicable** | 15-char; PBE text reads **"GSTIN or as applicable"** — the field is *not* uniformly mandatory on the form; the SOP's business-profile marks it mandatory but KYC Note-1 gates booking on **≥1 of IEC/GSTIN** | [follow-up §1.1; contradictions-map C2; H2] |
| **AD code** | 14-char; optional in DNK profile, required on ICEGATE for electronic claims | [SOP v1.3; Circular 01/2026] |
| **Authorised agent details** | Customs-broker licence (CBLR 2018) if an agent files — Reg 9; "Self-filing: Yes" otherwise | [Reg 9; SOP v1.3] |

Also captured at profile level (not per-PBE): LUT/Bond (FY-wise), DoP contract details (Customer ID + Contract ID for advance/BNPL customers; default retail ID otherwise) [SOP v1.3].

## 2. Parcel / line table (per piece/sub-piece)

| Field | Notes |
|---|---|
| **Consignee name/address/country** | Postcode validated; in-portal worldpostalcode.com lookup |
| **Product description** | **No vague descriptions** ("don't mention vague as clothes") — description↔HS mismatch is a documented error |
| **CTH (Customs Tariff Heading)** | HS/CTH code per item; in-portal description→HS search |
| **Quantity + unit** | e.g., 10 / PIECES |
| **Invoice no. / date** | Replicated from parcel details into tax-invoice fields |
| **Gross weight** | Weight of parcel with packaging |
| **Net weight** | Product weight; **gross ≤ 110% of net** validation |
| **PBE-III e-commerce columns (5)** | **GSTIN of e-comm operator · URL of the website/marketplace · payment transaction ID · SKU No. · postal tracking number** |
| **Assessable value (u/s 14)** | **FOB · currency (CBIC-notified; drop-down) · exchange rate · amount in INR** (INR conversion automated) |

Source: follow-up §1.1; SOP v1.3 (piece-details screen, validation notes). The 5 PBE-III e-commerce columns are the only structural difference in the line table between III and IV.

## 3. 2026 additions — "Additional details of parcel" (the new burden, Ntf 07/2026)

Circular 01/2026 §4.vi.b: *"The PBE forms (III and IV) now include additional tables to provide information related to duty drawback or any other export scheme chosen by the exporter. These tables also include additional fields to indicate the additional details about parcels for postal exports."* [Circular 01/2026, local copy].

| Field | Meaning |
|---|---|
| **RITC / ITC-HS code** | 8-digit ITC-HS code (the tariff code the claim keys on) |
| **DBK serial No.** | Duty-Drawback schedule serial number (if claiming drawback) |
| **Drawback quantity** | Quantity on which drawback is claimed |
| **IGST payment status** | Whether IGST was paid on inputs (governs IGST-refund vs drawback mutual exclusivity) |
| **End-use** | End-use description |
| **Scheme code** | The export scheme chosen (e.g., drawback / RoDTEP / RoSCTL) |
| **Add-freight** | Additional freight element in the assessable value |
| **Nature of contract** | Nature of the sale contract |

Source: follow-up §1.1; review-policy §5 (from Ntf 07/2026 as described). ⚠️ **Flag:** these field names are the corpus's summary of the substituted forms; the exact column labels in the official form PDF are not reproduced in any fetched source — verify against the live form before building a renderer.

## 4. The 6 declaration clusters

Declarations are captured on a declarations screen at booking; since Jan-2026 the clusters are [follow-up §1.1; review-policy §2/§5]:

| # | Cluster | Sub-declarations (as counted in corpus) |
|---|---|---|
| 1 | **Zero-rating under s.16 IGST** | Declaration that supply is a zero-rated export |
| 2 | **Exemption** | Exemption under CGST/SGST/UTGST/IGST, and IGST compensation-cess exemption where applicable |
| 3 | **Drawback** | **4 sub-declarations** — including that no Input Tax Credit was availed on inputs and no IGST refund was claimed on the same goods (mutual-exclusivity guard); drawback claims follow Rules 13 & 14, Drawback Rules 2017 (electronic) or Rule 12 (manual) |
| 4 | **RoDTEP** | **3 sub-declarations** (Remission of Duties and Taxes on Exported Products) |
| 5 | **RoSCTL** | **3 sub-declarations** (Rebate of State and Central Taxes and Levies) |
| 6 | **FEMA undertaking** | Undertaking to abide by FEMA 1999, including **realisation and repatriation** of export proceeds |

Source: follow-up §1.1 ("+ 6 declaration clusters: zero-rating u/s 16 IGST, exemption, **Drawback (4 sub-declarations)**, **RoDTEP (3 sub-declarations)**, **RoSCTL (3 sub-declarations)**, and **FEMA undertaking**"); review-policy §2 (2026 amendment) and §4. ⚠️ **Flag:** the *counts* (4/3/3) and the RoDTEP/RoSCTL audit-preservation undertaking wording come from the corpus summary of Ntf 07/2026, not a reproduced form page; the IGST-refund vs drawback mutual-exclusivity rule is confirmed in review-policy §4 ("PBE declarations are mutually exclusive in effect").

## 5. SDR and the CN22/CN23 consequence (auto-computed)

- **SDR value is auto-converted by the portal** — "System is converting it automatically. Customer need not to enter anything" [SOP v1.3].
- The **300 SDR threshold only decides the label**: ≤300 SDR → **CN 22**; >300 SDR → **CN 23** (UPU standard) [follow-up §1.1; UPU; India Post CN22 guidance].
- **Build consequence:** a document-pack generator must *display* the SDR and the resulting CN22/23 choice, never ask the artisan to enter or compute SDR.

## 6. Excel bulk-upload template schema (the de-facto machine interface)

Two sheets — an **Information Sheet** (code reference) and an **Article Details Sheet** (data). Columns observed in the SOP [SOP v1.3 bulk-upload section, local copy]:

| Column | Meaning | Example row |
|---|---|---|
| `id` (Note-2) | Unique article ID, **same for all sub-piece rows of one article** | — |
| `sender ref` (Note-2) | Sender reference, same rule | — |
| `totalval` | Total parcel value (declared) | 10000 |
| `decl1` | Declaration 1 (Yes/No) | Yes |
| `decl2` | Declaration 2 | No |
| `decl3` | Declaration 3 | Yes |
| `hscode` | 8-digit HS code | 12345678 |
| `prd_desc` | Product description | plastic container |
| `prd_qty` | Quantity | 10 |
| `prd_qty_unit` | Unit | PIECES |
| `count` | Number of items of this type | 10 |
| `prd_gross_wt` | Gross weight of the line | 14000 |
| `prd_wgt_net` | Net weight of the line | 14000 |
| `origincountry` | 2-digit ISO origin country code | IN |
| `invoiceno` | Invoice number | a1 |
| `prd_inv_date` | Invoice date | 23-03-2023 |
| `ecomm` | e-commerce flag (1/0) | 1 |
| `ecomm_url` | Marketplace URL (PBE-III) | www.AZ.com |
| `ecomm_pay_tranid` | Payment transaction ID (PBE-III) | 1 |
| `ecomm_sku_no` | SKU number (PBE-III) | 1246 |
| `tax_inv_date` | Tax-invoice date | 23-03-2023 |
| `tax_inv_sno` | Tax-invoice serial no. | 1 |
| `tax_inv_val` | Tax-invoice value | 10000 |

Source: SOP v1.3 (header row reproduced verbatim in the local copy: `totalval decl1 decl2 decl3 hscode prd_desc prd_qty_unit count prd_gross_wt prd_wgt_net origincountry invoiceno prd_inv_date ecomm ecomm_url ecomm_pay_tranid ecomm_sku_no tax_inv_date tax_inv_sno tax_inv_val`); example rows reproduced from the SOP sample file (multiple items of one article share the same `id`/`sender ref`). **No limit on items per file**; different services per article are allowed; CN22/CN23 per item printable after upload [SOP v1.3 Note-7/8/5].

## 7. Validation rules (error-proofing targets)

| Rule | Consequence if violated |
|---|---|
| **Σ piece values ≤ parcel value** | Reject: "Value of Sub pieces does not match" |
| **Σ piece gross weights ≤ parcel weight** | Reject: "Weight of Sub pieces does not match" |
| **gross weight ≤ 110% of net weight** | Reject |
| **FOB ≤ invoice value** | Reject |
| Invalid postcode | Reject: "Invalid post Code" |
| Description ↔ HS/CTH mismatch | Reject: "Description does not match with HS Code/CTH" |
| ITCH not applicable for restricted policy | Warn/block: "ITCH code not applicable for restricted policy" |
| DGFT registration data missing | Block until IEC document uploaded |

Source: SOP v1.3 (error table); follow-up §1.2. **No published error-rate statistics exist** — the taxonomy is documented, not the rates [follow-up §1.2].

## 8. Portal submission flow (register → … → ICES)

1. **Register** on the customer portal (mobile OTP, T&Cs).
2. **Business profile:** IEC mandatory + DGFT-validated; GSTIN marked mandatory in the SOP field but KYC Note-1 enables booking with **≥1 of IEC/GSTIN**; AD code optional; LUT FY-wise.
3. **KYC upload:** IEC, AD code, GSTIN, or Others (LUT/export licence/bond/Aadhaar); booking gated on ≥1 mandatory KYC doc.
4. **Book article:** destination → service availability + tariff + prohibitions check (EMS/ITPS/foreign parcel/letters) → consignment details (**gross weight, value, SDR auto**) → choose **PBE-III or PBE-IV** → sender/recipient → **piece details with HS/CTH code** (in-portal description search) → declarations.
5. **Submit → Article ID + PBE number** auto-generated → print **CN22/23 + harmonised label + address label + invoice**; upload documents per article (invoices, licences, NOCs — visible to Indian Customs only; **physical copies attach for destination customs**).
6. **Induct** parcel + labels at any DNK/booking PO; postage collected at counter (cash default).
7. **Faceless customs at FPO:** officer assesses/examines in the DNK customs portal (`app.indiapost.gov.in/ips/home` post-Circular 01/2026); queries via the bell-icon notification → exporter replies/uploads.
8. **LEO (Let Export Order)** — system-generated, no signature → **Post EGM filed in DNK portal → data pushed to ICES** → temporary scroll → final scroll → **Drawback → SB → PFMS → DBT**; **RoDTEP/RoSCTL → SB → ICEGATE scrip generation**.
9. **Approved PBE printable only after clearance + dispatch** ("PBE not yet generated" otherwise).

Sources: report §2.3; follow-up §1.2; review-policy §3 (SOP steps) + §4 (claim flow); Kolkata Customs PN 08/2026 (LEO + Post EGM → ICES). ⚠️ **Migrated portal:** these steps describe the SOP v1.3 flow; the URLs changed under Circular 01/2026 (customer login → `app.indiapost.gov.in/customer-selfservice/login`; customs portal → `app.indiapost.gov.in/ips/home`) and the migrated portal's actual rendering is **untested** [contradictions-map C4].

## 9. Build implications (for the P0 document-pack generator)

- **Never ask for SDR or INR conversion** — the portal auto-computes both.
- **Emit PBE-III e-commerce columns only when the order came via an e-marketplace with electronic payment**; otherwise PBE-IV.
- **Pre-fill header from IEC data** (DGFT name/address), validate GSTIN as "or as applicable", and treat the **AD code as the ICEGATE/claim key**, not just a display field.
- **Validate the four arithmetic rules client-side** (Σ values, Σ weights, gross ≤ 110% net, FOB ≤ invoice) — these are the portal's own error taxonomy, and error here is the #1 documented failure mode.
- **Surface the 2026 fields (RITC/ITC-HS, DBK serial, drawback qty, IGST status, end-use, scheme code, add-freight, nature of contract) as scheme-aware** — only populated when the exporter opts into an electronic claim, and then the E-Sanchit upload obligation (Circular 01/2026 §4.vi.e) applies.
- **The Excel template is the only documented machine interface** — no public API exists; build against the column schema in §6 and mock the submission [report §10; findings Ctx-2].

## 10. Sources & flags

**Sources:** Notification 104/2022-Customs (taxguru full text, https://taxguru.in/custom-duty/postal-export-electronic-declaration-processing-regulations-2022-implementation-pbe-automated-system.html); Notification 07/2026-Customs (N.T.) 15-Jan-2026 (corpus description via follow-up §1.1, review-policy §2/§5 — no fetched full form text); Circular 25/2022-Customs; Circular 01/2026-Customs (local copy); Kolkata Customs PN 08/2026; DNK SOP v1.3 (local copy); UPU CN22/CN23 standards (https://www.upu.int/UPU/media/upu/files/aboutUpu/acts/05-actsRegulationsConventionAndPostalPayment/actsCircular100-2022En.pdf); follow-ups/01-order-to-delivery-flow/findings.md §1.

**Flags:** (1) exact 2026 form column labels not reproduced in any fetched source — verify against the live form; (2) Drawback/RoDTEP/RoSCTL sub-declaration wording and counts come from the corpus summary of Ntf 07/2026; (3) migrated-portal rendering of the flow untested (O2/O5 instruments); (4) no public API — all PBE submission must be mocked in a demo and labelled mock [gap-feature-map F6].
