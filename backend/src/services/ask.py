from typing import List

from backend.src.constants import LlmModel, Technique
from backend.src.services.rag import RagTechnique

from ..models import Message
from ..prompts.techniques import TechniqueFactory


# pylint: disable=too-many-arguments
class ChatService:
    """This class represents the chat service. It is responsible for handling chat requests."""

    async def get_response(
        self,
        chat_id,
        user_input: str,
        chat_histories: List[Message],
        technique: Technique = Technique.NONE,
        model: LlmModel = LlmModel.GPT4O_MINI,
        rag_technique: RagTechnique = RagTechnique.VECTOR,
        vector_top_k: int = 3,
    ) -> Message:
        """Get a response based on the user's input, technique, and model."""
        prompt_technique = TechniqueFactory.create_technique(technique)

        return await prompt_technique.ask(
            user_input, chat_histories, model, rag_technique, chat_id, vector_top_k
        )
