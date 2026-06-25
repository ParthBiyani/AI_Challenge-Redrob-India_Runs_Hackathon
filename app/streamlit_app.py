import json
from pathlib import Path

import pandas as pd
import streamlit as st

from redrob_ranker.features import extract_features
from redrob_ranker.jd_spec import JDSpec
from redrob_ranker.reasoning import reason_for
from redrob_ranker.scoring import load_grades, load_weights, score_candidate

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "tests" / "fixtures" / "sample_candidates.jsonl"


@st.cache_resource
def setup():
    return JDSpec.load(), load_weights(), load_grades()


def parse_jsonl(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def rank(candidates, spec, weights, grades, top_n):
    scored = sorted(
        ((score_candidate(c, spec, weights, grades), c) for c in candidates),
        key=lambda x: (-x[0], x[1]["candidate_id"]),
    )
    rows = []
    for position, (score, c) in enumerate(scored[:top_n], start=1):
        p = c["profile"]
        rows.append({
            "rank": position,
            "candidate_id": c["candidate_id"],
            "score": round(score, 4),
            "title": p.get("current_title"),
            "years": p.get("years_of_experience"),
            "location": p.get("location"),
            "reasoning": reason_for(c, extract_features(c, spec), position),
        })
    return rows


st.set_page_config(page_title="Redrob candidate ranker", layout="wide")
st.title("Redrob candidate ranker")
st.caption(
    "Ranks candidates against the Senior AI Engineer job description. "
    "Relevance comes from offline LLM grades of each profile; structured modifiers "
    "(experience band, location, availability, product-vs-services) order within a tier; "
    "an integrity gate drops logically impossible honeypot profiles."
)

spec, weights, grades = setup()

source = st.radio("Candidates", ["Bundled sample", "Upload JSONL"], horizontal=True)
if source == "Upload JSONL":
    uploaded = st.file_uploader("candidates.jsonl (up to 100)", type=["jsonl", "json"])
    candidates = parse_jsonl(uploaded.read().decode("utf-8")) if uploaded else []
else:
    candidates = parse_jsonl(SAMPLE.read_text(encoding="utf-8"))

if not candidates:
    st.info("Upload a candidates JSONL file, or switch to the bundled sample.")
else:
    top_n = st.slider("Show top", 5, min(100, len(candidates)), min(20, len(candidates)))
    rows = rank(candidates, spec, weights, grades, top_n)
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
