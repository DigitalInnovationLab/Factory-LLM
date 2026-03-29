# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.

# pylint: disable=broad-exception-caught
# pylint: disable=line-too-long

from __future__ import annotations

import itertools
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Iterator, List

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.language_models import BaseChatModel

from backend.src.models import Message, MessageRole

from ...llm import llm_utils
from ..parser import Parser
from ..prompter import Prompter
from .thought import Thought


class OperationType(Enum):
    """
    Enum to represent different operation types that can be used as unique identifiers.
    """

    GENERATE: int = 0
    AGGREGATE: int = 1
    VOTE: int = 2


class Operation(ABC):
    """
    Abstract base class that defines the interface for all operations.
    """

    _ids: Iterator[int] = itertools.count(0)

    operation_type: OperationType = None

    def __init__(self) -> None:
        """
        Initializes a new Operation instance with a unique id,
        and empty predecessors and successors.
        """
        self.id: int = next(Operation._ids)
        self.predecessors: List[Operation] = []
        self.successors: List[Operation] = []
        self.executed: bool = False
        self.composed_messages: List[BaseMessage] = []

    def can_be_executed(self) -> bool:
        """
        Checks if the operation can be executed based on its predecessors.

        :return: True if all predecessors have been executed, False otherwise.
        :rtype: bool
        """
        return all(predecessor.executed for predecessor in self.predecessors)

    def get_previous_thoughts(self) -> List[Thought]:
        """
        Iterates over all predecessors and aggregates their thoughts.

        :return: A list of all thoughts from the predecessors.
        :rtype: List[Thought]
        """
        previous_thoughts: List[Thought] = [
            thought
            for predecessor in self.predecessors
            for thought in predecessor.get_thoughts()
        ]

        return previous_thoughts

    def add_predecessor(self, operation: Operation) -> None:
        """
        Add a preceding operation and update the relationships.

        :param operation: The operation to be set as a predecessor.
        :type operation: Operation
        """
        self.predecessors.append(operation)
        operation.successors.append(self)

    def add_successor(self, operation: Operation) -> None:
        """
        Add a succeeding operation and update the relationships.

        :param operation: The operation to be set as a successor.
        :type operation: Operation
        """
        self.successors.append(operation)
        operation.predecessors.append(self)

    async def execute(
        self,
        lm: BaseChatModel,
        chat_histories: List[Message],
        prompter: Prompter,
        parser: Parser,
        **kwargs,
    ) -> None:
        """
        Execute the operation, assuring that all predecessors have been executed.

        :param lm: The language model to be used.
        :type lm: BaseChatModel
        :param chat_histories: Chat histories
        :type chat_histories: List[Message]
        :param prompter: The prompter for crafting prompts.
        :type prompter: Prompter
        :param parser: The parser for parsing responses.
        :type parser: Parser
        :param kwargs: Additional parameters for execution.
        :raises AssertionError: If not all predecessors have been executed.
        """
        assert self.can_be_executed(), "Not all predecessors have been executed"
        self.compose_prompt(kwargs["contexts"], chat_histories)
        await self._execute(lm, prompter, parser, **kwargs)
        self.executed = True

    def compose_prompt(
        self,
        contexts: List[str],
        chat_histories: List[Message],
    ):
        """
        Compose prompts with contexts and historical chats
        :param contexts: Additional context.
        :type contexts: List[str]
        :param chat_histories: Past messages in the conversation
        :type chat_histories: List[Message]
        """
        initial_prompts = [
            message
            for message in chat_histories
            if (message.role == MessageRole.SYSTEM)
        ]

        self.composed_messages.extend(
            [
                SystemMessage(content=initial_prompt.content)
                for initial_prompt in initial_prompts
            ]
        )

        # For the natural thinking/understanding of AI, the context must be placed at the top
        # to help AI understand the scenario before being given specific instructions

        # Context can be found
        if len(contexts) > 0:
            context = f"""Here is the information that you know:
            <Info>"""+'\n\n'.join(contexts)+f"""</Info>
            You must only reply with the information from the above info. If you can't get your answer from there, say you don't know."""

        # Context exists but cannot be found
        else:
            context = "<Instruction>You are not given any information related to this question. Thus, you don't need to reply to this question, ONLY REPLY YOU DON'T KNOW </Instruction>"
        self.composed_messages.append(SystemMessage(content=context))

        for chat_history in chat_histories:
            if chat_history.role == MessageRole.USER:
                self.composed_messages.append(
                    HumanMessage(content=chat_history.content)
                )
            elif chat_history.role == MessageRole.ASSISTANT:
                self.composed_messages.append(AIMessage(content=chat_history.content))

    @abstractmethod
    async def _execute(
        self,
        lm: BaseChatModel,
        prompter: Prompter,
        parser: Parser,
        **kwargs,
    ) -> None:
        """
        Abstract method for the actual execution of the operation.
        This should be implemented in derived classes.

        :param lm: The language model to be used.
        :type lm: BaseChatModel
        :param prompter: The prompter for crafting prompts.
        :type prompter: Prompter
        :param parser: The parser for parsing responses.
        :type parser: Parser
        :param kwargs: Additional parameters for execution.
        """

    @abstractmethod
    def get_thoughts(self) -> List[Thought]:
        """
        Abstract method to retrieve the thoughts associated with the operation.
        This should be implemented in derived classes.

        :return: List of associated thoughts.
        :rtype: List[Thought]
        """


class Generate(Operation):
    """
    Operation to generate thoughts.
    """

    operation_type: OperationType = OperationType.GENERATE

    def __init__(
        self, num_branches_prompt: int = 1, num_branches_response: int = 1
    ) -> None:
        """
        Initializes a new Generate operation.

        :param num_branches_prompt: Number of responses that each prompt
        should generate (passed to prompter). Defaults to 1.
        :type num_branches_prompt: int
        :param num_branches_response: Number of responses the LM
        should generate for each prompt. Defaults to 1.
        :type num_branches_response: int
        """
        super().__init__()
        self.num_branches_prompt: int = num_branches_prompt
        self.num_branches_response: int = num_branches_response
        self.thoughts: List[Thought] = []

    def get_thoughts(self) -> List[Thought]:
        """
        Returns the thoughts associated with the operation.

        :return: List of generated thoughts.
        :rtype: List[Thought]
        """
        return self.thoughts

    async def _execute(
        self,
        lm: BaseChatModel,
        prompter: Prompter,
        parser: Parser,
        **kwargs,
    ) -> None:
        """
        Executes the Generate operation by generating thoughts from the predecessors.
        The thoughts are generated by prompting the LM with the predecessors' thought states.
        If there are no predecessors, the kwargs are used as a base state.

        :param lm: The language model to be used.
        :type lm: BaseChatModel
        :param prompter: The prompter for crafting prompts.
        :type prompter: Prompter
        :param parser: The parser for parsing responses.
        :type parser: Parser
        :param kwargs: Additional parameters for execution.
        """
        previous_thoughts: List[Thought] = self.get_previous_thoughts()

        if len(previous_thoughts) == 0:
            # no predecessors, use kwargs as base state
            previous_thoughts = [Thought(state=kwargs)]

        for thought in previous_thoughts:
            base_state = thought.state
            prompt = prompter.generate_prompt(
                num_branches=self.num_branches_prompt,
                final_cot_step=(base_state["method"] == "cot")
                and (len(self.successors) == 0),
                **base_state,
            )
            self.composed_messages.extend(prompt)
            responses = await llm_utils.query(
                llm=lm, messages=self.composed_messages, n=self.num_branches_response
            )
            if (base_state["method"] == "cot") and (len(self.successors) != 0):
                assert len(responses) == 1, "COT should only have 1 response per step"
                new_state = base_state.copy()
                new_state["current"] = responses[0]
                new_state["phase"] += 1
                new_state["id"] = str(uuid.uuid4())
                self.thoughts.append(Thought(new_state))
            else:
                for new_state in parser.parse_generate_answer(base_state, responses):
                    new_state = {**base_state, **new_state}
                    self.thoughts.append(Thought(new_state))


class Aggregate(Operation):
    """
    Operation to aggregate thoughts.
    """

    operation_type: OperationType = OperationType.AGGREGATE

    def __init__(self, num_responses: int = 1) -> None:
        """
        Initializes a new Aggregate operation.

        :param num_responses: Number of responses to use for aggregation. Defaults to 1.
        :type num_responses: int
        """
        super().__init__()
        self.thoughts: List[Thought] = []
        self.num_responses: int = num_responses

    def get_thoughts(self) -> List[Thought]:
        """
        Returns the thoughts associated with the operation after aggregation.

        :return: List of aggregated thoughts.
        :rtype: List[Thought]
        """
        return self.thoughts

    async def _execute(
        self,
        lm: BaseChatModel,
        prompter: Prompter,
        parser: Parser,
        **kwargs,
    ) -> None:
        """
        Executes the Aggregate operation by aggregating the predecessors' thoughts.
        The thoughts are aggregated by prompting the LM with the predecessors' thought states.

        :param lm: The language model to be used.
        :type lm: BaseChatModel
        :param prompter: The prompter for crafting prompts.
        :type prompter: Prompter
        :param parser: The parser for parsing responses.
        :type parser: Parser
        :param kwargs: Additional parameters for execution.
        :raises AssertionError: If operation has no predecessors.
        """
        assert (
            len(self.predecessors) >= 1
        ), "Aggregate operation must have at least one predecessor"

        previous_thoughts: List[Thought] = self.get_previous_thoughts()

        if len(previous_thoughts) == 0:
            return

        base_state: Dict = {}
        for thought in previous_thoughts:
            base_state = {**base_state, **thought.state}

        previous_thought_states = [thought.state for thought in previous_thoughts]
        prompt = prompter.aggregation_prompt(previous_thought_states, **kwargs)
        self.composed_messages.extend(prompt)
        responses = await llm_utils.query(
            llm=lm, messages=self.composed_messages, n=self.num_responses
        )

        parsed = parser.parse_aggregation_answer(previous_thought_states, responses)

        for new_state in parsed:
            self.thoughts.append(Thought({**base_state, **new_state}))


class Vote(Operation):
    """
    Operation to vote thoughts.
    """

    operation_type: OperationType = OperationType.VOTE

    def __init__(self, num_responses: int = 1, n: int = 1) -> None:
        """
        Initializes a new Vote operation.

        :param num_responses: Number of responses to use for Vote. Defaults to 1.
        :type num_responses: int
        :param n: Number of thoughts to keep. Defaults to 1.
        :type n: int
        """
        super().__init__()
        self.thoughts: List[Thought] = []
        self.num_responses: int = num_responses
        self.n: int = n

    def get_thoughts(self) -> List[Thought]:
        """
        Returns the thoughts associated with the operation after Vote.

        :return: List of voted thoughts.
        :rtype: List[Thought]
        """
        return self.thoughts

    async def _execute(
        self,
        lm: BaseChatModel,
        prompter: Prompter,
        parser: Parser,
        **kwargs,
    ) -> None:
        """
        Executes the Vote operation by voting the predecessors' thoughts.
        The thoughts are voted by prompting the LM with the predecessors' thought states.

        :param lm: The language model to be used.
        :type lm: BaseChatModel
        :param prompter: The prompter for crafting prompts.
        :type prompter: Prompter
        :param parser: The parser for parsing responses.
        :type parser: Parser
        :param kwargs: Additional parameters for execution.
        :raises AssertionError: If operation has no predecessors.
        """
        assert (
            len(self.predecessors) >= 1
        ), "Vote operation must have at least one predecessor"

        previous_thoughts: List[Thought] = self.get_previous_thoughts()

        if len(previous_thoughts) == 0:
            return
        previous_thought_states = [thought.state for thought in previous_thoughts]
        prompt = prompter.vote_prompt(previous_thought_states, **kwargs)
        self.composed_messages.extend(prompt)

        responses = await llm_utils.query(
            llm=lm, messages=self.composed_messages, n=self.num_responses
        )

        parsed = parser.parse_vote_answer(previous_thought_states, responses, self.n)

        for new_state in parsed:
            self.thoughts.append(Thought({**new_state}))
