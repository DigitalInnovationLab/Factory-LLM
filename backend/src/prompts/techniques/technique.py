from backend.src.constants import Technique

from .base_technique import BaseTechnique
from .cot import CotTechnique
from .got import GotTechnique
from .none import NoneTechnique
from .tot import TotTechnique


class TechniqueFactory:
    """Factory class to create prompting techniques."""

    @staticmethod
    def create_technique(technique: Technique) -> BaseTechnique:
        """Creates a prompting technique based on the specified technique."""
        match technique:
            case Technique.NONE:
                return NoneTechnique()
            case Technique.COT:
                return CotTechnique()
            case Technique.TOT:
                return TotTechnique()
            case Technique.GOT:
                return GotTechnique()
            case _:
                raise ValueError("Invalid technique")
