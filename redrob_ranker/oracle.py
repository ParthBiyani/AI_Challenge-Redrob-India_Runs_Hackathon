import json
import re

RUBRIC = """You screen candidates for a Senior AI Engineer role at Redrob AI, an AI-native talent
platform. The role owns the ranking, retrieval and matching systems: embeddings-based retrieval,
vector or hybrid search, learning-to-rank, and rigorous evaluation (NDCG, MRR, A/B testing). The
company wants someone who has actually built and shipped these systems in production at a product
company, with 5 to 9 years of applied ML experience.

Grade how well a snippet of a candidate's profile text fits this role, on this 0 to 5 scale:
5  built and shipped production ranking, search, recommendation or retrieval systems, with concrete
   evidence of embeddings, vector or hybrid search, learning-to-rank and evaluation.
4  strong production retrieval, ranking, search, recsys or applied NLP work, most of the must-haves.
3  relevant ML or data engineering with some retrieval, ranking, search or NLP exposure.
2  adjacent software or data engineering with little retrieval or ranking signal.
1  tangential technical work, not retrieval or ranking.
0  unrelated domain (hr, sales, marketing, accounting, mechanical or civil engineering, design,
   content, operations, support), or pure research with no production, or primarily computer vision,
   speech or robotics without nlp or information retrieval.

Judge only the text given. Reward concrete evidence of building these systems over keyword stuffing.
A buzzword list without a system behind it is not a 5. Plain language describing a real recommendation
or search system at a product company can be a 5."""

OUTPUT_INSTRUCTION = (
    'Return only a JSON array, one object per snippet, as '
    '[{"index": <int>, "grade": <0-5 int>, "reason": "<short phrase>"}]. No prose outside the JSON.'
)


def build_batch_prompt(texts: list[str], kind: str) -> str:
    snippets = "\n\n".join(f"[{i}] {t}" for i, t in enumerate(texts))
    return (
        f"Grade each of these {len(texts)} candidate {kind} snippets for the role.\n"
        f"{OUTPUT_INSTRUCTION}\n\n{snippets}"
    )


def extract_json_array(text: str) -> list:
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    raw = fenced.group(1) if fenced else text[text.find("[") : text.rfind("]") + 1]
    return json.loads(raw)


def grade_batch(client, texts: list[str], kind: str, model: str) -> dict[int, tuple[int, str]]:
    msg = client.messages.create(
        model=model,
        system=RUBRIC,
        max_tokens=2000,
        messages=[{"role": "user", "content": build_batch_prompt(texts, kind)}],
    )
    items = extract_json_array(msg.content[0].text)
    return {int(it["index"]): (int(it["grade"]), it.get("reason", "")) for it in items}


def grade_unique(client, texts: list[str], kind: str, model: str, batch_size: int = 12) -> dict[str, tuple[int, str]]:
    out: dict[str, tuple[int, str]] = {}
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        graded = grade_batch(client, batch, kind, model)
        for local_idx, text in enumerate(batch):
            if local_idx in graded:
                out[text] = graded[local_idx]
    return out
