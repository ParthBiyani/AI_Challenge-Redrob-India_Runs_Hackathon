from redrob_ranker.evaluate import (
    average_precision,
    composite,
    ndcg_at_k,
    precision_at_k,
    reciprocal_rank,
)


def test_ndcg_perfect_and_zero():
    assert ndcg_at_k([3, 2, 1, 0], 4) == 1.0
    assert ndcg_at_k([0, 0, 0], 3) == 0.0


def test_ndcg_rewards_better_order():
    assert ndcg_at_k([3, 2, 1], 3) > ndcg_at_k([1, 2, 3], 3)


def test_precision_map_mrr():
    grades = [5, 0, 4, 0]
    assert precision_at_k(grades, 4) == 0.5
    assert reciprocal_rank(grades) == 1.0
    assert abs(average_precision(grades) - (1.0 + 2 / 3) / 2) < 1e-9


def test_composite_perfect_ranking():
    labels = {"a": 5, "b": 4, "c": 0}
    m = composite(["a", "b", "c"], labels)
    assert abs(m["ndcg@10"] - 1.0) < 1e-9
    assert 0.0 <= m["composite"] <= 1.0
