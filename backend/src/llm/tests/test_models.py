import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding

from backend.src.constants import LlmModel
from backend.src.llm import LlmFactory


def test_create_llm():
    """Test create LLM"""
    model = LlmFactory.create_llm(LlmModel.GPT35)
    assert isinstance(model, ChatOpenAI)
    model = LlmFactory.create_llm(LlmModel.GEMINI15_FLASH)
    assert isinstance(model, ChatGoogleGenerativeAI)
    with pytest.raises(ValueError, match="Invalid model"):
        LlmFactory.create_llm("Invalid model")


def test_create_embedding_model():
    """Test create embedding model"""
    embedding = LlmFactory.create_embedding_model(LlmModel.GPT35)
    assert isinstance(embedding, OpenAIEmbedding)
    embedding = LlmFactory.create_embedding_model(LlmModel.GEMINI15_FLASH)
    assert isinstance(embedding, GeminiEmbedding)
    with pytest.raises(ValueError, match="Invalid model"):
        LlmFactory.create_embedding_model("Invalid model")
