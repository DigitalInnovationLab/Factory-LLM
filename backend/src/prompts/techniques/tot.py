from backend.src.constants import Technique

from ..operations import Generate, GraphOfOperations, Vote
from .base_technique import BaseTechnique


class TotTechnique(BaseTechnique):
    """
    Tree-of-thought prompting technique
    """

    @property
    def method_name(self):
        """
        Return the technique's name
        """
        return Technique.TOT.value

    def create_operation_graph(self) -> GraphOfOperations:
        """
        Generates the Graph of Operations for the ToT method.

        :return: Graph of Operations
        :rtype: GraphOfOperations
        """
        operations_graph = GraphOfOperations()

        for _ in range(2):
            operations_graph.append_operation(Generate(1, 5))
            operations_graph.append_operation(Vote(5, 1))

        return operations_graph
