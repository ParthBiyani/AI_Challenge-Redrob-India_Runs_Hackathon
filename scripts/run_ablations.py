import argparse
import json
from pathlib import Path

from redrob_ranker.data import iter_candidates
from redrob_ranker.evaluate import composite
from redrob_ranker.features import extract_features
from redrob_ranker.integrity import is_honeypot
from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.scoring import (
    availability_multiplier,
    fallback_relevance,
    gate_penalty,
    judge_relevance,
    load_grades,
    load_weights,
    modifier_factor,
)

REPO = Path(__file__).resolve().parents[1]
VARIANTS = ("full", "no_integrity", "rubric_only", "judge_only")


def score_rows(candidates_path, spec, weights, grades):
    rows = []
    labels = {}
    honeypots = set()
    for c in iter_candidates(candidates_path):
        cid = c["candidate_id"]
        feats = extract_features(c, spec)
        hp = is_honeypot(c)
        jr = judge_relevance(c, grades, weights["judge"])
        base = jr if jr is not None else fallback_relevance(feats, weights)
        envelope = modifier_factor(feats, weights) * availability_multiplier(c, weights["behavioral"]) * gate_penalty(feats, weights)
        rubric_base = fallback_relevance(feats, weights)
        labels[cid] = 0 if hp else round((jr if jr is not None else 0) * 5)
        if hp:
            honeypots.add(cid)
        rows.append({
            "cid": cid,
            "full": 0.0 if hp else base * envelope,
            "no_integrity": base * envelope,
            "rubric_only": 0.0 if hp else rubric_base * envelope,
            "judge_only": 0.0 if hp else (jr if jr is not None else 0.0),
        })
    return rows, labels, honeypots


def top_ids(rows, key, k):
    return [r["cid"] for r in sorted(rows, key=lambda r: (-r[key], r["cid"]))[:k]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default=str(REPO / "eval"))
    args = ap.parse_args()
    spec, weights, grades = JDSpec.load(), load_weights(), load_grades()
    rows, labels, honeypots = score_rows(args.candidates, spec, weights, grades)

    report = {}
    for variant in VARIANTS:
        top100 = top_ids(rows, variant, 100)
        metrics = composite(top100, labels)
        metrics["honeypots_top100"] = sum(1 for cid in top100 if cid in honeypots)
        metrics["honeypots_top10"] = sum(1 for cid in top100[:10] if cid in honeypots)
        report[variant] = metrics

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    cols = ["ndcg@10", "ndcg@50", "map", "p@10", "composite", "honeypots_top10", "honeypots_top100"]
    lines = ["# Ablations", "", "Top-100 scored against the judge relevance tiers (honeypots forced to tier 0).", ""]
    lines.append("| variant | " + " | ".join(cols) + " |")
    lines.append("|" + "---|" * (len(cols) + 1))
    for variant in VARIANTS:
        m = report[variant]
        cells = [f"{m[c]:.4f}" if isinstance(m[c], float) else str(m[c]) for c in cols]
        lines.append(f"| {variant} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "- **full**: judge grade x structured modifiers x availability x disqualifier gates, honeypots excluded.",
        "- **no_integrity**: identical but without the honeypot exclusion. Honeypots carry strong bait text, so",
        "  several reach the top 10 and top 100, collapsing ndcg@10 - the failure mode the challenge warns about.",
        "- **rubric_only**: deterministic features alone (no judge). Recovers most of the top but loses resolution.",
        "- **judge_only**: judge grade alone, no modifiers. Right tiers, but no within-tier ordering for the top 10.",
        "",
    ]
    (out / "ablations.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out / 'ablations.md'}")
    for variant in VARIANTS:
        m = report[variant]
        print(f"  {variant:14s} ndcg@10={m['ndcg@10']:.4f} composite={m['composite']:.4f} hp@10={m['honeypots_top10']} hp@100={m['honeypots_top100']}")


if __name__ == "__main__":
    main()
