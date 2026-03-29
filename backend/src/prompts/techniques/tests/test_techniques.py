from backend.src.constants import Technique
from backend.src.prompts.operations import Aggregate, Generate, Vote
from backend.src.prompts.techniques.technique import TechniqueFactory


def test_invalid_technique():
    "Test invalid technique"
    factory = TechniqueFactory()
    try:
        factory.create_technique("invalid")
    except ValueError as e:
        assert str(e) == "Invalid technique"


def test_cot_operation_graph():
    "Test cot technique create operation graph"
    factory = TechniqueFactory()
    cot = factory.create_technique(Technique.COT)
    assert cot.method_name == "cot"
    goo = cot.create_operation_graph()  # to be delete
    assert len(goo.operations) == 3

    for _, operation in enumerate(goo.operations):
        assert isinstance(operation, Generate)
        assert operation.num_branches_prompt == 1
        assert operation.num_branches_response == 1


def test_none_operation_graph():
    "Test none technique create operation graph"
    factory = TechniqueFactory()
    none = factory.create_technique(Technique.NONE)
    assert none.method_name == "io"
    goo = none.create_operation_graph()  # to be delete
    assert len(goo.operations) == 1
    operation = goo.operations[0]
    assert isinstance(operation, Generate)
    assert operation.num_branches_prompt == 1
    assert operation.num_branches_response == 1


def test_tot_operation_graph():
    "Test tot create operation graph"
    factory = TechniqueFactory()
    tot = factory.create_technique(Technique.TOT)
    assert tot.method_name == "tot"
    goo = tot.create_operation_graph()
    assert len(goo.operations) == 4
    operation = goo.operations[0]
    assert isinstance(operation, Generate)
    assert operation.num_branches_prompt == 1
    assert operation.num_branches_response == 5

    operation = goo.operations[1]
    assert isinstance(operation, Vote)
    assert operation.num_responses == 5
    assert operation.n == 1

    operation = goo.operations[2]
    assert isinstance(operation, Generate)
    assert operation.num_branches_prompt == 1
    assert operation.num_branches_response == 5

    operation = goo.operations[3]
    assert isinstance(operation, Vote)
    assert operation.num_responses == 5
    assert operation.n == 1


def test_got_operation_graph():
    "Test got technique create operation graph"
    factory = TechniqueFactory()
    got = factory.create_technique(Technique.GOT)
    assert got.method_name == "got"
    goo = got.create_operation_graph()
    assert len(goo.operations) == 6
    operation = goo.operations[0]
    assert isinstance(operation, Generate)
    assert operation.num_branches_prompt == 1
    assert operation.num_branches_response == 5

    operation = goo.operations[1]
    assert isinstance(operation, Aggregate)
    assert operation.num_responses == 2

    operation = goo.operations[2]
    assert isinstance(operation, Vote)
    assert operation.num_responses == 5
    assert operation.n == 1

    operation = goo.operations[3]
    assert isinstance(operation, Generate)
    assert operation.num_branches_prompt == 1
    assert operation.num_branches_response == 5

    operation = goo.operations[4]
    assert isinstance(operation, Aggregate)
    assert operation.num_responses == 2

    operation = goo.operations[5]
    assert isinstance(operation, Vote)
    assert operation.num_responses == 5
    assert operation.n == 1
