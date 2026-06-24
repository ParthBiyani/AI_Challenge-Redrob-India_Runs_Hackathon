import csv

from redrob_ranker.data import iter_candidates
from redrob_ranker.features import extract_features
from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.reasoning import reason_for
from redrob_ranker.scoring import load_grades, load_weights, score_candidate

HEADER = ["candidate_id", "rank", "score", "reasoning"]


def rank_candidates(candidates_path, spec, weights, grades, top_n=100):
    scored = [
        (round(score_candidate(c, spec, weights, grades), 6), c["candidate_id"])
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


def build_reasons(candidates_path, spec, ranked):
    top_ids = {cid for _, cid in ranked}
    objects = {
        c["candidate_id"]: c
        for c in iter_candidates(candidates_path)
        if c["candidate_id"] in top_ids
    }
    return {
        cid: reason_for(objects[cid], extract_features(objects[cid], spec), rank)
        for rank, (_, cid) in enumerate(ranked, start=1)
    }


def run(candidates_path, out_path, top_n=100):
    spec = JDSpec.load()
    weights = load_weights()
    grades = load_grades()
    ranked = rank_candidates(candidates_path, spec, weights, grades, top_n)
    reasons = build_reasons(candidates_path, spec, ranked)
    write_submission(ranked, out_path, reasons)
    return ranked
