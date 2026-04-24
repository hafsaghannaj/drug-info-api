"""Drug-drug interaction service.

Data source: OpenFDA drug label `drug_interactions` section.

The NLM Drug Interaction API (formerly rxnav.nlm.nih.gov/REST/interaction/...)
was discontinued in January 2024. This service uses FDA-official drug label
text instead: every approved label contains a `drug_interactions` section that
lists known interactions by name, mechanism, and clinical significance.

Approach:
  - Single-drug:  fetch that drug's label → return full drug_interactions section
                  as a list of named mentions with surrounding context.
  - Multi-drug:   for each drug pair (A, B), fetch A's label and search its
                  drug_interactions text for mentions of B, and vice-versa.
                  Returns matched excerpts with source labeling.
"""
import re
import httpx
from app.config import get_settings
from app.db.database import cache_get, cache_set

settings = get_settings()

_CLIENT: httpx.AsyncClient | None = None


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


async def _fetch_interaction_text(drug_name: str) -> str | None:
    """Return the raw drug_interactions label section for a drug, or None."""
    key = f"ddi_text:{drug_name.lower().strip()}"
    cached = await cache_get(key)
    if cached is not None:
        return cached.get("text")

    for field in ("openfda.generic_name", "openfda.brand_name", "openfda.substance_name"):
        try:
            resp = await _client().get(
                "/drug/label.json",
                params={
                    "search": f'{field}:"{drug_name}"',
                    "limit": 1,
                },
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    label = results[0]
                    raw = label.get("drug_interactions")
                    text = (raw[0] if isinstance(raw, list) else raw) if raw else None
                    await cache_set(
                        key, {"text": text}, settings.cache_ttl_label_seconds
                    )
                    return text
        except httpx.HTTPError:
            continue

    await cache_set(key, {"text": None}, settings.cache_ttl_label_seconds)
    return None


def _extract_mentions(
    source_drug: str,
    target_drug: str,
    text: str,
    window: int = 400,
) -> list[dict]:
    """
    Search `text` (the drug_interactions section of `source_drug`'s label)
    for mentions of `target_drug`. Returns a list of excerpt dicts.

    `window` is the number of characters of context to capture around each mention.
    """
    mentions = []
    pattern = re.compile(re.escape(target_drug), re.IGNORECASE)
    for m in pattern.finditer(text):
        start = max(0, m.start() - window // 2)
        end = min(len(text), m.end() + window // 2)
        excerpt = text[start:end].strip()
        # Trim to sentence boundaries where possible
        if start > 0 and ". " in text[start - 50 : start]:
            excerpt = excerpt[excerpt.find(" ") + 1 :]
        mentions.append(
            {
                "drug_1": source_drug,
                "drug_2": target_drug,
                "rxcui_1": None,
                "rxcui_2": None,
                "severity": _infer_severity(excerpt),
                "description": excerpt,
                "source": f"FDA label drug_interactions section ({source_drug})",
            }
        )
    return mentions


# Simple keyword-based severity inference from label text
_CONTRAINDICATED = re.compile(
    r"\b(contraindicated|do not use|must not|should not be used)\b", re.IGNORECASE
)
_MAJOR = re.compile(
    r"\b(serious|life.threatening|fatal|death|severe|significant increase|serotonin syndrome|"
    r"QT prolongation|respiratory depression|coma|avoid combination)\b",
    re.IGNORECASE,
)
_MODERATE = re.compile(
    r"\b(caution|monitor|adjust dose|reduce dose|increase dose|may increase|may decrease|"
    r"clinically significant|closely monitor)\b",
    re.IGNORECASE,
)


def _infer_severity(text: str) -> str:
    if _CONTRAINDICATED.search(text):
        return "contraindicated"
    if _MAJOR.search(text):
        return "major"
    if _MODERATE.search(text):
        return "moderate"
    return "minor"


async def get_interactions_multi(
    drug_names: list[str],
    rxcui_map: dict[str, str | None],
) -> list[dict]:
    """
    For each pair in drug_names, fetch one drug's label and search for
    mentions of the other drug. De-duplicates symmetric pairs.
    """
    import asyncio
    import itertools

    pairs = list(itertools.combinations(drug_names, 2))
    results: list[dict] = []

    async def check_pair(a: str, b: str):
        pair_results: list[dict] = []
        # Check A's label for B
        text_a = await _fetch_interaction_text(a)
        if text_a:
            hits = _extract_mentions(a, b, text_a)
            for h in hits:
                h["rxcui_1"] = rxcui_map.get(a)
                h["rxcui_2"] = rxcui_map.get(b)
            pair_results.extend(hits)
        # Check B's label for A (may surface different language)
        text_b = await _fetch_interaction_text(b)
        if text_b:
            hits = _extract_mentions(b, a, text_b)
            for h in hits:
                h["rxcui_1"] = rxcui_map.get(b)
                h["rxcui_2"] = rxcui_map.get(a)
            pair_results.extend(hits)
        return pair_results

    pair_results = await asyncio.gather(*[check_pair(a, b) for a, b in pairs])
    for pr in pair_results:
        results.extend(pr)
    return results


async def get_interactions_single(
    drug_name: str,
    rxcui: str | None,
) -> list[dict]:
    """
    Return the full drug_interactions label section for one drug,
    parsed into individual named-drug mentions with context excerpts.
    """
    text = await _fetch_interaction_text(drug_name)
    if not text:
        return []

    # Split on common label delimiters to get individual interaction blocks
    # FDA labels use headers like "Drug Name:", numbered lists, or paragraphs
    blocks = re.split(
        r"\n{2,}|(?<=[.!?])\s{2,}|(?:\d+\.\s+)|(?:[A-Z][A-Z\s]{2,}:)",
        text,
    )

    results = []
    for block in blocks:
        block = block.strip()
        if len(block) < 30:
            continue
        # Find what drug this block is about (first capitalised noun phrase)
        other_drug_match = re.search(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,})\b", block
        )
        other_name = other_drug_match.group(1) if other_drug_match else "Unknown"
        results.append(
            {
                "drug_1": drug_name,
                "drug_2": other_name,
                "rxcui_1": rxcui,
                "rxcui_2": None,
                "severity": _infer_severity(block),
                "description": block[:600],
                "source": f"FDA label drug_interactions section ({drug_name})",
            }
        )

    return results
