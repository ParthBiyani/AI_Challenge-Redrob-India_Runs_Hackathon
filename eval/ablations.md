# Ablations

Top-100 scored against the judge relevance tiers (honeypots forced to tier 0).

| variant | ndcg@10 | ndcg@50 | map | p@10 | composite | honeypots_top10 | honeypots_top100 |
|---|---|---|---|---|---|---|---|
| full | 1.0000 | 0.9695 | 1.0000 | 1.0000 | 0.9908 | 0 | 0 |
| no_integrity | 0.8416 | 0.8995 | 0.9264 | 0.8000 | 0.8696 | 2 | 4 |
| rubric_only | 0.8706 | 0.9175 | 1.0000 | 1.0000 | 0.9106 | 0 | 0 |
| judge_only | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 | 0 |

- **full**: judge grade x structured modifiers x availability x disqualifier gates, honeypots excluded.
- **no_integrity**: identical but without the honeypot exclusion. Honeypots carry strong bait text, so
  several reach the top 10 and top 100, collapsing ndcg@10 - the failure mode the challenge warns about.
- **rubric_only**: deterministic features alone (no judge). Recovers most of the top but loses resolution.
- **judge_only**: judge grade alone, no modifiers. Right tiers, but no within-tier ordering for the top 10.
