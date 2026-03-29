from backend.src.constants import Technique

from ..operations import Aggregate, Generate, GraphOfOperations, Vote
from .base_technique import BaseTechnique


class GotTechnique(BaseTechnique):
    """
    Graph-of-thought prompting technique
    """

    @property
    def method_name(self):
        """
        Return the technique's name
        """
        return Technique.GOT.value

    def create_operation_graph(self) -> GraphOfOperations:
        """
        Generates the Graph of Operations for the GoT method.

        :return: Graph of Operations
        :rtype: GraphOfOperations
        """
        operations_graph = GraphOfOperations()

        for _ in range(2):
            generate = Generate(1, 5)
            operations_graph.append_operation(generate)
            aggregate = Aggregate(2)
            operations_graph.append_operation(aggregate)

            vote_plans = Vote(5, 1)
            vote_plans.add_predecessor(generate)
            vote_plans.add_predecessor(aggregate)
            operations_graph.add_operation(vote_plans)

        return operations_graph
