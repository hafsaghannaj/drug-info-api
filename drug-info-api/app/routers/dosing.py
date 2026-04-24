"""GET /v1/drug/{name}/dosing  — therapeutic dosing with optional weight/age/renal params
"""
import json
import math
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import (
    DosingResponse,
    WeightBasedDosing,
    ComputedDose,
    RenalAdjustment,
    HepaticAdjustment,
)
from app.services import openfda, rxnav

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Load curated dosing seed once at import time
_SEED_PATH = Path(__file__).parent.parent.parent / "data" / "dosing_seed.json"
_DOSING_SEED: dict[str, dict] = {}

if _SEED_PATH.exists():
    raw = json.loads(_SEED_PATH.read_text())
    for entry in raw.get("drugs", []):
        _DOSING_SEED[entry["generic_name"].lower()] = entry


def _creatinine_clearance(
    age: float, weight_kg: float, sex: str, scr: float
) -> float:
    """Cockcroft-Gault CrCl (mL/min)."""
    cg = ((140 - age) * weight_kg) / (72 * scr)
    if sex.lower() in ("f", "female"):
        cg *= 0.85
    return cg


def _renal_category(crcl: float) -> str:
    if crcl >= 60:
        return "mild_impairment"
    if crcl >= 30:
        return "moderate_impairment"
    if crcl >= 15:
        return "severe_impairment"
    return "esrd_dialysis"


def _compute_dose(
    wb: WeightBasedDosing | None, weight_kg: float | None
) -> ComputedDose | None:
    if wb is None or weight_kg is None:
        return None
    typical = wb.typical_mg_per_kg or wb.min_mg_per_kg
    if typical is None:
        return None

    raw = typical * weight_kg
    max_single = None
    capped = False

    # Hard caps from WHO / FDA label conventions (where standard)
    if wb.max_mg_per_kg:
        cap = wb.max_mg_per_kg * weight_kg
        if raw > cap:
            raw = cap
            capped = True
        max_single = cap

    # Round to nearest 50 mg for cleaner clinical presentation
    rounded = round(raw / 50) * 50

    return ComputedDose(
        calculated_single_dose_mg=rounded,
        calculated_daily_dose_mg=None,  # needs frequency info
        basis=f"weight-based: {typical} mg/kg",
        capped_at_max=capped,
        max_single_dose_mg=round(max_single) if max_single else None,
    )


@router.get(
    "/drug/{name}/dosing",
    response_model=DosingResponse,
    summary="Therapeutic dosing with optional patient parameters",
    description=(
        "Returns FDA-label dosing information for a drug, with optional "
        "weight-based dose calculation and renal-adjustment lookup.\n\n"
        "Weight-based calculations are only returned for drugs where the curated "
        "dataset includes mg/kg parameters (e.g. antibiotics, oncology agents). "
        "For renally-cleared drugs, supply `weight_kg`, `age`, `sex`, and `scr` "
        "(serum creatinine) to receive a Cockcroft-Gault–based renal category and "
        "the corresponding dose adjustment from the FDA label.\n\n"
        "**All output is for educational use only and does not constitute medical advice.**"
    ),
)
@limiter.limit("60/minute")
async def get_dosing(
    request: Request,
    name: str,
    weight_kg: float | None = Query(
        None, ge=1, le=300, description="Patient weight in kg"
    ),
    age: float | None = Query(
        None, ge=0, le=120, description="Patient age in years"
    ),
    sex: str | None = Query(
        None, pattern="^(m|f|male|female)$", description="Sex for CrCl calculation (m/f)"
    ),
    scr: float | None = Query(
        None, ge=0.1, le=30, description="Serum creatinine (mg/dL) for renal adjustment"
    ),
    renal_function: str | None = Query(
        None,
        pattern="^(normal|mild_impairment|moderate_impairment|severe_impairment|esrd_dialysis)$",
        description="Override renal category if lab values not available",
    ),
) -> DosingResponse:
    rxcui = await rxnav.get_rxcui(name)

    # Curated dosing seed takes priority (structured, curated)
    seed = _DOSING_SEED.get(name.lower())

    # FDA label for full dosing text + pregnancy category
    label = await openfda.get_label(name)
    label_dosing = await openfda.parse_dosing(label) if label else {}

    if seed is None and not label:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No dosing data found for '{name}'. "
                "Try the generic name or GET /v1/drugs?q=... to search."
            ),
        )

    # ── Build weight-based dosing object ──────────────────────────────────────
    wb_obj: WeightBasedDosing | None = None
    if seed and seed.get("weight_based"):
        wb = seed["weight_based"]
        wb_obj = WeightBasedDosing(
            min_mg_per_kg=wb.get("min_mg_per_kg"),
            typical_mg_per_kg=wb.get("typical_mg_per_kg"),
            max_mg_per_kg=wb.get("max_mg_per_kg"),
            frequency=wb.get("frequency"),
            notes=wb.get("notes"),
        )

    # ── Compute dose for this patient ─────────────────────────────────────────
    computed: ComputedDose | None = _compute_dose(wb_obj, weight_kg)

    # ── Renal function classification ─────────────────────────────────────────
    if renal_function is None and all(
        v is not None for v in [weight_kg, age, sex, scr]
    ):
        crcl = _creatinine_clearance(age, weight_kg, sex, scr)
        renal_function = _renal_category(crcl)

    # ── Build renal adjustment ────────────────────────────────────────────────
    renal_obj: RenalAdjustment | None = None
    if seed and seed.get("renal_adjustment"):
        ra = seed["renal_adjustment"]
        renal_obj = RenalAdjustment(
            mild_impairment=ra.get("mild_impairment"),
            moderate_impairment=ra.get("moderate_impairment"),
            severe_impairment=ra.get("severe_impairment"),
            esrd_dialysis=ra.get("esrd_dialysis"),
        )

    # ── Hepatic adjustment ────────────────────────────────────────────────────
    hepatic_obj: HepaticAdjustment | None = None
    if seed and seed.get("hepatic_adjustment"):
        ha = seed["hepatic_adjustment"]
        hepatic_obj = HepaticAdjustment(
            mild=ha.get("mild"),
            moderate=ha.get("moderate"),
            severe=ha.get("severe"),
        )

    return DosingResponse(
        rxcui=rxcui,
        drug_name=name,
        weight_kg=weight_kg,
        age_years=age,
        renal_function=renal_function,
        adult_standard_dose=seed.get("adult_standard_dose") if seed else None,
        adult_max_dose=seed.get("adult_max_dose") if seed else None,
        weight_based=wb_obj,
        computed=computed,
        renal_adjustment=renal_obj,
        hepatic_adjustment=hepatic_obj,
        pediatric_notes=seed.get("pediatric_notes") if seed else None,
        pregnancy_category=label_dosing.get("pregnancy_category"),
        full_dosing_text=label_dosing.get("full_dosing_text"),
    )
