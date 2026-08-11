# Onboarding Guide — Zero to First Export via DNK (Artisan Journey)

**Project:** SIH260113 · **Research area:** dnk-export-enablement · **Date:** 2026-08-08
**Persona:** Sunita — ₹7,000/month, <7% beyond primary education, IEC-only, GSTIN-less by law, vernacular-first, first ever export [report §3.1, §9.1]. **Goal of this guide:** an honest, step-by-step path from "no documents" to "first parcel booked and claimed through DNK", naming who does what, what can fail, and who helps.
**Structure:** §1 one-glance table → §2 the eight steps in order → §3 decision tree (which steps are skippable) → §4 honesty flags.
**Key honesty rules (from the corpus, non-negotiable):** GSTIN is **not** stated as mandatory (contested, H2); no portal step outside the SOP/corpus is invented; no fee is fabricated — every figure is cited; the migrated portal (`app.indiapost.gov.in`) is **untested**, so every step on it is labelled "per SOP v1.3; verify live" [findings F-H2; contradictions-map C4].

---

## 1. The eight steps at a glance

| # | Step | Where | Cost | Time | Do you need it? |
|---|---|---|---|---|---|
| 1 | **Get IEC** | DGFT portal (`dgft.gov.in/CP/?opt=iec-profile-management`) | ₹500 application fee; e-Sign via Aadhaar (free) or DSC (vendor-priced) | Same-day auto-generation | **Yes — mandatory** (Reg 2) |
| 2 | **Open/link a firm-name bank account** | Any scheduled bank | Bank-set | Days | **Yes** — IEC prerequisite + refund destination |
| 3 | **Register AD Code on ICEGATE** | ICEGATE → AD Code/Bank-Account Registration | Bank-set issuance fee; ICEGATE free | Days (approval) | **Yes if claiming any incentive** |
| 4 | **ICEGATE registration + link bank to DNK site code** | `icegate.gov.in` | Free | Same-day–days | **Yes if claiming any incentive** |
| 5 | **DNK portal registration** | `app.indiapost.gov.in/customer-selfservice/login` (migrated from `dnk.cept.gov.in` per Circular 01/2026) | Free | Minutes (OTP) | **Yes — mandatory** |
| 6 | **KYC upload** | DNK portal → Manage Profile → KYC | Free | Minutes | **Yes — booking gated on ≥1 of IEC/GSTIN** |
| 7 | **UDYAM + EPCH RCMC** | `udyamregistration.gov.in`; DGFT e-RCMC (`dgft.gov.in/CP/?opt=e-rcmc`) | UDYAM: zero; RCMC: council-set | Minutes (UDYAM); days–weeks (RCMC) | **Only if claiming FTP benefits** beyond PBE-channel incentives |
| 8 | **Per-claim E-Sanchit uploads** | `foservices.icegate.gov.in` (login via ICEGATE) | Free | Per claim, minutes | **Only when claiming electronically** |

*Full citations in §2 per step.*

---

## 2. The eight steps, in order

### Step 1 — Get the IEC (Import-Exporter Code)

- **What.** 10-character DGFT exporter identity; mandatory to file any PBE (Reg 2, Ntf 104/2022) [report §2.1, §5.1].
- **Where.** DGFT portal: `https://www.dgft.gov.in/CP/?opt=iec-profile-management`; application form **ANF-2A** (ANF-1A merged into it from 20-Nov-2025, PN 32/2025-26) [taxguru.in/dgft/dgft-merges-anf-1a-anf-2a-streamline-iec-applications.html].
- **Prerequisites.** Firm **PAN** (validated online with Income Tax), **bank account in the firm's name** + proof (cancelled cheque / bank certificate), **Aadhaar e-Sign or DSC** of a firm member, valid address (may be physically verified). **GSTIN not required** — "GSTIN … if applicable" [DGFT IEC Manual v2.0, https://content.dgft.gov.in/Website/IEC_Manual_V2.0_Updated.pdf].
- **Cost.** **₹500** application fee via Bharatkosh (₹200 for modifications) per the official IEC Module User Help File [https://content.dgft.gov.in/Website/DGFT%20-%20IEC%20Module%20User%20Help%20File.pdf]. ⚠️ **Flag:** the corpus also describes IEC as "free under FTP 2023" — both statements appear in official sources; ₹500 is the portal processing fee. Aadhaar e-Sign itself is free; a **DSC** is vendor-priced (no public fixed figure).
- **Time.** Auto-generated on submission; informed by e-mail/SMS; RA post-verification afterwards [HBP 2023 Ch-2 §2.08].
- **Failure modes.** (a) Aadhaar-PAN details mismatch → e-Sign fails; (b) no firm-name bank account yet (Step 2) → application stalls; (c) Aadhaar not linked to mobile → no OTP; (d) suspended/blacklisted status on an existing IEC → DNK booking disabled [SOP v1.3]; (e) DGFT English-first form overwhelms the user.
- **Who can help.** **Dak Niryat Sahayak** — their documented job includes "generation of Import-Export Code" [New Indian Express, 19-Mar-2023; ThePrint 1455312]. Also DGFT helpdesk and common-service-centre (CSC) operators.

### Step 2 — Open / link a firm-name bank account

- **What.** A bank account in the name of the firm that holds the IEC — the *silent* precondition behind Step 1 and behind every refund (IGST, Drawback via PFMS DBT) and e-BRC.
- **Where.** Any scheduled commercial bank; ask for a current account suited to small enterprises (many banks have zero-balance MSME current accounts — bank-specific, verify at branch).
- **Cost / time.** Bank-set; typically days.
- **Failure modes.** KYC proof gaps for a household-based artisan (address proof for a business address); the 97% household-based, cash-first persona may not have a separate business address [report §3.1]. ⚠️ **Note:** 0.1% of UP establishments keep accounts — this step is a real friction point, not paperwork [report §3.1].
- **Who can help.** Dak Niryat Sahayaks / DNK staff advise on which documents the bank will accept; banks' own small-enterprise desks.

### Step 3 — Register the AD Code on ICEGATE

- **What.** The bank issues a **14-digit AD Code** letter; you register it on ICEGATE so Customs links your bank account to your IEC [skydo.com/blog/ad-code-registration; ICEGATE advisory].
- **Where.** ICEGATE → "AD Code / Bank Account Registration": `https://www.icegate.gov.in/guidelines/ad-code-bank-account-registration-advisory`; upload bank authorisation letter + passbook/cancelled cheque/IEC/PAN/DSC via **e-Sanchit**; select port of registration (usable across all ports once approved) [taxguru.in/custom-duty/online-registration-authorised-dealer-ad-code-bank-accounts-icegate.html; Kolkata PN 08/2026].
- **Cost.** Bank-set issuance fee (no public fixed figure — flag); ICEGATE free.
- **Time.** Days; approval delays are officially acknowledged by CBIC [findings F-H1-a].
- **Failure modes.** DSC absent; bank letter mismatch with IEC name; approval pending → incentive claims can't key to the account.
- **Who can help.** Dak Niryat Sahayak; the bank's export desk; DNK counter staff.

### Step 4 — ICEGATE registration + link bank account to the DNK site code

- **What.** Register on ICEGATE (mandatory for **every electronic incentive claim**), then add the bank account **corresponding to the DNK site code** [Circular 01/2026 §4.vi.a; local copy].
- **Where.** `icegate.gov.in` → Register Now → Fresh Registration → IEC + GSTIN validated live, PAN, contact, **Class-3 DSC**, bank account [cleartax.in/s/icegate-registration]. Then Bank-Account Management → add account for the DNK site code; customs officer approves in ICES (CLK role); **auto-approval at end of day if the IEC+account is already approved for another site** [Kolkata PN 08/2026, kolkatacustoms.gov.in/storage/uploads/custom_notice_order/20260211153259.pdf].
- **Cost.** Free. **Time.** Same-day–days.
- **Failure modes.** Class-3 DSC cost/literacy; GSTIN field on the registration form (validated live against GSTN — an IEC-only user may hit a form block; **untested on the migrated stack, flag O2**); bank-account approval queue.
- **Who can help.** Dak Niryat Sahayak; ICEGATE helpdesk.

### Step 5 — Register on the DNK customer portal

- **What.** Create the exporter account on the DNK customer portal (self-registration: user ID 8–15 chars, email, mobile, password, OTP to mobile, accept T&Cs).
- **Where.** **`https://app.indiapost.gov.in/customer-selfservice/login`** — the post-Circular 01/2026 URL. The stale SOP documents `https://dnk.cept.gov.in/customers.web/`; **build/teach against the new URL** [Circular 01/2026 §4.i; contradictions-map C4].
- **Cost.** Free. **Time.** Minutes.
- **Failure modes.** OTP not received (mobile not registered); portal language barrier; (for a contractual customer only) backend CEPT mapping of Customer/Contract IDs is required for advance/BNPL — not needed for the default cash retail route.
- **Who can help.** Dak Niryat Sahayak / DNK Postmaster at the counter — this is their daily workflow.

### Step 6 — Complete the business profile + KYC upload

- **What.** In **Manage Profile → Business details**: Customer Type (Commercial), **IEC (mandatory, validated live)**, GSTIN, AD code, LUT. Then **KYC**: upload IEC, AD code, GSTIN, or **Others** (LUT/export licence/bond/Aadhaar). **Booking is enabled only after ≥1 mandatory KYC doc — IEC or GSTIN** [SOP v1.3 Note-1].
- **Where.** DNK portal → Manage Profile → Business Details / KYC.
- **Cost.** Free. **Time.** Minutes.
- **Failure modes.** **Do not present GSTIN as mandatory.** The SOP's business-details screen marks GSTIN mandatory but the KYC note and the PBE form ("GSTIN or as applicable") provide escape hatches; whether the migrated portal honours them is **untested** [findings F-H2-b; contradictions-map C2]. Real failure modes: IEC suspended → booking disabled; upload format issues.
- **Who can help.** Dak Niryat Sahayak.

### Step 7 — UDYAM registration + EPCH RCMC (only if claiming FTP benefits)

- **What.** UDYAM MSME certificate (free, self-declaration, Aadhaar OTP) then EPCH RCMC for handicrafts (needed for FTP scheme benefits; manufacturer exporters must show the UDYAM certificate). **Not required by the DNK portal itself** [review-policy §6].
- **Where.** `https://udyamregistration.gov.in` (official — the portal warns other sites/apps charging fees are fraudulent); EPCH via DGFT e-RCMC: `https://www.dgft.gov.in/CP/?opt=e-rcmc` (ANF 2C; new memberships through DGFT login; membership is a pre-condition) [https://www.epch.in/apply-new-membership; epch.in/faqs].
- **Cost.** UDYAM: **zero** [udyamregistration.gov.in]. RCMC: council-set (not a public fixed figure — flag).
- **Time.** UDYAM minutes–same day; RCMC days–weeks.
- **Failure modes.** UDYAM needs Aadhaar-linked mobile; manufacturer-exporter RCMC needs UDYAM first; DGFT-login friction; council fee unknown in corpus.
- **Who can help.** Dak Niryat Sahayak (ODOP/GI listing assistance is their documented role); EPCH/DGFT helpdesk.

### Step 8 — Per-claim E-Sanchit uploads (when claiming electronically)

- **What.** For each PBE claimed electronically, upload the supporting documents to **E-Sanchit/ICEGATE** [Circular 01/2026 §4.vi.e]. Only ICEGATE-registered users can upload; validate for digital signature; select the document type [eSANCHIT FAQ, icegate.gov.in/sites/default/files/2022-02/eSANCHIT_FAQs.pdf].
- **Where.** `https://foservices.icegate.gov.in/` (login via ICEGATE → e-Sanchit link).
- **Cost.** Free. **Time.** Per claim, minutes.
- **Failure modes.** Export-side E-Sanchit capability is **undocumented/verified-lagging** (C14) — the requirement exists but the importer-focused FAQ is a red flag; scan specs (≥200 dpi, ≤1 MB/PDF) trip the artisan's phone scans [jawaharcustoms.gov.in eSANCHIT procedure].
- **Who can help.** Dak Niryat Sahayak / DNK counter — do not send an artisan to e-Sanchit alone.

---

## 3. Decision tree — which steps are actually needed for this shipment?

```
Any DNK export?                        → Step 1 (IEC) + Step 5 (DNK portal) + Step 6 (KYC ≥1 doc) — MANDATORY
  ↓
Claiming IGST refund / Drawback /
RoDTEP / RoSCTL electronically?        → Step 2 (bank acct) + Step 3 (AD Code) + Step 4 (ICEGATE + DNK-site bank link) + Step 8 (E-Sanchit) — REQUIRED
  ↓
Claiming FTP benefits beyond the
PBE channel (status certs, schemes)?   → Step 7 (UDYAM + EPCH RCMC) — OPTIONAL for DNK, required for those schemes
```

No claim-size threshold exists in the regulations — micro-claims are claimable in law, but in practice the stack gates them [review-policy §8b.1]. The product's **realization tracker** (P0 feature F2) exists precisely because entitlement ≠ cash-in-hand [gap-feature-map F2].

---

## 4. Honesty flags (must stay in any derivative material)

1. **GSTIN is NOT stated as mandatory** anywhere in this guide — the legal position is that the modal artisan is GSTIN-less (90% High) and on-paper escape hatches exist (SOP KYC Note-1 ≥1-of-IEC/GSTIN; PBE "GSTIN or as applicable"; KYC "Others"); the migrated-portal *enforcement* is untested [findings F-H2].
2. **The migrated portal flow is per-SOP-v1.3, not verified live** (O2 instrument). Every step above that touches `app.indiapost.gov.in` should be re-tested at a DNK before teaching it as fact.
3. **Fees:** IEC ₹500 (official help file) vs "free under FTP 2023" (corpus) — both cited; AD Code and RCMC fees are bank/council-set and **unverified**; DSC price is vendor-set and unverified. **No fee has been fabricated.**
4. **No public API** exists on the DNK/ICEGATE/EDPMS path — any onboarding wizard in a demo must **mock** the portal/ICEGATE steps and label them mock [report §10; gap-feature-map F6].
5. **E-Sanchit export-side capability** is unresolved (C14) — surface it as a possible blocker rather than promising a smooth upload.
6. **Dak Niryat Sahayak is a co-user, not a replacement:** staff help itself confirms the target user cannot self-serve (H2 note) [findings F-H2-b]. Design the onboarding as assisted-first.

## 5. Sources

DNK SOP v1.3 (local copy `data/06-legal-sources/dnk-sop-wayback.txt`); Circular 01/2026-Customs (local copy `data/06-legal-sources/circular-01-2026-customs.txt`); Kolkata Customs PN 08/2026 (kolkatacustoms.gov.in, 11-Feb-2026); DGFT IEC Manual v2.0 + IEC Module User Help File + HBP 2023 Ch-2 (content.dgft.gov.in); PN 32/2025-26 (taxguru); ICEGATE AD-Code advisory + Bank-Account Management manual + eSANCHIT FAQ (icegate.gov.in); UDYAM (udyamregistration.gov.in); EPCH membership + FAQ (epch.in); DGFT e-RCMC; New Indian Express / ThePrint Dak Niryat Sahayak coverage (19-Mar-2023); PIB PRID 2055743; corpus anchors report.md §2.3/§5.1/§9.1, findings F-H1/F-H2/Ctx-1, gap-feature-map F1/F2/F6/F8, review-policy §3/§6, review-data-tech §1–2.
