from pathlib import Path

from redrob_ranker.data import load_candidates
from redrob_ranker.features import extract_features
from redrob_ranker.jd_spec import JDSpec

FIXTURE = Path(__file__).parent / "fixtures" / "sample_candidates.jsonl"
STRONG = {"CAND_0002025", "CAND_0000031", "CAND_0005260"}
OFF_DOMAIN = {"CAND_0002164", "CAND_0004989"}


def _features_by_id() -> dict[str, dict]:
    spec = JDSpec.load()
    return {c["candidate_id"]: extract_features(c, spec) for c in load_candidates(FIXTURE)}


def test_strong_fits_score_high():
    feats = _features_by_id()
    for cid in STRONG:
        f = feats[cid]
        assert f["role_fit"] == 1.0
        assert f["must_have_evidence"] >= 0.6
        assert f["ranking_evidence"] >= 0.6


def test_off_domain_collapses():
    feats = _features_by_id()
    for cid in OFF_DOMAIN:
        f = feats[cid]
        assert f["role_fit"] == 0.0
        assert f["must_have_evidence"] == 0.0


def test_non_india_down_weighted():
    f = _features_by_id()["CAND_0000001"]
    assert f["non_india"] is True
    assert f["location_fit"] <= 0.4
