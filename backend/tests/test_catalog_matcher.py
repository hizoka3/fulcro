"""Catalog matcher unit tests against the seeded recommendations.json."""

from app.core.catalog_matcher import get_matcher
from app.models.schemas import Segment


def test_vulnerable_high_consumo_ratio_picks_consolidation_first():
    """Trigger match wins over priority alone."""
    recs = get_matcher().match(Segment.VULNERABLE, "high_consumo_ratio")
    assert recs, "expected at least one recommendation"
    assert recs[0].id == "vuln_001"
    assert recs[0].trigger == "high_consumo_ratio"


def test_vulnerable_past_due_picks_renegotiate_first():
    recs = get_matcher().match(Segment.VULNERABLE, "past_due_present")
    assert recs[0].id == "vuln_004"


def test_unknown_signal_falls_back_to_priority():
    """No trigger matches → all candidates score by priority asc."""
    recs = get_matcher().match(Segment.VULNERABLE, "no_such_signal")
    assert recs, "expected fallback recommendations"
    # vuln_001, _002, _004 all have priority 1; one of them ranks first.
    assert recs[0].priority == 1


def test_max_results_caps_output():
    recs = get_matcher().match(Segment.VULNERABLE, "high_consumo_ratio", max_results=2)
    assert len(recs) == 2


def test_segment_filter_excludes_other_segments():
    recs = get_matcher().match(Segment.UNBANKED, "low_engagement")
    for r in recs:
        # All returned items must belong to the asked segment.
        # We assert via id prefix since the schema doesn't expose `segment`.
        assert r.id.startswith("unb_"), f"leaked non-unbanked rec: {r.id}"
