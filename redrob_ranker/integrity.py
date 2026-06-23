from redrob_ranker.timeline import (
    AS_OF,
    career_span_months,
    job_end,
    parse_date,
    total_duration_months,
)


def impossibility_flags(candidate: dict, as_of=AS_OF) -> list[str]:
    profile = candidate["profile"]
    career = candidate["career_history"]
    skills = candidate.get("skills", [])
    signals = candidate["redrob_signals"]
    yoe = profile.get("years_of_experience", 0) or 0
    span = career_span_months(career, as_of)

    flags: list[str] = []

    if span > 0 and yoe * 12 > span + 30:
        flags.append("experience_exceeds_timeline")

    for j in career:
        start = parse_date(j.get("start_date"))
        dur = j.get("duration_months")
        if start is not None and dur is not None:
            actual = (job_end(j, as_of) - start).days / 30.4
            if dur > actual + 24:
                flags.append("job_duration_exceeds_dates")
                break

    if span > 0 and total_duration_months(career) > span * 1.8 + 6:
        flags.append("tenure_exceeds_span")

    if any(s.get("proficiency") == "expert" and (s.get("duration_months") or 0) == 0 for s in skills):
        flags.append("expert_skill_zero_months")

    listed = {s.get("name") for s in skills}
    orphans = [k for k in signals.get("skill_assessment_scores", {}) if k not in listed]
    if len(orphans) >= 3:
        flags.append("assessment_for_unlisted_skills")

    for j in career:
        start, end = parse_date(j.get("start_date")), parse_date(j.get("end_date"))
        if start and end and end < start:
            flags.append("end_before_start")
            break

    if sum(1 for j in career if j.get("is_current")) > 1:
        flags.append("multiple_current_roles")

    return flags


def is_honeypot(candidate: dict, as_of=AS_OF) -> bool:
    return bool(impossibility_flags(candidate, as_of))
