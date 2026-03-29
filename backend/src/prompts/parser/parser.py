# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class Parser(ABC):
    """
    Abstract base class that defines the interface for all parsers.
    Parsers are used to parse the responses from the language models.
    """

    @abstractmethod
    def parse_aggregation_answer(
        self, states: List[Dict], texts: List[str]
    ) -> List[Dict]:
        """
        Parse the response from the language model for a aggregation prompt.

        :param states: The thought states used to generate the prompt.
        :type states: List[Dict]
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the response from the language model.
        :rtype: List[Dict]
        """

    @abstractmethod
    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        """
        Parse the response from the language model for a generate prompt.

        :param state: The thought state used to generate the prompt.
        :type state: Dict
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the response from the language model.
        :rtype: List[Dict]
        """

    @abstractmethod
    def parse_vote_answer(
        self, state_dicts: List[Dict], texts: List[str], n: int
    ) -> List[Dict]:
        """
        Parse the response from the language model for a vote prompt.

        :param state_dicts: The thought states used to generate the prompt.
        :type state_dicts: List[Dict]
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :param n: The number of thoughts to be kept after voting.
        :type n: int
        :return: The new thought states after parsing the response from the language model.
        :rtype: List[Dict]
        """
