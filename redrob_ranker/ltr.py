FEATURE_NAMES = [
    "role_fit",
    "must_have_evidence",
    "ranking_evidence",
    "nice_to_have",
    "domain_fit",
    "experience_fit",
    "product_ratio",
    "location_fit",
    "external_validation",
    "consulting_only",
    "research_only",
    "title_chaser",
    "non_india",
]


def feature_vector(features: dict) -> list[float]:
    return [float(features[name]) for name in FEATURE_NAMES]
