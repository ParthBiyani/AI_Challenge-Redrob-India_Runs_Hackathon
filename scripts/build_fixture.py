import argparse
import json
from pathlib import Path

from redrob_ranker.data import iter_candidates

# curated ids spanning the trap taxonomy, reused for the demo sample and anchor tests
CURATED = {
    "CAND_0002025": "strong fit, senior ai engineer, hybrid retrieval and ltr",
    "CAND_0000031": "strong fit, recommendation and ranking at product companies",
    "CAND_0005260": "strong fit, nlp rag and vector search",
    "CAND_0003977": "fit, recommendation systems engineer",
    "CAND_0001930": "fit, senior software engineer ml with ranking",
    "CAND_0000422": "research decoy, ai research engineer analytics only",
    "CAND_0000705": "research decoy, ai research engineer",
    "CAND_0000001": "non india, backend data engineer in toronto",
    "CAND_0000190": "adjacent, data warehouse engineer",
    "CAND_0000043": "adjacent, cloud engineer",
    "CAND_0004989": "off domain stuffer, hr manager",
    "CAND_0001218": "off domain stuffer, graphic designer",
    "CAND_0002164": "off domain stuffer, marketing manager",
    "CAND_0003430": "honeypot, claims 13.7y on an 11 month career",
    "CAND_0003582": "honeypot, expert skills with zero months used",
    "CAND_0010770": "honeypot, recommendation engineer 15y on 87 months",
    "CAND_0039754": "honeypot, applied scientist 16y impossible",
    "CAND_0007353": "honeypot, inflated current job duration",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="tests/fixtures/sample_candidates.jsonl")
    args = ap.parse_args()
    wanted = set(CURATED)
    found: dict[str, dict] = {}
    for c in iter_candidates(args.candidates):
        if c["candidate_id"] in wanted:
            found[c["candidate_id"]] = c
            if len(found) == len(wanted):
                break
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for cid in sorted(found):
            f.write(json.dumps(found[cid], ensure_ascii=False) + "\n")
    print(f"wrote {len(found)} of {len(wanted)} to {out}")
    missing = wanted - set(found)
    if missing:
        print(f"missing: {sorted(missing)}")


if __name__ == "__main__":
    main()
