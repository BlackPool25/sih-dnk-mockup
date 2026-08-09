# PBE-III vs PBE-IV — Which Form When (Rules & Validation)

**Project:** SIH260113 · **Research area:** dnk-export-enablement · **Date:** 2026-08-08
**Purpose:** the decision rule an artisan/assistant applies at booking, the legal text behind it (Reg 5, Notification 104/2022-Customs), the 5 e-commerce columns PBE-III adds, the 2026 substituted forms (Notification 07/2026-Customs), the manual PBE-I/II legacy, and what each choice means for the payment evidence the artisan must keep.
**Honesty header.** The PBE-III/IV field structure below is taken from the **full text of Notification 104/2022-Customs (N.T.) 09-Dec-2022** (fetched via taxguru, L1 reproduction) and the **substituted forms in Notification 07/2026-Customs (N.T.) 15-Jan-2026** (local copy `data/06-legal-sources/notification-07-2026-customs.txt`). Where a field's *exact* rendering on the migrated portal (`app.indiapost.gov.in/customer-selfservice`) is untested, that is flagged [contradictions-map C4; findings H2-b].

---

## 0. The decision in one line

**PBE-III** = the order came through an **e-marketplace / e-commerce platform** **AND** payment was made by **electronic means** (RBI guidelines) → capture the marketplace's Order/Payment ID.
**PBE-IV** = **everything else** (order by phone, WhatsApp, exhibition, direct email, cash-on-delivery, no e-marketplace) → no e-commerce particulars needed.

| Form | Use for | Route | Payment evidence needed |
|---|---|---|---|
| **PBE-III** | **E-commerce** exports — order via an e-marketplace platform, paid by electronic means per RBI guidelines | Electronic (DNK portal) | **5 e-commerce columns** (§2): e-comm operator GSTIN, marketplace URL, **payment transaction ID**, SKU, postal tracking no. |
| **PBE-IV** | **All other** postal exports | Electronic (DNK portal) | Ordinary invoice + FOB value; no e-commerce columns |
| PBE-I / PBE-II | Manual legacy equivalents (e-commerce / other) | Manual (APSO, Exports-by-Posts 2018 route) | n/a — paper forms |

Source: Reg 5, Notification 104/2022-Customs (verbatim §1.1 below); DNK SOP v1.3 ("In this scenario, exporter has to choose PBE-III… If the exporter get order by other mode… he has to choose PBE-IV") [DNK SOP v1.3, local copy]; report §2.2.

---

## 1. Legal basis (verbatim, L1)

### 1.1 Regulation 3(d) — what "e-commerce" means (Ntf 104/2022)
> *"e-commerce" means **buying and selling of goods through the internet on an e-commerce platform, the payment for which shall be done through various electronic means and in accordance with the guidelines issued by the Reserve Bank of India from time-to-time;***

So PBE-III requires **two things together**: (a) the transaction happens **on an e-commerce platform** (marketplace/website), **and** (b) **payment via electronic means** per RBI guidelines. If either leg is missing (order came in offline, or payment was cash/cheque), the export is **PBE-IV**, even if the parcel itself is booked electronically on the DNK portal.

### 1.2 Regulation 5(1) — which form (Ntf 104/2022)
> *(1) For export of goods by post, in furtherance of the business, the exporter or his authorised agent shall make an entry thereof through an electronic declaration in the following forms, namely—*
> *(i) **Postal Bill of Export-III (PBE-III) for postal exports effected through e-commerce**; or*
> *(ii) **Postal Bill of Export-IV (PBE-IV) for all other postal exports**.*

Reg 5(2) makes the declarant responsible for accuracy/completeness of the entry, authenticity/validity of supporting documents, and compliance with prohibitions/restrictions.

Source: Notification 104/2022-Customs (N.T.), G.S.R. 874(E), 09-Dec-2022 — full text at https://taxguru.in/custom-duty/postal-export-electronic-declaration-processing-regulations-2022.html (mirrored locally in `data/06-legal-sources/notification-104-2022-taxguru.html`).

---

## 2. The 5 e-commerce columns PBE-III adds

In the **PBE-III "Details of parcel"** line table there is an **"E-commerce particulars"** block that PBE-IV does not have (in PBE-IV the parcel table carries only the **postal tracking number**). The 5 columns (2022 form; carried into the 2026 substituted form):

| # | Column | What the artisan must fill / keep |
|---|---|---|
| 1 | **GSTIN of e-commerce operator** | GSTIN of the marketplace operator (the platform you sold through — e.g., the marketplace's GSTIN, not the artisan's own) |
| 2 | **URL (Name) of website** | The marketplace / website URL where the order was placed |
| 3 | **Payment transaction ID** | **The electronic payment reference** from the marketplace checkout (the payment-evidence anchor) |
| 4 | **SKU No.** | The marketplace SKU / product identifier for the item |
| 5 | **Postal tracking number** | The article's postal tracking number (S10) once generated |

Source: PBE-III form, Notification 104/2022 (fetched full text); Notification 07/2026 substituted PBE-III (local copy); pbe-iii-iv-fields.md §2. **Build note:** a document-pack generator must emit these 5 columns **only when the order came via an e-marketplace with electronic payment** — otherwise PBE-IV [pbe-iii-iv-fields.md §9].

**Excel bulk-upload mapping** (the de-facto machine interface): the bulk template carries `ecomm` (1/0 flag), `ecomm_url`, `ecomm_pay_tranid`, `ecomm_sku_no` — i.e., PBE-III is *flagged*, not a separate sheet [DNK SOP v1.3; pbe-iii-iv-fields.md §6].

---

## 3. Manual legacy PBE-I / PBE-II (the non-electronic route)

- **PBE-I** (e-commerce) and **PBE-II** (other than e-commerce) are the **manual** paper forms under the earlier Exports-by-Post regime (Postal Export (Electronic Declaration and Processing) Regulations replaced the manual system; the manual route remains for non-electronic filing at the APSO).
- The **DNK portal always files electronically**, so portal users choose **only PBE-III or PBE-IV** — PBE-I/II never appear on the electronic route. [DNK SOP v1.3: "Since filling of PBE for exports through the DNK portal falls under electronic mode, the exporter needs to opt either PBE-III or PBE-IV based on export type"]; report §2.2; pbe-iii-iv-fields.md §0.

---

## 4. The 2026 substituted forms (Ntf 07/2026) — what changed for claims

Notification 07/2026-Customs (N.T.), 15-Jan-2026, substituted both electronic forms. The header/parcel structure is unchanged; the additions are:

1. **"Additional details of parcel"** table (in both PBE-III and PBE-IV): **RITC code / ITC-HS code · DBK serial No. · Drawback quantity · IGST payment status (Yes/No) · End use of item · Scheme code · Add Freight (₹/YN) · Nature of contract (CIF/CF/C&F/FOB)** — this is where the exporter keys the Drawback / RoDTEP / RoSCTL claim.
2. **Six declaration clusters** (all with Yes/No-as-applicable):
   1. Zero-rating under **s.16 IGST**;
   2. Exemption under CGST/SGST/UTGST/IGST;
   3. **Drawback** (4 sub-declarations: no ITC availed; no IGST refund claimed on the same goods; CENVAT not carried forward; conditions of Drawback Rules complied);
   4. **RoDTEP** (3 sub-declarations: abide by scheme; no claim on duties already exempted/remitted outside RoDTEP; preserve audit documents per Customs Audit Regulations 2018);
   5. **RoSCTL** (3 sub-declarations, mirroring RoDTEP);
   6. **FEMA undertaking** (abide by FEMA 1999, including **realisation and repatriation** of foreign exchange).

Source: Notification 07/2026-Customs (N.T.) 15-Jan-2026 — local copy; Circular 01/2026 §4.vi.b; pbe-iii-iv-fields.md §3–4. ⚠️ Flag: the 2022 form carried only 3 declaration blocks (export-promotion-scheme/Drawback, zero-rating, exemption); the 2026 form expands Drawback/RoDTEP/RoSCTL and adds the FEMA undertaking — the incentive claim happens *on the form*, not after it.

---

## 5. Implications for payment evidence (which rail evidence does the artisan need)

| Scenario | Form | Payment evidence the artisan must keep |
|---|---|---|
| Sold via marketplace (Etsy, Amazon, ONDC…), paid online | **PBE-III** | **Payment transaction ID** + marketplace URL + SKU + e-comm operator GSTIN → ties the order to the payment; keep the marketplace payout statement + Payoneer/aggregator FIRC for the CA |
| Direct sale (WhatsApp/email/exhibition), paid by card/bank transfer via a rail | **PBE-IV** | Commercial invoice + **payment transaction ID / FIRC** from the rail (Razorpay eFIRC, Wise e-FIRC, PayPal FIRA) — the *rail's* payment evidence replaces the marketplace's transaction ID |
| Any export | both | **FEMA realisation** is still mandatory for every export (9-month base rule, FEMA Reg 9 as amended 5-Jun-2026; 15-month relaxation in force per RBI 31-Mar-2026) [payment-rails.md §7] — e-BRC/EDPMS closure is form-agnostic |

**Build consequence:** PBE-III's payment-transaction-ID column is the **order→payment binding key** — on PBE-IV that binding is the commercial invoice + the rail's FIRC. Either way, the **FIRC-sender-mismatch trap** (aggregator FIRC names partner bank, not buyer) applies and must be surfaced (FR-043) [payment-rails.md §6].

---

## 6. Validation rules (the error-proofing taxonomy)

The portal enforces (and a document-pack generator should pre-validate) [DNK SOP v1.3; follow-up §1.2; pbe-iii-iv-fields.md §7]:

| Rule | Consequence if violated |
|---|---|
| **Σ piece values ≤ parcel value** | Reject: "Value of Sub pieces does not match" |
| **Σ piece gross weights ≤ parcel weight** | Reject: "Weight of Sub pieces does not match" |
| **gross weight ≤ 110% of net weight** | Reject |
| **FOB ≤ invoice value** | Reject |
| Invalid postcode | Reject: "Invalid post Code" |
| Description ↔ HS/CTH mismatch | Reject: "Description does not match with HS Code/CTH" |
| ITC-HS not applicable for restricted policy | Warn/block |
| DGFT registration data missing | Block until IEC document uploaded |
| IEC suspended/blacklisted/cancelled | **Booking disabled** (IEC validated live against DGFT) |

No published error-rate statistics exist — the taxonomy is documented, not the rates [follow-up §1.2].

---

## 7. Build implications (for the P0 document-pack generator)

- **Decision logic:** emit PBE-III (with the 5 e-commerce columns) only when the order source = e-marketplace **AND** payment = electronic means; else PBE-IV [pbe-iii-iv-fields.md §9].
- **SDR / INR / FOB**: the portal auto-computes SDR and INR conversion ("Customer need not to enter anything"); the generator must *display*, never ask the artisan to compute [DNK SOP v1.3; pbe-iii-iv-fields.md §5].
- **2026 fields are scheme-aware:** surface RITC/ITC-HS, DBK serial, drawback qty, IGST status, end-use, scheme code, add-freight, nature of contract only when the exporter opts into an electronic incentive claim — and then the **E-Sanchit upload obligation** applies (Circular 01/2026 §4.vi.e) [pbe-iii-iv-fields.md §9].
- **GSTIN is "or as applicable"** on the form, not uniformly mandatory — never build a hard GSTIN block (H2; FR-060) [pbe-iii-iv-fields.md §1].
- **The Excel bulk template is the only documented machine interface** — no public API exists; build against the `ecomm_*` column schema and mock submission (FR-090, FR-003) [pbe-iii-iv-fields.md §6, §9].

---

## 8. Sources & flags

**Sources (accessed 2026-08-08 unless dated):**
- Notification 104/2022-Customs (N.T.), G.S.R. 874(E), 09-Dec-2022 — full text incl. Reg 3(d)/Reg 5 and the original PBE-III/IV forms: https://taxguru.in/custom-duty/postal-export-electronic-declaration-processing-regulations-2022.html (mirror locally)
- Notification 07/2026-Customs (N.T.), 15-Jan-2026 — substituted PBE-III/IV: local copy `data/06-legal-sources/notification-07-2026-customs.txt`
- Circular 01/2026-Customs, 15-Jan-2026 (§4.vi.b additional PBE tables): local copy `data/06-legal-sources/circular-01-2026-customs.txt`
- DNK Customer Portal SOP v1.3 (PBE selection, validation rules, bulk-upload columns, "If no contract is mapped… cash"): local copy `data/06-legal-sources/dnk-sop-wayback.txt`
- Kolkata Customs PN 08/2026 (LEO + Post EGM → ICES): https://kolkatacustoms.gov.in/storage/uploads/custom_notice_order/20260211153259.pdf
- Corpus anchors: report §2.2–2.4, §5.1; findings Ctx-2, H2-b/c; contradictions-map C2/C4; follow-up 01-order-to-delivery-flow §1.1–1.2; pbe-iii-iv-fields.md (companion file in `data/02-dnk-documents/forms-pbe/`)

**Flags:** (1) migrated-portal rendering (`app.indiapost.gov.in/customer-selfservice`) untested — C4/H2-b; (2) exact column labels of the 2026 substituted forms as rendered are the corpus's summary — verify against the live form before building a renderer [pbe-iii-iv-fields.md §3]; (3) no public API — PBE submission must be mocked and labelled mock (FR-003); (4) PBE-III's "e-commerce" test is the *RBI-guideline electronic payment* definition — a cash/cheque order on a marketplace is PBE-IV.
