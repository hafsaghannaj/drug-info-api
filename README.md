# Clinical Drug Information API

A free, public REST API providing clinical pharmacology data aggregated from FDA and NIH public databases. No API key required to run.

> **Disclaimer:** For educational and research purposes only. Not medical advice. Always consult a licensed healthcare provider for clinical decisions.

---

## What it does

| Module | What you get |
|---|---|
| **Drug Information** | Search by name, full FDA label, dosage forms, black-box warnings, manufacturer |
| **Therapeutic Dosing** | Standard doses, weight-based calculations, renal/hepatic adjustments (Cockcroft-Gault built in) |
| **Drug Interactions** | Pairwise DDI screening from FDA-official label text |
| **Pharmacokinetics** | Bioavailability, Vd, protein binding, half-life, CYP enzymes, therapeutic range |
| **Adverse Events** | FDA FAERS post-market report data — top reactions, serious outcomes breakdown |
| **DailyMed** | NIH structured product labeling (SPL), NDC package codes |

---

## Data Sources

All sources are free, public, and require no license.

| Source | Used for |
|---|---|
| [OpenFDA Drug Labels](https://open.fda.gov/apis/drug/label/) | Drug info, dosing text, label sections, interactions |
| [OpenFDA FAERS](https://open.fda.gov/apis/drug/event/) | Adverse event reports |
| [NLM RxNorm / RxNav](https://rxnav.nlm.nih.gov) | Drug name → RxCUI resolution, drug search |
| [NLM DailyMed](https://dailymed.nlm.nih.gov) | SPL records, NDC codes |
| Curated seed data | PK parameters and structured dosing for 16 common drugs (from FDA labels + literature) |

---

## Quickstart

**Requirements:** Python 3.12+, or Docker.

### Option 1 — Python

```bash
git clone https://github.com/your-org/drug-info-api
cd drug-info-api

pip install -r requirements.txt

cp .env.example .env   # optionally add OpenFDA API key

uvicorn app.main:app --reload
```

### Option 2 — Docker

```bash
cp .env.example .env
docker compose up
```

Server runs on `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

---

## API Endpoints

Base URL: `http://localhost:8000/v1`

### Drug Information

```
GET /drugs?q={name}&limit={n}
```
Search drug names via NLM RxNorm.

```
GET /drug/{name}
```
Full drug info: generic name, brand names, drug class, indications, dosage forms, black-box warnings.

```
GET /drug/{name}/label
```
All FDA label sections as raw text (indications, warnings, dosing, adverse reactions, etc.). Uses OpenFDA with DailyMed as fallback.

---

### Therapeutic Dosing

```
GET /drug/{name}/dosing
  ?weight_kg=46.3
  &age=25
  &sex=f
  &scr=0.9
  &renal_function=moderate_impairment
```

Returns standard adult dose, max dose, weight-based calculation (where applicable), and renal/hepatic adjustment guidance.

Supply `weight_kg` + `age` + `sex` + `scr` (serum creatinine) to get an automatic Cockcroft-Gault renal category and matching dose adjustment.

**Example — Benadryl at 102 lbs / 5'0":**
```
GET /drug/diphenhydramine/dosing?weight_kg=46.3&age=25
→ calculated_single_dose_mg: 50.0 mg (2 tablets)
```

---

### Drug Interactions

```
GET /interactions?drugs=warfarin,aspirin,metformin
```
Checks all pairs in a comma-separated list (2–10 drugs). Fetches each drug's FDA label and searches the `drug_interactions` section for mentions of the other drugs. Returns excerpts with inferred severity.

```
GET /drug/{name}/interactions
```
All interactions listed in a single drug's FDA label.

**Severity levels:** `contraindicated` · `major` · `moderate` · `minor`

---

### Pharmacokinetics

```
GET /drug/{name}/pk
```

Returns: bioavailability, volume of distribution, protein binding, half-life, metabolism (CYP enzymes, active metabolites, prodrug status), elimination route, therapeutic range, narrow therapeutic index flag.

**Curated drugs (full PK data):**
amoxicillin, amlodipine, atorvastatin, clopidogrel, digoxin, diphenhydramine, levothyroxine, lisinopril, lithium, metformin, metoprolol, omeprazole, phenytoin, sertraline, vancomycin, warfarin

Other drugs return label-derived partial data.

---

### Adverse Events

```
GET /drug/{name}/adverse-events?limit=20
```

From FDA FAERS: total report count, top reaction terms (MedDRA), serious outcome breakdown (deaths, hospitalizations, life-threatening events), and route of administration distribution.

> ⚠️ FAERS counts are **not incidence rates**. High counts reflect reporting volume, not risk magnitude. Signal detection requires PRR/ROR comparator analysis.

---

### DailyMed

```
GET /drug/{name}/dailymed
```

NIH DailyMed structured product label records and NDC package codes for a drug.

---

## Example Response — Diphenhydramine PK

```json
GET /v1/drug/diphenhydramine/pk

{
  "rxcui": "1362",
  "drug_name": "diphenhydramine",
  "bioavailability_oral_pct": 50.0,
  "time_to_peak_hours": 2.0,
  "volume_of_distribution_l_kg": 3.3,
  "protein_binding_pct": 78.0,
  "half_life_hours": 8.0,
  "half_life_range": "4–15 h (extended in elderly: up to 17 h)",
  "metabolism": {
    "primary_enzyme": "CYP2D6",
    "active_metabolites": [],
    "prodrug": false
  },
  "elimination": {
    "primary_route": "renal",
    "renal_fraction": 0.9
  },
  "onset_minutes": 30,
  "duration_hours": 4.0,
  "narrow_therapeutic_index": false,
  "data_quality": "curated"
}
```

---

## Project Structure

```
drug-info-api/
├── app/
│   ├── main.py                  FastAPI app, middleware, rate limiting
│   ├── config.py                Settings (env-driven via pydantic-settings)
│   ├── models/schemas.py        All Pydantic response models
│   ├── routers/
│   │   ├── drugs.py             Search, drug info, label sections
│   │   ├── dosing.py            Therapeutic dosing + weight/renal calc
│   │   ├── interactions.py      DDI checker (FDA label–based)
│   │   ├── pk.py                Pharmacokinetic parameters
│   │   └── adverse_events.py    FAERS adverse events + DailyMed
│   ├── services/
│   │   ├── openfda.py           OpenFDA label client (async, cached)
│   │   ├── rxnav.py             NLM RxNorm client
│   │   ├── dailymed.py          NLM DailyMed client
│   │   ├── faers.py             OpenFDA FAERS client
│   │   └── interactions.py      FDA label DDI parser
│   └── db/database.py           SQLite response cache (TTL-based)
├── data/
│   ├── pk_seed.json             Curated PK data (16 drugs)
│   └── dosing_seed.json         Curated dosing data (6 drugs)
├── tests/
│   └── test_api.py              17 unit tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Configuration

Copy `.env.example` to `.env`:

```env
# Optional — raises OpenFDA rate limit from 240 → 1000 req/min
# Register free at: https://open.fda.gov/apis/authentication/
OPENFDA_API_KEY=

CACHE_DB_PATH=./cache.db
CACHE_TTL_LABEL_SECONDS=86400     # 24h
CACHE_TTL_RXCUI_SECONDS=604800    # 7 days
CACHE_TTL_INTERACTION_SECONDS=3600
CACHE_TTL_SEARCH_SECONDS=3600
```

---

## Rate Limits

| Endpoint group | Limit |
|---|---|
| Search, drug info, dosing, PK | 60 requests / minute per IP |
| Interactions, adverse events, DailyMed | 30 requests / minute per IP |

Upstream OpenFDA: 240 req/min without API key, 1000/min with key.

---

## Running Tests

```bash
pytest tests/ -v
```

17 tests, all mocked (no network calls required).

---

## Tech Stack

- **FastAPI** — async REST framework
- **httpx** — async HTTP client
- **aiosqlite** — async SQLite cache
- **pydantic-settings** — env-based config
- **slowapi** — rate limiting
- **uvicorn** — ASGI server
