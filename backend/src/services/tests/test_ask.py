from unittest.mock import AsyncMock, patch

import pytest

from backend.src.constants import LlmModel, RagTechnique, Technique
from backend.src.models import Message, MessageRole
from backend.src.prompts.techniques import TechniqueFactory
from backend.src.services.ask import ChatService


@pytest.mark.asyncio
async def test_get_response():
    """Test get response"""
    chat_id = 1
    user_input = "What is glaucoma?"
    technique = Technique.COT
    model = LlmModel.GPT4O_MINI
    rag_technique = RagTechnique.VECTOR
    service = ChatService()

    with patch.object(
        TechniqueFactory, "create_technique", return_value=AsyncMock()
    ) as mock_create_technique:
        mock_ask = mock_create_technique.return_value.ask
        mock_ask.return_value = Message(
            content="Here is an AI response", role=MessageRole.ASSISTANT
        )

        response = await service.get_response(
            chat_id=chat_id,
            user_input=user_input,
            chat_histories=[],
            technique=technique,
            model=model,
            rag_technique=rag_technique,
        )

        mock_ask.assert_called_once_with(
            user_input, [], model, rag_technique, chat_id, 3
        )

        assert isinstance(response, Message)
        assert response.content == "Here is an AI response"
