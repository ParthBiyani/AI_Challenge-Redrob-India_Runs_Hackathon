import argparse
import collections
from pathlib import Path

from redrob_ranker.data import iter_candidates


def profile(path: str | Path) -> dict:
    titles: collections.Counter = collections.Counter()
    countries: collections.Counter = collections.Counter()
    yoe_buckets: collections.Counter = collections.Counter()
    summaries: set[str] = set()
    descriptions: set[str] = set()
    total = github_linked = india = 0
    for c in iter_candidates(path):
        total += 1
        p = c["profile"]
        titles[p["current_title"]] += 1
        countries[p["country"]] += 1
        yoe_buckets[int(p["years_of_experience"] // 2 * 2)] += 1
        summaries.add(p.get("summary", ""))
        for job in c["career_history"]:
            descriptions.add(job.get("description", ""))
        if c["redrob_signals"].get("github_activity_score", -1) >= 0:
            github_linked += 1
        if "india" in (p.get("location", "") + " " + p.get("country", "")).lower():
            india += 1
    return {
        "total": total,
        "unique_titles": len(titles),
        "unique_summaries": len(summaries),
        "unique_descriptions": len(descriptions),
        "github_linked": github_linked,
        "india": india,
        "top_titles": titles.most_common(25),
        "countries": countries.most_common(),
        "yoe_buckets": sorted(yoe_buckets.items()),
    }


def _table(rows: list[tuple], headers: tuple[str, str]) -> str:
    lines = [f"| {headers[0]} | {headers[1]} |", "| --- | ---: |"]
    lines += [f"| {k} | {v} |" for k, v in rows]
    return "\n".join(lines)


def render(stats: dict) -> str:
    n = stats["total"]
    parts = [
        "# Dataset profile",
        "",
        f"- candidates: {n}",
        f"- unique current titles: {stats['unique_titles']}",
        f"- unique summaries: {stats['unique_summaries']}",
        f"- unique career descriptions: {stats['unique_descriptions']}",
        f"- github linked (score >= 0): {stats['github_linked']}",
        f"- located in india: {stats['india']}",
        "",
        "## Top current titles",
        _table(stats["top_titles"], ("title", "count")),
        "",
        "## Country",
        _table(stats["countries"], ("country", "count")),
        "",
        "## Years of experience (2-year buckets)",
        _table([(f"{a}-{a + 2}", c) for a, c in stats["yoe_buckets"]], ("band", "count")),
        "",
    ]
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="eval/eda_report.md")
    args = ap.parse_args()
    stats = profile(args.candidates)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(stats), encoding="utf-8")
    print(f"wrote {out} ({stats['total']} candidates)")


if __name__ == "__main__":
    main()
