import math

RELEVANT_TIER = 3


def dcg_at_k(grades: list[float], k: int) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(grades[:k]))


def ndcg_at_k(grades: list[float], k: int, ideal: list[float] | None = None) -> float:
    ideal = sorted(ideal if ideal is not None else grades, reverse=True)
    idcg = dcg_at_k(ideal, k)
    return dcg_at_k(grades, k) / idcg if idcg else 0.0


def precision_at_k(grades: list[float], k: int, threshold: int = RELEVANT_TIER) -> float:
    if k == 0:
        return 0.0
    return sum(1 for g in grades[:k] if g >= threshold) / k


def average_precision(grades: list[float], threshold: int = RELEVANT_TIER) -> float:
    hits = 0
    running = 0.0
    for i, g in enumerate(grades, start=1):
        if g >= threshold:
            hits += 1
            running += hits / i
    total = sum(1 for g in grades if g >= threshold)
    return running / total if total else 0.0


def reciprocal_rank(grades: list[float], threshold: int = RELEVANT_TIER) -> float:
    for i, g in enumerate(grades, start=1):
        if g >= threshold:
            return 1.0 / i
    return 0.0


def ranked_grades(ranked_ids: list[str], labels: dict[str, float]) -> list[float]:
    return [labels.get(cid, 0.0) for cid in ranked_ids]


def composite(ranked_ids: list[str], labels: dict[str, float], ideal: list[float] | None = None) -> dict:
    grades = ranked_grades(ranked_ids, labels)
    if ideal is None:
        ideal = sorted(labels.values(), reverse=True)
    metrics = {
        "ndcg@10": ndcg_at_k(grades, 10, ideal),
        "ndcg@50": ndcg_at_k(grades, 50, ideal),
        "map": average_precision(grades),
        "p@10": precision_at_k(grades, 10),
        "p@5": precision_at_k(grades, 5),
        "mrr": reciprocal_rank(grades),
    }
    metrics["composite"] = (
        0.50 * metrics["ndcg@10"]
        + 0.30 * metrics["ndcg@50"]
        + 0.15 * metrics["map"]
        + 0.05 * metrics["p@10"]
    )
    return metrics
