# pylint: disable=redefined-outer-name, unused-argument
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from llama_index.core import Document
from nebula3.common.ttypes import ErrorCode

from backend.src.constants import LlmModel, RagTechnique
from backend.src.services.etl import (
    create_nebula_space,
    delete_graph_data,
    delete_vector_data,
    get_chroma_client,
    get_chroma_collection,
    get_documents_from_binaries,
    get_exponetial_backoff,
    get_nebula_storage_context,
    insert_data,
    insert_graph_data,
    insert_vector_data,
)
from common import File


@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Set environment variables
    """
    monkeypatch.setenv("NEBULA_USER", "test_user")
    monkeypatch.setenv("NEBULA_PASSWORD", "test_password")
    monkeypatch.setenv("NEBULA_ADDRESS", "localhost:3699")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8000")
    monkeypatch.setenv("CHROMA_TOKEN", "test_token")


@pytest.fixture
def mock_time_sleep():
    """
    Mock time.sleep
    """
    with patch("backend.src.services.etl.time.sleep") as mock_sleep:
        yield mock_sleep


@pytest.fixture
def mock_file():
    """
    Mock File object
    """
    return File(name="test_file", content=mock.Mock())


@patch("backend.src.services.etl.chromadb.HttpClient")
def test_get_chroma_client(mock_http_client, mock_env_vars):
    """
    Test create chroma client
    """
    get_chroma_client()
    mock_http_client.assert_called_once_with(
        host="localhost",
        port="8000",
        settings=mock.ANY,
    )


@patch("backend.src.services.etl.get_chroma_client")
def test_get_chroma_collection(mock_get_chroma_client):
    """
    Test get chroma collection
    """
    mock_collection = mock.Mock()
    mock_get_chroma_client.return_value.get_or_create_collection.return_value = (
        mock_collection
    )

    collection = get_chroma_collection("test_chat_id")
    assert collection == mock_collection
    mock_get_chroma_client.assert_called_once()


@patch("backend.src.services.etl.Path")
@patch("backend.src.services.etl.os.path.exists")
@patch("backend.src.services.etl.os.remove")
@patch("backend.src.services.etl.tempfile.NamedTemporaryFile")
@patch("backend.src.services.etl.SimpleDirectoryReader.load_file")
def test_get_documents_from_binaries(
    mock_load_file, mock_tempfile, mock_remove, mock_path_exist, mock_path, mock_file
):
    """
    Test get documents from binaries
    """
    mock_tempfile.return_value.__enter__.return_value.name = "temp_file"
    mock_load_file.return_value = [Document(text="test")]
    mock_path_exist.return_value = True
    mock_path.return_value = "temp_path"

    documents = get_documents_from_binaries([mock_file])

    assert len(documents) == 1
    assert documents[0].text == "test"
    mock_tempfile.assert_called_once_with(suffix=".bin.test_file", delete=False)
    mock_file.content.read.assert_called_once()
    mock_tempfile.return_value.__enter__.return_value.write.assert_called_once()
    mock_tempfile.return_value.__enter__.return_value.flush.assert_called_once()
    mock_path.assert_called_once_with("temp_file")
    mock_load_file.assert_called_once_with("temp_path", mock.ANY, {})
    mock_path_exist.assert_called_once()
    mock_remove.assert_called_once()


@patch("backend.src.services.etl.get_chroma_collection")
@patch("backend.src.llm.models.LlmFactory.create_embedding_model")
@patch("backend.src.services.etl.ChromaVectorStore")
@patch("backend.src.services.etl.StorageContext.from_defaults")
@patch("backend.src.services.etl.VectorStoreIndex.from_documents")
@patch("backend.src.services.etl.LlamaIndexSettings")
def test_insert_vector_data(
    mock_llama_index_settings,
    mock_from_documents,
    mock_storage_context,
    mock_vector_store,
    mock_create_model,
    mock_get_collection,
):
    """
    Test insert data to vector database
    """
    mock_collection = mock.Mock()
    mock_get_collection.return_value = mock_collection
    mock_model = mock.Mock()
    mock_create_model.return_value = mock_model
    mock_vector_store.return_value = mock.Mock()
    mock_storage_context.return_value = mock.Mock()
    mock_from_documents.return_value = mock.Mock()

    documents = [Document(text="test")]
    index = insert_vector_data(1, documents, chunk_size=512, chunk_overlap=10)

    assert index == mock_from_documents.return_value
    mock_get_collection.assert_called_once_with("chat-1")
    mock_create_model.assert_called_once_with(LlmModel.GPT4O_MINI)
    mock_vector_store.assert_called_once_with(chroma_collection=mock_collection)
    mock_storage_context.assert_called_once_with(
        vector_store=mock_vector_store.return_value
    )
    mock_llama_index_settings.chunk_size = 512
    mock_llama_index_settings.chunk_overlap = 10
    mock_from_documents.assert_called_once_with(
        documents,
        storage_context=mock_storage_context.return_value,
        embed_model=mock_model,
    )


@patch("backend.src.services.etl.get_chroma_client")
def test_delete_vector_data(mock_get_chroma_client):
    """
    Test delete data from vector database
    """
    mock_delete = mock.Mock()
    mock_get_chroma_client.return_value.delete_collection = mock_delete

    delete_vector_data(1)
    mock_delete.assert_called_once_with("chat-1")


def test_get_exponetial_backoff():
    """
    Test get exponential backoff time
    """
    assert get_exponetial_backoff(3, 2) == 16
    assert get_exponetial_backoff(0, 2) == 2


@patch("backend.src.services.etl.Connection")
def test_create_nebula_space(mock_connection, mock_env_vars, mock_time_sleep):
    """
    Test create nebula space
    """
    mock_conn = MagicMock()
    mock_connection.return_value = mock_conn
    mock_conn.open.return_value = None
    mock_conn.authenticate.return_value.get_session_id.return_value = 1
    mock_conn_return_values = [
        MagicMock(error_code=ErrorCode.SUCCEEDED),
        MagicMock(error_code=ErrorCode.E_EXECUTION_ERROR),
        MagicMock(error_code=ErrorCode.SUCCEEDED),
        MagicMock(error_code=ErrorCode.SUCCEEDED),
        MagicMock(error_code=ErrorCode.E_EXECUTION_ERROR),
        MagicMock(error_code=ErrorCode.E_EXECUTION_ERROR),
        MagicMock(error_code=ErrorCode.E_EXECUTION_ERROR),
        MagicMock(error_code=ErrorCode.SUCCEEDED, data=MagicMock(rows=[""])),
        MagicMock(error_code=ErrorCode.SUCCEEDED, data=MagicMock(rows=[""])),
        MagicMock(error_code=ErrorCode.SUCCEEDED, data=MagicMock(rows=[""])),
    ]
    mock_conn.execute.side_effect = mock_conn_return_values

    create_nebula_space("test_space")
    mock_conn.execute.assert_any_call(
        1,
        "CREATE SPACE IF NOT EXISTS test_space(vid_type=FIXED_STRING(256));",
    )
    mock_time_sleep.assert_any_call(2)
    mock_conn.execute.assert_any_call(1, "USE test_space;")
    mock_conn.execute.assert_any_call(
        1,
        "USE test_space;"
        + "CREATE TAG IF NOT EXISTS entity(name string);"
        + "CREATE EDGE IF NOT EXISTS relationship(relationship string);"
        + "CREATE TAG INDEX IF NOT EXISTS entity_index ON entity(name(256));",
    )
    mock_conn.execute.assert_any_call(
        1,
        "USE test_space;SHOW TAGS;",
    )
    mock_conn.execute.assert_any_call(
        1,
        "USE test_space;SHOW EDGES;",
    )
    mock_conn.execute.assert_any_call(
        1,
        "USE test_space;SHOW TAG INDEXES;",
    )
    mock_time_sleep.assert_any_call(2)
    mock_time_sleep.assert_any_call(10)
    mock_conn.close.assert_called_once()


@patch("backend.src.services.etl.Connection")
def test_failed_create_nebula_space(mock_connection, mock_env_vars, mock_time_sleep):
    """
    Test the case where the space creation fails
    """
    mock_conn = MagicMock()
    mock_connection.return_value = mock_conn
    mock_conn.open.return_value = None
    mock_conn.authenticate.return_value.get_session_id.return_value = 1
    mock_conn_return_values = [
        MagicMock(error_code=ErrorCode.SUCCEEDED),
    ]
    mock_conn_return_values.extend(
        [MagicMock(error_code=ErrorCode.E_EXECUTION_ERROR)] * 10
    )
    mock_conn.execute.side_effect = mock_conn_return_values

    with pytest.raises(ValueError, match="Failed to create space"):
        create_nebula_space("test_space")
        mock_time_sleep.assert_called()
        assert mock_time_sleep.call_count == 10


@patch("backend.src.services.etl.Connection")
def test_failed_create_nebula_space_tag_index(
    mock_connection, mock_env_vars, mock_time_sleep
):
    """
    Test the case where the tag index creation fails
    """
    mock_conn = MagicMock()
    mock_connection.return_value = mock_conn
    mock_conn.open.return_value = None
    mock_conn.authenticate.return_value.get_session_id.return_value = 1
    mock_conn_return_values = []
    mock_conn_return_values.extend([MagicMock(error_code=ErrorCode.SUCCEEDED)] * 3)
    mock_conn_return_values.extend(
        [MagicMock(error_code=ErrorCode.E_EXECUTION_ERROR)] * 30
    )
    mock_conn.execute.side_effect = mock_conn_return_values

    with pytest.raises(ValueError, match="Failed to create tag index"):
        create_nebula_space("test_space")
        mock_time_sleep.assert_called()
        assert mock_time_sleep.call_count == 30


@patch("backend.src.services.etl.NebulaGraphStore")
@patch("backend.src.services.etl.StorageContext.from_defaults")
def test_get_nebula_storage_context(mock_storage_context, mock_graph_store):
    """
    Test get nebula storage context
    """
    mock_graph_store.return_value = mock.Mock()
    mock_storage_context.return_value = mock.Mock()

    context = get_nebula_storage_context("test_space")
    mock_graph_store.assert_called_once_with(
        space_name="test_space",
        edge_types=["relationship"],
        rel_prop_names=["relationship"],
        tags=["entity"],
    )
    assert context == mock_storage_context.return_value


@patch("backend.src.services.etl.create_nebula_space")
@patch("backend.src.services.etl.get_nebula_storage_context")
@patch("backend.src.llm.models.LlmFactory.create_llm")
@patch("backend.src.llm.models.LlmFactory.create_embedding_model")
@patch("backend.src.services.etl.KnowledgeGraphIndex.from_documents")
@patch("backend.src.services.etl.LlamaIndexSettings")
def test_insert_graph_data(
    mock_llama_index_settings,
    mock_from_documents,
    mock_create_model,
    mock_create_llm,
    mock_get_context,
    mock_create_space,
):
    """
    Test insert data to graph database
    """
    mock_create_space.return_value = None
    mock_get_context.return_value = mock.Mock()
    mock_create_llm.return_value = mock.Mock()
    mock_create_model.return_value = mock.Mock()
    mock_from_documents.return_value = mock.Mock()

    documents = [Document(text="test")]
    index = insert_graph_data(1, documents, chunk_size=512, chunk_overlap=10)

    assert index == mock_from_documents.return_value
    mock_llama_index_settings.chunk_size = 512
    mock_llama_index_settings.chunk_overlap = 10
    mock_llama_index_settings.embed_model = mock_create_model.return_value
    mock_llama_index_settings.llm = mock_create_llm.return_value
    mock_create_space.assert_called_once_with("chat_1")
    mock_get_context.assert_called_once_with("chat_1")
    mock_from_documents.assert_called_once_with(
        documents,
        storage_context=mock_get_context.return_value,
        max_triplets_per_chunk=10,
    )


@patch("backend.src.services.etl.Connection")
def test_delete_graph_data(mock_connection, mock_env_vars):
    """
    Test delete data from graph database
    """
    mock_conn = MagicMock()
    mock_connection.return_value = mock_conn
    mock_conn.open.return_value = None
    mock_conn.authenticate.return_value.get_session_id.return_value = 1
    mock_conn.execute.return_value.error_code = ErrorCode.SUCCEEDED

    delete_graph_data(1)
    mock_conn.execute.assert_called()
    mock_conn.execute.assert_called_once_with(
        1,
        "DROP SPACE chat_1;",
    )
    mock_conn.close.assert_called_once()


@pytest.mark.asyncio
@patch("backend.src.services.etl.get_documents_from_binaries")
@patch("backend.src.services.etl.insert_vector_data")
@patch("backend.src.services.etl.insert_graph_data")
@patch("backend.src.services.file.create_files")
async def test_insert_data(
    mock_create_files,
    mock_insert_graph,
    mock_insert_vector,
    mock_get_documents,
    mock_file,
):
    """
    Test insert data into knowledge database
    """
    mock_get_documents.return_value = [
        Document(text="test", metadata={"file_name": "test_file"})
    ]
    mock_insert_vector.return_value = mock.Mock()
    mock_insert_graph.return_value = mock.Mock()
    mock_create_files.return_value = None

    index = await insert_data(1, [mock_file], technique=RagTechnique.VECTOR)
    assert index == mock_insert_vector.return_value
    mock_get_documents.assert_called_with([mock_file])
    mock_insert_vector.assert_called_once_with(
        1, mock_get_documents.return_value, LlmModel.GPT4O_MINI, 1024, 20
    )

    index = await insert_data(1, [mock_file], technique=RagTechnique.GRAPH)
    assert index == mock_insert_graph.return_value
    mock_get_documents.assert_called_with([mock_file])
    mock_insert_graph.assert_called_once_with(
        1, mock_get_documents.return_value, LlmModel.GPT4O_MINI, 1024, 20
    )

    with pytest.raises(ValueError, match="Invalid technique"):
        index = await insert_data(1, [mock_file], technique="invalid")
