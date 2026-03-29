# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.

# pylint: disable=too-many-arguments
from typing import List

from langchain_core.language_models import BaseChatModel

from backend.src.models import Message
from backend.src.services.chat import add_reasoning_steps_to_message

from ..operations import GraphOfOperations
from ..parser import Parser
from ..prompter import Prompter


class Controller:
    """
    Controller class to manage the execution flow of the Graph of Operations,
    generating the Graph Reasoning State.
    This involves language models, graph operations, prompting, and parsing.
    """

    def __init__(
        self,
        lm: BaseChatModel,
        graph: GraphOfOperations,
        prompter: Prompter,
        parser: Parser,
        problem_parameters: dict,
    ) -> None:
        """
        Initialize the Controller instance with the language model,
        operations graph, prompter, parser, and problem parameters.

        :param lm: An instance of the BaseChatModel.
        :type lm: BaseChatModel
        :param graph: The Graph of Operations to be executed.
        :type graph: OperationsGraph
        :param prompter: An instance of the Prompter class, used to generate prompts.
        :type prompter: Prompter
        :param parser: An instance of the Parser class, used to parse responses.
        :type parser: Parser
        :param problem_parameters: Initial parameters/state of the problem.
        :type problem_parameters: dict
        """
        self.lm = lm
        self.graph = graph
        self.prompter = prompter
        self.parser = parser
        self.problem_parameters = problem_parameters
        self.run_executed = False

    async def run(self, chat_histories: List[Message]) -> str:
        """
        Run the controller and execute the operations from the Graph of
        Operations based on their readiness.
        Ensures the program is in a valid state before execution.
        :raises AssertionError: If the Graph of Operation has no roots.
        :raises AssertionError: If the successor of an operation is not in the Graph of Operations.
        """
        assert self.graph.roots is not None, "The operations graph has no root"

        execution_queue = [
            operation
            for operation in self.graph.operations
            if operation.can_be_executed()
        ]

        while len(execution_queue) > 0:
            current_operation = execution_queue.pop(0)
            await current_operation.execute(
                self.lm,
                chat_histories,
                self.prompter,
                self.parser,
                **self.problem_parameters
            )

            for operation in current_operation.successors:
                assert (
                    operation in self.graph.operations
                ), "The successor of an operation is not in the operations graph"
                if operation.can_be_executed():
                    execution_queue.append(operation)
        self.run_executed = True

        assert (
            len(self.graph.leaves) == 1
        ), "There are more than 1 leave operations in the graph."
        leave = self.graph.leaves[0]

        assert (
            len(leave.get_thoughts()) == 1
        ), "The final solution should contain only 1 thought."

        final_thought = leave.get_thoughts()[0]
        return final_thought.state["current"]

    async def store_reasonings(self, message_id: int) -> None:
        """
        Storing reasoning steps in db
        :param message_id: Response message id
        :type message_id: int
        """
        reasonings = []
        for operation in self.graph.operations:
            name = operation.operation_type.name
            content = [thought.state for thought in operation.get_thoughts()]
            reasonings.append((name, content))

        await add_reasoning_steps_to_message(
            message_id=message_id, reasonning_steps=reasonings
        )
