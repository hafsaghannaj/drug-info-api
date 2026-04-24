"""Integration-style tests using FastAPI TestClient + httpx mocking.

Run with:  pytest tests/ -v
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ── Fixtures: mock upstream responses ────────────────────────────────────────

MOCK_RXCUI = "860975"

MOCK_LABEL = {
    "openfda": {
        "generic_name": ["metformin hydrochloride"],
        "brand_name": ["Glucophage"],
        "pharm_class_epc": ["Biguanide [EPC]"],
        "manufacturer_name": ["Bristol-Myers Squibb"],
        "route": ["ORAL"],
        "dosage_form": ["TABLET"],
        "strength": ["500 mg/1"],
    },
    "indications_and_usage": [
        "Metformin is indicated as an adjunct to diet and exercise to improve glycemic control "
        "in adults with type 2 diabetes mellitus."
    ],
    "dosage_and_administration": [
        "Adults: Initial dose 500 mg twice daily or 850 mg once daily with meals. "
        "Titrate dose in increments of 500 mg weekly as tolerated. "
        "Maximum dose: 2550 mg/day."
    ],
    "boxed_warning": None,
    "pregnancy": ["Category B"],
}

MOCK_INTERACTIONS = {
    "fullInteractionTypeGroup": [
        {
            "sourceName": "DrugBank",
            "fullInteractionType": [
                {
                    "minConcept": [
                        {"rxcui": "11289", "name": "warfarin", "tty": "IN"},
                        {"rxcui": "1191", "name": "aspirin", "tty": "IN"},
                    ],
                    "interactionPair": [
                        {
                            "interactionConcept": [
                                {"minConceptItem": {"rxcui": "11289", "name": "warfarin"}},
                                {"minConceptItem": {"rxcui": "1191", "name": "aspirin"}},
                            ],
                            "severity": "major",
                            "description": (
                                "The anticoagulant effect of warfarin may be increased by aspirin, "
                                "raising the risk of bleeding."
                            ),
                        }
                    ],
                }
            ],
        }
    ]
}


# ── Health ────────────────────────────────────────────────────────────────────

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "endpoints" in data
    assert data["disclaimer"]


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Drug search ───────────────────────────────────────────────────────────────

@patch("app.routers.drugs.rxnav.search_drugs", new_callable=AsyncMock)
def test_search_drugs(mock_search):
    mock_search.return_value = [
        {"rxcui": "860975", "name": "metformin", "synonym": None, "tty": "IN"}
    ]
    resp = client.get("/v1/drugs?q=metformin")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "metformin"


def test_search_drugs_too_short():
    resp = client.get("/v1/drugs?q=a")
    assert resp.status_code == 422


# ── Drug info ─────────────────────────────────────────────────────────────────

@patch("app.routers.drugs.rxnav.get_rxcui", new_callable=AsyncMock)
@patch("app.routers.drugs.openfda.get_label", new_callable=AsyncMock)
@patch("app.routers.drugs.openfda.parse_drug_info", new_callable=AsyncMock)
def test_get_drug(mock_parse, mock_label, mock_rxcui):
    mock_rxcui.return_value = MOCK_RXCUI
    mock_label.return_value = MOCK_LABEL
    mock_parse.return_value = {
        "generic_name": "metformin hydrochloride",
        "brand_names": ["Glucophage"],
        "drug_class": "Biguanide [EPC]",
        "pharmacologic_class": ["Biguanide [EPC]"],
        "manufacturer": "Bristol-Myers Squibb",
        "route": ["ORAL"],
        "dosage_forms": [],
        "indications": "Indicated for type 2 diabetes.",
        "black_box_warnings": [],
        "controlled_substance": None,
    }
    resp = client.get("/v1/drug/metformin")
    assert resp.status_code == 200
    data = resp.json()
    assert data["generic_name"] == "metformin hydrochloride"
    assert data["rxcui"] == MOCK_RXCUI
    assert data["disclaimer"]


@patch("app.routers.drugs.rxnav.get_rxcui", new_callable=AsyncMock)
@patch("app.routers.drugs.openfda.get_label", new_callable=AsyncMock)
def test_get_drug_not_found(mock_label, mock_rxcui):
    mock_rxcui.return_value = None
    mock_label.return_value = None
    resp = client.get("/v1/drug/notadrugxyz")
    assert resp.status_code == 404


# ── Dosing ────────────────────────────────────────────────────────────────────

@patch("app.routers.dosing.rxnav.get_rxcui", new_callable=AsyncMock)
@patch("app.routers.dosing.openfda.get_label", new_callable=AsyncMock)
@patch("app.routers.dosing.openfda.parse_dosing", new_callable=AsyncMock)
def test_dosing_seed_drug(mock_parse_dosing, mock_label, mock_rxcui):
    """Amoxicillin is in the curated seed — should return structured dosing."""
    mock_rxcui.return_value = "723"
    mock_label.return_value = MOCK_LABEL
    mock_parse_dosing.return_value = {"full_dosing_text": "500 mg every 8 h", "pregnancy_category": None, "_renal_raw": None, "_hepatic_raw": None}

    resp = client.get("/v1/drug/amoxicillin/dosing?weight_kg=70&age=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["drug_name"] == "amoxicillin"
    assert data["weight_based"] is not None
    assert data["computed"] is not None
    # 70 kg × 25 mg/kg = 1750 mg → rounded to nearest 50 = 1750
    assert data["computed"]["calculated_single_dose_mg"] == pytest.approx(1750, abs=50)


@patch("app.routers.dosing.rxnav.get_rxcui", new_callable=AsyncMock)
@patch("app.routers.dosing.openfda.get_label", new_callable=AsyncMock)
@patch("app.routers.dosing.openfda.parse_dosing", new_callable=AsyncMock)
def test_dosing_renal_adjustment(mock_parse_dosing, mock_label, mock_rxcui):
    """Metformin with renal impairment override."""
    mock_rxcui.return_value = MOCK_RXCUI
    mock_label.return_value = MOCK_LABEL
    mock_parse_dosing.return_value = {"full_dosing_text": None, "pregnancy_category": None, "_renal_raw": None, "_hepatic_raw": None}

    resp = client.get(
        "/v1/drug/metformin/dosing?weight_kg=75&age=60&renal_function=moderate_impairment"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["renal_function"] == "moderate_impairment"
    assert data["renal_adjustment"] is not None
    assert "contraindicated" in data["renal_adjustment"]["moderate_impairment"].lower()


# ── Interactions ──────────────────────────────────────────────────────────────

@patch("app.routers.interactions.rxnav.get_rxcuis_bulk", new_callable=AsyncMock)
@patch("app.routers.interactions.get_interactions_multi", new_callable=AsyncMock)
def test_interactions(mock_interactions, mock_rxcuis):
    mock_rxcuis.return_value = {"warfarin": "11289", "aspirin": "1191"}
    mock_interactions.return_value = [
        {
            "drug_1": "warfarin",
            "drug_2": "aspirin",
            "rxcui_1": "11289",
            "rxcui_2": "1191",
            "severity": "major",
            "description": "Concomitant use of aspirin may increase the risk of serious bleeding.",
            "source": "FDA label drug_interactions section (warfarin)",
        }
    ]
    resp = client.get("/v1/interactions?drugs=warfarin,aspirin")
    assert resp.status_code == 200
    data = resp.json()
    assert data["interaction_count"] == 1
    assert data["interactions"][0]["severity"] == "major"
    assert data["disclaimer"]


def test_interactions_too_few_drugs():
    resp = client.get("/v1/interactions?drugs=warfarin")
    assert resp.status_code == 422


def test_interactions_too_many_drugs():
    drugs = ",".join([f"drug{i}" for i in range(11)])
    resp = client.get(f"/v1/interactions?drugs={drugs}")
    assert resp.status_code == 422


# ── Pharmacokinetics ──────────────────────────────────────────────────────────

@patch("app.routers.pk.rxnav.get_rxcui", new_callable=AsyncMock)
def test_pk_curated(mock_rxcui):
    """Warfarin is in curated seed — should return full PK."""
    mock_rxcui.return_value = "11289"
    resp = client.get("/v1/drug/warfarin/pk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data_quality"] == "curated"
    assert data["narrow_therapeutic_index"] is True
    assert data["protein_binding_pct"] == 99
    assert data["metabolism"]["primary_enzyme"] == "CYP2C9"


@patch("app.routers.pk.rxnav.get_rxcui", new_callable=AsyncMock)
def test_pk_nti_flag(mock_rxcui):
    """Digoxin narrow therapeutic index check."""
    mock_rxcui.return_value = "3407"
    resp = client.get("/v1/drug/digoxin/pk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["narrow_therapeutic_index"] is True
    assert "0.5" in data["therapeutic_range"]


# ── Adverse Events (FAERS) ────────────────────────────────────────────────────

MOCK_FAERS = {
    "total_reports": 15000,
    "reactions": [
        {"term": "NAUSEA", "count": 2000, "pct_of_reports": 13.3},
        {"term": "DIZZINESS", "count": 1200, "pct_of_reports": 8.0},
    ],
    "serious_outcomes": {
        "death": 150,
        "life_threatening": 300,
        "hospitalization": 1200,
        "disability": 90,
        "congenital_anomaly": 5,
        "other_serious": 500,
    },
    "routes": [{"route": "ORAL", "count": 14000}],
    "data_caveat": "FAERS counts are raw report volumes, not incidence rates.",
    "search_field": "rxcui",
}


@patch("app.routers.adverse_events.rxnav.get_rxcui", new_callable=AsyncMock)
@patch("app.routers.adverse_events.faers.get_adverse_events_by_rxcui", new_callable=AsyncMock)
def test_adverse_events(mock_faers, mock_rxcui):
    mock_rxcui.return_value = "41493"
    mock_faers.return_value = MOCK_FAERS
    resp = client.get("/v1/drug/atorvastatin/adverse-events")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_reports"] == 15000
    assert data["reactions"][0]["term"] == "NAUSEA"
    assert data["serious_outcomes"]["death"] == 150
    assert "incidence rates" in data["disclaimer"].lower()
    assert data["data_caveat"]


@patch("app.routers.adverse_events.rxnav.get_rxcui", new_callable=AsyncMock)
@patch("app.routers.adverse_events.faers.get_adverse_events_by_rxcui", new_callable=AsyncMock)
@patch("app.routers.adverse_events.faers.get_adverse_events", new_callable=AsyncMock)
def test_adverse_events_not_found(mock_faers_name, mock_faers_rxcui, mock_rxcui):
    empty = {"total_reports": 0, "reactions": [], "serious_outcomes": {}, "routes": [], "data_caveat": ""}
    mock_rxcui.return_value = None
    mock_faers_rxcui.return_value = empty
    mock_faers_name.return_value = empty
    resp = client.get("/v1/drug/notadrugxyz/adverse-events")
    assert resp.status_code == 404


# ── DailyMed ──────────────────────────────────────────────────────────────────

@patch("app.routers.adverse_events.rxnav.get_rxcui", new_callable=AsyncMock)
@patch("app.routers.adverse_events.dailymed.search_spl", new_callable=AsyncMock)
@patch("app.routers.adverse_events.dailymed.get_spl_sections", new_callable=AsyncMock)
@patch("app.routers.adverse_events.dailymed.get_drug_ndc", new_callable=AsyncMock)
def test_dailymed(mock_ndc, mock_sections, mock_spl, mock_rxcui):
    mock_rxcui.return_value = "41493"
    mock_spl.return_value = [{"setid": "abc-123", "title": "ATORVASTATIN label", "published": "2024-01-01"}]
    mock_sections.return_value = {
        "INDICATIONS AND USAGE": "Atorvastatin is indicated to reduce LDL-C.",
        "DOSAGE AND ADMINISTRATION": "10–80 mg once daily.",
    }
    mock_ndc.return_value = [{"ndc": "0071-0155-23", "packaging": ["90 tablets"], "labeler": "Pfizer", "setid": "abc-123"}]
    resp = client.get("/v1/drug/atorvastatin/dailymed")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["spl_records"]) == 1
    assert "INDICATIONS AND USAGE" in data["sections"]
    assert data["ndcs"][0]["ndc"] == "0071-0155-23"


@patch("app.routers.adverse_events.rxnav.get_rxcui", new_callable=AsyncMock)
@patch("app.routers.adverse_events.dailymed.search_spl", new_callable=AsyncMock)
def test_dailymed_not_found(mock_spl, mock_rxcui):
    mock_rxcui.return_value = None
    mock_spl.return_value = []
    resp = client.get("/v1/drug/notadrugxyz/dailymed")
    assert resp.status_code == 404
