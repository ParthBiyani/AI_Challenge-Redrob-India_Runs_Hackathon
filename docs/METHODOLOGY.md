# Methodology

## The problem, restated

The job description is for a Senior AI Engineer who owns ranking, retrieval and
matching. It is deliberately written as prose, not a checklist, and it spells out
the traps: a Marketing Manager who lists every AI keyword is not a fit, while a
candidate who "built a recommendation system at a product company" is, even if they
never write the word RAG. The dataset backs this up. Skills are close to uniform
noise (about 12,200 of the 100k candidates list each skill, including HTML, NLP and
Databricks), so any approach that counts skill keywords ranks HR Managers above ML
Engineers. That is exactly the failure the provided sample_submission.csv
demonstrates.

So the real signal is in the free text: the summary and the career-history
descriptions. The task is to read those the way a recruiter would.

## The structural insight

Profiling the pool showed it is generated from a tiny template set. After
normalising out numbers (years, counts), there are only **76 distinct summary
templates and 44 distinct career-description templates**, 120 in total, and the top
nine summaries already cover 90 percent of candidates (`redrob_ranker/eda.py`,
`scripts/extract_templates.py`).

That changes the economics of judging. Instead of scoring 100k candidates we grade
each of the 120 unique narratives once, and every candidate inherits the grade of
its templates. There is no recall problem to engineer around: we judge every
archetype that exists.

## The chain of correctness

The hidden ground truth was built from a rubric the organizers handed us in the job
description. We follow that rubric in three stages.

1. **Offline LLM judge (the relevance core).** Claude (Opus 4.8) read each of the
   120 templates and graded it 0-5 against the job description
   (`oracle/grade_offline.py`, output in `eval/template_grades.json`). The tiers:
   5 is a senior engineer who shipped search/retrieval/ranking with hybrid
   retrieval, learning-to-rank and evaluation; 4 shipped one strong
   retrieval/recsys/RAG project; 3 is applied ML without retrieval depth; 2 is
   software or data engineering with only hobby ML; 0 is off-domain or a
   keyword-stuffed off-domain profile. A candidate's relevance blends its summary
   grade (0.6) and the best of its description grades (0.4). The resulting pyramid is
   29 candidates at tier 5, 150 at tier 4, 1,000 at tier 3, which matches the JD line
   "we'd rather see 10 great matches than 1000 maybes".

   This is allowed and declared. The compute rules forbid LLM calls **during the
   ranking step**; offline judging is explicitly permitted and not penalized. The
   ranking step itself makes no LLM or network calls.

2. **Deterministic integrity gate (the disqualification defense).**
   `redrob_ranker/integrity.py` flags logically impossible profiles: years of
   experience exceeding the career timeline, "expert" proficiency in skills used zero
   months, a job whose stated duration exceeds the months between its dates,
   assessment scores for skills not listed, overlapping current roles. The union of
   these high-precision checks flags 69 of the roughly 80 honeypots. Flagged
   candidates are excluded. This matters because several honeypots are given the
   strongest JD-relevant text in the dataset precisely to bait embedding rankers
   (CAND_0010770 reads as a recommendation engineer but claims 15 years on an
   87-month career). The ablation in `eval/ablations.md` shows the cost of removing
   the gate: honeypots reach the top 10 and NDCG@10 drops from 1.00 to 0.84.

3. **Structured modifiers (the within-tier ordering).** Because NDCG@10 is half the
   score, the top-10 ordering is decided inside the relevance tiers. `features.py`
   extracts experience-band fit (5-9, ideal 6-8), location (India and tier-1 cities,
   no visa sponsorship for others), product-versus-services history, and external
   validation (GitHub activity). These combine into a bounded modifier, a bounded
   availability multiplier (recency, recruiter response rate, notice period), and
   multiplicative penalties for the JD's explicit disqualifiers (consulting-only
   career, research-without-production, non-India, title-chasing). The final score is
   `relevance x modifier x availability x gates`, with honeypots forced to zero.

## Reasoning

The reasoning column is generated deterministically from each candidate's real
fields (`redrob_ranker/reasoning.py`): the retrieval and ranking terms that actually
appear in their text, a real skill from their skills list, their current employer,
years, location, and the single biggest concern (out-of-band experience, low
response rate, long notice, non-India). Because every clause comes from the profile,
the strings reference genuine facts, never hallucinate, vary candidate to candidate,
and stay consistent with the rank.

## Validation without a leaderboard

There is no live score during the competition, so validation is internal.

- **Anchor tests** (`tests/test_anchors.py`): every honeypot is excluded, the three
  hand-checked strong fits land in the top 5, off-domain profiles sit below them, and
  the non-India candidate is penalised.
- **Ablations** (`scripts/run_ablations.py`, `eval/ablations.md`): full pipeline
  versus no-integrity versus rubric-only versus judge-only, scored against the judge
  tiers.
- **Manual top-20 inspection**: uniformly senior AI/ML/NLP/search engineers, in the
  5-9 band, India-located, zero honeypots.
- **Format and DQ safety**: the provided `validate_submission.py` passes, and the
  top 100 contains zero honeypots.

## Reproducibility and compute

Two steps. Pre-computation (`scripts/extract_templates.py` then
`oracle/grade_offline.py`) produces `eval/template_grades.json`, a small artifact
that ships in the repo. The ranking step (`rank.py`) loads candidates plus that
artifact and writes the submission. It uses numpy and pandas only, runs on CPU with
no network, completes in about 35 seconds on 100k candidates, and is deterministic
(tie-break by candidate_id ascending, matching the validator).

## What we deliberately did not do

We did not build an embedding index as the load-bearing component. With only 120
unique narratives, exhaustive judging is both cheaper and more accurate than
approximate retrieval, and it sidesteps the honeypot-bait problem that an
embedding-similarity ranker walks straight into. An embedding-based hybrid retrieval
layer is the right answer at 200k+ scale, where exhaustive judging stops being
practical, and is the natural next step for the production system.
