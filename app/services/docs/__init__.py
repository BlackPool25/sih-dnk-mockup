"""Document generation pipeline (todo 11).

Deterministic-only pipeline: a ``DocumentData`` is assembled strictly from
DB lookups (``app.services.db_tools``), the validated Shipment keys, and CLI
order fields — never from free-form LLM text.  ``DocumentData.model_validate``
plus ``missing_required`` (completeness against ``pbe_field_schemas.required``)
are the ONLY validity gates; the LLM is never the validator.

The rendered forms are ENGLISH.  Hindi/Kannada labels live only in the
preview/confirmation UI (``build_preview``) — never in the PDF.

Public surface:
    DocumentData           — Pydantic document data (document.py)
    build_document_data    — assemble a DocumentData from a validated Shipment
    render                 — gate -> Jinja2 -> WeasyPrint -> sha256 -> documents row
    build_preview          — form summary + hi/kn confirm labels (UI only)
    build_html             — the form HTML (exposed for tests)
"""

from app.services.docs.document import DocumentData, build_document_data
from app.services.docs.renderer import build_html, build_preview, render

__all__ = [
    "DocumentData",
    "build_document_data",
    "build_html",
    "build_preview",
    "render",
]
