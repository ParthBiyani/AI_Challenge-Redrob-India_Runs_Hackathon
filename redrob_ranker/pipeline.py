import csv

from redrob_ranker.data import iter_candidates
from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.scoring import load_weights, score_candidate

HEADER = ["candidate_id", "rank", "score", "reasoning"]


def rank_candidates(candidates_path, spec, weights, top_n=100):
    scored = [
        (round(score_candidate(c, spec, weights), 6), c["candidate_id"])
        for c in iter_candidates(candidates_path)
    ]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[:top_n]


def write_submission(rows, out_path, reasons=None):
    reasons = reasons or {}
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for rank, (score, cid) in enumerate(rows, start=1):
            writer.writerow([cid, rank, f"{score:.6f}", reasons.get(cid, "")])


def run(candidates_path, out_path, top_n=100):
    spec = JDSpec.load()
    weights = load_weights()
    rows = rank_candidates(candidates_path, spec, weights, top_n)
    write_submission(rows, out_path)
    return rows
