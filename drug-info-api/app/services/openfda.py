"""OpenFDA drug label client.

Endpoint: https://api.fda.gov/drug/label.json
Docs:     https://open.fda.gov/apis/drug/label/

Rate limits:
  - Without API key: 240 req/min, 1000/day
  - With API key:    1000 req/min
Set OPENFDA_API_KEY in .env to raise the limit.
"""
import httpx
from app.config import get_settings
from app.db.database import cache_get, cache_set

settings = get_settings()

_CLIENT: httpx.AsyncClient | None = None


def _client() -> httpx.AsyncClient:
    global _CLIENT
    if _CLIENT is None:
        params = {}
        if settings.openfda_api_key:
            params["api_key"] = settings.openfda_api_key
        _CLIENT = httpx.AsyncClient(
            base_url=settings.openfda_base_url,
            timeout=15.0,
            params=params,
        )
    return _CLIENT


def _first(lst: list | None, default: str | None = None) -> str | None:
    """Return first non-empty element of a list field from an FDA label."""
    if not lst:
        return default
    for item in lst:
        if item and item.strip():
            return item.strip()
    return default


async def get_label(drug_name: str) -> dict | None:
    """
    Fetch one structured product label by generic or brand name.
    Returns the raw OpenFDA label result dict, or None if not found.
    """
    key = f"fda_label:{drug_name.lower().strip()}"
    cached = await cache_get(key)
    if cached is not None:
        return cached if cached else None

    for search_field in (
        "openfda.generic_name",
        "openfda.brand_name",
        "openfda.substance_name",
    ):
        try:
            resp = await _client().get(
                "/drug/label.json",
                params={
                    "search": f'{search_field}:"{drug_name}"',
                    "limit": 1,
                },
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    label = results[0]
                    await cache_set(key, label, settings.cache_ttl_label_seconds)
                    return label
        except httpx.HTTPStatusError:
            continue

    # Cache negative result (empty dict = not found)
    await cache_set(key, {}, settings.cache_ttl_label_seconds)
    return None


async def parse_drug_info(label: dict) -> dict:
    """
    Extract structured fields from a raw FDA label dict.
    Returns a flat dict matching the DrugSummary schema.
    """
    openfda = label.get("openfda", {})

    # Dosage forms
    dosage_forms: list[dict] = []
    for form in openfda.get("dosage_form", []):
        dosage_forms.append(
            {
                "form": form,
                "strengths": openfda.get("strength", []),
                "route": ", ".join(openfda.get("route", [])),
            }
        )

    # Black box warnings
    bbw_text = _first(label.get("boxed_warning"))
    bbws = [{"text": bbw_text}] if bbw_text else []

    return {
        "generic_name": _first(openfda.get("generic_name"), drug_name_fallback(label)),
        "brand_names": openfda.get("brand_name", []),
        "drug_class": _first(openfda.get("pharm_class_cs"))
        or _first(openfda.get("pharm_class_moa")),
        "pharmacologic_class": (
            openfda.get("pharm_class_cs", [])
            + openfda.get("pharm_class_moa", [])
            + openfda.get("pharm_class_epc", [])
        ),
        "manufacturer": _first(openfda.get("manufacturer_name")),
        "route": openfda.get("route", []),
        "dosage_forms": dosage_forms,
        "indications": _first(label.get("indications_and_usage")),
        "black_box_warnings": bbws,
        "controlled_substance": _first(label.get("drug_abuse_and_dependence")),
    }


async def parse_dosing(label: dict) -> dict:
    """
    Extract dosing information from an FDA label.
    Returns a dict matching the DosingResponse schema fields (minus computed/weight fields).
    """
    dosing_text = _first(label.get("dosage_and_administration"))
    renal_text = None
    hepatic_text = None

    # FDA labels sometimes put renal dosing in dosage_and_administration
    # or in a separate warnings section — capture both
    for section in ("dosage_and_administration", "warnings_and_cautions", "warnings"):
        text = _first(label.get(section))
        if text and "renal" in text.lower() and renal_text is None:
            renal_text = text
        if text and "hepatic" in text.lower() and hepatic_text is None:
            hepatic_text = text

    return {
        "full_dosing_text": dosing_text,
        "pregnancy_category": _first(label.get("pregnancy")),
        "_renal_raw": renal_text,
        "_hepatic_raw": hepatic_text,
    }


def drug_name_fallback(label: dict) -> str:
    """Best-effort drug name when openfda fields are sparse."""
    for key in ("id", "set_id"):
        val = label.get(key)
        if val:
            return val
    return "Unknown"
