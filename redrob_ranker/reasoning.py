from redrob_ranker.text import lower_narrative
from redrob_ranker.timeline import AS_OF, parse_date

# (term to look for, human phrasing). order matters: most specific first.
EVIDENCE_TERMS = [
    ("hybrid retrieval", "hybrid retrieval"),
    ("learning-to-rank", "learning-to-rank"),
    ("learning to rank", "learning-to-rank"),
    ("recommendation system", "a recommendation system"),
    ("semantic search", "semantic search"),
    ("vector search", "vector search"),
    ("candidate-jd matching", "candidate-JD matching"),
    ("rag", "a RAG pipeline"),
    ("faiss", "FAISS retrieval"),
    ("sentence-transformers", "sentence-transformer embeddings"),
    ("embedding-based retrieval", "embedding-based retrieval"),
    ("ranking", "ranking models"),
    ("retrieval", "retrieval"),
]
EVAL_TERMS = [("ndcg", "NDCG"), ("mrr", "MRR"), ("offline-online", "offline/online eval"),
              ("a/b test", "A/B testing"), ("eval framework", "an eval framework")]
SKILL_HINTS = {"learning to rank", "learning-to-rank", "faiss", "rag", "vector search",
               "semantic search", "embeddings", "elasticsearch", "opensearch", "lora", "qlora", "ndcg"}


def _present(text, terms):
    found = []
    for needle, phrase in terms:
        if needle in text and phrase not in found:
            found.append(phrase)
    return found


def _relevant_skill(candidate):
    for s in candidate.get("skills", []):
        if s.get("name", "").lower() in SKILL_HINTS:
            return s["name"]
    return None


def _concerns(candidate, f, as_of):
    sig = candidate["redrob_signals"]
    p = candidate["profile"]
    out = []
    if f["non_india"]:
        out.append(f"based outside India ({p.get('country', '')}), no visa sponsorship")
    if f["consulting_only"]:
        out.append("entire career at services firms")
    if f["research_only"]:
        out.append("leans research over production")
    if f["experience_fit"] < 0.85:
        out.append(f"{p.get('years_of_experience', 0):.1f} years is outside the 5-9 band")
    rr = sig.get("recruiter_response_rate", 0) or 0
    if rr < 0.2:
        out.append(f"low recruiter response rate ({rr:.2f})")
    last = parse_date(sig.get("last_active_date"))
    if last and (as_of - last).days > 180:
        out.append(f"inactive for about {(as_of - last).days // 30} months")
    if sig.get("notice_period_days", 0) >= 90:
        out.append(f"{sig['notice_period_days']}-day notice period")
    if f["title_chaser"]:
        out.append("short tenures suggest frequent switching")
    return out


def reason_for(candidate, f, rank, as_of=AS_OF):
    p = candidate["profile"]
    text = lower_narrative(candidate)
    title = p.get("current_title", "candidate")
    yoe = p.get("years_of_experience", 0)
    city = p.get("location", "").split(",")[0]
    company = p.get("current_company", "")

    subject = f"{title}, {yoe:.1f}y"
    if f["location_fit"] >= 0.8 and city:
        subject += f" in {city}"

    evidence = _present(text, EVIDENCE_TERMS)[:2]
    evals = _present(text, EVAL_TERMS)[:1]
    skill = _relevant_skill(candidate)
    concerns = _concerns(candidate, f, as_of)

    strengths = []
    if evidence:
        at = f" at {company}" if company else ""
        strengths.append(f"history shows {' and '.join(evidence)}{at}")
    if evals:
        strengths.append(f"evaluation experience ({evals[0]})")
    if f["external_validation"] >= 0.4:
        gh = candidate["redrob_signals"].get("github_activity_score", 0)
        strengths.append(f"active github ({gh:.0f})")
    if skill and len(strengths) < 3:
        strengths.append(f"lists {skill}")
    if not strengths:
        strengths.append("adjacent experience")

    if rank <= 10:
        text_out = f"{subject}; {'; '.join(strengths[:2])}."
        if concerns:
            text_out += f" Minor concern: {concerns[0]}."
    elif rank <= 50:
        text_out = f"{subject}; {strengths[0]}."
        if concerns:
            text_out += f" Concern: {concerns[0]}."
    else:
        text_out = f"{subject}; {strengths[0]}, included as lower-confidence filler."
        if concerns:
            text_out += f" Concerns: {', '.join(concerns[:2])}."
    return text_out
