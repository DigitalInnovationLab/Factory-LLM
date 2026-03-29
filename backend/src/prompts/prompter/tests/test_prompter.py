import pytest

from backend.src.prompts.prompter import MedicalPrompter


def test_aggregate_prompt():
    """Test aggregate prompt"""
    state_plan_dicts = [
        {
            "method": "got",
            "phase": 1,
            "current": "First plan",
            "user_input": "What is the plan?",
        },
        {
            "method": "got",
            "phase": 1,
            "current": "Second plan",
            "user_input": "What is the plan?",
        },
    ]
    prompter = MedicalPrompter()
    messages = prompter.aggregation_prompt(state_plan_dicts, **{})
    assert "Plan 1: First plan" in messages[0].content
    assert "Plan 2: Second plan" in messages[0].content

    state_answer_dicts = [
        {
            "method": "got",
            "phase": 2,
            "current": "First answer",
            "user_input": "What is the answ?",
        },
        {
            "method": "got",
            "phase": 2,
            "current": "Second answer",
            "user_input": "What is the plan?",
        },
    ]
    messages = prompter.aggregation_prompt(state_answer_dicts, **{})
    assert "Answer 1: First answer" in messages[0].content
    assert "Answer 2: Second answer" in messages[0].content


def test_generate_cot_prompt():
    """Separate test method for cot prompt"""
    prompter = MedicalPrompter()
    user_input = "User input"
    num_branches = 1
    # Case 1: Not final step & Empty current
    final_step = False
    current = ""
    messages = prompter.generate_prompt(
        num_branches, final_step, user_input, current, "cot"
    )

    assert len(messages) == 1
    assert user_input in messages[0].content
    assert (
        "1. Given the question, create a plan to answer the question."
        in messages[0].content
    )
    assert (
        "The final output response (in step 2) must be prefixed with 'Output: '"
        not in messages[0].content
    )

    # Case 2: Final step & Empty current
    final_step = True
    messages = prompter.generate_prompt(
        num_branches, final_step, user_input, current, "cot"
    )
    assert len(messages) == 1
    assert user_input in messages[0].content
    assert (
        "1. Given the question, create a plan to answer the question."
        in messages[0].content
    )
    assert (
        "The final output response (in step 2) must be prefixed with 'Output: '"
        in messages[0].content
    )

    # Case 3: Not final step & Not empty current
    final_step = False
    current = "Here is my answer"
    messages = prompter.generate_prompt(
        num_branches, final_step, user_input, current, "cot"
    )
    assert len(messages) == 2
    assert current in messages[0].content
    assert user_input in messages[1].content
    assert (
        "1. Reflect and give feedback to your previous attempt to answer the question."
        in messages[1].content
    )
    assert (
        "The final output response (in step 3) must be prefixed with 'Output: '"
        not in messages[1].content
    )

    # Case 4: Final step & Not empty current
    final_step = True
    current = "Here is my answer"
    messages = prompter.generate_prompt(
        num_branches, final_step, user_input, current, "cot"
    )
    assert len(messages) == 2
    assert current in messages[0].content
    assert user_input in messages[1].content
    assert (
        "1. Reflect and give feedback to your previous attempt to answer the question."
        in messages[1].content
    )
    assert (
        "The final output response (in step 3) must be prefixed with 'Output: '"
        in messages[1].content
    )


def test_generate_prompt():
    """Test generate prompt"""
    prompter = MedicalPrompter()
    user_input = "User input"
    num_branches = 1
    with pytest.raises(ValueError, match="Invalid technique"):
        prompter.generate_prompt(
            num_branches, False, user_input, "", "wrong method name"
        )

    messages = prompter.generate_prompt(num_branches, False, user_input, "", "io")
    assert messages[0].content == user_input

    for method in ("tot", "got"):
        messages = prompter.generate_prompt(num_branches, False, user_input, "", method)
        assert user_input in messages[0].content
        assert 'your plan must be prefixed with "Plan:"' in messages[0].content

        current = "Here is the current plan"
        messages = prompter.generate_prompt(
            num_branches, False, user_input, current, method
        )
        assert user_input in messages[0].content
        assert (
            'but the final answer must be prefixed with "Output: "'
            in messages[0].content
        )
        assert current in messages[0].content


def test_vote_prompt():
    """Test vote prompt"""
    user_input = "What is glaucoma?"
    state_plan_dicts = [
        {"phase": 1, "current": "First plan", "user_input": user_input},
        {"phase": 1, "current": "Second plan", "user_input": user_input},
    ]
    prompter = MedicalPrompter()
    messages = prompter.vote_prompt(state_plan_dicts, **{})
    assert "Plan 1: First plan" in messages[0].content
    assert "Plan 2: Second plan" in messages[0].content
    assert user_input in messages[0].content
    assert (
        '"The best choice is {s}", where s the integer id of the Plan'
        in messages[0].content
    )

    state_answer_dicts = [
        {"phase": 2, "current": "First answer", "user_input": user_input},
        {"phase": 2, "current": "Second answer", "user_input": user_input},
    ]
    messages = prompter.vote_prompt(state_answer_dicts, **{})
    assert "Answer 1: First answer" in messages[0].content
    assert "Answer 2: Second answer" in messages[0].content
    assert user_input in messages[0].content
    assert (
        '"The best choice is {s}", where s the integer id of the Answer'
        in messages[0].content
    )
