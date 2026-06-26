# The Data & AI Challenge
India Runs Hackathon by Redrob AI

Submission for **India Runs by Redrob AI - Track 1: The Data & AI Challenge**
(the Intelligent Candidate Discovery & Ranking Challenge).

Given one job description (Senior AI Engineer, Founding Team) and a pool of 100,000
candidates, this system returns the **top 100, ranked best-fit first**, with a short
grounded justification for each. It ranks the way a recruiter reads, not the way a
keyword filter matches.

## Result at a glance

- Top 20 are uniformly senior AI / ML / NLP / search / recommendation engineers, all
  in the 5-9 year band the JD asks for, all India-located.
- **0 honeypots in the top 100** (the disqualification trap that catches naive
  embedding rankers - see below).
- The official `validate_submission.py` passes.
- The ranking step runs on **CPU, offline, in ~35 seconds** on 100k candidates, well
  inside the 5-minute / 16 GB / no-network budget.
- `pytest`: 30 tests passing, CI green.

## Quickstart

```bash
pip install -e .                       # numpy, scipy, pandas, pyarrow, pyyaml
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
python validate_submission.py submission.csv      # -> "Submission is valid."
```

The ranking step depends only on the candidate file and a small shipped artifact
(`eval/template_grades.json`). It makes no network or LLM calls.

## How it works

The challenge is built to punish keyword matching. Skills are close to uniform noise
(about 12,200 of the 100k list each skill, including HTML and NLP), so counting AI
skills ranks HR Managers above ML Engineers, which is exactly what the provided
`sample_submission.csv` demonstrates. The signal lives in the free text: the summary
and the career-history descriptions.

Two facts shape the design:

1. The pool is generated from only **120 distinct profile templates** (76 summaries +
   44 career descriptions, after normalising out numbers). So we judge each unique
   narrative once and let every candidate inherit its grade.
2. About 80 **honeypots** carry logically impossible profiles, and several are given
   the strongest JD-relevant text on purpose to bait embedding rankers into the top
   10. Ranking more than 10% of them disqualifies the submission.

```
 OFFLINE PRE-COMPUTATION                     RANKING STEP  (rank.py, CPU, no network)
 ----------------------                      ------------------------------------------
 extract 120 templates                       load candidates + template grades
        |                                              |
        v                                              v
 grade each 0-5 with an                        judge relevance  (summary 0.6 + best desc 0.4)
 offline LLM judge (Claude)                            |
        |                                              x  structured modifiers (band, location,
        v                                              |  product-vs-services, github)
 eval/template_grades.json  ----------------->         x  bounded availability multiplier
                                                       x  disqualifier gates
                                                       |
                                              integrity gate: honeypots -> 0
                                                       |
                                                       v
                                              top 100 + grounded reasoning -> submission.csv
```

**1. Offline LLM judge (relevance).** Claude (Opus 4.8) read each of the 120 templates
and graded it 0-5 against the JD (`oracle/grade_offline.py`). Tiers run from 5 (senior
engineer who shipped search/retrieval/ranking with hybrid retrieval, learning-to-rank
and evaluation) down to 0 (off-domain, or off-domain padded with AI buzzwords). The
pyramid - 29 candidates at tier 5, 150 at tier 4, 1,000 at tier 3 - matches the JD
line "we'd rather see 10 great matches than 1000 maybes". This is allowed: the rules
forbid LLM calls *during the ranking step*; offline judging is permitted and declared.

**2. Integrity gate (no disqualification).** `integrity.py` excludes logically
impossible profiles (experience exceeding the career timeline, "expert" skills used
zero months, a job claiming more months than its dates allow, assessment scores for
unlisted skills). High precision, catches 69 of ~80. The ablation below shows why it
matters.

**3. Structured modifiers (top-10 ordering).** Because NDCG@10 is half the score, the
top order is decided inside a tier. `features.py` scores experience-band fit, India
location and visa, product-vs-services history, and GitHub activity; these and a
bounded availability multiplier, plus multiplicative penalties for the JD's explicit
disqualifiers (consulting-only, research-without-production, non-India, title-chasing),
order candidates within their relevance tier.

**4. Reasoning.** Generated deterministically from each candidate's real fields
(`reasoning.py`), so every claim cites a genuine skill, employer or signal, varies
per candidate, and never hallucinates.

## Design choices mapped to the JD

| JD asks for | In this repo |
|---|---|
| embeddings retrieval, vector / hybrid search | judged as a tier-5 signal; ranking_evidence feature |
| evaluation frameworks (NDCG, MRR, A/B) | `evaluate.py`, ablations, judged in the rubric |
| learning-to-rank (XGBoost/neural) | `ltr.py` distillation, NDCG@10 0.94 with no LLM |
| reject keyword-stuffers and research-only | judge grades them 0; deterministic disqualifier gates |
| down-weight unavailable / non-India | bounded availability multiplier; location gate |
| latency-quality tradeoff at scale | offline judge for quality, distilled LightGBM ranker for scale |

## Validation (there is no live leaderboard)

- `tests/test_anchors.py`: every honeypot excluded, the hand-checked strong fits land
  top-5, off-domain below them, non-India penalised.
- `eval/ablations.md`: without the integrity gate, honeypots reach the top 10 and
  **NDCG@10 falls from 1.00 to 0.84**. Rubric-only (no judge) reaches 0.87, judge-only
  reaches 1.00 - the judge plus modifiers is the combination.
- `eval/ltr_report.md`: a features-only LightGBM ranker recovers the judge ordering at
  NDCG@10 0.94, the no-LLM ranker for a 200k+ production pool.
- Manual top-20 inspection.

## Reproducing from scratch

```bash
pip install -e ".[precompute]"
python scripts/extract_templates.py --candidates ./candidates.jsonl   # -> eval/templates_*.jsonl
python oracle/grade_offline.py                                         # -> eval/template_grades.json
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

The judge grades in `oracle/grade_offline.py` are committed, so `rank.py` reproduces
the exact submission without re-running the judge. `scripts/grade_templates.py` is the
alternative path that regenerates the grades through the Anthropic API.

### Docker

```bash
docker build -t redrob-ranker .
docker run --rm -v "$PWD/candidates.jsonl:/app/candidates.jsonl" redrob-ranker
```

### Demo app

```bash
streamlit run app/streamlit_app.py
```

Hosted on Streamlit Community Cloud (link in `submission_metadata.yaml`). Runs the
ranker on a small uploaded sample and shows scores + reasoning.

## Repo layout

```
rank.py                 ranking entrypoint (reproduce command)
configs/                jd_spec.yaml (the JD rubric), weights.yaml (tunable)
redrob_ranker/          data, text, timeline, jd_spec, features, integrity,
                        scoring, reasoning, evaluate, pipeline, eda, oracle, ltr
oracle/grade_offline.py the offline judge grades (0-5 per template)
scripts/                extract_templates, grade_templates (api), run_ablations, train_ltr, build_fixture
eval/                   template grades, ablations, ltr report, eda report, metrics
tests/                  schema, integrity, features, metrics, anchors, output (+ curated fixture)
app/streamlit_app.py    demo sandbox
docs/METHODOLOGY.md     full write-up
Dockerfile              CPU-only reproduction of the ranking step
```

## AI tools declaration

Claude (Opus 4.8, via Claude Code) was used for engineering and, offline, as the
relevance judge that graded the 120 profile templates. The ranking step makes no LLM
or network calls. See `submission_metadata.yaml`.

## License

MIT, see `LICENSE`.
