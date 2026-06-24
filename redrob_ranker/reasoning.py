from redrob_ranker.timeline import AS_OF, parse_date

JD_SKILL_HINTS = [
    "learning to rank", "learning-to-rank", "faiss", "rag", "vector search", "semantic search",
    "embeddings", "elasticsearch", "opensearch", "recommendation", "information retrieval",
    "ranking", "lora", "qlora", "ndcg",
]


def _relevant_skill(candidate: dict) -> str | None:
    for s in candidate.get("skills", []):
        name = s.get("name", "")
        if name.lower() in JD_SKILL_HINTS:
            return name
    return None


def _strengths(candidate: dict, f: dict) -> list[str]:
    out = []
    if f["ranking_evidence"] >= 0.66:
        out.append("history shows shipped ranking or retrieval work")
    if f["must_have_evidence"] >= 0.75:
        out.append("covers the embeddings, vector search and evaluation stack the role asks for")
    elif f["must_have_evidence"] >= 0.5:
        out.append("solid overlap with the retrieval and ranking stack")
    if f["product_ratio"] >= 0.66 and not f["consulting_only"]:
        out.append("product-company background rather than services")
    if f["external_validation"] >= 0.4:
        gh = candidate["redrob_signals"].get("github_activity_score", 0)
        out.append(f"external signal from github activity ({gh:.0f})")
    if f["domain_fit"] >= 1.0 and f["ranking_evidence"] < 0.66:
        out.append("clear nlp and retrieval focus")
    return out


def _concerns(candidate: dict, f: dict, as_of=AS_OF) -> list[str]:
    sig = candidate["redrob_signals"]
    out = []
    if f["non_india"]:
        out.append(f"based outside India ({candidate['profile'].get('country', '')}), no visa sponsorship")
    if f["consulting_only"]:
        out.append("entire career at services firms")
    if f["research_only"]:
        out.append("leans research over production")
    yoe = candidate["profile"].get("years_of_experience", 0)
    if f["experience_fit"] < 0.85:
        out.append(f"{yoe:.1f} years sits outside the 5-9 band")
    rr = sig.get("recruiter_response_rate", 0) or 0
    if rr < 0.2:
        out.append(f"low recruiter response rate ({rr:.2f})")
    last = parse_date(sig.get("last_active_date"))
    if last and (as_of - last).days > 180:
        out.append(f"inactive for about {(as_of - last).days // 30} months")
    notice = sig.get("notice_period_days", 0)
    if notice >= 90:
        out.append(f"{notice}-day notice period")
    if f["title_chaser"]:
        out.append("short tenures suggest frequent switching")
    return out


def reason_for(candidate: dict, f: dict, rank: int, as_of=AS_OF) -> str:
    p = candidate["profile"]
    title = p.get("current_title", "candidate")
    yoe = p.get("years_of_experience", 0)
    city = p.get("location", "").split(",")[0]
    subject = f"{title} with {yoe:.1f} years"
    if f["location_fit"] >= 0.8 and city:
        subject += f" in {city}"

    strengths = _strengths(candidate, f)
    skill = _relevant_skill(candidate)
    if skill and len(strengths) < 3:
        strengths.append(f"lists {skill} as a skill")
    concerns = _concerns(candidate, f, as_of)

    if rank <= 10:
        lead = subject
        body = "; ".join(strengths[:2]) if strengths else "strong overall match to the role"
        text = f"{lead}; {body}."
        if concerns:
            text += f" Minor concern: {concerns[0]}."
    elif rank <= 50:
        body = "; ".join(strengths[:2]) if strengths else "reasonable match"
        text = f"{subject}; {body}."
        if concerns:
            text += f" Concern: {concerns[0]}."
    else:
        keep = strengths[:1] or ["adjacent experience"]
        text = f"{subject}; {keep[0]}, included as lower-confidence filler."
        if concerns:
            text += f" Concerns: {', '.join(concerns[:2])}."
    return text
