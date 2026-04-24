from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Drug Information ──────────────────────────────────────────────────────────

class DosageForm(BaseModel):
    form: str
    strengths: list[str]
    route: str


class BlackBoxWarning(BaseModel):
    text: str


class DrugSummary(BaseModel):
    rxcui: Optional[str] = None
    generic_name: str
    brand_names: list[str] = []
    drug_class: Optional[str] = None
    pharmacologic_class: list[str] = []
    manufacturer: Optional[str] = None
    route: list[str] = []
    dosage_forms: list[DosageForm] = []
    indications: Optional[str] = None
    black_box_warnings: list[BlackBoxWarning] = []
    controlled_substance: Optional[str] = None
    source: str = "OpenFDA / NLM DailyMed"
    disclaimer: str = (
        "For educational and research purposes only. "
        "Not medical advice. Consult a licensed clinician for all treatment decisions."
    )


# ── Therapeutic Dosing ────────────────────────────────────────────────────────

class WeightBasedDosing(BaseModel):
    min_mg_per_kg: Optional[float] = None
    typical_mg_per_kg: Optional[float] = None
    max_mg_per_kg: Optional[float] = None
    frequency: Optional[str] = None
    notes: Optional[str] = None


class RenalAdjustment(BaseModel):
    mild_impairment: Optional[str] = None    # CrCl 60-89
    moderate_impairment: Optional[str] = None  # CrCl 30-59
    severe_impairment: Optional[str] = None  # CrCl 15-29
    esrd_dialysis: Optional[str] = None


class HepaticAdjustment(BaseModel):
    mild: Optional[str] = None    # Child-Pugh A
    moderate: Optional[str] = None  # Child-Pugh B
    severe: Optional[str] = None  # Child-Pugh C


class ComputedDose(BaseModel):
    calculated_single_dose_mg: Optional[float] = None
    calculated_daily_dose_mg: Optional[float] = None
    basis: str  # e.g. "weight-based: 10 mg/kg"
    capped_at_max: bool = False
    max_single_dose_mg: Optional[float] = None


class DosingResponse(BaseModel):
    rxcui: Optional[str] = None
    drug_name: str
    weight_kg: Optional[float] = None
    age_years: Optional[float] = None
    renal_function: Optional[str] = None
    adult_standard_dose: Optional[str] = None
    adult_max_dose: Optional[str] = None
    weight_based: Optional[WeightBasedDosing] = None
    computed: Optional[ComputedDose] = None
    renal_adjustment: Optional[RenalAdjustment] = None
    hepatic_adjustment: Optional[HepaticAdjustment] = None
    pediatric_notes: Optional[str] = None
    pregnancy_category: Optional[str] = None
    full_dosing_text: Optional[str] = None   # raw FDA label section
    source: str = "OpenFDA label + NLM RxNorm"
    disclaimer: str = (
        "For educational and research purposes only. "
        "Not medical advice. Consult a licensed clinician for all treatment decisions."
    )


# ── Drug Interactions ─────────────────────────────────────────────────────────

class InteractionPair(BaseModel):
    drug_1: str
    drug_2: str
    rxcui_1: Optional[str] = None
    rxcui_2: Optional[str] = None
    severity: Optional[str] = None  # "major", "moderate", "minor", "N/A"
    description: str
    source: str


class InteractionResponse(BaseModel):
    drugs_queried: list[str]
    resolved_rxcuis: dict[str, Optional[str]] = {}
    interaction_count: int
    interactions: list[InteractionPair]
    sources: list[str] = ["NLM Drug Interaction API (ONCHigh, DrugBank)"]
    disclaimer: str = (
        "Interaction data is provided for educational purposes. "
        "Clinical significance depends on dose, patient factors, and context. "
        "Always verify with a pharmacist or prescriber."
    )


# ── Pharmacokinetics ──────────────────────────────────────────────────────────

class MetabolismInfo(BaseModel):
    primary_enzyme: Optional[str] = None       # e.g. "CYP3A4"
    secondary_enzymes: list[str] = []
    active_metabolites: list[str] = []
    prodrug: bool = False
    notes: Optional[str] = None


class EliminationInfo(BaseModel):
    primary_route: Optional[str] = None   # "renal", "hepatic", "mixed"
    renal_fraction: Optional[float] = None  # 0.0–1.0
    half_life_hours: Optional[float] = None
    half_life_range_hours: Optional[tuple[float, float]] = None
    clearance_ml_min_kg: Optional[float] = None


class PKResponse(BaseModel):
    rxcui: Optional[str] = None
    drug_name: str
    bioavailability_oral_pct: Optional[float] = None
    time_to_peak_hours: Optional[float] = None
    volume_of_distribution_l_kg: Optional[float] = None
    protein_binding_pct: Optional[float] = None
    half_life_hours: Optional[float] = None
    half_life_range: Optional[str] = None
    metabolism: Optional[MetabolismInfo] = None
    elimination: Optional[EliminationInfo] = None
    onset_minutes: Optional[int] = None
    duration_hours: Optional[float] = None
    therapeutic_range: Optional[str] = None   # e.g. "0.5–2 µg/mL"
    narrow_therapeutic_index: bool = False
    data_quality: str = "curated"   # "curated" | "label-derived" | "partial"
    references: list[str] = []
    source: str = "Curated from FDA labels, clinical pharmacology literature"
    disclaimer: str = (
        "For educational and research purposes only. "
        "Not medical advice. Consult a licensed clinician for all treatment decisions."
    )


# ── Search / List ─────────────────────────────────────────────────────────────

# ── Adverse Events (FAERS) ────────────────────────────────────────────────────

class AdverseReaction(BaseModel):
    term: str
    count: int
    pct_of_reports: float


class SeriousOutcomes(BaseModel):
    death: Optional[int] = None
    life_threatening: Optional[int] = None
    hospitalization: Optional[int] = None
    disability: Optional[int] = None
    congenital_anomaly: Optional[int] = None
    other_serious: Optional[int] = None


class RouteCount(BaseModel):
    route: str
    count: int


class AdverseEventsResponse(BaseModel):
    rxcui: Optional[str] = None
    drug_name: str
    total_reports: int
    search_field: str = "name"
    reactions: list[AdverseReaction] = []
    serious_outcomes: Optional[SeriousOutcomes] = None
    routes: list[RouteCount] = []
    data_caveat: str
    source: str = "OpenFDA FAERS (FDA Adverse Event Reporting System)"
    disclaimer: str = (
        "FAERS data is for educational and research use only. "
        "Report counts are NOT incidence rates. A high count does not imply "
        "high risk — it reflects reporting volume, which is influenced by drug "
        "popularity, label warnings, and media attention. "
        "Signal detection requires comparator-based analysis (PRR/ROR). "
        "Not medical advice."
    )


# ── DailyMed SPL ──────────────────────────────────────────────────────────────

class SPLRecord(BaseModel):
    setid: Optional[str] = None
    title: Optional[str] = None
    published: Optional[str] = None


class DailyMedResponse(BaseModel):
    drug_name: str
    rxcui: Optional[str] = None
    spl_records: list[SPLRecord] = []
    sections: dict = {}
    ndcs: list[dict] = []
    source: str = "NLM DailyMed"
    disclaimer: str = (
        "For educational and research purposes only. Not medical advice."
    )


# ── Search / List ─────────────────────────────────────────────────────────────

class DrugSearchResult(BaseModel):
    rxcui: Optional[str] = None
    name: str
    synonym: Optional[str] = None
    drug_class: Optional[str] = None
    tty: Optional[str] = None  # RxNorm term type


class DrugListResponse(BaseModel):
    query: str
    count: int
    results: list[DrugSearchResult]
    source: str = "NLM RxNorm"
