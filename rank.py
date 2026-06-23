import argparse

from redrob_ranker.pipeline import run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="submission.csv")
    args = ap.parse_args()
    rows = run(args.candidates, args.out)
    print(f"wrote {len(rows)} ranked candidates to {args.out}")


if __name__ == "__main__":
    main()
