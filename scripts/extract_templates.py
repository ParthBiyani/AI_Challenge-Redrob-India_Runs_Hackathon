import argparse
import json
from pathlib import Path

from redrob_ranker.data import iter_candidates
from redrob_ranker.text import normalize_template

REPO = Path(__file__).resolve().parents[1]


def collect(candidates_path: str):
    summaries: dict[str, list] = {}
    descriptions: dict[str, list] = {}
    for c in iter_candidates(candidates_path):
        s = c["profile"].get("summary", "").strip()
        if s:
            key = normalize_template(s)
            slot = summaries.setdefault(key, [0, s])
            slot[0] += 1
        for job in c["career_history"]:
            d = job.get("description", "").strip()
            if d:
                key = normalize_template(d)
                slot = descriptions.setdefault(key, [0, d])
                slot[0] += 1
    return summaries, descriptions


def dump(table: dict, path: Path) -> int:
    rows = sorted(table.items(), key=lambda kv: -kv[1][0])
    with path.open("w", encoding="utf-8") as f:
        for idx, (key, (count, example)) in enumerate(rows):
            f.write(json.dumps({"idx": idx, "key": key, "count": count, "example": example}, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--outdir", default=str(REPO / "eval"))
    args = ap.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    summaries, descriptions = collect(args.candidates)
    ns = dump(summaries, out / "templates_summary.jsonl")
    nd = dump(descriptions, out / "templates_description.jsonl")
    print(f"wrote {ns} summary templates and {nd} description templates to {out}")


if __name__ == "__main__":
    main()
