from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.src.constants import LlmModel, RagTechnique
from backend.src.services.rag import query_graph, query_knowledge, query_vector


@pytest.mark.asyncio
@patch("backend.src.services.rag.get_chroma_collection")
@patch("backend.src.services.rag.ChromaVectorStore")
@patch("backend.src.services.rag.LlmFactory.create_embedding_model")
@patch("backend.src.services.rag.VectorStoreIndex.from_vector_store")
@patch("backend.src.services.rag.VectorIndexRetriever")
async def test_query_vector(
    mock_vector_index_retriever,
    mock_from_vector_store,
    mock_create_embedding_model,
    mock_chroma_vector_store,
    mock_get_chroma_collection,
):
    """
    Test query_vector function
    """
    mock_get_chroma_collection.return_value = "mock_collection"
    mock_chroma_vector_store.return_value = "mock_vector_store"
    mock_create_embedding_model.return_value = "mock_embedding_model"
    mock_from_vector_store.return_value = "mock_index"
    mock_aretrieve = AsyncMock()
    mock_aretrieve.return_value = [AsyncMock(text="doc1"), AsyncMock(text="doc2")]
    mock_vector_index_retriever.return_value.aretrieve = mock_aretrieve

    result = await query_vector(chat_id=1, query="test query")

    assert result == ["doc1", "doc2"]
    mock_get_chroma_collection.assert_called_once_with("chat-1")
    mock_chroma_vector_store.assert_called_once_with(
        chroma_collection="mock_collection"
    )
    mock_create_embedding_model.assert_called_once_with(LlmModel.GPT4O_MINI)
    mock_from_vector_store.assert_called_once_with(
        vector_store="mock_vector_store", embed_model="mock_embedding_model"
    )
    mock_vector_index_retriever.assert_called_once_with(
        index="mock_index", similarity_top_k=3
    )
    mock_aretrieve.assert_called_once_with("test query")


@pytest.mark.asyncio
@patch("backend.src.services.rag.get_nebula_storage_context")
@patch("backend.src.services.rag.LlmFactory.create_llm")
@patch("backend.src.services.rag.LlmFactory.create_embedding_model")
@patch("backend.src.services.rag.LlamaIndexSettings")
@patch("backend.src.services.rag.KnowledgeGraphRAGRetriever")
async def test_query_graph(
    mock_knowledge_graph_rag_retriever,
    mock_llama_index_settings,
    mock_create_embedding_model,
    mock_create_llm,
    mock_get_nebula_storage_context,
):
    """
    Test query_graph function
    """
    mock_get_nebula_storage_context.return_value = "mock_storage_context"
    mock_create_llm.return_value = "mock_llm"
    mock_create_embedding_model.return_value = "mock_embedding_model"
    mock_aretrieve = AsyncMock()
    mock_aretrieve.return_value = [AsyncMock(text="doc1"), AsyncMock(text="doc2")]
    mock_retriever = MagicMock()
    mock_retriever.aretrieve = mock_aretrieve
    mock_knowledge_graph_rag_retriever.return_value = mock_retriever

    result = await query_graph(chat_id=1, query="test query")

    assert result == ["doc1", "doc2"]
    mock_llama_index_settings.llm = "mock_llm"
    mock_llama_index_settings.chunk_size = 512
    mock_llama_index_settings.embed_model = "mock_embedding_model"
    mock_get_nebula_storage_context.assert_called_once_with("chat_1")
    mock_create_llm.assert_called_once_with(LlmModel.GPT4O_MINI, temperature=0)
    mock_create_embedding_model.assert_called_once_with(LlmModel.GPT4O_MINI)
    mock_knowledge_graph_rag_retriever.assert_called_once_with(
        storage_context="mock_storage_context", llm="mock_llm"
    )
    mock_aretrieve.assert_called_once_with("test query")


@pytest.mark.asyncio
@patch("backend.src.services.rag.query_vector")
@patch("backend.src.services.rag.query_graph")
async def test_query_knowledge_vector(mock_query_graph, mock_query_vector):
    """
    Test query_knowledge function with technique=VECTOR
    """
    mock_query_vector.return_value = ["doc1", "doc2"]

    result = await query_knowledge(
        chat_id=1, query="test query", technique=RagTechnique.VECTOR
    )

    assert result == ["doc1", "doc2"]
    mock_query_vector.assert_called_once_with(
        1, "test query", LlmModel.GPT4O_MINI, None, 3
    )
    mock_query_graph.assert_not_called()


@pytest.mark.asyncio
@patch("backend.src.services.rag.query_vector")
@patch("backend.src.services.rag.query_graph")
async def test_query_knowledge_graph(mock_query_graph, mock_query_vector):
    """
    Test query_knowledge function with technique=GRAPH
    """
    mock_query_graph.return_value = ["doc1", "doc2"]

    result = await query_knowledge(
        chat_id=1, query="test query", technique=RagTechnique.GRAPH
    )

    assert result == ["doc1", "doc2"]
    mock_query_graph.assert_called_once_with(1, "test query", LlmModel.GPT4O_MINI)
    mock_query_vector.assert_not_called()


@pytest.mark.asyncio
async def test_query_knowledge_invalid_technique():
    """
    Test query_knowledge function with invalid technique
    """
    with pytest.raises(ValueError, match="Invalid technique"):
        await query_knowledge(chat_id=1, query="test query", technique="INVALID")
