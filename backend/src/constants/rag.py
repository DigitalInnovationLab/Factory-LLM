from enum import Enum


class RagTechnique(Enum):
    """Enum for RAG techniques"""

    NONE = "none"
    VECTOR = "vector"
    GRAPH = "graph"
