"""NLM RxNav / RxNorm client.

Free, no API key required.  Rate limit: ~20 req/s.
Docs: https://lhncbc.nlm.nih.gov/RxNav/APIs/
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
            base_url=settings.rxnav_base_url,
            timeout=10.0,
            headers={"Accept": "application/json"},
        )
    return _CLIENT


# ── RxCUI lookup ──────────────────────────────────────────────────────────────

async def get_rxcui(drug_name: str) -> str | None:
    """Resolve a drug name → RxCUI (ingredient-level)."""
    key = f"rxcui:{drug_name.lower().strip()}"
    cached = await cache_get(key)
    if cached is not None:
        return cached.get("rxcui")

    resp = await _client().get(
        "/rxcui.json",
        params={"name": drug_name, "search": "1"},
    )
    resp.raise_for_status()
    data = resp.json()
    ids: list[str] = data.get("idGroup", {}).get("rxnormId") or []
    rxcui = ids[0] if ids else None

    # Fallback: approximate match
    if rxcui is None:
        resp2 = await _client().get(
            "/approximateTerm.json",
            params={"term": drug_name, "maxEntries": 1},
        )
        resp2.raise_for_status()
        candidates = (
            resp2.json()
            .get("approximateGroup", {})
            .get("candidate", [])
        )
        if candidates:
            rxcui = candidates[0].get("rxcui")

    await cache_set(key, {"rxcui": rxcui}, settings.cache_ttl_rxcui_seconds)
    return rxcui


async def get_rxcuis_bulk(names: list[str]) -> dict[str, str | None]:
    """Resolve multiple drug names concurrently."""
    import asyncio
    results = await asyncio.gather(*[get_rxcui(n) for n in names])
    return dict(zip(names, results))


# ── Drug search ───────────────────────────────────────────────────────────────

async def search_drugs(query: str, max_results: int = 20) -> list[dict]:
    """Search drug names via RxNorm spelling suggestions + drugs endpoint."""
    key = f"search:{query.lower().strip()}:{max_results}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    resp = await _client().get(
        "/drugs.json",
        params={"name": query},
    )
    resp.raise_for_status()
    concept_group = resp.json().get("drugGroup", {}).get("conceptGroup", [])

    results: list[dict] = []
    for group in concept_group:
        tty = group.get("tty", "")
        for prop in group.get("conceptProperties", []):
            results.append(
                {
                    "rxcui": prop.get("rxcui"),
                    "name": prop.get("name"),
                    "synonym": prop.get("synonym"),
                    "tty": tty,
                }
            )
            if len(results) >= max_results:
                break
        if len(results) >= max_results:
            break

    await cache_set(key, results, settings.cache_ttl_search_seconds)
    return results


# ── Drug-drug interactions ────────────────────────────────────────────────────

async def get_interactions(rxcuis: list[str]) -> list[dict]:
    """
    Fetch drug-drug interactions for a list of RxCUIs.

    Uses NLM Drug Interaction API which aggregates:
      - ONCHigh (clinical decision support)
      - DrugBank
    Returns normalised list of interaction dicts.
    """
    if len(rxcuis) < 2:
        return []

    key = f"interactions:{'+'.join(sorted(rxcuis))}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    resp = await _client().get(
        "/interaction/list.json",
        params={"rxcuis": " ".join(rxcuis)},
    )
    # NLM returns 404 when no interactions exist — treat as empty, not an error
    if resp.status_code == 404:
        await cache_set(key, [], settings.cache_ttl_interaction_seconds)
        return []
    resp.raise_for_status()
    data = resp.json()

    interactions: list[dict] = []
    for group in data.get("fullInteractionTypeGroup", []):
        source = group.get("sourceName", "Unknown")
        for itype in group.get("fullInteractionType", []):
            concepts = {
                c["rxcui"]: c["name"]
                for c in itype.get("minConcept", [])
            }
            for pair in itype.get("interactionPair", []):
                pair_concepts = pair.get("interactionConcept", [])
                d1 = pair_concepts[0]["minConceptItem"] if len(pair_concepts) > 0 else {}
                d2 = pair_concepts[1]["minConceptItem"] if len(pair_concepts) > 1 else {}
                interactions.append(
                    {
                        "drug_1": d1.get("name", ""),
                        "drug_2": d2.get("name", ""),
                        "rxcui_1": d1.get("rxcui"),
                        "rxcui_2": d2.get("rxcui"),
                        "severity": pair.get("severity", "N/A"),
                        "description": pair.get("description", ""),
                        "source": source,
                    }
                )

    await cache_set(key, interactions, settings.cache_ttl_interaction_seconds)
    return interactions


async def get_interactions_for_single(rxcui: str) -> list[dict]:
    """All known interactions for one drug (NLM single-drug endpoint)."""
    key = f"interaction_single:{rxcui}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    resp = await _client().get(f"/interaction/interaction.json?rxcui={rxcui}")
    # NLM returns 404 when no interactions exist — treat as empty, not an error
    if resp.status_code == 404:
        await cache_set(key, [], settings.cache_ttl_interaction_seconds)
        return []
    resp.raise_for_status()
    data = resp.json()

    interactions: list[dict] = []
    for group in data.get("interactionTypeGroup", []):
        source = group.get("sourceName", "Unknown")
        for itype in group.get("interactionType", []):
            for pair in itype.get("interactionPair", []):
                pair_concepts = pair.get("interactionConcept", [])
                d1 = pair_concepts[0]["minConceptItem"] if len(pair_concepts) > 0 else {}
                d2 = pair_concepts[1]["minConceptItem"] if len(pair_concepts) > 1 else {}
                interactions.append(
                    {
                        "drug_1": d1.get("name", ""),
                        "drug_2": d2.get("name", ""),
                        "rxcui_1": d1.get("rxcui"),
                        "rxcui_2": d2.get("rxcui"),
                        "severity": pair.get("severity", "N/A"),
                        "description": pair.get("description", ""),
                        "source": source,
                    }
                )

    await cache_set(key, interactions, settings.cache_ttl_interaction_seconds)
    return interactions
