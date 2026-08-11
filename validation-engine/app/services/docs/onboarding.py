"""Onboarding kit generator — IEC + AD-code + readiness routing for exporters.

Public surface:
    generate_onboarding_kit — returns structured JSON with 5 sections
"""

from __future__ import annotations


def generate_onboarding_kit(
    pan: str | None = None,
    has_bank_account: bool = False,
    firm_name: str | None = None,
    bank_name: str | None = None,
    bank_account: str | None = None,
    ifsc: str | None = None,
    iec: str | None = None,
    path: str = "individual",
) -> dict:
    """Return a structured onboarding kit with 5 sections.

    All values are demo/mock — no real banking data and no external API calls.
    """
    # ── Section 1: IEC registration form (ANF-2A) ────────────────────────
    is_collective = path == "collective"
    pan_label_hi = "पैन" if not is_collective else "समूह पैन"
    firm_label_hi = "फर्म का नाम" if not is_collective else "SHG/सहकारी का नाम"
    firm_label_en = "Firm Name" if not is_collective else "SHG/Co-operative Name"
    bank_label_hi = "बैंक खाता" if not is_collective else "SHG/सहकारी बैंक खाता"
    bank_label_en = "Bank Account" if not is_collective else "SHG/Co-operative Bank Account"

    iec_form: dict = {
        "form_id": "ANF-2A",
        "fields": [
            {
                "field_key": "pan",
                "label_hi": pan_label_hi,
                "label_en": "PAN" if not is_collective else "Group PAN",
                "value": pan,
                "required": True,
            },
            {
                "field_key": "firm_name",
                "label_hi": firm_label_hi,
                "label_en": firm_label_en,
                "value": firm_name,
                "required": True,
            },
            {
                "field_key": "bank_account",
                "label_hi": bank_label_hi,
                "label_en": bank_label_en,
                "value": bank_account,
                "required": True,
            },
            {
                "field_key": "address",
                "label_hi": "पता",
                "label_en": "Address",
                "value": None,
                "required": True,
            },
            {
                "field_key": "aadhaar",
                "label_hi": "आधार",
                "label_en": "Aadhaar",
                "value": None,
                "required": True,
            },
            {
                "field_key": "email",
                "label_hi": "ईमेल",
                "label_en": "Email",
                "value": None,
                "required": True,
            },
            {
                "field_key": "phone",
                "label_hi": "फोन",
                "label_en": "Phone",
                "value": None,
                "required": True,
            },
        ],
    }

    # ── Section 2: AD-code letter ────────────────────────────────────────
    ad_code_letter: dict = {
        "bank_name": bank_name,
        "account_number": bank_account,
        "ifsc": ifsc,
        "iec": iec,
        "branch_address": None,
    }

    # ── Section 3: onboarding checklist ──────────────────────────────────
    checklist: list[dict] = [
        {
            "step_number": 0,
            "description_hi": "चालू खाता सत्यापित करें — व्यवसाय चालू खाता मौजूद है की पुष्टि करें",
            "description_en": "Current account check — verify business current account exists",
            "status": "pending",
            "action_type": "bank_visit",
            "required_docs": ["bank_statement", "passbook"],
        },
        {
            "step_number": 1,
            "description_hi": "बैंक सहायक से AD-कोड खाते की पुष्टि कराएं (§5A)",
            "description_en": "Confirm AD-code account with bank Sahayak (§5A bank-confirmation gate)",
            "status": "pending",
            "action_type": "bank_visit",
            "required_docs": ["iec", "pan_card", "firm_proof"],
        },
        {
            "step_number": 2,
            "description_hi": "ICEGATE पोर्टल पर आधार ई-हस्ताक्षर करें",
            "description_en": "ICEGATE Aadhaar e-sign",
            "status": "pending",
            "action_type": "otp",
            "required_docs": ["aadhaar_linked_mobile"],
        },
        {
            "step_number": 3,
            "description_hi": "पैन सत्यापन — DGFT/IT विभाग से PAN को सत्यापित करें",
            "description_en": "PAN verification — verify PAN with DGFT/Income Tax department",
            "status": "pending",
            "action_type": "otp",
            "required_docs": ["pan_card"],
        },
        {
            "step_number": 4,
            "description_hi": "IEC आवेदन फॉर्म (ANF-2A) भरें और अपलोड करें",
            "description_en": "Fill and upload IEC application form (ANF-2A)",
            "status": "pending",
            "action_type": "upload",
            "required_docs": ["pan_card", "aadhaar_card", "bank_certificate", "address_proof"],
        },
        {
            "step_number": 5,
            "description_hi": "डिजिटल हस्ताक्षर प्रमाणपत्र (DSC) अपलोड करें",
            "description_en": "Upload Digital Signature Certificate (DSC)",
            "status": "pending",
            "action_type": "upload",
            "required_docs": ["dsc_token"],
        },
        {
            "step_number": 6,
            "description_hi": "DGFT द्वारा IEC आवेदन की स्वीकृति की प्रतीक्षा करें",
            "description_en": "Wait for DGFT approval of IEC application",
            "status": "pending",
            "action_type": "sign",
            "required_docs": [],
        },
    ]

    # ── Section 4: readiness routing ─────────────────────────────────────
    readiness_routing: dict = {
        "has_pan": pan is not None,
        "has_bank_account": has_bank_account,
        "path": path,
        "explanation_hi": (
            "व्यक्तिगत पथ" if path == "individual" else "सामूहिक पथ (SHG/सहकारी)"
        ),
        "explanation_en": (
            "Individual exporter path" if path == "individual" else "Collective path (SHG/Co-operative)"
        ),
    }

    # ── Section 5: scoreboard ────────────────────────────────────────────
    scoreboard: dict = {
        "completed": 0,
        "total": 7,
        "ready": False,
        "next_step_hi": "चालू खाता सत्यापित करें",
        "next_step_en": "Verify current account",
    }

    return {
        "iec_form": iec_form,
        "ad_code_letter": ad_code_letter,
        "checklist": checklist,
        "readiness_routing": readiness_routing,
        "scoreboard": scoreboard,
    }


__all__ = ["generate_onboarding_kit"]
