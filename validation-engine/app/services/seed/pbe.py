"""PBE-III/IV field-schema seeds (todo 7) — the official column labels and
declaration wording VERBATIM from CBIC Notification No. 07/2026-Customs
(N.T.), 15-Jan-2026 (data/06-legal-sources/notification-07-2026-customs).
This module is data-heavy by design.
"""

from __future__ import annotations

from app.models import PbeFieldSchema
from app.services.seed._common import DATA_DIR, SNAPSHOT_DATE, VERIFIED_AT

PBE_FIELDS_FILE = DATA_DIR / "02-dnk-documents" / "forms-pbe" / "pbe-iii-iv-fields.md"

# --- pbe -----------------------------------------------------------------------
#
# Field schemas for Forms PBE-III and PBE-IV as SUBSTITUTED by CBIC
# Notification No. 07/2026-Customs (N.T.), 15-Jan-2026 — the primary document
# is data/06-legal-sources/notification-07-2026-customs.{pdf,txt}.  The
# sections, column labels and declaration wording below are VERBATIM from that
# Notification (the .txt is an OCR render: "poslal"→"postal",
# "publiested"→"published", "l5"→"15", etc. were cleaned, but the column
# labels are kept in their official form).
#
# Only fields with a REAL data source in DocumentData are marked required:
# consignee_details, product_description, cth, quantity_unit, gross_weight,
# net_weight (the six extraction-contract fields) and assessable_value
# (value_minor).  Everything else renders "—" — the form is honest about what
# the pipeline does not know (the exporter fills those at submission).

PBE_SOURCE_LEVEL = {"high": "L1", "moderate": "L2"}
_PBE_NTF07 = "data/06-legal-sources/notification-07-2026-customs.pdf"


def _pbe_rows() -> list[PbeFieldSchema]:
    """Official PBE-III/IV field schemas (Notification No. 07/2026-Customs)."""
    rows: list[PbeFieldSchema] = []

    def add(
        form: str, section: str, key: str, label: str, required: bool,
        vtype: str, validation: str, options: dict | None = None, conf: str = "high",
    ) -> None:
        rows.append(PbeFieldSchema(
            form_type=form, section=section, field_key=key, label=label,
            required=required, value_type=vtype, validation=validation, options=options,
            source_url=_PBE_NTF07, source_level=PBE_SOURCE_LEVEL[conf],
            confidence=conf, is_estimate=False,
            effective_from=SNAPSHOT_DATE, verified_at=VERIFIED_AT,
        ))

    # --- Header (the official 9-field header block) ---------------------------
    header = [
        ("boe_no", "Bill of Export No. and date", False, "auto",
         "System-generated on submission (Article ID + PBE number pop-up)"),
        ("fpo_code", "Foreign Post Office code", False, "string",
         "Code of the Board-appointed Foreign Post Office mapped to the booking post office"),
        ("exporter_name", "Name of Exporter", False, "string",
         "Auto-populated from DGFT IEC validation (name, address, city, pincode, PAN)"),
        ("exporter_address", "Address of Exporter", False, "string",
         "Auto-populated from DGFT IEC validation (name, address, city, pincode, PAN)"),
        ("iec", "IEC", False, "string",
         "10-char alphanumeric, validated live against DGFT; booking disabled if suspended"),
        ("state_code", "State Code", False, "string", "Exporter's state code"),
        ("gstin_or_as_applicable", "GSTIN or as applicable", False, "string",
         "15-char GSTIN; not uniformly mandatory — booking gates on ≥1 of IEC/GSTIN"),
        ("ad_code", "AD code (if Applicable)", False, "string",
         "14-char AD code; required on ICEGATE for electronic claims"),
        ("customs_broker_license_no", "Customs Broker License No.", False, "string",
         "Details of authorized agent — Customs Broker License No. (CBLR 2018)"),
        ("agent_name_address", "Name and address", False, "string",
         "Details of authorized agent — name and address"),
    ]
    # --- Details of parcel (columns common to both forms) ---------------------
    parcel = [
        ("si_no", "SI. No", False, "number", "Line number of the item in the consignment"),
        ("consignee_details", "Name and Address", True, "string",
         "Consignee name and address (postcode validated; in-portal lookup)"),
        ("destination_country", "Country of destination", False, "string",
         "ISO2 country code of destination"),
        ("product_description", "Description", True, "string",
         "No vague descriptions — description↔HS mismatch is a documented error"),
        ("cth", "CTH", True, "string", "Customs Tariff Heading (HS/CTH code per item)"),
        ("quantity_unit", "Quantity / Unit (pieces, liters, kgs., meters, Pairs etc.)",
         True, "number", "Quantity with unit — pieces, liters, kgs., meters, Pairs etc."),
        ("invoice_no_date", "Invoice No. and date", False, "string",
         "Invoice number and date of the parcel item"),
        ("gross_weight", "Gross", True, "number", "Weight of parcel with packaging"),
        ("net_weight", "Net", True, "number", "Product weight (net of packaging)"),
    ]
    # PBE-III only — E-commerce particulars (5 official columns).
    ecomm = [
        ("ecomm_operator_gstin", "GSTIN of E-commerce operator", False, "string",
         "GSTIN of the marketplace operator — not the artisan's own"),
        ("ecomm_url", "URL (Name) of website", False, "url",
         "Marketplace/website URL where the order was placed"),
        ("ecomm_payment_txn_id", "Payment transaction ID", False, "string",
         "Electronic payment reference — the order→payment binding key"),
        ("ecomm_sku_no", "SKU No.", False, "string",
         "Marketplace SKU / product identifier"),
        ("ecomm_postal_tracking", "Postal Tracking Number", False, "string",
         "The article's S10 postal tracking number once generated"),
    ]
    # PBE-IV only — Postal Tracking number (PBE-IV = other postal exports).
    postal_tracking = [
        ("postal_tracking_number", "Postal Tracking number", False, "string",
         "The article's S10 postal tracking number once generated"),
    ]
    # --- Assessable value under section 14 (of the Customs Act, 1962) ---------
    assessable = [
        ("fob_value", "FOB", False, "money", "FOB value of the goods"),
        ("currency", "Currency", False, "string",
         "Currency of the invoice (INR when the declared value is in INR)"),
        ("exchange_rate", "Exchange rate", False, "number",
         "CBIC-notified exchange rate for the currency"),
        ("amount_inr", "Amount in INR", False, "money",
         "Amount in INR after conversion at the exchange rate"),
        ("hs_code", "H.S code", False, "string", "H.S code of the item"),
        ("tax_invoice_no_date", "Invoice no. and date", False, "string",
         "Details of Tax Invoice or commercial invoice — invoice no. and date"),
        ("si_no_item", "SI. No of item in invoice", False, "number",
         "Details of Tax Invoice or commercial invoice — line number in the invoice"),
        ("assessable_value", "Value", True, "money",
         "Value of the item — assessable value under section 14 of the Customs Act, 1962"),
    ]
    # --- Details of Duty/Tax --------------------------------------------------
    duty = [
        ("export_duty_rate", "Export duty Rate", False, "number", "Export duty rate (%)"),
        ("export_duty_amount", "Export duty Amount", False, "money", "Export duty amount"),
        ("cess_rate", "Cess Rate", False, "number", "Cess rate (%)"),
        ("cess_amount", "Cess Amount", False, "money", "Cess amount"),
        ("igst_rate", "IGST (if applicable) Rate", False, "number", "IGST rate (%)"),
        ("igst_amount", "IGST (if applicable) Amount", False, "money", "IGST amount"),
        ("comp_cess_rate", "Compensation cess (if applicable) Rate", False, "number",
         "Compensation cess rate (%)"),
        ("comp_cess_amount", "Compensation cess (if applicable) Amount", False, "money",
         "Compensation cess amount"),
        ("lut_bond", "LUT/bond details (if applicable)", False, "string",
         "Letter of Undertaking / bond details"),
        ("gst_duties", "Duties", False, "money", "GST details — duties"),
        ("gst_cess", "Cess", False, "money", "GST details — cess"),
        ("total_duty_tax", "Total", False, "money", "Total duty/tax for the parcel"),
    ]
    # --- Additional details of parcel (duty drawback / export scheme) ---------
    additions = [
        ("invoice_no", "Invoice No.", False, "string", "Invoice number of the item", None),
        ("item_serial_no", "Item Serial No. in Invoice", False, "number",
         "Line number of the item in the invoice", None),
        ("ritc_itc_hs", "RITC code/ITC-HS code", False, "string",
         "8-digit ITC-HS code the claim keys on", None),
        ("dbk_serial_no", "DBK serial No.", False, "string",
         "Duty-Drawback schedule serial number (if claiming drawback)", None),
        ("drawback_quantity", "Drawback quantity", False, "number",
         "Quantity on which drawback is claimed", None),
        ("igst_payment_status", "IGST payment status (Yes/No)", False, "boolean",
         "Yes/No — governs IGST-refund vs drawback mutual exclusivity",
         {"values": ["Yes", "No"]}),
        ("end_use", "End use of item", False, "string", "End-use description", None),
        ("scheme_code", "Scheme code", False, "string",
         "The export scheme chosen", {"values": ["drawback", "rodtep", "rosctl"]}),
        ("add_freight", "Add Freight (₹/Y/N)", False, "string",
         "Whether freight is added to the assessable value", {"values": ["Y", "N"]}),
        ("nature_of_contract", "Nature of contract (CIF/CF/C&F/FOB)", False, "string",
         "Nature of the sale contract", {"values": ["CIF", "CF", "C&F", "FOB"]}),
    ]
    # --- Declarations (verbatim wording from Ntf 07/2026, Yes/No as applicable)
    zero_rate_decl = (
        "1. I/We declare that we intend to zero rate our exports under section 16 of "
        "Integrated Goods and Services Tax Act, 2017."
    )
    exemption_decl = (
        "2. I/We declare that the goods are exempted under Central Goods and Services "
        "Tax Act/State Goods and Services Tax Act/Union Territory Goods and Services "
        "Tax/Integrated Goods and Services Tax Act, 2017."
    )
    drawback_decl = (
        "3. I/We declare that I/we intend to claim Drawback under Sec. 75 of Customs "
        "Act, 1962 and Customs and Central Excise Duties Drawback Rules, 2011.\n"
        "(a) I/We declare that no input tax credit of the central goods and Services Tax or of the "
        "integrated Goods and Services Tax has been availed for any of the inputs or input services used "
        "in the manufacture of the export goods.\n"
        "(b) I/We declare that no refund of Integrated Goods and Service Tax paid on export goods shall "
        "be claimed.\n"
        "(c) I/We declare that CENVAT credit on the inputs or input services used in the manufacture of "
        "the export goods, has not been carried forward in terms of the Central Goods and Service Tax Act, "
        "2017.\n"
        "(d) I/We certify that I/We have complied with the conditions laid down in the said Rules and the "
        "conditions subject to which Drawback Rates are applicable."
    )
    rodtep_decl = (
        "4. I/We declare that I/we intend to claim RoDTEP (Remission of Duties and Taxes on Exported "
        "Products),\n"
        "(a) I/We undertake to abide by the provisions, including conditions, restrictions, exclusions "
        "and time-limits as provided under RoDTEP scheme, and relevant notifications, regulations, etc.\n"
        "(b) Any claim made in this Postal Bill of Export is not with respect to any duties or taxes or "
        "levies which are exempted or remitted or credited under any other mechanism outside RoDTEP.\n"
        "(c) I/We undertake to preserve and make available relevant documents relating to the exported "
        "goods for the purposes of audit in the manner and for the time period prescribed in the Customs "
        "Audit Regulations, 2018."
    )
    rosctl_decl = (
        "5. I/We declare that I/we intend to claim RoSCTL (Rebate of State and Central Taxes and "
        "Levies),\n"
        "(a) I/We undertake to abide by the provisions, including conditions, restrictions, exclusions "
        "and time-limits as provided under RoSCTL scheme, and relevant notifications, regulations, etc.\n"
        "(b) Any claim made in this Postal Bill of Export is not with respect to any duties or taxes or "
        "levies which are exempted or remitted or credited under any other mechanism outside RoSCTL.\n"
        "(c) I/We undertake to preserve and make available relevant documents relating to the exported "
        "goods for the purposes of audit in the manner and for the time period prescribed in the Customs "
        "Audit Regulations, 2018."
    )
    fema_decl = (
        "6. I/We undertake to abide by the provisions of Foreign Exchange Management Act, 1999, as "
        "amended from time to time, including realisation or repatriation of foreign exchange to or from "
        "India."
    )
    decls = [
        ("decl.zero_rating_s16_igst", zero_rate_decl,
         "Declaration that the supply is a zero-rated export (s.16 IGST)"),
        ("decl.exemption", exemption_decl,
         "Exemption declaration (CGST/SGST/UTGST/IGST)"),
        ("decl.drawback", drawback_decl,
         "Drawback declaration — 4 sub-declarations (a)–(d), verbatim wording"),
        ("decl.rodtep", rodtep_decl,
         "RoDTEP declaration — 3 sub-declarations (a)–(c)"),
        ("decl.rosctl", rosctl_decl,
         "RoSCTL declaration — 3 sub-declarations (a)–(c)"),
        ("decl.fema_undertaking", fema_decl,
         "FEMA 1999 undertaking — realisation/repatriation of export proceeds"),
    ]

    for form in ("PBE_III", "PBE_IV"):
        for key, label, req, vtype, val in header:
            add(form, "Header", key, label, req, vtype, val)
        for key, label, req, vtype, val in parcel:
            add(form, "Details of parcel", key, label, req, vtype, val)
        if form == "PBE_III":
            for key, label, req, vtype, val in ecomm:
                add(form, "Details of parcel", key, label, req, vtype, val)
        else:
            for key, label, req, vtype, val in postal_tracking:
                add(form, "Details of parcel", key, label, req, vtype, val)
        for key, label, req, vtype, val in assessable:
            add(form, "Assessable value", key, label, req, vtype, val)
        for key, label, req, vtype, val in duty:
            add(form, "Details of Duty/Tax", key, label, req, vtype, val)
        for key, label, req, vtype, val, options in additions:
            add(form, "Additional details of parcel", key, label, req, vtype, val, options)
        for key, label, val in decls:
            add(form, "Declarations", key, label, False, "boolean", val,
                {"values": ["Yes", "No", "NA"]})
    return rows


def _import_pbe(session: object) -> tuple[int, int]:
    rows = _pbe_rows()
    if len(rows) < 30:
        raise RuntimeError(f"PBE schema gate failed: {len(rows)} rows (< 30)")
    n3 = sum(1 for r in rows if r.form_type == "PBE_III")
    for r in rows:
        session.add(r)  # type: ignore[attr-defined]
    return n3, len(rows) - n3
