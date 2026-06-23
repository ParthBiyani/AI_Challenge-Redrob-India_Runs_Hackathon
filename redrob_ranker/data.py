import gzip
import json
import re
from pathlib import Path
from typing import Iterator

CANDIDATE_ID_RE = re.compile(r"^CAND_\d{7}$")

_REQUIRED = ("candidate_id", "profile", "career_history", "education", "skills", "redrob_signals")


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def iter_candidates(path: str | Path) -> Iterator[dict]:
    path = Path(path)
    with _open_text(path) as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def load_candidates(path: str | Path) -> list[dict]:
    return list(iter_candidates(path))


def validate_candidate(c: dict) -> list[str]:
    problems = [f"missing {k}" for k in _REQUIRED if k not in c]
    cid = c.get("candidate_id", "")
    if not CANDIDATE_ID_RE.match(cid):
        problems.append(f"bad candidate_id {cid!r}")
    return problems


def validate_dataset(path: str | Path, limit: int | None = None) -> tuple[int, list[str]]:
    seen: set[str] = set()
    issues: list[str] = []
    total = 0
    for c in iter_candidates(path):
        total += 1
        cid = c.get("candidate_id", "")
        if cid in seen:
            issues.append(f"duplicate id {cid}")
        seen.add(cid)
        issues.extend(f"{cid}: {p}" for p in validate_candidate(c))
        if limit and total >= limit:
            break
    return total, issues
