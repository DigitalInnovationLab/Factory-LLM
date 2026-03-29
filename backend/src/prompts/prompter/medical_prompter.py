# pylint: disable=arguments-differ
# pylint: disable=too-many-arguments
from typing import Dict, List

from langchain_core.messages import BaseMessage, HumanMessage

from .prompter import Prompter
from .templates import (
    get_aggregate_answer_prompt,
    get_aggregate_plan_prompt,
    get_cot_prompt,
    get_generate_plan_prompt,
    get_generate_solution_prompt,
    get_vote_prompt,
)


class MedicalPrompter(Prompter):
    """Specific prompter for Medical"""

    def aggregation_prompt(
        self, state_dicts: List[Dict], **kwargs
    ) -> List[BaseMessage]:
        """
        Generate an aggregation prompt for the language model.

        :param state_dicts: The thought states that should be aggregated.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The aggregation prompt.
        :rtype: List[BaseMessage]
        """
        assert (
            len(state_dicts) > 0
        ), "There should be more than 1 thoughts to be aggregated."
        state = state_dicts[0]
        assert (
            state["method"] == "got"
        ), f"Method {state['method']} does not support aggregation."
        phase = state["phase"]
        keyword = "Plan" if phase == 1 else "Answer"
        plan_counter = 1
        source_contents = ""
        for state in state_dicts:
            source_contents += f"{keyword} {str(plan_counter)}: {state['current']}\n\n"
            plan_counter += 1

        if phase == 1:
            return get_aggregate_plan_prompt(
                user_input=state["user_input"], plans=source_contents
            )
        return get_aggregate_answer_prompt(
            user_input=state["user_input"], answers=source_contents
        )

    def generate_prompt(
        self,
        num_branches: int,
        final_cot_step: bool,
        user_input: str,
        current: str,
        method: str,
        **kwargs,
    ) -> List[BaseMessage]:
        """
        Generate a generate prompt for the language model.

        :param num_branches: The number of responses the prompt should ask the LM to generate.
        :type num_branches: int
        :param user_input: User input.
        :type user_input: str
        :param current: Intermediate solution.
        :type current: str
        :param method: Method for which the generate prompt is generated.
        :type method: str
        :param kwargs: Additional keyword arguments.
        :return: The generate prompt.
        :rtype: List[BaseMessage]
        :raise AssertionError: If the requested number of branches is not one.
        """

        assert num_branches == 1, "Branching should be done via multiple requests."

        if method.startswith("io"):
            # Standard input-output: No prompt template required
            return [HumanMessage(content=user_input)]
        if method.startswith("cot"):
            return get_cot_prompt(
                user_input=user_input,
                previous_answer=current,
                final_step=final_cot_step,
            )
        if method.startswith("tot") or method.startswith("got"):
            if current is None or current == "":
                return get_generate_plan_prompt(user_input=user_input)
            return get_generate_solution_prompt(user_input=user_input, plan=current)
        raise ValueError("Invalid technique")

    def vote_prompt(self, state_dicts: List[Dict], **kwargs) -> List[BaseMessage]:
        """
        Generate a vote prompt for the language model.

        :param state_dicts: The thought states that should be voted.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The vote prompt.
        :rtype: List[BaseMessage]
        """
        assert len(state_dicts) > 0, "There should be more than 1 thoughts to be voted."
        state = state_dicts[0]
        phase = state["phase"]
        keyword = "Plan" if phase == 1 else "Answer"
        plan_counter = 1
        source_contents = ""
        for state in state_dicts:
            source_contents += f"{keyword} {str(plan_counter)}: {state['current']}\n\n"
            plan_counter += 1

        return get_vote_prompt(
            keyword=keyword, user_input=state["user_input"], content=source_contents
        )
