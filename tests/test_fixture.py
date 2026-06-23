from pathlib import Path

from redrob_ranker.data import load_candidates, validate_dataset

FIXTURE = Path(__file__).parent / "fixtures" / "sample_candidates.jsonl"


def test_fixture_loads_and_is_valid():
    cands = load_candidates(FIXTURE)
    assert len(cands) == 18
    total, issues = validate_dataset(FIXTURE)
    assert total == 18
    assert issues == []


def test_fixture_spans_trap_types():
    ids = {c["candidate_id"] for c in load_candidates(FIXTURE)}
    assert {"CAND_0002025", "CAND_0000031"} <= ids
    assert {"CAND_0003430", "CAND_0010770"} <= ids
