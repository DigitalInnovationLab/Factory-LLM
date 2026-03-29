from typing import List

from backend.src.prompts.operations import (
    Aggregate,
    GraphOfOperations,
    Operation,
)


def test_append_operation():
    """Test append operation"""
    goo = GraphOfOperations()
    operation1 = Aggregate()
    goo.append_operation(operation1)
    assert_operations(goo, [operation1], [operation1], [operation1])

    operation2 = Aggregate()
    goo.append_operation(operation2)
    assert_operations(goo, [operation1, operation2], [operation1], [operation2])
    assert len(operation2.successors) == 0
    assert len(operation1.predecessors) == 0


def test_add_operation():
    """Test add operation"""
    goo = GraphOfOperations()
    root1 = Aggregate()
    goo.add_operation(root1)
    assert_operations(goo, [root1], [root1], [root1])

    root2 = Aggregate()
    goo.add_operation(root2)
    assert_operations(goo, [root1, root2], [root1, root2], [root1, root2])

    leave = Aggregate()
    leave.add_predecessor(root2)
    goo.add_operation(leave)
    assert_operations(goo, [root1, root2, leave], [root1, root2], [root1, leave])


def assert_operations(
    goo: GraphOfOperations,
    operations: List[Operation],  # Order of operations matter
    roots: List[Operation],  # Order of operations matter
    leaves: List[Operation],  # Order of operations matter
):
    """Helper method for assertion"""
    assert len(goo.operations) == len(operations)
    assert len(goo.roots) == len(roots)
    assert len(goo.leaves) == len(leaves)

    for i, op in enumerate(operations):
        assert goo.operations[i] == op
    for i, op in enumerate(roots):
        assert goo.roots[i] == op
    for i, op in enumerate(leaves):
        assert goo.leaves[i] == op
