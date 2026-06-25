import argparse
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore", category=UserWarning)

from redrob_ranker.data import iter_candidates
from redrob_ranker.evaluate import ndcg_at_k
from redrob_ranker.features import extract_features
from redrob_ranker.integrity import is_honeypot
from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.ltr import FEATURE_NAMES, feature_vector
from redrob_ranker.scoring import judge_relevance, load_grades

REPO = Path(__file__).resolve().parents[1]
JUDGE_PARAMS = {"summary_weight": 0.6, "description_weight": 0.4}


def build_dataset(candidates_path, spec, grades):
    X, y = [], []
    for c in iter_candidates(candidates_path):
        feats = extract_features(c, spec)
        jr = judge_relevance(c, grades, JUDGE_PARAMS)
        tier = 0 if is_honeypot(c) else round((jr if jr is not None else 0) * 5)
        X.append(feature_vector(feats))
        y.append(tier)
    return np.array(X, dtype=float), np.array(y, dtype=float)


def ndcg_of(scores, labels, k):
    order = np.argsort(-scores)
    return ndcg_at_k([labels[i] for i in order], k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default=str(REPO / "eval" / "ltr_report.md"))
    args = ap.parse_args()
    spec, grades = JDSpec.load(), load_grades()
    X, y = build_dataset(args.candidates, spec, grades)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=0)

    model = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.05, num_leaves=31, random_state=0, verbose=-1)
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)

    ltr10, ltr50 = ndcg_of(pred, y_te, 10), ndcg_of(pred, y_te, 50)
    base_idx = FEATURE_NAMES.index("ranking_evidence")
    base10 = ndcg_of(X_te[:, base_idx], y_te, 10)
    importance = sorted(zip(FEATURE_NAMES, model.feature_importances_), key=lambda t: -t[1])

    lines = [
        "# Learning-to-rank distillation",
        "",
        "A LightGBM regressor distils the LLM judge tiers from the structured features",
        "alone. It calls no LLM at inference, so this is the ranker that scales to a",
        "200k+ production pool where exhaustive judging stops being practical.",
        "",
        f"- held-out NDCG@10 vs judge tiers: {ltr10:.4f}",
        f"- held-out NDCG@50 vs judge tiers: {ltr50:.4f}",
        f"- single-feature baseline (ranking_evidence) NDCG@10: {base10:.4f}",
        "",
        "Feature importance (gain split count):",
        "",
    ]
    lines += [f"- {name}: {int(val)}" for name, val in importance]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"LTR held-out NDCG@10={ltr10:.4f} NDCG@50={ltr50:.4f} (baseline {base10:.4f}); wrote {args.out}")


if __name__ == "__main__":
    main()
