"""NLM DailyMed client.

Endpoint: https://dailymed.nlm.nih.gov/dailymed/services/v2/
Docs:     https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm

No API key required. Provides NIH-curated structured product labeling (SPL).
Used as a fallback / complement to OpenFDA for label text.
"""
import httpx
from app.config import get_settings
from app.db.database import cache_get, cache_set

settings = get_settings()

_CLIENT: httpx.AsyncClient | None = None


def _client() -> httpx.AsyncClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = httpx.AsyncClient(
            base_url=settings.dailymed_base_url,
            timeout=10.0,
            headers={"Accept": "application/json"},
        )
    return _CLIENT


async def search_spl(drug_name: str, limit: int = 5) -> list[dict]:
    """
    Search DailyMed SPL records by drug name.
    Returns list of {setid, title, published} dicts.
    """
    key = f"dailymed_search:{drug_name.lower().strip()}:{limit}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    resp = await _client().get(
        "/spls.json",
        params={"drug_name": drug_name, "limit": limit},
    )
    resp.raise_for_status()
    data = resp.json()
    results = [
        {
            "setid": item.get("setid"),
            "title": item.get("title"),
            "published": item.get("published_date"),  # DailyMed field is published_date
        }
        for item in data.get("data", [])
    ]
    await cache_set(key, results, settings.cache_ttl_search_seconds)
    return results


async def get_spl_sections(setid: str) -> dict:
    """
    Fetch all sections of a specific SPL record by setid.
    Returns {section_name: text} mapping for clinical sections.
    """
    key = f"dailymed_spl:{setid}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    resp = await _client().get(f"/spls/{setid}/sections.json")
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "")
    if "json" not in content_type:
        # DailyMed sections endpoint may redirect to HTML for some setids
        return {}
    data = resp.json()

    sections: dict = {}
    for section in data.get("data", {}).get("sections", []):
        name = section.get("title", "").strip()
        text = section.get("text", "").strip()
        if name and text:
            sections[name] = text

    await cache_set(key, sections, settings.cache_ttl_label_seconds)
    return sections


async def get_drug_ndc(drug_name: str) -> list[dict]:
    """
    Look up NDC codes and packaging info for a drug via DailyMed.
    Returns list of {ndc, packaging, labeler} dicts.
    """
    spls = await search_spl(drug_name, limit=3)
    ndcs: list[dict] = []
    for spl in spls:
        if not spl.get("setid"):
            continue
        try:
            resp = await _client().get(f"/spls/{spl['setid']}/ndcs.json")
            resp.raise_for_status()
            data = resp.json()
            # DailyMed NDC response: {"data": {"ndcs": [...], "title": ..., ...}}
            spl_data = data.get("data", {})
            for ndc_item in spl_data.get("ndcs", []):
                ndcs.append(
                    {
                        "ndc": ndc_item if isinstance(ndc_item, str) else ndc_item.get("ndc"),
                        "packaging": [],
                        "labeler": spl_data.get("title", ""),
                        "setid": spl["setid"],
                    }
                )
        except httpx.HTTPError:
            continue
    return ndcs
