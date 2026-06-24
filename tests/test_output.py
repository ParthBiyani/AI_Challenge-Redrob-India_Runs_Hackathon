from pathlib import Path

from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.pipeline import rank_candidates, write_submission
from redrob_ranker.scoring import load_grades, load_weights

FIXTURE = Path(__file__).parent / "fixtures" / "sample_candidates.jsonl"


def _setup():
    return JDSpec.load(), load_weights(), load_grades()


def test_ranking_orders_fits_above_traps():
    spec, weights, grades = _setup()
    rows = rank_candidates(FIXTURE, spec, weights, grades, top_n=10)
    ids = [cid for _, cid in rows]
    assert "CAND_0002025" in ids[:5]
    assert "CAND_0010770" not in ids
    assert "CAND_0003430" not in ids
    scores = [s for s, _ in rows]
    assert scores == sorted(scores, reverse=True)


def test_write_submission_format(tmp_path):
    spec, weights, grades = _setup()
    rows = rank_candidates(FIXTURE, spec, weights, grades, top_n=5)
    out = tmp_path / "sub.csv"
    write_submission(rows, out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert lines[0] == "candidate_id,rank,score,reasoning"
    assert len(lines) == 6
