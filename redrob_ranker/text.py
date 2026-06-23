def segments(candidate: dict) -> list[tuple[str, str]]:
    p = candidate["profile"]
    out: list[tuple[str, str]] = []
    if p.get("headline"):
        out.append(("headline", p["headline"]))
    if p.get("summary"):
        out.append(("summary", p["summary"]))
    for j in candidate["career_history"]:
        text = " ".join(x for x in (j.get("title", ""), j.get("description", "")) if x)
        if text:
            out.append(("career", text))
    return out


def narrative_text(candidate: dict) -> str:
    p = candidate["profile"]
    parts = [p.get("current_title", "")]
    parts += [t for _, t in segments(candidate)]
    return " ".join(x for x in parts if x)


def lower_narrative(candidate: dict) -> str:
    return narrative_text(candidate).lower()
