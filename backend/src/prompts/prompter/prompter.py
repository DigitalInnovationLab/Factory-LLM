# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from langchain_core.messages import BaseMessage


class Prompter(ABC):
    """
    Abstract base class that defines the interface for all prompters.
    Prompters are used to generate the prompts for the language models.
    """

    @abstractmethod
    def aggregation_prompt(
        self, state_dicts: List[Dict], **kwargs
    ) -> List[BaseMessage]:
        """
        Generate a aggregation prompt for the language model.

        :param state_dicts: The thought states that should be aggregated.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The aggregation prompt.
        :rtype: List[BaseMessage]
        """

    @abstractmethod
    def generate_prompt(
        self, num_branches: int, final_cot_step: bool, **kwargs
    ) -> List[BaseMessage]:
        """
        Generate a generate prompt for the language model.
        The thought state is unpacked to allow for additional keyword arguments
        and concrete implementations to specify required arguments explicitly.

        :param num_branches: The number of responses the prompt should ask the LM to generate.
        :type num_branches: int
        :param kwargs: Additional keyword arguments.
        :return: The generate prompt.
        :rtype: List[BaseMessage]
        """

    @abstractmethod
    def vote_prompt(self, state_dicts: List[Dict], **kwargs) -> List[BaseMessage]:
        """
        Generate a vote prompt for the language model.

        :param state_dicts: The thought states that should be voted.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The vote prompt.
        :rtype: List[BaseMessage]
        """
