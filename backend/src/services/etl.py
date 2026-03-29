import os
import tempfile
import time
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from dotenv import load_dotenv
from llama_index.core import Document, KnowledgeGraphIndex
from llama_index.core import Settings as LlamaIndexSettings
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.indices.base import BaseIndex
from llama_index.graph_stores.nebula import NebulaGraphStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from nebula3.common.ttypes import ErrorCode
from nebula3.gclient.net import Connection
from nicegui import run

from backend.src.constants import LlmModel, RagTechnique
from backend.src.llamaindex_extensions.pdftextimagereader import PDFTextImageReader
from backend.src.llm.models import LlmFactory
from backend.src.services.file import create_files
from common import File

load_dotenv()

NEBULA_USER = os.getenv("NEBULA_USER")
NEBULA_PASSWORD = os.getenv("NEBULA_PASSWORD")
NEBULA_ADDRESS = os.getenv("NEBULA_ADDRESS")
NEBULA_ADDRESS, NEBULA_PORT = (
    NEBULA_ADDRESS.split(":")
    if isinstance(NEBULA_ADDRESS, str) and ":" in NEBULA_ADDRESS
    else (NEBULA_ADDRESS, "9669")
)


def get_chroma_client():
    """
    Get a ChromaDB client
    """
    return chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST"),
        port=os.getenv("CHROMA_PORT"),
        settings=ChromaSettings(
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=os.getenv("CHROMA_TOKEN"),
        ),
    )


def get_chroma_collection(chat_id: str) -> chromadb.Collection:
    """
    Get or create a collection for a given chat_id
    """
    chroma_client = get_chroma_client()
    return chroma_client.get_or_create_collection(chat_id)


def get_documents_from_binaries(files: list[File]) -> list[Document]:
    """
    Load documents from binary files
    """
    documents = []
    for file in files:
        file_suffix = ".bin." + file.name
        temp_filename = None  # Initialize temp_filename
        try:
            # save a tempfile
            with tempfile.NamedTemporaryFile(
                suffix=file_suffix, delete=False
            ) as temp_file:
                temp_file.write(file.content.read())
                temp_file.flush()
                temp_filename = temp_file.name  # Capture the temporary filename

            reader = SimpleDirectoryReader(
                    input_files=[Path(temp_filename)]
                ) 
            # reader = PDFTextImageReader(
            #     input_files=[Path(temp_filename)],
            #     image_output_dir="./extracted_images",
            #     recursive=True
            # )           
            documents.extend(                
                reader.load_data(num_workers=4)
            )
        except Exception as e:
            # Log the exception properly
            print(f"Failed to load file {file.name}: {e}")
        finally:
            # Ensure the temporary file is deleted
            if temp_filename and os.path.exists(temp_filename):
                os.remove(temp_filename)

    return documents


def insert_vector_data(
    chat_id: int,
    documents: list[Document],
    model=LlmModel.GPT4O_MINI,
    chunk_size=1024,
    chunk_overlap=20,
) -> VectorStoreIndex:
    """
    Insert data into ChromaDB and create a VectorStoreIndex
    """
    chroma_collection = get_chroma_collection("chat-" + str(chat_id))

    print(chroma_collection)

    embedding_model = LlmFactory.create_embedding_model(model)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # by default, the LlamaIndex applys transformation to the documents including splitting
    LlamaIndexSettings.chunk_size = chunk_size
    LlamaIndexSettings.chunk_overlap = chunk_overlap
    return VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, embed_model=embedding_model
    )


def delete_vector_data(chat_id: int):
    """
    Delete data from ChromaDB
    """
    chroma_client = get_chroma_client()
    chroma_client.delete_collection("chat-" + str(chat_id))


def get_exponetial_backoff(retry_times: int, base_sleep_time: int):
    """
    Get exponential backoff time
    """
    return (2**retry_times) * base_sleep_time


def create_nebula_space(space_name):
    """
    Create a NebulaDB space for a given chat_id
    """
    conn = Connection()
    conn.open(NEBULA_ADDRESS, NEBULA_PORT, 1000)
    auth_result = conn.authenticate(NEBULA_USER, NEBULA_PASSWORD)
    session_id = auth_result.get_session_id()
    assert session_id != 0
    resp = conn.execute(
        session_id,
        f"CREATE SPACE IF NOT EXISTS {space_name}(vid_type=FIXED_STRING(256));",
    )
    assert resp.error_code == ErrorCode.SUCCEEDED

    retry_times = 6
    default_sleep_time = 10
    base_sleep_time = 2
    # check if the space is available
    for retry in range(retry_times):
        resp = conn.execute(session_id, f"USE {space_name};")
        if resp.error_code == ErrorCode.SUCCEEDED:
            break
        time.sleep(get_exponetial_backoff(retry, base_sleep_time))
    if resp.error_code != ErrorCode.SUCCEEDED:
        raise ValueError("Failed to create space")

    # create tags, edges and indexes
    resp = conn.execute(
        session_id,
        f"USE {space_name};"
        + "CREATE TAG IF NOT EXISTS entity(name string);"
        + "CREATE EDGE IF NOT EXISTS relationship(relationship string);"
        + "CREATE TAG INDEX IF NOT EXISTS entity_index ON entity(name(256));",
    )
    assert resp.error_code == ErrorCode.SUCCEEDED

    # check if the tag edge and tag index are available
    for _ in range(retry_times):
        resp_tag = conn.execute(session_id, f"USE {space_name};" + "SHOW TAGS;")
        resp_edge = conn.execute(session_id, f"USE {space_name};" + "SHOW EDGES;")
        resp_index = conn.execute(
            session_id, f"USE {space_name};" + "SHOW TAG INDEXES;"
        )
        if (
            resp_tag.error_code == ErrorCode.SUCCEEDED
            and resp_edge.error_code == ErrorCode.SUCCEEDED
            and resp_index.error_code == ErrorCode.SUCCEEDED
            and resp_tag.data
            and len(resp_tag.data.rows) > 0
            and resp_edge.data
            and len(resp_edge.data.rows) > 0
            and resp_index.data
            and len(resp_index.data.rows) > 0
        ):
            break
        time.sleep(get_exponetial_backoff(retry, base_sleep_time))
    if (
        resp_tag.error_code != ErrorCode.SUCCEEDED
        or resp_edge.error_code != ErrorCode.SUCCEEDED
        or resp_index.error_code != ErrorCode.SUCCEEDED
    ):
        raise ValueError("Failed to create tag index")

    time.sleep(default_sleep_time)
    conn.close()


def get_nebula_storage_context(space_name):
    """
    Get a NebulaDB storage context
    """
    edge_types = ["relationship"]
    rel_prop_names = ["relationship"]
    tags = ["entity"]

    graph_store = NebulaGraphStore(
        space_name=space_name,
        edge_types=edge_types,
        rel_prop_names=rel_prop_names,
        tags=tags,
    )

    return StorageContext.from_defaults(graph_store=graph_store)


def insert_graph_data(
    chat_id: int,
    documents: list[Document],
    model=LlmModel.GPT4O_MINI,
    chunk_size=1024,
    chunk_overlap=20,
) -> BaseIndex:
    """
    Insert data into NebulaDB and create a GraphIndex
    """
    LlamaIndexSettings.llm = LlmFactory.create_llm(model, temperature=0)
    LlamaIndexSettings.chunk_size = chunk_size
    LlamaIndexSettings.chunk_overlap = chunk_overlap
    LlamaIndexSettings.embed_model = LlmFactory.create_embedding_model(model)

    space_name = "chat_" + str(chat_id)

    create_nebula_space(space_name)
    storage_context = get_nebula_storage_context(space_name)

    return KnowledgeGraphIndex.from_documents(
        documents,
        storage_context=storage_context,
        max_triplets_per_chunk=10,
    )


def delete_graph_data(chat_id: int):
    """
    Delete data from NebulaDB
    """
    space_name = "chat_" + str(chat_id)
    conn = Connection()
    conn.open(NEBULA_ADDRESS, NEBULA_PORT, 1000)
    auth_result = conn.authenticate(NEBULA_USER, NEBULA_PASSWORD)
    session_id = auth_result.get_session_id()
    assert session_id != 0
    resp = conn.execute(session_id, f"DROP SPACE {space_name};")
    assert resp.error_code == ErrorCode.SUCCEEDED
    conn.close()


async def insert_data(
    chat_id: int,
    files: list[File],
    technique=RagTechnique.VECTOR,
    model=LlmModel.GPT4O_MINI,
    chunk_size=1024,
    chunk_overlap=20,
) -> BaseIndex:
    """
    Insert data into knowledge database based on the specified technique
    """
    documents = get_documents_from_binaries(files)
    document_names = [file.name for file in files]

    match technique:
        case RagTechnique.VECTOR:
            index = await run.io_bound(
                insert_vector_data, chat_id, documents, model, chunk_size, chunk_overlap
            )
        case RagTechnique.GRAPH:
            index = await run.io_bound(
                insert_graph_data, chat_id, documents, model, chunk_size, chunk_overlap
            )
        case _:
            raise ValueError("Invalid technique")

    await create_files(chat_id, document_names)

    return index
