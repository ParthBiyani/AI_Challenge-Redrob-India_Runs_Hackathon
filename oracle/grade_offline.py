"""Relevance grades for the distinct profile templates.

Each unique summary and career-description template (after normalising out
numbers) was read against the job description and assigned a 0-5 tier by Claude
(Opus 4.8). This module records those grades by template index in
eval/templates_*.jsonl and writes eval/template_grades.json, keyed by the
normalised template text so scoring can look a candidate up by their text.
This is a pre-computation step; rank.py only reads the resulting json.

Tiers: 5 built and shipped search/retrieval/ranking/recsys with evaluation,
4 shipped one strong retrieval/recsys/rag project, 3 applied ml without
retrieval depth, 2 software/data engineering with only hobby ml, 1 tangential
technical work, 0 off-domain or keyword-stuffed.
"""

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SUMMARY_GRADES: dict[int, int] = {}
for _i in range(0, 3):
    SUMMARY_GRADES[_i] = 0          # marketing managers dabbling with chatgpt
for _i in range(3, 11):
    SUMMARY_GRADES[_i] = 2          # software/data engineers with only self-taught ml
for _i in range(11, 23):
    SUMMARY_GRADES[_i] = 0          # off-domain roles padded with ai-course buzzwords
for _i in range(23, 35):
    SUMMARY_GRADES[_i] = 3          # applied data scientists aspiring toward retrieval
for _i in range(35, 56):
    SUMMARY_GRADES[_i] = 4          # ml engineers who shipped retrieval/recsys/rag
SUMMARY_GRADES[41] = 5             # senior engineer owning the intelligence layer
for _i in range(56, 76):
    SUMMARY_GRADES[_i] = 5          # senior ai engineers across search, retrieval, ranking

DESCRIPTION_GRADES: dict[int, int] = {}
for _i in range(0, 9):
    DESCRIPTION_GRADES[_i] = 0
for _i in (9, 10, 11, 14, 23):
    DESCRIPTION_GRADES[_i] = 1
for _i in (12, 13, 15, 16, 17, 18, 20, 24):
    DESCRIPTION_GRADES[_i] = 2
for _i in (19, 21, 25, 26, 32):
    DESCRIPTION_GRADES[_i] = 3
for _i in (22, 30):
    DESCRIPTION_GRADES[_i] = 4
for _i in (27, 28, 29, 31, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43):
    DESCRIPTION_GRADES[_i] = 5


def load_keys(path: Path) -> dict[int, str]:
    keys = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        keys[row["idx"]] = row["key"]
    return keys


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--templates-dir", default=str(REPO / "eval"))
    ap.add_argument("--out", default=str(REPO / "eval" / "template_grades.json"))
    args = ap.parse_args()
    tdir = Path(args.templates_dir)
    summary_keys = load_keys(tdir / "templates_summary.jsonl")
    description_keys = load_keys(tdir / "templates_description.jsonl")
    grades = {
        "summaries": {summary_keys[i]: g for i, g in SUMMARY_GRADES.items()},
        "descriptions": {description_keys[i]: g for i, g in DESCRIPTION_GRADES.items()},
    }
    Path(args.out).write_text(json.dumps(grades, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(grades['summaries'])} summary and {len(grades['descriptions'])} description grades")


if __name__ == "__main__":
    main()
