import logging
import re
import uuid
from typing import Dict, List

from .parser import Parser


class MedicalParser(Parser):
    """
    MedicalParser provides the parsing of language model reponses.

    Inherits from the Parser class and implements its abstract methods.
    """

    def __init__(self) -> None:
        """
        Inits the response cache.
        """
        self.cache = {}

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
        state = states[0]
        assert (
            state["method"] == "got"
        ), f"Method {state['method']} does not support aggregation."
        new_states = []
        phase = state["phase"]
        assert phase in [1, 2], "Undefined state: " + str(phase)
        if phase == 1:
            key = "Plan:"
        else:
            key = "Output:"

        for text in texts:
            if key not in text:
                logging.warning(
                    "%s not in %s. Could not parse aggregating answer.", key, text
                )
                answer = text
            else:
                answer = text.split(key)[-1].strip()

            new_state = state.copy()
            new_state["current"] = answer
            new_state["id"] = str(uuid.uuid4())
            new_states.append(new_state)
        return new_states

    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        """
        Parse the response from the language model for a generate prompt.

        :param state: The thought state used to generate the prompt.
        :type state: Dict
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the respones from the language model.
        :rtype: List[Dict]
        """
        if state["method"] == "io":
            new_state = state.copy()
            new_state["current"] = texts[0]
            return [new_state]

        new_states = []
        if (state["method"] in ("tot", "got")) and (state["current"] == ""):
            key = "Plan:"
        else:
            key = "Output:"

        for text in texts:
            if key not in text:
                logging.warning("%s not in %s. Could not parse answer.", key, text)
                answer = text
            else:
                answer = text.split(key)[-1].strip()

            new_state = state.copy()
            new_state["current"] = answer
            new_state["phase"] += 1
            new_state["id"] = str(uuid.uuid4())
            new_states.append(new_state)
        return new_states

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
        n_candidates = len(state_dicts)
        vote_results = [0] * n_candidates
        new_states = []
        for vote_output in texts:
            pattern = r".*best choice is .*(\d+).*"
            match = re.match(pattern, vote_output, re.DOTALL)
            if match:
                vote = int(match.groups()[0]) - 1
                if vote in range(n_candidates):
                    vote_results[vote] += 1
            else:
                print(f"vote no match: {[vote_output]}")

        ids = list(range(len(state_dicts)))
        selected_ids = sorted(ids, key=lambda x: vote_results[x], reverse=True)[:n]
        for selected_id in selected_ids:
            new_state = state_dicts[selected_id].copy()
            new_states.append(new_state)

        return new_states
