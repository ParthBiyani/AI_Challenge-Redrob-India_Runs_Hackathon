from pathlib import Path

import yaml

from redrob_ranker.features import extract_features
from redrob_ranker.integrity import is_honeypot
from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.timeline import AS_OF, parse_date

WEIGHTS_PATH = Path(__file__).resolve().parents[1] / "configs" / "weights.yaml"


def load_weights(path: str | Path = WEIGHTS_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


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


def rubric_score(features: dict, weights: dict) -> float:
    base = sum(w * features[name] for name, w in weights["components"].items())
    gate = 1.0
    for name, mult in weights["gates"].items():
        if features.get(name):
            gate *= mult
    return base * gate


def score_candidate(candidate: dict, spec: JDSpec, weights: dict, as_of=AS_OF) -> float:
    if is_honeypot(candidate, as_of):
        return 0.0
    features = extract_features(candidate, spec)
    base = rubric_score(features, weights)
    return base * availability_multiplier(candidate, weights["behavioral"], as_of)
