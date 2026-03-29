from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import HumanMessage
from langchain_core.outputs import Generation, LLMResult
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.src.llm.llm_utils import query


@pytest.mark.asyncio
async def test_query():
    """Test query with mock llm"""
    # Create a mock LLM
    mock_llm = AsyncMock()
    mock_llm.agenerate.return_value = LLMResult(
        generations=[[Generation(text="Response 1"), Generation(text="Response 2")]]
    )

    messages = [HumanMessage(content="Input")]
    result = await query(mock_llm, messages, 2)

    assert result == ["Response 1", "Response 2"]


@pytest.mark.asyncio
async def test_query_with_google_genai():
    """Test query with ChatGoogleGenerativeAI mock"""
    # Create a mock ChatGoogleGenerativeAI
    mock_llm = AsyncMock(spec=ChatGoogleGenerativeAI)
    mock_llm.agenerate.side_effect = [
        LLMResult(generations=[[Generation(text="Response 1")]]),
        LLMResult(generations=[[Generation(text="Response 2")]]),
    ]

    messages = [HumanMessage(content="Input")]
    result = await query(mock_llm, messages, 2)

    assert result == ["Response 1", "Response 2"]
