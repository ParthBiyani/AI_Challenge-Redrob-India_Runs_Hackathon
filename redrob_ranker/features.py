from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.text import lower_narrative
from redrob_ranker.timeline import total_duration_months

OFF_DOMAIN = [
    "hr manager", "sales executive", "accountant", "marketing manager", "mechanical engineer",
    "civil engineer", "graphic designer", "content writer", "customer support",
    "operations manager", "project manager", "business analyst",
]
CORE_ROLE = [
    "ai engineer", "ml engineer", "machine learning", "data scientist", "applied scientist",
    "nlp", "research engineer", "recommendation", "search engineer", "ai specialist", "mlops",
]
DATA_ROLE = ["data engineer", "analytics engineer", "data analyst"]
SWE_ROLE = [
    "software engineer", "full stack", "frontend", "backend", "java developer",
    ".net developer", "mobile developer", "qa engineer", "devops", "cloud engineer",
]
RANKING_SYSTEM = [
    "recommendation system", "recommender", "ranking model", "ranking system", "learning to rank",
    "learning-to-rank", "search relevance", "retrieval", "semantic search", "vector search",
    "hybrid retrieval", "personalization", "ranking pipeline", "search engine", "rag", "re-ranker",
]
RESEARCH_TERMS = ["research", "phd", "thesis", "publication", "published a paper", "academic", "research lab"]
PRODUCTION_TERMS = ["production", "deployed", "shipped", "real users", "at scale", "serving", "a/b test",
                    "ab test", "live traffic", "in prod"]
NONIC_TERMS = ["engineering manager", "director", "vp ", "vice president", "head of", "architect"]


def _role_score(title_lower: str) -> float:
    if any(t in title_lower for t in CORE_ROLE):
        return 1.0
    if any(t in title_lower for t in DATA_ROLE):
        return 0.6
    if any(t in title_lower for t in SWE_ROLE):
        return 0.4
    if any(t in title_lower for t in OFF_DOMAIN):
        return 0.0
    return 0.25


def role_fit(candidate: dict) -> float:
    titles = [candidate["profile"].get("current_title", "")]
    titles += [j.get("title", "") for j in candidate["career_history"]]
    return max(_role_score(t.lower()) for t in titles)


def _term_hits(text: str, terms: list[str]) -> int:
    return sum(1 for t in terms if t in text)


def must_have_evidence(text: str, spec: JDSpec) -> float:
    total = hit = 0.0
    for group in spec.must_haves.values():
        total += group["weight"]
        if any(t in text for t in group["terms"]):
            hit += group["weight"]
    return hit / total if total else 0.0


def nice_to_have_evidence(text: str, spec: JDSpec) -> float:
    total = hit = 0.0
    for group in spec.nice_to_haves.values():
        total += group["weight"]
        if any(t in text for t in group["terms"]):
            hit += group["weight"]
    return hit / total if total else 0.0


def ranking_evidence(text: str) -> float:
    return min(_term_hits(text, RANKING_SYSTEM) / 3.0, 1.0)


def domain_fit(text: str, spec: JDSpec) -> float:
    pos = _term_hits(text, spec.positive_domains)
    neg = _term_hits(text, spec.negative_domains)
    if neg > 0 and pos == 0:
        return 0.2
    if pos > 0:
        return min(0.6 + 0.1 * pos, 1.0)
    return 0.5


def experience_fit(yoe: float, band: dict) -> float:
    if band["ideal_min"] <= yoe <= band["ideal_max"]:
        return 1.0
    if band["min"] <= yoe <= band["max"]:
        return 0.85
    dist = band["min"] - yoe if yoe < band["min"] else yoe - band["max"]
    return max(0.0, 0.85 - 0.12 * dist)


def _company_names(candidate: dict) -> list[str]:
    return [j.get("company", "").lower() for j in candidate["career_history"]]


def product_ratio(candidate: dict, spec: JDSpec) -> float:
    serv = prod = 0
    for name in _company_names(candidate):
        if any(c in name for c in spec.consulting_companies):
            serv += 1
        elif any(p in name for p in spec.product_companies):
            prod += 1
    matched = serv + prod
    return prod / matched if matched else 0.5


def consulting_only(candidate: dict, spec: JDSpec) -> bool:
    names = _company_names(candidate)
    return bool(names) and all(any(c in n for c in spec.consulting_companies) for n in names)


def location_fit(candidate: dict, spec: JDSpec) -> float:
    p = candidate["profile"]
    loc = (p.get("location", "") + " " + p.get("country", "")).lower()
    in_india = "india" in loc
    tier1 = any(city in loc for city in spec.tier1_cities)
    relocate = candidate["redrob_signals"].get("willing_to_relocate", False)
    if in_india and tier1:
        return 1.0
    if in_india:
        return 0.8
    if relocate:
        return 0.4
    return 0.2


def external_validation(candidate: dict, text: str) -> float:
    score = 0.0
    gh = candidate["redrob_signals"].get("github_activity_score", -1)
    if gh > 0:
        score += min(gh / 100.0, 1.0) * 0.7
    if any(t in text for t in ("open source", "open-source", "contributor", "maintainer", "published")):
        score += 0.3
    return min(score, 1.0)


def looks_research_only(text: str) -> bool:
    return _term_hits(text, RESEARCH_TERMS) >= 2 and _term_hits(text, PRODUCTION_TERMS) == 0


def avg_tenure_months(candidate: dict) -> float:
    jobs = candidate["career_history"]
    return total_duration_months(jobs) / len(jobs) if jobs else 0.0


def title_chaser(candidate: dict) -> bool:
    jobs = candidate["career_history"]
    return len(jobs) >= 3 and avg_tenure_months(candidate) < 18


def extract_features(candidate: dict, spec: JDSpec) -> dict:
    text = lower_narrative(candidate)
    yoe = candidate["profile"].get("years_of_experience", 0) or 0
    loc = (candidate["profile"].get("location", "") + " " + candidate["profile"].get("country", "")).lower()
    return {
        "role_fit": role_fit(candidate),
        "must_have_evidence": must_have_evidence(text, spec),
        "ranking_evidence": ranking_evidence(text),
        "nice_to_have": nice_to_have_evidence(text, spec),
        "domain_fit": domain_fit(text, spec),
        "experience_fit": experience_fit(yoe, spec.experience_band),
        "product_ratio": product_ratio(candidate, spec),
        "location_fit": location_fit(candidate, spec),
        "external_validation": external_validation(candidate, text),
        "consulting_only": consulting_only(candidate, spec),
        "research_only": looks_research_only(text),
        "title_chaser": title_chaser(candidate),
        "non_india": "india" not in loc,
    }
