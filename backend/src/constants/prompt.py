from enum import Enum


class Technique(Enum):
    """Enum for prompting techniques"""

    NONE = "io"
    COT = "cot"
    TOT = "tot"
    GOT = "got"
