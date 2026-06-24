from pathlib import Path

from redrob_ranker.data import load_candidates
from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.scoring import load_grades, load_weights, score_candidate

FIXTURE = Path(__file__).parent / "fixtures" / "sample_candidates.jsonl"
STRONG = {"CAND_0002025", "CAND_0000031", "CAND_0005260"}
HONEYPOTS = {"CAND_0003430", "CAND_0003582", "CAND_0010770", "CAND_0039754", "CAND_0007353"}
OFF_DOMAIN = {"CAND_0002164", "CAND_0004989"}


def _scores() -> dict[str, float]:
    spec, weights, grades = JDSpec.load(), load_weights(), load_grades()
    return {c["candidate_id"]: score_candidate(c, spec, weights, grades) for c in load_candidates(FIXTURE)}


def test_honeypots_excluded():
    scores = _scores()
    assert all(scores[cid] == 0.0 for cid in HONEYPOTS)


def test_strong_fits_on_top():
    scores = _scores()
    order = sorted(scores, key=lambda c: -scores[c])
    assert STRONG <= set(order[:5])


def test_off_domain_below_strong_fits():
    scores = _scores()
    assert min(scores[c] for c in STRONG) > max(scores[c] for c in OFF_DOMAIN)


def test_non_india_penalised():
    scores = _scores()
    assert scores["CAND_0000001"] < min(scores[c] for c in STRONG)
