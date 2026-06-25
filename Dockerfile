FROM python:3.11-slim

WORKDIR /app
COPY . .

# installs only the project runtime dependencies (numpy, scipy, pandas, pyarrow,
# pyyaml) from pyproject; the precompute and app extras are not pulled in.
RUN pip install --no-cache-dir -e .

# mount the candidate file at runtime:
#   docker run --rm -v "$PWD/candidates.jsonl:/app/candidates.jsonl" redrob-ranker
ENTRYPOINT ["python", "rank.py"]
CMD ["--candidates", "candidates.jsonl", "--out", "submission.csv"]
