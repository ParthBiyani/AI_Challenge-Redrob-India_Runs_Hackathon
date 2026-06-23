import datetime

AS_OF = datetime.date(2026, 6, 24)


def parse_date(s: str | None) -> datetime.date | None:
    if not s:
        return None
    try:
        return datetime.date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def job_end(job: dict, as_of: datetime.date = AS_OF) -> datetime.date:
    if job.get("is_current") or not job.get("end_date"):
        return as_of
    return parse_date(job.get("end_date")) or as_of


def career_span_months(career: list[dict], as_of: datetime.date = AS_OF) -> float:
    starts = [d for d in (parse_date(j.get("start_date")) for j in career) if d]
    if not starts:
        return 0.0
    ends = [job_end(j, as_of) for j in career]
    return (max(ends) - min(starts)).days / 30.4


def total_duration_months(career: list[dict]) -> int:
    return sum((j.get("duration_months") or 0) for j in career)
