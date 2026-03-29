from typing import List, Optional

from llama_index.core import Settings as LlamaIndexSettings
from llama_index.core import VectorStoreIndex
from llama_index.core.indices.base import BaseIndex
from llama_index.core.retrievers import (
    KnowledgeGraphRAGRetriever,
    VectorIndexRetriever,
)
from llama_index.vector_stores.chroma import ChromaVectorStore

from backend.src.constants import LlmModel, RagTechnique
from backend.src.llm.models import LlmFactory
from backend.src.services.etl import (
    get_chroma_collection,
    get_nebula_storage_context,
)


async def query_vector(
    chat_id: int,
    query: str,
    model=LlmModel.GPT4O_MINI,
    index: Optional[VectorStoreIndex] = None,
    top_k=3,
) -> List[str]:
    """
    Query the vector database
    """
    collection = get_chroma_collection(f"chat-{chat_id}")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    embedding_model = LlmFactory.create_embedding_model(model)

    if index is None:
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, embed_model=embedding_model
        )

    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=top_k,
    )
    retrieved_documents = await retriever.aretrieve(query)

    text_contexts: List[str] = []
    for doc in retrieved_documents:
        text_context = f"""{doc.text}"""
        if "image_paths" in doc.metadata:
            text_context += f"""###IMAGES_START###{doc.metadata["image_paths"]}###IMAGES_END###"""
        text_contexts.append(text_context)


    return text_contexts

async def query_vector_with_score(
    chat_id: int,
    query: str,
    model=LlmModel.GPT4O_MINI,
    index: Optional[VectorStoreIndex] = None,
    top_k=3,
) -> List:
    """
    Query the vector database
    """
    collection = get_chroma_collection(f"chat-{chat_id}")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    embedding_model = LlmFactory.create_embedding_model(model)

    if index is None:
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, embed_model=embedding_model
        )

    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=top_k,
    )
    retrieved_documents = await retriever.aretrieve(query)

    text_contexts: List = {}
    for doc in retrieved_documents:
        text_context = f"""{doc.text}"""
        text_contexts.append({
            "text": text_context,
            "score": doc.score,
        })


    return text_contexts


async def query_graph(
    chat_id: int,
    query: str,
    model=LlmModel.GPT4O_MINI,
) -> List[str]:
    """
    Query the graph database
    """
    LlamaIndexSettings.llm = LlmFactory.create_llm(model, temperature=0)
    LlamaIndexSettings.chunk_size = 512
    LlamaIndexSettings.embed_model = LlmFactory.create_embedding_model(model)

    storage_context = get_nebula_storage_context("chat_" + str(chat_id))

    retriever = KnowledgeGraphRAGRetriever(
        storage_context=storage_context,
        llm=LlamaIndexSettings.llm,
    )
    retrieved_documents = await retriever.aretrieve(query)

    return [doc.text for doc in retrieved_documents]


async def query_knowledge(
    chat_id: int,
    query: str,
    technique=RagTechnique.VECTOR,
    model=LlmModel.GPT4O_MINI,
    index: Optional[BaseIndex] = None,
    vector_top_k=3,
) -> List[str]:
    """
    Query the knowledge base
    """
    match technique:
        case RagTechnique.VECTOR:
            return await query_vector(chat_id, query, model, index, vector_top_k)
        case RagTechnique.GRAPH:
            return await query_graph(chat_id, query, model)
        case _:
            raise ValueError("Invalid technique")
