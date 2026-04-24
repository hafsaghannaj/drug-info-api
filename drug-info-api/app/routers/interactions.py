"""GET /v1/interactions         — check interactions between 2–10 drugs
GET /v1/drug/{name}/interactions — all known interactions for one drug

Data source: OpenFDA FDA drug label drug_interactions sections.
The NLM Drug Interaction API was discontinued in January 2024.
"""
from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import InteractionResponse, InteractionPair
from app.services import rxnav
from app.services.interactions import get_interactions_multi, get_interactions_single

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/interactions",
    response_model=InteractionResponse,
    summary="Drug-drug interaction checker",
    description=(
        "Checks for known drug-drug interactions among 2–10 drugs using "
        "FDA-official drug label `drug_interactions` sections via OpenFDA.\n\n"
        "For each pair, the endpoint fetches both drugs' labels and searches "
        "each label's interaction section for mentions of the other drug, "
        "returning matching excerpts with inferred severity.\n\n"
        "**Severity inference** is keyword-based from label text:\n"
        "- `contraindicated` — label uses contraindicated/do not use language\n"
        "- `major` — serious/life-threatening/fatal/serotonin syndrome/QT prolongation\n"
        "- `moderate` — caution/monitor/dose adjustment language\n"
        "- `minor` — mentioned without severity keywords\n\n"
        "**Source:** FDA-approved prescribing information via OpenFDA.\n\n"
        "*Note: The NLM Drug Interaction API (ONCHigh/DrugBank) was discontinued "
        "January 2024 — FDA label text is the authoritative replacement.*"
    ),
)
@limiter.limit("30/minute")
async def check_interactions(
    request: Request,
    drugs: str = Query(
        ...,
        description="Comma-separated list of 2–10 drug names (generic preferred)",
        examples=["warfarin,aspirin,metformin"],
    ),
) -> InteractionResponse:
    names = [n.strip() for n in drugs.split(",") if n.strip()]

    if len(names) < 2:
        raise HTTPException(
            status_code=422, detail="Provide at least 2 drug names separated by commas."
        )
    if len(names) > 10:
        raise HTTPException(
            status_code=422, detail="Maximum 10 drugs per request."
        )

    rxcui_map = await rxnav.get_rxcuis_bulk(names)
    raw = await get_interactions_multi(names, rxcui_map)
    pairs = [InteractionPair(**r) for r in raw]

    return InteractionResponse(
        drugs_queried=names,
        resolved_rxcuis=rxcui_map,
        interaction_count=len(pairs),
        interactions=pairs,
        sources=["OpenFDA drug label drug_interactions sections (FDA-official prescribing information)"],
    )


@router.get(
    "/drug/{name}/interactions",
    response_model=InteractionResponse,
    summary="All interactions listed in a drug's FDA label",
    description=(
        "Returns all drug interactions documented in the FDA-approved prescribing "
        "information for a single drug, parsed from the label's `drug_interactions` section.\n\n"
        "Each entry is an excerpt from the label text with an inferred severity level. "
        "For the full unstructured label text, see `GET /v1/drug/{name}/label`."
    ),
)
@limiter.limit("30/minute")
async def get_drug_interactions(request: Request, name: str) -> InteractionResponse:
    rxcui = await rxnav.get_rxcui(name)
    raw = await get_interactions_single(name, rxcui)

    if not raw:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No drug interaction section found in FDA label for '{name}'. "
                "Use the generic drug name for best results."
            ),
        )

    pairs = [InteractionPair(**r) for r in raw]
    return InteractionResponse(
        drugs_queried=[name],
        resolved_rxcuis={name: rxcui},
        interaction_count=len(pairs),
        interactions=pairs,
        sources=["OpenFDA drug label drug_interactions section (FDA-official prescribing information)"],
    )
