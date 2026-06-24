from redrob_ranker.oracle import build_batch_prompt, extract_json_array


def test_build_prompt_lists_snippets():
    prompt = build_batch_prompt(["alpha", "beta"], "summary")
    assert "[0] alpha" in prompt
    assert "[1] beta" in prompt


def test_extract_json_array_with_fence():
    raw = 'sure\n```json\n[{"index": 0, "grade": 5, "reason": "x"}]\n```'
    assert extract_json_array(raw)[0]["grade"] == 5


def test_extract_json_array_bare():
    assert extract_json_array('[{"index": 0, "grade": 3, "reason": "y"}]')[0]["index"] == 0
