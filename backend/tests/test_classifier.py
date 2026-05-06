"""Classifier unit tests — one per segment, plus boundary cases."""

from app.core.classifier import classify
from app.models.schemas import Segment


def test_maria_vulnerable():
    """Maria: high consumo ratio + past-due + many institutions → VULNERABLE."""
    features = {
        "total_debt": 4_500_000,
        "consumo_ratio": 0.82,
        "past_due_ratio": 0.15,
        "num_institutions": 5,
        "num_refinancings": 2,
        "has_mortgage": False,
    }
    assert classify(features, ingreso_mensual=580_000) == Segment.VULNERABLE


def test_carlos_functional():
    """Carlos: mortgage holder, healthy income, no past-due → FUNCTIONAL.

    Important: 80M debt with 2.5M income is only sustainable because most of
    that debt is a 20-year mortgage. The classifier amortizes mortgage over
    240 months and other debt over 36 — without that split he'd register as
    VULNERABLE on carga.
    """
    features = {
        "total_debt": 80_000_000,
        "consumo_ratio": 0.05,
        "past_due_ratio": 0.0,
        "num_institutions": 3,
        "num_refinancings": 0,
        "has_mortgage": True,
    }
    assert classify(features, ingreso_mensual=2_500_000) == Segment.FUNCTIONAL


def test_pedro_recently_banked():
    """Pedro: 1 account, no debt → RECENTLY_BANKED (he has a footprint)."""
    features = {
        "total_debt": 0,
        "consumo_ratio": 0,
        "past_due_ratio": 0,
        "num_institutions": 1,
        "num_refinancings": 0,
        "has_mortgage": False,
    }
    assert classify(features, ingreso_mensual=400_000) == Segment.RECENTLY_BANKED


def test_unbanked():
    """No debt AND no institution footprint → UNBANKED."""
    features = {
        "total_debt": 0,
        "consumo_ratio": 0,
        "past_due_ratio": 0,
        "num_institutions": 0,
        "num_refinancings": 0,
        "has_mortgage": False,
    }
    assert classify(features) == Segment.UNBANKED


def test_high_carga_without_past_due_is_vulnerable():
    """Over-leveraged consumer (no mortgage cushion) → VULNERABLE on carga."""
    features = {
        "total_debt": 30_000_000,
        "consumo_ratio": 0.5,
        "past_due_ratio": 0.0,
        "num_institutions": 2,
        "num_refinancings": 0,
        "has_mortgage": False,
    }
    assert classify(features, ingreso_mensual=600_000) == Segment.VULNERABLE


def test_many_institutions_alone_is_vulnerable():
    """4+ institutions even without past-due → VULNERABLE (over-extended)."""
    features = {
        "total_debt": 1_500_000,
        "consumo_ratio": 0.5,
        "past_due_ratio": 0,
        "num_institutions": 5,
        "num_refinancings": 0,
        "has_mortgage": False,
    }
    assert classify(features, ingreso_mensual=1_500_000) == Segment.VULNERABLE
