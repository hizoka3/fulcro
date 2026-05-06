"""Recommendation catalog matcher.

Loads ``fixtures/recommendations.json`` (produced by BE-2) and selects up to
``max_results`` recommendations for a given (segment, dominant_signal) pair.

Scoring is intentionally trivial:
    base = 0  if trigger == dominant_signal else 100
    score = base + priority    (lower wins)

This is a content-driven layer, not an inference layer — no LLM, no ranking
model. Curated catalog + simple scoring keeps it auditable.
"""

import json
from pathlib import Path
from typing import List, Optional

from app.models.schemas import Recommendation, Segment

# fixtures/ lives at the project root, alongside backend/.
_DEFAULT_CATALOG_PATH = Path(__file__).resolve().parents[3] / "fixtures" / "recommendations.json"


class CatalogMatcher:
    def __init__(self, catalog_path: Path):
        with open(catalog_path) as f:
            self._catalog = json.load(f)

    def match(
        self,
        segment: Segment,
        dominant_signal: str,
        max_results: int = 4,
    ) -> List[Recommendation]:
        """Return up to ``max_results`` recommendations for ``segment``.

        Recommendations whose ``trigger`` matches ``dominant_signal`` are
        promoted; ties are broken by ``priority`` ascending.
        """
        scored = [
            {
                **r,
                "_score": (0 if r.get("trigger") == dominant_signal else 100)
                + r.get("priority", 99),
            }
            for r in self._catalog
            if r.get("segment") == segment.value
        ]
        scored.sort(key=lambda x: x["_score"])
        return [
            Recommendation(
                id=r["id"],
                title=r["title"],
                trigger=r.get("trigger", ""),
                action=r.get("action", ""),
                priority=r.get("priority", 99),
                explanation_short=r.get("explanation_short"),
                articulos_referencia=r.get("articulos_referencia"),
            )
            for r in scored[:max_results]
        ]


_matcher: Optional[CatalogMatcher] = None


def get_matcher() -> CatalogMatcher:
    """Lazy-loaded singleton. Reads the catalog once at first call."""
    global _matcher
    if _matcher is None:
        _matcher = CatalogMatcher(_DEFAULT_CATALOG_PATH)
    return _matcher
