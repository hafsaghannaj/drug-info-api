"""GET /v1/drugs  — search
GET /v1/drug/{name}  — full drug info
GET /v1/drug/{name}/label  — raw FDA label sections (OpenFDA primary, DailyMed fallback)
"""
from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import DrugSummary, DrugListResponse, DrugSearchResult
from app.services import openfda, rxnav, dailymed

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/drugs",
    response_model=DrugListResponse,
    summary="Search drugs by name",
    description=(
        "Searches NLM RxNorm for drug concepts matching the query string. "
        "Returns ingredient-level results by default."
    ),
)
@limiter.limit("60/minute")
async def search_drugs(
    request: Request,
    q: str = Query(..., min_length=2, max_length=100, description="Drug name or partial name"),
    limit: int = Query(20, ge=1, le=50),
) -> DrugListResponse:
    results = await rxnav.search_drugs(q, max_results=limit)
    return DrugListResponse(
        query=q,
        count=len(results),
        results=[DrugSearchResult(**r) for r in results],
    )


@router.get(
    "/drug/{name}",
    response_model=DrugSummary,
    summary="Full drug information",
    description=(
        "Returns structured drug information from OpenFDA and NLM RxNorm: "
        "drug class, indications, dosage forms, black-box warnings, "
        "controlled substance schedule, manufacturer."
    ),
)
@limiter.limit("60/minute")
async def get_drug(request: Request, name: str) -> DrugSummary:
    rxcui = await rxnav.get_rxcui(name)
    label = await openfda.get_label(name)

    if not label:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No FDA label found for '{name}'. "
                "Try the generic name, or use GET /v1/drugs?q=... to search."
            ),
        )

    info = await openfda.parse_drug_info(label)
    return DrugSummary(rxcui=rxcui, **info)


@router.get(
    "/drug/{name}/label",
    summary="Raw FDA label sections",
    description=(
        "Returns all available label sections (indications, warnings, "
        "dosing, adverse reactions, etc.) as raw text from OpenFDA. "
        "Useful for researchers who need the complete label narrative."
    ),
)
@limiter.limit("30/minute")
async def get_label_sections(request: Request, name: str) -> dict:
    label = await openfda.get_label(name)
    if not label:
        raise HTTPException(status_code=404, detail=f"No FDA label found for '{name}'.")

    # Return every text section present in the label
    text_keys = [
        "indications_and_usage",
        "dosage_and_administration",
        "warnings_and_cautions",
        "warnings",
        "precautions",
        "contraindications",
        "adverse_reactions",
        "drug_interactions",
        "use_in_specific_populations",
        "pregnancy",
        "nursing_mothers",
        "pediatric_use",
        "geriatric_use",
        "clinical_pharmacology",
        "mechanism_of_action",
        "pharmacodynamics",
        "pharmacokinetics",
        "boxed_warning",
        "overdosage",
        "description",
        "how_supplied",
        "storage_and_handling",
    ]
    sections: dict = {}
    for key in text_keys:
        val = label.get(key)
        if val:
            text = val[0] if isinstance(val, list) else val
            if text and text.strip():
                sections[key] = text.strip()

    # ── DailyMed fallback for any sections missing from OpenFDA ─────────────
    dailymed_sections: dict = {}
    if len(sections) < 3:
        # OpenFDA returned very sparse label — try DailyMed
        spls = await dailymed.search_spl(name, limit=1)
        if spls and spls[0].get("setid"):
            try:
                dailymed_sections = await dailymed.get_spl_sections(spls[0]["setid"])
            except Exception:
                pass

    # Merge: OpenFDA takes priority; DailyMed fills gaps
    merged = {**dailymed_sections, **sections}
    source = "OpenFDA" if sections else "NLM DailyMed"
    if sections and dailymed_sections:
        source = "OpenFDA (primary) + NLM DailyMed (supplemental)"

    return {
        "drug_name": name,
        "rxcui": await rxnav.get_rxcui(name),
        "sections": merged,
        "source": source,
        "disclaimer": (
            "For educational and research purposes only. "
            "Not medical advice."
        ),
    }
