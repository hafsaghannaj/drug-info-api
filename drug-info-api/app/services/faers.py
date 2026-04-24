"""OpenFDA FAERS (adverse event) client.

Endpoint: https://api.fda.gov/drug/event.json
Docs:     https://open.fda.gov/apis/drug/event/

FAERS = FDA Adverse Event Reporting System.
Returns post-market safety reports submitted by patients, providers, and manufacturers.
"""
import httpx
from app.config import get_settings
from app.db.database import cache_get, cache_set

settings = get_settings()

_CLIENT: httpx.AsyncClient | None = None

# Minimum reports threshold — suppress results for drugs with very few reports
# to avoid surfacing noise from single case reports out of context.
_MIN_REPORTS = 5


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


async def get_adverse_events(
    drug_name: str, limit: int = 20
) -> dict:
    """
    Fetch top adverse event terms for a drug from OpenFDA FAERS.

    Returns:
      {
        "total_reports": int,
        "reactions": [{"term": str, "count": int, "pct_of_reports": float}, ...],
        "serious_outcomes": {"death": int, "hospitalization": int, "life_threatening": int, ...},
        "routes": [{"route": str, "count": int}, ...],
      }

    Note on interpretation:
      FAERS counts are raw report counts, NOT incidence rates.
      A high count reflects reporting volume (influenced by drug popularity,
      label warnings, and media attention), not necessarily risk magnitude.
      Proportional reporting ratio (PRR) or reporting odds ratio (ROR) are
      required for signal detection — this endpoint returns raw counts only.
    """
    key = f"faers:{drug_name.lower().strip()}:{limit}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    result: dict = {
        "total_reports": 0,
        "reactions": [],
        "serious_outcomes": {},
        "routes": [],
        "data_caveat": (
            "FAERS counts are raw report volumes, not incidence rates. "
            "High counts reflect reporting activity, not necessarily risk magnitude. "
            "Signal detection requires PRR or ROR analysis against a comparator."
        ),
    }

    # ── 1. Total report count ─────────────────────────────────────────────────
    try:
        count_resp = await _client().get(
            "/drug/event.json",
            params={
                "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                "limit": 1,
            },
        )
        if count_resp.status_code == 200:
            meta = count_resp.json().get("meta", {}).get("results", {})
            result["total_reports"] = meta.get("total", 0)
    except httpx.HTTPError:
        pass

    if result["total_reports"] < _MIN_REPORTS:
        await cache_set(key, result, 3600)
        return result

    # ── 2. Top reaction terms ─────────────────────────────────────────────────
    try:
        rx_resp = await _client().get(
            "/drug/event.json",
            params={
                "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": limit,
            },
        )
        if rx_resp.status_code == 200:
            terms = rx_resp.json().get("results", [])
            total = result["total_reports"] or 1
            result["reactions"] = [
                {
                    "term": t["term"],
                    "count": t["count"],
                    "pct_of_reports": round(t["count"] / total * 100, 2),
                }
                for t in terms
            ]
    except httpx.HTTPError:
        pass

    # ── 3. Serious outcomes breakdown ─────────────────────────────────────────
    outcome_fields = {
        "death": "seriousnessdeath",
        "life_threatening": "seriousnesslifethreatening",
        "hospitalization": "seriousnesshospitalization",
        "disability": "seriousnessdisabling",
        "congenital_anomaly": "seriousnesscongenitalanomali",
        "other_serious": "seriousnessother",
    }
    outcomes: dict = {}
    for label, field in outcome_fields.items():
        try:
            out_resp = await _client().get(
                "/drug/event.json",
                params={
                    "search": (
                        f'patient.drug.medicinalproduct:"{drug_name}"'
                        f'+AND+{field}:1'
                    ),
                    "limit": 1,
                },
            )
            if out_resp.status_code == 200:
                meta = out_resp.json().get("meta", {}).get("results", {})
                outcomes[label] = meta.get("total", 0)
        except httpx.HTTPError:
            outcomes[label] = None
    result["serious_outcomes"] = outcomes

    # ── 4. Route of administration breakdown ─────────────────────────────────
    try:
        route_resp = await _client().get(
            "/drug/event.json",
            params={
                "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                "count": "patient.drug.drugadministrationroute.exact",
                "limit": 10,
            },
        )
        if route_resp.status_code == 200:
            result["routes"] = [
                {"route": r["term"], "count": r["count"]}
                for r in route_resp.json().get("results", [])
            ]
    except httpx.HTTPError:
        pass

    await cache_set(key, result, 3600)
    return result


async def get_adverse_events_by_rxcui(rxcui: str, drug_name: str, limit: int = 20) -> dict:
    """Try FAERS search by RxCUI first (more precise), fall back to name."""
    key = f"faers_rxcui:{rxcui}:{limit}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    # OpenFDA FAERS supports openfda.rxcui field
    try:
        resp = await _client().get(
            "/drug/event.json",
            params={
                "search": f"patient.drug.openfda.rxcui:{rxcui}",
                "limit": 1,
            },
        )
        if resp.status_code == 200:
            total = resp.json().get("meta", {}).get("results", {}).get("total", 0)
            if total >= _MIN_REPORTS:
                # Enough data via RxCUI — re-run full query with RxCUI
                result = await _get_by_field(
                    f"patient.drug.openfda.rxcui:{rxcui}", limit
                )
                result["search_field"] = "rxcui"
                await cache_set(key, result, 3600)
                return result
    except httpx.HTTPError:
        pass

    # Fallback to name-based
    return await get_adverse_events(drug_name, limit)


async def _get_by_field(search_expr: str, limit: int) -> dict:
    """Run the full 4-part FAERS query against an arbitrary search expression."""
    result: dict = {
        "total_reports": 0,
        "reactions": [],
        "serious_outcomes": {},
        "routes": [],
        "data_caveat": (
            "FAERS counts are raw report volumes, not incidence rates. "
            "Signal detection requires PRR or ROR analysis against a comparator."
        ),
    }
    try:
        r = await _client().get(
            "/drug/event.json",
            params={"search": search_expr, "limit": 1},
        )
        if r.status_code == 200:
            result["total_reports"] = (
                r.json().get("meta", {}).get("results", {}).get("total", 0)
            )
    except httpx.HTTPError:
        return result

    if result["total_reports"] < _MIN_REPORTS:
        return result

    try:
        rx_resp = await _client().get(
            "/drug/event.json",
            params={
                "search": search_expr,
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": limit,
            },
        )
        if rx_resp.status_code == 200:
            terms = rx_resp.json().get("results", [])
            total = result["total_reports"] or 1
            result["reactions"] = [
                {
                    "term": t["term"],
                    "count": t["count"],
                    "pct_of_reports": round(t["count"] / total * 100, 2),
                }
                for t in terms
            ]
    except httpx.HTTPError:
        pass

    return result
