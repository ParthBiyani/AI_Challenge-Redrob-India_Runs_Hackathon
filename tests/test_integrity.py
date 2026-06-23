from pathlib import Path

from redrob_ranker.data import load_candidates
from redrob_ranker.integrity import impossibility_flags, is_honeypot

FIXTURE = Path(__file__).parent / "fixtures" / "sample_candidates.jsonl"
HONEYPOTS = {
    "CAND_0003430",
    "CAND_0003582",
    "CAND_0010770",
    "CAND_0039754",
    "CAND_0007353",
}


def test_fixture_honeypots_detected_without_false_positives():
    for c in load_candidates(FIXTURE):
        cid = c["candidate_id"]
        if cid in HONEYPOTS:
            assert is_honeypot(c), f"missed honeypot {cid}"
        else:
            assert not is_honeypot(c), f"false positive {cid}: {impossibility_flags(c)}"


def test_experience_exceeding_timeline():
    c = {
        "profile": {"years_of_experience": 14},
        "career_history": [
            {"start_date": "2025-06-01", "end_date": None, "is_current": True, "duration_months": 12}
        ],
        "skills": [],
        "redrob_signals": {},
    }
    assert "experience_exceeds_timeline" in impossibility_flags(c)


def test_expert_skill_with_zero_months():
    c = {
        "profile": {"years_of_experience": 6},
        "career_history": [
            {"start_date": "2020-01-01", "end_date": None, "is_current": True, "duration_months": 72}
        ],
        "skills": [{"name": "RAG", "proficiency": "expert", "duration_months": 0}],
        "redrob_signals": {},
    }
    assert "expert_skill_zero_months" in impossibility_flags(c)
