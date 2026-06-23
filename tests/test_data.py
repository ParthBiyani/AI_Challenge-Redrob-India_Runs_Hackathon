import json
from pathlib import Path

from redrob_ranker.data import (
    load_candidates,
    validate_candidate,
    validate_dataset,
)


def _minimal(cid="CAND_0000001"):
    return {
        "candidate_id": cid,
        "profile": {},
        "career_history": [],
        "education": [],
        "skills": [],
        "redrob_signals": {},
    }


def test_validate_ok():
    assert validate_candidate(_minimal()) == []


def test_validate_bad_id():
    assert any("candidate_id" in p for p in validate_candidate(_minimal("X123")))


def test_validate_missing_field():
    c = _minimal()
    del c["redrob_signals"]
    assert any("redrob_signals" in p for p in validate_candidate(c))


def test_iter_and_load(tmp_path: Path):
    p = tmp_path / "c.jsonl"
    rows = "\n".join(json.dumps(_minimal(f"CAND_000000{i}")) for i in range(1, 4))
    p.write_text(rows + "\n", encoding="utf-8")
    assert len(load_candidates(p)) == 3
    total, issues = validate_dataset(p)
    assert total == 3
    assert issues == []
