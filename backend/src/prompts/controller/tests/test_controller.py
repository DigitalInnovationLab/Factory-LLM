from unittest.mock import AsyncMock, patch

import pytest

from backend.src.llm import LlmFactory
from backend.src.prompts.controller import Controller
from backend.src.prompts.operations import (
    Aggregate,
    GraphOfOperations,
    Thought,
)
from backend.src.prompts.parser import MedicalParser
from backend.src.prompts.prompter import MedicalPrompter

# pylint: disable=unused-argument


@pytest.mark.asyncio
async def test_run():
    """Test run method inside controller"""
    goo = GraphOfOperations()
    operation1 = Aggregate()
    operation1.thoughts = [
        Thought(
            {
                "user_input": "This is user input",
                "current": "This is the plan",
                "phase": 1,
                "method": "got",
                "contexts": [],
            }
        )
    ]
    operation2 = Aggregate()
    operation2.thoughts = [
        Thought(
            {
                "user_input": "This is user input",
                "current": "This is the answer",
                "phase": 2,
                "method": "got",
                "contexts": [],
            }
        )
    ]

    goo.append_operation(operation1)
    goo.append_operation(operation2)
    llm = LlmFactory.create_llm()
    prompter = MedicalPrompter()
    parser = MedicalParser()
    with patch.object(
        operation1, "execute", new_callable=AsyncMock
    ) as mock_execute_1, patch.object(
        operation2, "execute", new_callable=AsyncMock
    ) as mock_execute_2:

        async def mock_execute_side_effect(
            lm, chat_histories, prompter, parser, **problem_parameters
        ):
            operation1.executed = True

        mock_execute_1.side_effect = mock_execute_side_effect
        mock_execute_2.side_effect = mock_execute_side_effect
        controller = Controller(llm, goo, prompter, parser, {})
        result = await controller.run([])
        assert result == "This is the answer"
        assert controller.run_executed is True
        mock_execute_1.assert_awaited_once()
        mock_execute_2.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_reasonings():
    """Test output graph method inside controller"""
    goo = GraphOfOperations()
    operation1 = Aggregate()
    thought_state_1 = {
        "user_input": "This is user input",
        "current": "This is the plan",
        "phase": 1,
        "method": "got",
        "contexts": [],
    }
    thought_state_2 = {
        "user_input": "This is user input",
        "current": "This is the answer",
        "phase": 2,
        "method": "got",
        "contexts": [],
    }
    operation1.thoughts = [Thought(thought_state_1)]
    operation2 = Aggregate()
    operation2.thoughts = [Thought(thought_state_2)]

    goo.append_operation(operation1)
    goo.append_operation(operation2)
    llm = LlmFactory.create_llm()
    prompter = MedicalPrompter()
    parser = MedicalParser()
    controller = Controller(llm, goo, prompter, parser, {})
    with patch(
        "backend.src.prompts.controller.controller.add_reasoning_steps_to_message",
        new_callable=AsyncMock,
    ) as mock_add_reasoning_steps:

        message_id = "dummy_message_id"

        await controller.store_reasonings(message_id)

        mock_add_reasoning_steps.assert_awaited_once_with(
            message_id=message_id,
            reasonning_steps=[
                ("AGGREGATE", [thought_state_1]),
                ("AGGREGATE", [thought_state_2]),
            ],
        )
