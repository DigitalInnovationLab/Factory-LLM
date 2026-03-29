from backend.src.constants import Technique

from ..operations import Generate, GraphOfOperations
from .base_technique import BaseTechnique


class CotTechnique(BaseTechnique):
    """
    Chain-of-thought prompting technique
    """

    @property
    def method_name(self):
        """
        Return the technique's name
        """
        return Technique.COT.value

    def create_operation_graph(self) -> GraphOfOperations:
        """
        Generates the Graph of Operations for the CoT method.

        :return: Graph of Operations
        :rtype: GraphOfOperations
        """
        operations_graph = GraphOfOperations()
        for _ in range(3):
            operations_graph.append_operation(Generate(1, 1))
        return operations_graph
