"""Clinical Drug Information API

Data sources:
  - OpenFDA (FDA drug labels, adverse events)     — api.fda.gov
  - NLM RxNorm / RxNav (drug name normalisation)  — rxnav.nlm.nih.gov
  - NLM Drug Interaction API                      — rxnav.nlm.nih.gov
  - NLM DailyMed (structured product labeling)    — dailymed.nlm.nih.gov
  - Curated PK / dosing datasets (from FDA labels + literature)

Disclaimer: For educational and research purposes only. Not medical advice.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.db.database import init_db
from app.routers import drugs, dosing, interactions, pk, adverse_events

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising cache database…")
    await init_db()
    logger.info("Ready.")
    yield
    logger.info("Shutting down.")


limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="Clinical Drug Information API",
    description="""
## Overview
A free, public API providing clinical pharmacology data aggregated from
**OpenFDA**, **NLM RxNorm/RxNav**, and **NLM DailyMed**.

### What this API provides
| Module | Endpoints |
|---|---|
| **Drug information** | Search by name; full label; dosage forms; black-box warnings |
| **Therapeutic dosing** | Standard doses; weight-based calculations; renal/hepatic adjustments |
| **Drug interactions** | Pairwise DDI screening via NLM Drug Interaction API |
| **Pharmacokinetics** | Bioavailability, Vd, protein binding, t½, CYP enzymes, therapeutic range |

### Data sources
- [OpenFDA Drug Labels](https://open.fda.gov/apis/drug/label/) — FDA structured product labeling
- [NLM RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/) — drug name normalisation
- [NLM Drug Interaction API](https://lhncbc.nlm.nih.gov/RxNav/APIs/InteractionAPIs.html) — ONCHigh + DrugBank interactions
- [NLM DailyMed](https://dailymed.nlm.nih.gov/dailymed/) — NIH-curated product labeling

### Disclaimer
> **This API is for educational and research purposes only.**
> It does not constitute medical advice, diagnosis, or treatment.
> Always consult a licensed healthcare provider for clinical decisions.
""",
    version="1.0.0",
    contact={
        "name": "Clinical Drug Information API",
        "url": "https://github.com/your-org/drug-info-api",
    },
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_disclaimer_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Disclaimer"] = (
        "Educational/research use only. Not medical advice."
    )
    return response


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(drugs.router, prefix="/v1", tags=["Drug Information"])
app.include_router(dosing.router, prefix="/v1", tags=["Therapeutic Dosing"])
app.include_router(interactions.router, prefix="/v1", tags=["Drug Interactions"])
app.include_router(pk.router, prefix="/v1", tags=["Pharmacokinetics"])
app.include_router(adverse_events.router, prefix="/v1", tags=["Adverse Events & DailyMed"])


# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], include_in_schema=False)
async def root():
    return JSONResponse(
        {
            "name": "Clinical Drug Information API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "endpoints": {
                "search_drugs": "GET /v1/drugs?q={name}",
                "drug_info": "GET /v1/drug/{name}",
                "drug_label": "GET /v1/drug/{name}/label",
                "dosing": "GET /v1/drug/{name}/dosing",
                "interactions": "GET /v1/interactions?drugs=drug1,drug2",
                "drug_interactions": "GET /v1/drug/{name}/interactions",
                "pk": "GET /v1/drug/{name}/pk",
                "adverse_events": "GET /v1/drug/{name}/adverse-events",
                "dailymed": "GET /v1/drug/{name}/dailymed",
            },
            "sources": ["OpenFDA", "OpenFDA FAERS", "NLM RxNorm", "NLM DailyMed", "NLM Drug Interaction API"],
            "disclaimer": "Educational/research use only. Not medical advice.",
        }
    )


@app.get("/health", tags=["Health"], include_in_schema=False)
async def health():
    return {"status": "ok"}
