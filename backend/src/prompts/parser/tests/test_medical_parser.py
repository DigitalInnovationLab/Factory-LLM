from backend.src.prompts.parser import MedicalParser


def test_parse_aggregate():
    """Test parse aggregation"""
    states = [{"method": "got", "phase": 1}]
    texts = ["Plan: Aggregated plan 1", "Plan: Aggregated plan 2", "Answer: Answer 1"]
    parser = MedicalParser()
    result = parser.parse_aggregation_answer(states, texts)

    assert len(result) == 3
    assert result[0]["current"] == "Aggregated plan 1"
    assert result[1]["current"] == "Aggregated plan 2"
    assert result[2]["current"] == "Answer: Answer 1"

    states = [{"method": "got", "phase": 2}]
    texts = [
        "Output: Aggregated answer 1",
        "Output: Aggregated answer 2",
        "Answer: Answer 1",
    ]
    result = parser.parse_aggregation_answer(states, texts)

    assert len(result) == 3
    assert result[0]["current"] == "Aggregated answer 1"
    assert result[1]["current"] == "Aggregated answer 2"
    assert result[2]["current"] == "Answer: Answer 1"


def test_parse_generate():
    """Test parse generation"""
    state = {"method": "io", "phase": 0, "current": ""}
    texts = ["Here is the answer for io"]
    parser = MedicalParser()
    result = parser.parse_generate_answer(state, texts)
    assert len(result) == 1
    assert result[0]["current"] == "Here is the answer for io"

    for method in ("tot", "got", "cot"):
        if method != "cot":
            state = {"method": method, "phase": 0, "current": ""}
            texts = ["Plan: Plan 1", "Plan: Plan 2", "Answer: Plan 3"]
            result = parser.parse_generate_answer(state, texts)
            assert len(result) == 3
            assert result[0]["current"] == "Plan 1"
            assert result[0]["phase"] == 1
            assert result[1]["current"] == "Plan 2"
            assert result[0]["phase"] == 1
            assert result[2]["current"] == "Answer: Plan 3"
            assert result[0]["phase"] == 1

        state = {"method": method, "phase": 1, "current": "Current plan"}
        texts = ["Output: Output 1", "Output: Output 2", "Answer: Plan 3"]
        result = parser.parse_generate_answer(state, texts)
        assert len(result) == 3
        assert result[0]["current"] == "Output 1"
        assert result[0]["phase"] == 2
        assert result[1]["current"] == "Output 2"
        assert result[0]["phase"] == 2
        assert result[2]["current"] == "Answer: Plan 3"
        assert result[0]["phase"] == 2


def test_parse_vote():
    """Test parse vote"""
    states = [{"id": 1, "current": "Current 1"}, {"id": 2, "current": "Current 2"}]
    choices = [
        "The best choice is 1",
        "I feel the best choice is 2",
        "I think the best choice is 1",
        "choice is 1",  # Invalid
    ]
    parser = MedicalParser()
    n = 1
    result = parser.parse_vote_answer(states, choices, n)
    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["current"] == "Current 1"

    n = 2
    result = parser.parse_vote_answer(states, choices, n)
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["current"] == "Current 1"
    assert result[1]["id"] == 2
    assert result[1]["current"] == "Current 2"
