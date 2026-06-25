# Learning-to-rank distillation

A LightGBM regressor distils the LLM judge tiers from the structured features
alone. It calls no LLM at inference, so this is the ranker that scales to a
200k+ production pool where exhaustive judging stops being practical.

- held-out NDCG@10 vs judge tiers: 0.9370
- held-out NDCG@50 vs judge tiers: 0.9847
- single-feature baseline (ranking_evidence) NDCG@10: 0.8572

Feature importance (gain split count):

- external_validation: 3482
- experience_fit: 2699
- nice_to_have: 1414
- must_have_evidence: 1207
- product_ratio: 958
- domain_fit: 729
- ranking_evidence: 686
- location_fit: 479
- role_fit: 342
- consulting_only: 4
- research_only: 0
- title_chaser: 0
- non_india: 0
