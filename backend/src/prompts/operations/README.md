# Operations

The Operations module contains operations to manipulate and process thoughts represented by the [Thought](thought.py) class.  
Operations interface with a language model and use other helper classes like [Prompter](../prompter/prompter.py) and [Parser](../parser/parser.py) for effective communication and extraction of results from the language model.  
The [Graph of Operations](graph_of_operations.py) class is the main class of the module and is responsible for orchestrating the operations, defining their relationships and maintaining the state of the thought graph, also known as Graph Reasoning State.

## Graph of Operations
The [GraphOfOperations](graph_of_operations.py) class facilitates the creation and management of a directed graph representing the sequence and interrelationships of operations on thoughts. Here’s how you can construct and work with the Graph of Operations:

### Initialization
Creating a new instance of GraphOfOperations:

```python
from graph_of_thoughts.operations import GraphOfOperations

graph = GraphOfOperations()
```

Upon initialization, the graph will be empty with no operations, roots, or leaves.

### Adding Operations
**Append Operation:** You can append operations to the end of the graph using the append_operation method. This ensures that the operation becomes a successor to all current leaf operations in the graph.
```python
from graph_of_thoughts.operations import Generate

operationA = Generate()
graph.append_operation(operationA)
```
**Add Operation with Relationships:** If you want to define specific relationships for an operation, use the add_operation method.
```python
operationB = Generate()
operationB.predecessors.append(operationA)
graph.add_operation(operationB)
```
Remember to set up the predecessors (and optionally successors) for your operation before adding it to the graph.

## Available Operations
The following operations are available in the module:

**Generate:** Generate new thoughts from the current thoughts. If no previous thoughts are available, the thoughts are initialized with the input to the [Controller](../controller/controller.py).  
- num_branches_prompt (Optional): Number of responses that each prompt should generate (passed to prompter). Defaults to 1.
- num_branches_response (Optional): Number of responses the LLM should generate for each prompt. Defaults to 1.

**Aggregate:** Aggregate the current thoughts into a single thought. This operation is useful when you want to combine multiple thoughts into a single thought.  
- num_responses (Optional): Number of responses to request from the LLM (generates multiple new thoughts). Defaults to 1.

