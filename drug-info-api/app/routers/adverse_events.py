"""GET /v1/drug/{name}/adverse-events  — FAERS adverse event data
GET /v1/drug/{name}/dailymed          — DailyMed SPL sections + NDCs
"""
from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import AdverseEventsResponse, AdverseReaction, SeriousOutcomes, RouteCount, DailyMedResponse, SPLRecord
from app.services import rxnav, faers, dailymed

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/drug/{name}/adverse-events",
    response_model=AdverseEventsResponse,
    summary="Adverse event data from FDA FAERS",
    description=(
        "Returns post-market adverse event data from the FDA Adverse Event Reporting System "
        "(FAERS) via OpenFDA.\n\n"
        "**What FAERS is:**\n"
        "Voluntary + mandatory reports submitted by patients, healthcare providers, and "
        "manufacturers after a drug reaches market. It captures signals that may not have "
        "appeared in pre-approval clinical trials.\n\n"
        "**What FAERS is NOT:**\n"
        "- Not an incidence rate or risk estimate\n"
        "- High report counts reflect *reporting volume*, not necessarily high risk\n"
        "- No denominator (exposure data) is available in FAERS\n"
        "- Signal detection requires PRR/ROR analysis against a comparator population\n\n"
        "This endpoint returns: top reaction terms (MedDRA), serious outcome breakdown "
        "(deaths, hospitalizations, etc.), and route of administration distribution."
    ),
)
@limiter.limit("30/minute")
async def get_adverse_events(
    request: Request,
    name: str,
    limit: int = Query(20, ge=5, le=50, description="Number of top reaction terms to return"),
) -> AdverseEventsResponse:
    rxcui = await rxnav.get_rxcui(name)

    if rxcui:
        data = await faers.get_adverse_events_by_rxcui(rxcui, name, limit)
    else:
        data = await faers.get_adverse_events(name, limit)

    if data["total_reports"] == 0:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No FAERS reports found for '{name}'. "
                "Try the generic drug name (e.g. 'atorvastatin' not 'Lipitor')."
            ),
        )

    serious = data.get("serious_outcomes") or {}
    return AdverseEventsResponse(
        rxcui=rxcui,
        drug_name=name,
        total_reports=data["total_reports"],
        search_field=data.get("search_field", "name"),
        reactions=[AdverseReaction(**r) for r in data.get("reactions", [])],
        serious_outcomes=SeriousOutcomes(**serious) if serious else None,
        routes=[RouteCount(**r) for r in data.get("routes", [])],
        data_caveat=data.get("data_caveat", ""),
    )


@router.get(
    "/drug/{name}/dailymed",
    response_model=DailyMedResponse,
    summary="NLM DailyMed structured product labeling",
    description=(
        "Returns NIH DailyMed structured product label (SPL) data: "
        "label sections (indications, dosing, warnings, etc.) and NDC package codes.\n\n"
        "DailyMed is the official NIH repository of FDA-approved drug labeling. "
        "It is an independent source from OpenFDA and sometimes has more complete "
        "or more recent label text for generic products."
    ),
)
@limiter.limit("30/minute")
async def get_dailymed(request: Request, name: str) -> DailyMedResponse:
    rxcui = await rxnav.get_rxcui(name)

    spls = await dailymed.search_spl(name, limit=3)
    if not spls:
        raise HTTPException(
            status_code=404,
            detail=f"No DailyMed SPL records found for '{name}'.",
        )

    # Fetch full sections for the first (most relevant) SPL record
    sections: dict = {}
    if spls[0].get("setid"):
        try:
            sections = await dailymed.get_spl_sections(spls[0]["setid"])
        except Exception:
            sections = {}

    # NDC codes from up to 3 matching SPL records
    ndcs = await dailymed.get_drug_ndc(name)

    return DailyMedResponse(
        drug_name=name,
        rxcui=rxcui,
        spl_records=[SPLRecord(**s) for s in spls],
        sections=sections,
        ndcs=ndcs,
    )
