# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.

# pylint: disable=too-many-instance-attributes
from __future__ import annotations

import itertools
from typing import Dict, Iterator, Optional


class Thought:
    """
    Represents an LLM thought with its state, constructed by the parser, and various flags.
    """

    _ids: Iterator[int] = itertools.count(0)

    def __init__(self, state: Optional[Dict] = None) -> None:
        """
        Initializes a new Thought instance with a state and various default flags.

        :param state: The state of the thought. Defaults to None.
        :type state: Optional[Dict]
        """
        self.id: int = next(Thought._ids)
        self.state: Dict = state
