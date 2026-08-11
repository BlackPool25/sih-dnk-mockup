"""Config-flag seeds (todo 7) — every flag traceable to the pack
(country duties-taxes files, lane docs, payment/incentive docs).
flag_value is a JSONB scalar or flat array — never an object wrapper
(pinned by the verification gates).
"""

from __future__ import annotations

from datetime import date

from app.models import ConfigFlag
from app.services.seed._common import SNAPSHOT_DATE, VERIFIED_AT

# --- flags ---------------------------------------------------------------------
# Every flag is traceable to the pack (country duties-taxes files, lane docs,
# payment/incentive docs).  flag_value is a JSONB scalar or flat array —
# never an object wrapper (pinned by the verification gates).

_US_USTR = ("https://ustr.gov/sites/default/files/files/Press/Releases/2026/"
            "FLIP%20301%20Investigation%20Final%20Action%20FRN%207-23-26%20FINAL.pdf")
_US_DEMINIMIS = ("https://www.cbp.gov/sites/default/files/2025-08/"
                 "factsheet_suspension_of_duty-free_de_minimis_treatment.pdf")
_US_CBP_FAQ = "https://www.cbp.gov/trade/basic-import-export/e-commerce/faqs"
_US_USPS_FEE = "https://www.govinfo.gov/content/pkg/FR-2026-01-08/html/2026-00164.htm"
_UK_GOV_TAX = "https://www.gov.uk/goods-sent-from-abroad/tax-and-duty"
_UK_RM_FEE = "https://www.royalmail.com/receiving-mail/pay-a-fee"
_UK_CETA = ("https://www.gov.uk/government/news/"
            "historic-uk-india-free-trade-agreement-is-now-in-effect")
_AE_FTA = "https://tax.gov.ae"
_AE_EMX = "https://www.emx.ae/vat"
_AE_CUSTOMS = ("https://www.dubaicustoms.gov.ae/en/OpenData/Publications/"
               "Customer_Guide_Booklet_EN.pdf")
_AE_DEMINIMIS = "https://samvertex.com/blog/uae-customs-de-minimis-2026/"
_AE_CEPA = ("https://www.moet.gov.ae/documents/20121/1347101/"
            "Final+Agreement_UAE+India+CEPA.pdf")
_AE_WHO_PAYS = ("https://www.thenationalnews.com/business/money/vat-q-a-why-am-i-"
                "charged-tax-to-pick-up-a-parcel-from-the-post-office-1.730293")
_AU_ATO_LVIG = ("https://www.ato.gov.au/businesses-and-organisations/international-"
                "tax-for-business/gst-for-non-resident-businesses/"
                "gst-on-low-value-imported-goods")
_AU_ATO_IMPORT = ("https://www.ato.gov.au/businesses-and-organisations/gst-excise-"
                  "and-indirect-taxes/gst/in-detail/rules-for-specific-transactions/"
                  "international-transactions/gst-and-imported-goods")
_AU_ATO_GST = ("https://www.ato.gov.au/businesses-and-organisations/international-"
               "tax-for-business/gst-for-non-resident-businesses/how-australian-gst-works")
_AU_IPC = ("https://www.legislation.gov.au/C2004A00857/2016-07-01/2016-07-01/text/"
           "original/epub/OEBPS/document_1/document_1.html")
_AU_ECTA = ("https://www.dfat.gov.au/trade/agreements/in-force/australia-india-ecta/"
            "australia-india-ecta-official-text")
_AU_COO = "https://coo.dgft.gov.in/"
_AU_DAFF = "https://www.agriculture.gov.au/biosecurity-trade/import/goods/timber"
_AU_BICON = "https://bicon.agriculture.gov.au/"
_ITPS_OM = "https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html"
_ITPS_SOP = "https://www.potoolsblog.in/2025/04/standard-operating-procedure-sop-for.html"
_ITPS_TRANSIT = "https://trackmyspeedpost.com/delivery-time-by-service"
_EMS_INDIA_POST = "https://indiapost.org/international-speed-post-ems"
_EMS_DOP = "https://test.cept.gov.in/enterpriseportal/mails/international-mail/international-speedpost"
_EMS_SCHEDULE_IV = "https://www.speedpost.report/2024/12/schedule-iv.html"
_EMS_CLICKPOST = "https://www.clickpost.ai/blog/international-speed-post"
_EMS_CONFLICTS = "https://www.clickpost.ai/blog/india-post-courier-charges"
_CN22_POSTALSTUDY = "https://www.postalstudy.in/2022/03/instructions-on-kyc-for-foreign.html"
_PBE_NTF104 = ("https://taxguru.in/custom-duty/postal-export-electronic-declaration-"
               "processing-regulations-2022-implementation-pbe-automated-system.html")
_RAZORPAY = "https://razorpay.com/pricing/"
_WISE_HELP = ("https://wise.com/help/articles/71lNXW0Ls3gEFhUH8PtodV/"
              "receiving-payments-for-indian-businesses")
_WISE_REVIEW = ("https://www.infinityapp.in/blog/"
                "wise-(transferwise)-india-features-benefits-and-alternatives")
_PAYPAL_FEES = "https://www.paypal.com/in/business/paypal-business-fees"
_ETSY_FEES = "https://www.karboncard.com/blog/etsy-payouts-india-fees-conversion"
_FEMA_9MO = ("https://taxguru.in/rbi/foreign-exchange-management-export-goods-services-"
             "first-amendment-regulations-2026.html")
_FEMA_15MO = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=62478"
_RODTEP_SCRIP = ("https://www.icegate.gov.in/guidelines/advisory-e-scrip-avail-export-"
                 "incentive-schemes-rosctl-rodtep")
_RODTEP_DISCOUNT = "https://allfrontierglobal.com/gdocs/doc106-faq-rodtep-scheme/"
_LABELS_SRC = "https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2055743"

# (flag_key, value, source_url, source_level, confidence, is_estimate, effective_from)
FLAG_SPECS: list[tuple[str, object, str, str, str, bool, date | None]] = [
    # --- US (duties-taxes.md §1/§7) ---
    ("us.usps_clearance_fee_minor", 935, _US_USPS_FEE, "L1", "high", False, None),
    ("us.deminimis.suspended", True, _US_DEMINIMIS, "L1", "high", False, date(2025, 8, 29)),
    ("us.s301.rate_pct", 10, _US_USTR, "L1", "high", False, date(2026, 7, 24)),
    ("us.s301.basis", "netofmfn", _US_USTR, "L1", "high", False, date(2026, 7, 24)),
    ("us.entry_formal_threshold_minor", 250000, _US_CBP_FAQ, "L1", "high", False, None),
    ("us.duty_basis", "S301_10_pct_netofmfn", _US_USTR, "L1", "high", False, date(2026, 7, 24)),
    ("us.mpf.postal", "exempt_itps_liable_ems", _US_CBP_FAQ, "L1", "high", False, None),
    # --- UK (duties-taxes.md §1–§6) ---
    ("uk.duty_freethreshold_minor", 13500, _UK_GOV_TAX, "L1", "high", False, None),
    ("uk.vat_pct", 20, _UK_GOV_TAX, "L1", "high", False, None),
    ("uk.royalmail_handling_fee_minor", 800, _UK_RM_FEE, "L1", "high", False, None),
    ("uk.parcelforce_handling_fee_minor", 1200, _UK_RM_FEE, "L1", "high", False, None),
    ("uk.ceta_in_force", True, _UK_CETA, "L1", "high", False, date(2026, 7, 15)),
    ("uk.gift_vat_threshold_minor", 3900, _UK_GOV_TAX, "L1", "high", False, None),
    ("uk.gift_reduced_duty_rate_pct", 2.5, _UK_GOV_TAX, "L1", "high", False, None),
    # --- UAE (duties-taxes.md §1) ---
    ("uae.vat_pct", 5, _AE_FTA, "L1", "high", False, None),
    ("uae.duty_rate_pct", 5, _AE_CUSTOMS, "L1", "high", False, None),
    ("uae.deminimis_duty_only_aed", 1000, _AE_DEMINIMIS, "L3", "high", False, None),
    ("uae.default_value_aed", 1000, _AE_EMX, "L1", "high", False, None),
    ("uae.cepa_preferential", True, _AE_CEPA, "L1", "high", False, None),
    ("uae.who_pays", "recipient_at_pickup", _AE_WHO_PAYS, "L2", "high", False, None),
    # --- Australia (duties-taxes.md §5) ---
    ("au.gst_pct", 10, _AU_ATO_LVIG, "L1", "high", False, None),
    ("au.deminimis_aud", 1000, _AU_ATO_IMPORT, "L1", "high", False, None),
    ("au.lvig_vendor_collection", True, _AU_ATO_LVIG, "L1", "high", False, date(2018, 7, 1)),
    ("au.gst_registration_threshold_aud", 75000, _AU_ATO_GST, "L1", "high", False, None),
    ("au.ipc_fee_1k_10k_minor", 5000, _AU_IPC, "L1", "moderate", False, None),
    ("au.ipc_fee_10k_plus_minor", 15200, _AU_IPC, "L1", "moderate", False, None),
    ("au.ecta_preferential", True, _AU_ECTA, "L1", "high", False, date(2022, 12, 29)),
    ("au.ecta_coo_required", True, _AU_COO, "L1", "high", False, None),
    ("au.biosecurity_wood", "required_bicon", _AU_DAFF, "L1", "moderate", False, None),
    ("au.biosecurity_jute", "required_bicon", _AU_BICON, "L1", "moderate", False, None),
    # --- ITPS (itps-lane.md §4/§5, S.O. 659(E) via potoolsblog mirror) ---
    ("itps.portal_discount_pct", 2, _ITPS_SOP, "L3", "moderate", False, None),
    ("itps.us.first50_minor", 40000, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.us.addl50_minor", 3500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.uk.first50_minor", 20000, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.uk.addl50_minor", 2500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.uae.first50_minor", 18500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.uae.addl50_minor", 1500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.au.first50_minor", 39500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.au.addl50_minor", 4500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.us.cap_kg", 5, _ITPS_OM, "L2", "high", False, date(2026, 1, 1)),  # O10 resolved
    ("itps.au.cap_kg", 2, _ITPS_OM, "L1", "high", False, None),
    ("itps.canada.cap_kg", 2, _ITPS_OM, "L1", "high", False, None),
    # --- EMS (ems-lane.md §4/§9/§11; rates L5 — Schedule I never public, C11) ---
    ("ems.portal_discount_pct", 1, _ITPS_SOP, "L3", "moderate", False, None),
    ("ems.delay_comp_pct", 5, _EMS_DOP, "L1", "high", False, None),
    ("ems.us.first250_minor", 86500, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.us.addl250_minor", 10000, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.uk.first250_minor", 86500, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.uk.addl250_minor", 10000, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.au.first250_minor", 63000, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.au.addl250_minor", 15500, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.insurance_first_200_minor", 1000, _EMS_SCHEDULE_IV, "L1", "high", False, None),
    ("ems.insurance_addl_100_minor", 600, _EMS_SCHEDULE_IV, "L1", "high", False, None),
    # --- forms / volumetric / KYC ---
    ("cn22.sdr_max", 300, _CN22_POSTALSTUDY, "L3", "high", False, None),
    # 1 SDR = ₹109.4194 (2024) ⇒ 300 SDR ≈ ₹32,800 — itps-lane.md §6; the SDR
    # value is AUTO-computed by the DNK portal (document-stack.md §10), the
    # exporter never enters it.  Stored in INR minor units (10942 paise).
    ("sdr.fx_minor_per_sdr", 10942, "data/05-itps-ems-lanes/itps-lane.md",
     "L3", "low", True, None),
    ("kyc.declared_value_minor", 2500000, _EMS_CLICKPOST, "L5", "low", True, None),
    ("volumetric.divisors", [4000, 5000, 6000], _EMS_CONFLICTS, "L5", "unverified", True, None),
    ("pbe.declaration_clusters", 6, _PBE_NTF104, "L1", "moderate", False, None),
    ("pbe.ecomm_columns", 5, _PBE_NTF104, "L1", "high", False, None),
    # --- transit (L5 ranges only — never points) ---
    ("itps.transit.us_days", [18, 28], _ITPS_TRANSIT, "L5", "low", True, None),
    ("itps.transit.uk_days", [16, 25], _ITPS_TRANSIT, "L5", "low", True, None),
    ("itps.transit.uae_days", [14, 21], _ITPS_TRANSIT, "L5", "low", True, None),
    ("itps.transit.au_days", [18, 28], _ITPS_TRANSIT, "L5", "low", True, None),
    ("ems.transit.us_days", [5, 14], _EMS_CLICKPOST, "L5", "low", True, None),
    ("ems.transit.uk_days", [4, 14], _EMS_CLICKPOST, "L5", "low", True, None),
    ("ems.transit.uae_days", [3, 8], _EMS_CLICKPOST, "L5", "low", True, None),
    ("ems.transit.au_days", [5, 14], _EMS_CLICKPOST, "L5", "low", True, None),
    # --- payment rails (vendor-published; ranges/estimates labelled) ---
    ("razorpay.intl_cards_fee_pct", 3, _RAZORPAY, "L3", "moderate", False, None),
    ("razorpay.bank_transfer_fee_pct", 1, _RAZORPAY, "L3", "moderate", False, None),
    ("wise.conversion_fee_range_pct", [1.6, 1.7], _WISE_REVIEW, "L4", "low", True, None),
    ("wise.efirc_fee_minor", 200, _WISE_HELP, "L3", "moderate", False, None),
    ("paypal.allin_fee_range_pct", [7, 8], _PAYPAL_FEES, "L3", "low", True, None),
    ("etsy.payoneer_total_fee_range_pct", [12, 15], _ETSY_FEES, "L4", "low", True, None),
    # --- FEMA / incentives ---
    ("fema.realisation_months", 9, _FEMA_9MO, "L2", "high", False, date(2026, 6, 5)),
    ("fema.relaxation_months", 15, _FEMA_15MO, "L1", "high", False, date(2026, 3, 31)),
    ("rodtep.not_cash", True, _RODTEP_SCRIP, "L1", "high", False, None),
    ("rodtep.scrip_discount_range_pct", [3, 8], _RODTEP_DISCOUNT, "L5", "low", True, None),
    # --- bilingual UI labels (pinned by todo 11's preview gate) ---
    ("labels.estimate.hi", "अनुमानित", _LABELS_SRC, "L2", "high", False, None),
    ("labels.estimate.kn", "ಅಂದಾಜು", _LABELS_SRC, "L2", "high", False, None),
    ("labels.estimate.en", "estimate", _LABELS_SRC, "L2", "high", False, None),
    ("labels.please.hi", "कृपया", _LABELS_SRC, "L2", "high", False, None),
    ("labels.please.kn", "ದಯವಿಟ್ಟು", _LABELS_SRC, "L2", "high", False, None),
    ("labels.source.hi", "स्रोत", _LABELS_SRC, "L2", "high", False, None),
    ("labels.source.kn", "ಮೂಲ", _LABELS_SRC, "L2", "high", False, None),
    ("labels.source.en", "source", _LABELS_SRC, "L2", "high", False, None),
    ("labels.confirm.hi", "कृपया पुष्टि करें", _LABELS_SRC, "L2", "high", False, None),
    ("labels.confirm.kn", "ದಯವಿಟ್ಟು ದೃಢೀಕರಿಸಿ", _LABELS_SRC, "L2", "high", False, None),
    # --- prompt templates: missing-field guides ---
    ("prompt.missing.consignee_details.hi",
     "कृपया {label} प्रदान करें — उदाहरण: {example}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.missing.consignee_details.en",
     "Please provide {label} — example: {example}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.missing.destination_country.hi",
     "कृपया {label} प्रदान करें — उदाहरण: {example}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.missing.destination_country.en",
     "Please provide {label} — example: {example}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.missing.product_description.hi",
     "कृपया {label} प्रदान करें — उदाहरण: {example}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.missing.product_description.en",
     "Please provide {label} — example: {example}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.missing.generic.hi",
     "कृपया {label} ({field_key}) प्रदान करें",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.missing.generic.en",
     "Please provide {label} ({field_key})",
     _PBE_NTF104, "L2", "high", False, None),
    # --- prompt templates: error-field guides ---
    ("prompt.error.generic.hi",
     "कृपया {field} को सही करें: {message}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.error.generic.en",
     "Please correct {field}: {message}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.error.document_rules.hi",
     "कृपया {field} दस्तावेज़ नियम त्रुटि को ठीक करें: {message}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.error.document_rules.en",
     "Please fix {field} document rule error: {message}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.error.destination_country.hi",
     "कृपया {field} गंतव्य देश कोड को सही करें: {message}",
     _PBE_NTF104, "L2", "high", False, None),
    ("prompt.error.destination_country.en",
     "Please correct {field} destination country code: {message}",
     _PBE_NTF104, "L2", "high", False, None),
]


def _import_flags(session: object) -> tuple[int, int]:
    if len(FLAG_SPECS) < 40:
        raise RuntimeError(f"config-flag gate failed: pack yields {len(FLAG_SPECS)} flags (< 40)")
    for key, value, url, level, conf, est, eff in FLAG_SPECS:
        session.add(ConfigFlag(  # type: ignore[attr-defined]
            flag_key=key, flag_value=value,
            source_url=url, source_level=level, confidence=conf, is_estimate=est,
            effective_from=eff or SNAPSHOT_DATE, verified_at=VERIFIED_AT,
        ))
    n_labels = sum(1 for spec in FLAG_SPECS if spec[0].startswith("labels."))
    return len(FLAG_SPECS), n_labels
