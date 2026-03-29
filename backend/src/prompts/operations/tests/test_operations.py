from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.src.llm import LlmFactory
from backend.src.models import Message, MessageRole
from backend.src.prompts.operations import Aggregate, Generate, Thought, Vote
from backend.src.prompts.parser import MedicalParser
from backend.src.prompts.prompter import MedicalPrompter

# pylint: disable=line-too-long


def test_add_predecessor():
    """Test add predecessor"""
    parent = Aggregate()
    child = Aggregate()
    child.add_predecessor(parent)
    assert len(parent.successors) == 1
    assert len(parent.predecessors) == 0
    assert len(child.predecessors) == 1
    assert len(child.successors) == 0
    assert child.predecessors[0] == parent
    assert parent.successors[0] == child


def test_add_successor():
    """test add successor"""
    parent = Aggregate()
    child = Aggregate()
    parent.add_successor(child)
    assert len(parent.successors) == 1
    assert len(parent.predecessors) == 0
    assert len(child.predecessors) == 1
    assert len(child.successors) == 0
    assert child.predecessors[0] == parent
    assert parent.successors[0] == child


def test_compose_prompt():
    """test compose successor"""
    contexts = ["This is the contexts"]
    initial_prompt = Message(content="Initial prompt", role=MessageRole.SYSTEM)
    human_message = Message(content="User input", role=MessageRole.USER)
    ai_message = Message(content="AI response", role=MessageRole.ASSISTANT)

    operation = Aggregate()
    # With contexts
    operation.compose_prompt(contexts, [initial_prompt, human_message, ai_message])

    expected_composed_messages = [
        SystemMessage(content="Initial prompt"),
        SystemMessage(
            content="""Here is the information that you know:
<Info>
This is the contexts
</Info>
You must only reply with the information from the above info. If you can't get your answer from there, say you don't know."""
        ),
        HumanMessage(content="User input"),
        AIMessage(content="AI response"),
    ]
    assert operation.composed_messages == expected_composed_messages

    # Without contexts
    operation = Aggregate()
    operation.compose_prompt([], [initial_prompt, human_message, ai_message])
    expected_composed_messages[1] = SystemMessage(
        content="<Instruction>You are not given any information related to this question. Thus, you don't need to reply to this question, ONLY REPLY YOU DON'T KNOW </Instruction>"
    )
    assert operation.composed_messages == expected_composed_messages


@pytest.mark.asyncio
async def test_generate_operation():
    """Test generate operation"""
    generate = Generate(num_branches_response=2)
    llm = LlmFactory.create_llm()

    with patch("backend.src.llm.llm_utils.query", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [
            """Here is my answer:
            Plan: This is my first plan
            """,
            """Here is my answer:
            Plan: This is my second plan
            """,
        ]

        await generate.execute(
            llm,
            [],
            MedicalPrompter(),
            MedicalParser(),
            **{
                "user_input": "User input",
                "current": "",
                "phase": 0,
                "method": "got",
                "contexts": [],
            }
        )

        assert len(generate.get_thoughts()) == 2
        assert generate.thoughts[0].state["current"] == "This is my first plan"
        assert generate.thoughts[0].state["phase"] == 1
        assert generate.thoughts[1].state["current"] == "This is my second plan"
        assert generate.thoughts[1].state["phase"] == 1

        mock_query.assert_awaited_once()
        assert generate.executed is True


@pytest.mark.asyncio
async def test_generate_cot_operation():
    """Separate Test for cot generate operation"""
    generate1 = Generate()
    generate2 = Generate()
    generate1.add_successor(generate2)
    llm = LlmFactory.create_llm()

    with patch("backend.src.llm.llm_utils.query", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [
            "Here is my answer",
        ]

        await generate1.execute(
            llm,
            [],
            MedicalPrompter(),
            MedicalParser(),
            **{
                "user_input": "User input",
                "current": "",
                "phase": 0,
                "method": "cot",
                "contexts": [],
            }
        )

        assert len(generate1.get_thoughts()) == 1
        assert generate1.thoughts[0].state["current"] == "Here is my answer"
        assert generate1.thoughts[0].state["phase"] == 1

        mock_query.assert_awaited_once()
        assert generate1.executed is True


@pytest.mark.asyncio
async def test_aggregate_operation():
    "Test Aggregate Operation"
    previous_thoughts = [
        Thought(
            {
                "user_input": "This is user input",
                "current": "This is the current plan",
                "phase": 1,
                "method": "got",
                "contexts": [],
            }
        ),
        Thought(
            {
                "user_input": "This is user input",
                "current": "This is the current plan",
                "phase": 1,
                "method": "got",
                "contexts": [],
            }
        ),
    ]
    generate = Generate()
    generate.executed = True

    aggregate = Aggregate(num_responses=2)
    aggregate.add_predecessor(generate)
    llm = LlmFactory.create_llm()
    with patch("backend.src.llm.llm_utils.query", new_callable=AsyncMock) as mock_query:
        await aggregate.execute(
            llm,
            [],
            MedicalPrompter(),
            MedicalParser(),
            **{
                "user_input": "This is user input",
                "current": "",
                "phase": 1,
                "method": "got",
                "contexts": [],
            }
        )
        assert len(aggregate.get_thoughts()) == 0

        mock_query.return_value = [
            """Here is my answer:
            Plan: This is my first plan
            """,
            """Here is my answer:
            Plan: This is my second plan
            """,
        ]
        generate.thoughts = previous_thoughts

        await aggregate.execute(
            llm,
            [],
            MedicalPrompter(),
            MedicalParser(),
            **{
                "user_input": "This is user input",
                "current": "",
                "phase": 1,
                "method": "got",
                "contexts": [],
            }
        )

        assert len(aggregate.get_thoughts()) == 2
        assert aggregate.thoughts[0].state["current"] == "This is my first plan"
        assert aggregate.thoughts[0].state["phase"] == 1
        assert aggregate.thoughts[1].state["current"] == "This is my second plan"
        assert aggregate.thoughts[1].state["phase"] == 1

        mock_query.assert_awaited_once()
        assert aggregate.executed is True


@pytest.mark.asyncio
async def test_vote_operation():
    """test Vote Operation"""
    previous_thoughts = [
        Thought(
            {
                "user_input": "This is user input",
                "current": "This is plan 1",
                "phase": 1,
                "method": "got",
                "contexts": [],
            }
        ),
        Thought(
            {
                "user_input": "This is user input",
                "current": "This is plan 2",
                "phase": 1,
                "method": "got",
                "contexts": [],
            }
        ),
    ]
    generate = Generate()
    generate.executed = True

    vote = Vote(num_responses=3, n=1)
    vote.add_predecessor(generate)

    llm = LlmFactory.create_llm()
    with patch("backend.src.llm.llm_utils.query", new_callable=AsyncMock) as mock_query:
        await vote.execute(
            llm,
            [],
            MedicalPrompter(),
            MedicalParser(),
            **{
                "user_input": "This is user input",
                "current": "",
                "phase": 1,
                "method": "got",
                "contexts": [],
            }
        )
        assert len(vote.get_thoughts()) == 0

        mock_query.return_value = [
            """Here is my answer:
            The best choice is 1
            """,
            """Here is my answer:
            The best choice is 2
            """,
            """Here is my answer:
            The best choice is 2
            """,
        ]

        generate.thoughts = previous_thoughts
        await vote.execute(
            llm,
            [],
            MedicalPrompter(),
            MedicalParser(),
            **{
                "user_input": "This is user input",
                "current": "",
                "phase": 1,
                "method": "got",
                "contexts": [],
            }
        )

        assert len(vote.get_thoughts()) == 1
        assert vote.thoughts[0].state["current"] == "This is plan 2"
        assert vote.thoughts[0].state["phase"] == 1

        mock_query.assert_awaited_once()
        assert vote.executed is True
