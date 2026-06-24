import argparse
import json
import os
from pathlib import Path

from redrob_ranker.data import iter_candidates
from redrob_ranker.oracle import grade_batch

REPO = Path(__file__).resolve().parents[1]


def load_env() -> None:
    env = REPO / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def unique_texts(candidates_path: str) -> tuple[list[str], list[str]]:
    summaries: set[str] = set()
    descriptions: set[str] = set()
    for c in iter_candidates(candidates_path):
        s = c["profile"].get("summary", "").strip()
        if s:
            summaries.add(s)
        for job in c["career_history"]:
            d = job.get("description", "").strip()
            if d:
                descriptions.add(d)
    return sorted(summaries), sorted(descriptions)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default=str(REPO / "eval" / "template_grades.json"))
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    import anthropic

    load_env()
    client = anthropic.Anthropic()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"summaries": {}, "descriptions": {}}

    summaries, descriptions = unique_texts(args.candidates)
    if args.limit:
        summaries = summaries[: args.limit]
        descriptions = descriptions[: args.limit]

    for kind, texts, key in (("summary", summaries, "summaries"), ("career description", descriptions, "descriptions")):
        store = data[key]
        todo = [t for t in texts if t not in store]
        print(f"{kind}: {len(texts)} unique, {len(todo)} to grade")
        for start in range(0, len(todo), args.batch_size):
            batch = todo[start : start + args.batch_size]
            try:
                graded = grade_batch(client, batch, kind, args.model)
            except Exception as exc:
                print(f"  batch at {start} failed: {exc}")
                continue
            for i, text in enumerate(batch):
                if i in graded:
                    store[text] = list(graded[i])
            if start % (args.batch_size * 20) == 0:
                out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    print(f"saved {len(data['summaries'])} summary and {len(data['descriptions'])} description grades to {out}")


if __name__ == "__main__":
    main()
