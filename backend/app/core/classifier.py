"""Deterministic segment classifier. First-match-wins, no LLM."""

from typing import Dict

from app.models.schemas import Segment

# Mortgage amortizes over ~20y, consumer credit over ~3y.
# Used to estimate monthly payment without per-loan rate data.
_MORTGAGE_TERM_MONTHS = 240
_CONSUMO_TERM_MONTHS = 36


def classify(features: Dict, ingreso_mensual: float = 580_000) -> Segment:
    """Return the segment for a given Features dict.

    Mutates `features` to write back the computed `carga_financiera_pct` so the
    caller (and the dominant_signal logic) sees the same number.
    """
    total_debt = features.get("total_debt", 0)
    past_due_ratio = features.get("past_due_ratio", 0)
    consumo_ratio = features.get("consumo_ratio", 0)
    num_institutions = features.get("num_institutions", 0)
    num_refinancings = features.get("num_refinancings", 0)
    has_mortgage = features.get("has_mortgage", False)

    carga = _carga_financiera(features, ingreso_mensual)
    features["carga_financiera_pct"] = round(carga, 2)

    if total_debt == 0 and num_institutions == 0:
        return Segment.UNBANKED

    if (
        past_due_ratio > 0
        or consumo_ratio > 0.7
        or num_institutions >= 4
        or num_refinancings >= 2
        or carga > 0.4
    ):
        return Segment.VULNERABLE

    if has_mortgage and past_due_ratio == 0 and carga < 0.3:
        return Segment.FUNCTIONAL

    if num_institutions <= 2 and total_debt < 500_000:
        return Segment.RECENTLY_BANKED

    return Segment.FUNCTIONAL


def _carga_financiera(features: Dict, ingreso_mensual: float) -> float:
    """Estimate monthly debt service / income.

    Splits debt into mortgage vs. non-mortgage to amortize them differently.
    Mortgage at 240 months, everything else at 36 months. Without this split,
    a borrower with a healthy mortgage would always look over-leveraged.
    """
    if ingreso_mensual <= 0:
        return 0.0

    total_debt = features.get("total_debt", 0)
    mortgage_debt = features.get("mortgage_debt")
    consumo_debt = features.get("consumo_debt")
    commercial_debt = features.get("commercial_debt") or 0

    if mortgage_debt is None or consumo_debt is None:
        # Per-type breakdown not available (e.g., test fixture). Reconstruct
        # from total_debt + consumo_ratio + has_mortgage.
        consumo_ratio = features.get("consumo_ratio", 0)
        has_mortgage = features.get("has_mortgage", False)
        consumo_debt = total_debt * consumo_ratio
        mortgage_debt = (total_debt - consumo_debt) if has_mortgage else 0
        commercial_debt = 0 if has_mortgage else (total_debt - consumo_debt)

    non_mortgage = (consumo_debt or 0) + commercial_debt
    monthly = (mortgage_debt / _MORTGAGE_TERM_MONTHS) + (non_mortgage / _CONSUMO_TERM_MONTHS)
    return monthly / ingreso_mensual
