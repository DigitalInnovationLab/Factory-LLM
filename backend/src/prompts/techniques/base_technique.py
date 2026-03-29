# pylint: disable=broad-exception-caught

# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals

import os
from abc import ABC, abstractmethod
from typing import List

from langchain_core.language_models import BaseChatModel

from backend.src.constants import LlmModel, RagTechnique
from backend.src.models import Message, MessageRole
from backend.src.services.chat import add_message_to_chat
from backend.src.services.rag import query_knowledge
from backend.src.services.cache import Cache

from ...llm import LlmFactory
from ..controller import Controller
from ..operations import GraphOfOperations
from ..parser import MedicalParser
from ..prompter import MedicalPrompter

EVAL_MODE = os.getenv("APP_ENV") == "evaluation"


class BaseTechnique(ABC):
    """
    Base class for prompting techniques.
    All prompting techniques should inherit from this class.
    """

    async def ask(
        self,
        user_input: str,
        chat_histories: List[Message],
        model: LlmModel,
        rag_technique: RagTechnique,
        chat_id: int,
        vector_top_k: int = 3,
        documents: List[str] = None,
    ) -> Message:
        """Apply prompting technique & RAG to generate a response based on
        user's input and the specified model."""
        llm = LlmFactory.create_llm(model)

        contexts = documents or []
        if len(contexts) == 0:
            contexts = await query_knowledge(
                chat_id,
                user_input,
                rag_technique,
                model,
                vector_top_k=vector_top_k,
            )
        if len(contexts) == 0 and not EVAL_MODE:
            return await add_message_to_chat(
                chat_id=chat_id,
                content="Sorry I don't know.",
                role=MessageRole.ASSISTANT,
            )
        return await self.run(user_input, chat_histories, llm, contexts, chat_id)

    @property
    @abstractmethod
    def method_name(self):
        """Get prompt technique's name"""

    @abstractmethod
    def create_operation_graph(self) -> GraphOfOperations:
        """
        Create a graph of operation instance
        """

    async def run(
        self,
        user_input: str,
        chat_histories: List[Message],
        llm: BaseChatModel,
        contexts: List[str],
        chat_id: int,
    ) -> Message:
        """
        Controller function that executes the GoO.

        :param user_input: Input to be run
        :type user_input: str
        :param chat_histories: Chat histories
        :type user_input: List[Message]
        :param llm: Instance of the model to be used
        :type llm: BaseChatModel
        :param contexts: Contexts for the user input
        :type contexts: List[str]
        :param chat_id: Chat ID
        :type chat_id: str
        :return: Final output after the execution of GoO.
        :rtype: Message
        """        

        operations_graph = self.create_operation_graph()
        executor = Controller(
            llm,
            operations_graph,
            MedicalPrompter(),
            MedicalParser(),
            {
                "user_input": user_input,
                "current": "",
                "phase": 0,
                "method": self.method_name,
                "contexts": contexts,
            },
        )

        cache = Cache("caches")
        cache_key = cache.create_cache_key(
            model=llm.model_name,
            prompt=user_input)
        
        if cache.get(cache_key):
            result = cache.get(cache_key)
        else:
            result = await executor.run(chat_histories)
            cache.set(cache_key, result)
            
        if not EVAL_MODE:
            message = await add_message_to_chat(
                chat_id=chat_id, content=result, role=MessageRole.ASSISTANT
            )
            await executor.store_reasonings(message.id)
        else:
            return result
        return message
