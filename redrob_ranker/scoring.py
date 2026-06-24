import json
from pathlib import Path

import yaml

from redrob_ranker.features import extract_features
from redrob_ranker.integrity import is_honeypot
from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.text import normalize_template
from redrob_ranker.timeline import AS_OF, parse_date

WEIGHTS_PATH = Path(__file__).resolve().parents[1] / "configs" / "weights.yaml"
GRADES_PATH = Path(__file__).resolve().parents[1] / "eval" / "template_grades.json"


def load_weights(path: str | Path = WEIGHTS_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_grades(path: str | Path = GRADES_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def judge_relevance(candidate: dict, grades: dict, params: dict) -> float | None:
    summaries, descriptions = grades["summaries"], grades["descriptions"]
    summary_grade = summaries.get(normalize_template(candidate["profile"].get("summary", "")))
    desc = [descriptions.get(normalize_template(j.get("description", ""))) for j in candidate["career_history"]]
    desc = [g for g in desc if g is not None]
    best_desc = max(desc) if desc else None
    if summary_grade is None and best_desc is None:
        return None
    s = summary_grade if summary_grade is not None else 0
    d = best_desc if best_desc is not None else s
    return (params["summary_weight"] * s + params["description_weight"] * d) / 5.0


def fallback_relevance(features: dict, weights: dict) -> float:
    return sum(w * features[name] for name, w in weights["fallback_components"].items())


def modifier_factor(features: dict, weights: dict) -> float:
    score = sum(w * features[name] for name, w in weights["modifier"]["components"].items())
    floor = weights["modifier"]["floor"]
    return floor + (1 - floor) * score


def gate_penalty(features: dict, weights: dict) -> float:
    penalty = 1.0
    for name, mult in weights["gates"].items():
        if features.get(name):
            penalty *= mult
    return penalty


def availability_multiplier(candidate: dict, params: dict, as_of=AS_OF) -> float:
    sig = candidate["redrob_signals"]
    mult = 1.0
    last = parse_date(sig.get("last_active_date"))
    if last:
        days = (as_of - last).days
        if days > params["inactive_days_strong"]:
            mult *= params["recency_strong_mult"]
        elif days > params["inactive_days_mild"]:
            mult *= params["recency_mild_mult"]
    rr = sig.get("recruiter_response_rate", 0) or 0
    mult *= params["response_base"] + params["response_slope"] * rr
    if sig.get("open_to_work_flag"):
        mult *= params["open_to_work_mult"]
    notice = sig.get("notice_period_days", 90)
    if notice <= params["notice_good_days"]:
        mult *= params["notice_good_mult"]
    elif notice >= params["notice_long_days"]:
        mult *= params["notice_long_mult"]
    return _clamp(mult, params["floor"], params["ceil"])


def score_candidate(candidate: dict, spec: JDSpec, weights: dict, grades: dict, as_of=AS_OF) -> float:
    if is_honeypot(candidate, as_of):
        return 0.0
    features = extract_features(candidate, spec)
    relevance = judge_relevance(candidate, grades, weights["judge"])
    if relevance is None:
        relevance = fallback_relevance(features, weights)
    return (
        relevance
        * modifier_factor(features, weights)
        * availability_multiplier(candidate, weights["behavioral"], as_of)
        * gate_penalty(features, weights)
    )
