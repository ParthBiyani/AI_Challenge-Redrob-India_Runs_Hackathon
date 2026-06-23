# redrob-ranker

Candidate ranking for the Redrob Intelligent Candidate Discovery and Ranking Challenge.

Reads the job description, ranks the top 100 candidates from a 100k pool, and writes a submission CSV.
The ranking step runs on CPU within the challenge compute budget over precomputed artifacts.

Setup and full reproduction steps are documented as the project takes shape.

```
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```
