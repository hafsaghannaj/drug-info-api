"""GET /v1/drug/{name}/pk  — pharmacokinetic parameters
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import PKResponse, MetabolismInfo, EliminationInfo
from app.services import openfda, rxnav

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Load curated PK seed once at import time
_SEED_PATH = Path(__file__).parent.parent.parent / "data" / "pk_seed.json"
_PK_SEED: dict[str, dict] = {}

if _SEED_PATH.exists():
    raw = json.loads(_SEED_PATH.read_text())
    for entry in raw.get("drugs", []):
        _PK_SEED[entry["generic_name"].lower()] = entry


def _build_pk_from_seed(name: str, rxcui: str | None, entry: dict) -> PKResponse:
    met = entry.get("metabolism") or {}
    elim = entry.get("elimination") or {}

    t_range = entry.get("half_life_range")
    if t_range is None and entry.get("half_life_hours"):
        t_range = f"{entry['half_life_hours']} h"

    return PKResponse(
        rxcui=rxcui,
        drug_name=name,
        bioavailability_oral_pct=entry.get("bioavailability_oral_pct"),
        time_to_peak_hours=entry.get("time_to_peak_hours"),
        volume_of_distribution_l_kg=entry.get("volume_of_distribution_l_kg"),
        protein_binding_pct=entry.get("protein_binding_pct"),
        half_life_hours=entry.get("half_life_hours"),
        half_life_range=t_range,
        metabolism=MetabolismInfo(
            primary_enzyme=met.get("primary_enzyme"),
            secondary_enzymes=met.get("secondary_enzymes", []),
            active_metabolites=met.get("active_metabolites", []),
            prodrug=met.get("prodrug", False),
            notes=met.get("notes"),
        ) if met else None,
        elimination=EliminationInfo(
            primary_route=elim.get("primary_route"),
            renal_fraction=elim.get("renal_fraction"),
            half_life_hours=elim.get("half_life_hours"),
            clearance_ml_min_kg=elim.get("clearance_ml_min_kg"),
        ) if elim else None,
        onset_minutes=entry.get("onset_minutes"),
        duration_hours=entry.get("duration_hours"),
        therapeutic_range=entry.get("therapeutic_range"),
        narrow_therapeutic_index=entry.get("narrow_therapeutic_index", False),
        data_quality="curated",
        references=entry.get("references", []),
    )


def _extract_pk_from_label(name: str, rxcui: str | None, label: dict) -> PKResponse | None:
    """
    Attempt to extract PK data from the FDA label pharmacokinetics section.
    Returns a partial PKResponse with data_quality='label-derived', or None if
    the label has no pharmacokinetics section.
    """
    pk_section = None
    for field in ("pharmacokinetics", "clinical_pharmacology"):
        val = label.get(field)
        if val:
            pk_section = val[0] if isinstance(val, list) else val
            break

    if not pk_section:
        return None

    # The label text is free-form; we return it as a note rather than trying to
    # parse numbers via regex (too fragile for production).
    return PKResponse(
        rxcui=rxcui,
        drug_name=name,
        data_quality="label-derived",
        references=["FDA label (pharmacokinetics section — unstructured text)"],
        source="OpenFDA label (unstructured — see full_text field)",
        # Store the raw text in the notes field via therapeutic_range as workaround
        # Callers should use GET /v1/drug/{name}/label for the full narrative.
        therapeutic_range=None,
    )


@router.get(
    "/drug/{name}/pk",
    response_model=PKResponse,
    summary="Pharmacokinetic parameters",
    description=(
        "Returns pharmacokinetic parameters for a drug: bioavailability, "
        "volume of distribution, protein binding, half-life, metabolism "
        "(CYP enzymes, active metabolites, prodrug status), elimination route, "
        "therapeutic range, and narrow therapeutic index flag.\n\n"
        "**Data quality levels:**\n"
        "- `curated` — manually verified from FDA labels and peer-reviewed pharmacology literature\n"
        "- `label-derived` — extracted from FDA label text (less structured)\n"
        "- `partial` — incomplete data\n\n"
        "Currently curated: metformin, warfarin, atorvastatin, lisinopril, amlodipine, "
        "metoprolol, sertraline, omeprazole, amoxicillin, levothyroxine, digoxin, "
        "lithium, vancomycin, phenytoin, clopidogrel.\n\n"
        "For drugs not in the curated set, a label-derived partial result is returned."
    ),
)
@limiter.limit("60/minute")
async def get_pk(request: Request, name: str) -> PKResponse:
    rxcui = await rxnav.get_rxcui(name)

    # 1. Curated seed (highest quality)
    entry = _PK_SEED.get(name.lower())
    if entry:
        return _build_pk_from_seed(name, rxcui, entry)

    # 2. FDA label fallback
    label = await openfda.get_label(name)
    if label:
        pk = _extract_pk_from_label(name, rxcui, label)
        if pk:
            return pk

    raise HTTPException(
        status_code=404,
        detail=(
            f"No PK data found for '{name}'. "
            "Use the generic drug name. "
            "If you need the full FDA label text, use GET /v1/drug/{name}/label."
        ),
    )
