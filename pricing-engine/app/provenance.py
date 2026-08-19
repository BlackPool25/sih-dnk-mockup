from datetime import date,datetime
from typing import Any

PROVENANCE_FIELDS = (
    "source_url",
    "source_level",
    "confidence",
    "is_estimate",
    "effective_from",
    "effective_to",
    "verified_at",
)

def _json_safe(value:Any)->Any:
    if isinstance(value,date|datetime):
        return value.isoformat()
    return value
def row_provenance(row:object)->dict[str,Any]:
    provenance:dict[str,Any]={}
    for field in PROVENANCE_FIELDS:
        value=getattr(row,field,None)
        if value is not None:
            provenance[field]=_json_safe(value)
    return provenance