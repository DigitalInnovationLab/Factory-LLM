from backend.src.constants import Technique

from ..operations import Generate, GraphOfOperations
from .base_technique import BaseTechnique


class NoneTechnique(BaseTechnique):
    """Technique that does nothing to the input. It is used when no technique is specified."""

    @property
    def method_name(self):
        """
        Return the technique's name
        """
        return Technique.NONE.value

    def create_operation_graph(self) -> GraphOfOperations:
        """
        Generates the Graph of Operations for the non-technique method.

        :return: Graph of Operations
        :rtype: GraphOfOperations
        """
        operations_graph = GraphOfOperations()
        operations_graph.append_operation(Generate(1, 1))
        return operations_graph
