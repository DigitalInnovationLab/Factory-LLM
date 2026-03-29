from unittest.mock import AsyncMock, patch

import pytest

from backend.src.prompts.techniques.base_technique import (
    BaseTechnique,
    LlmFactory,
    LlmModel,
    Message,
    MessageRole,
    RagTechnique,
)
from backend.src.prompts.techniques.technique import (
    Technique,
    TechniqueFactory,
)


@pytest.mark.asyncio
@patch(
    "backend.src.prompts.techniques.base_technique.query_knowledge",
    new_callable=AsyncMock,
)
@patch.object(BaseTechnique, "run", new_callable=AsyncMock)
async def test_ask_with_contexts(mock_run, mock_query_knowledge):
    """Test ask with contexts"""
    user_input = "What is glaucoma?"
    chat_histories = [Message(content="Previous message", role=MessageRole.ASSISTANT)]
    model = LlmModel.GPT4O_MINI
    rag_technique = RagTechnique.GRAPH
    chat_id = 123
    vector_top_k = 4

    mock_query_knowledge.return_value = ["Here is the known context."]
    mock_run.return_value = Message(
        content="Glaucoma is an eye disease.", role=MessageRole.ASSISTANT
    )

    technique = TechniqueFactory.create_technique(Technique.GOT)

    result = await technique.ask(
        user_input=user_input,
        chat_histories=chat_histories,
        model=model,
        rag_technique=rag_technique,
        chat_id=chat_id,
        vector_top_k=vector_top_k,
    )

    mock_query_knowledge.assert_awaited_with(
        chat_id, user_input, rag_technique, model, vector_top_k=vector_top_k
    )
    assert result.content == "Glaucoma is an eye disease."


@pytest.mark.asyncio
@patch(
    "backend.src.prompts.techniques.base_technique.add_message_to_chat",
    new_callable=AsyncMock,
)
@patch(
    "backend.src.prompts.techniques.base_technique.query_knowledge",
    new_callable=AsyncMock,
)
async def test_ask_without_contexts(mock_query_knowledge, mock_add_message):
    "Test ask without contexts"
    user_input = "What is glaucoma?"
    chat_histories = [Message(content="Previous message", role=MessageRole.ASSISTANT)]
    model = LlmModel.GPT4O_MINI
    rag_technique = RagTechnique.GRAPH
    chat_id = 123

    mock_query_knowledge.return_value = []
    mock_add_message.return_value = Message(
        content="Sorry I don't know", role=MessageRole.ASSISTANT
    )
    technique = TechniqueFactory.create_technique(Technique.GOT)

    result = await technique.ask(
        user_input=user_input,
        chat_histories=chat_histories,
        model=model,
        rag_technique=rag_technique,
        chat_id=chat_id,
    )
    mock_add_message.assert_awaited_once_with(
        chat_id=chat_id, content="Sorry I don't know.", role=MessageRole.ASSISTANT
    )
    assert result.content == "Sorry I don't know"


@pytest.mark.asyncio
@patch(
    "backend.src.prompts.techniques.base_technique.add_message_to_chat",
    new_callable=AsyncMock,
)
@patch(
    "backend.src.prompts.techniques.base_technique.Controller.run",
    new_callable=AsyncMock,
)
@patch(
    "backend.src.prompts.techniques.base_technique.Controller.store_reasonings",
    new_callable=AsyncMock,
)
async def test_run(
    mock_store_reasonings, mock_controller_run, mock_add_message_to_chat
):
    """Test run method"""

    user_input = "What is glaucoma?"
    chat_histories = [Message(content="Previous message", role=MessageRole.ASSISTANT)]
    llm = LlmFactory.create_llm()

    contexts = ["Context for glaucoma"]
    chat_id = "123"

    technique = TechniqueFactory.create_technique(Technique.GOT)

    # Mock the result of running the controller
    mock_controller_run.return_value = "Glaucoma is an eye disease."

    # Mock the return value of add_message_to_chat
    mock_add_message_to_chat.return_value = Message(
        content="Glaucoma is an eye disease.", role=MessageRole.ASSISTANT, id=1234
    )

    result = await technique.run(
        user_input=user_input,
        chat_histories=chat_histories,
        llm=llm,
        contexts=contexts,
        chat_id=chat_id,
    )

    mock_controller_run.assert_awaited_once_with(chat_histories)
    mock_add_message_to_chat.assert_awaited_once_with(
        chat_id=chat_id,
        content="Glaucoma is an eye disease.",
        role=MessageRole.ASSISTANT,
    )

    mock_store_reasonings.assert_awaited()

    assert result.content == "Glaucoma is an eye disease."
    assert result.role == MessageRole.ASSISTANT
    assert result.id == 1234
