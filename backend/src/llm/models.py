import os

import dotenv
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.embeddings.openai import (
    OpenAIEmbedding,
    OpenAIEmbeddingModelType,
)

from backend.src.constants import LlmModel

dotenv.load_dotenv()


class LlmFactory:
    """Factory class for creating LLM chat models"""

    @staticmethod
    def create_llm(
        model=LlmModel.GPT4O_MINI, api_key="", max_tokens=4096, temperature=0.6
    ) -> BaseChatModel:
        """Creates an LLM chat model based on the specified model"""

        match model:
            case (
                LlmModel.GPT35 | LlmModel.GPT4 | LlmModel.GPT4O_MINI | LlmModel.GPT4O 
            ):
                return ChatOpenAI(
                    model=model.value,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    openai_api_key=api_key if api_key else os.getenv("OPENAI_API_KEY"),
                )
            case (
                LlmModel.QUASARALPHA
                | LlmModel.GEMINI23_PRO_EXP
                | LlmModel.DEEPSEEKV3
                | LlmModel.DEEPSEEKR1
                | LlmModel.DEEPSEEKR1_ZERO
                | LlmModel.LLAMA4_MAVERICK
                | LlmModel.LLAMA4_SCOUT
                | LlmModel.QWEN3_235B_INSTRUCT
                | LlmModel.GEMMA3_27B
		| LlmModel.GEMINI31_PRO
		| LlmModel.GEMINI31_PRO
            ):
            
                return ChatOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    model=model.value,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    openai_api_key=api_key if api_key else os.getenv("OPENROUTER_API_KEY"),
                )
            # case (
            #     #new models LlmModel
            # ):
            
            #     return ChatOpenAI(
            #         base_url="https://openrouter.ai/api/v1",
            #         model=model.value,
            #         temperature=temperature,
            #         max_tokens=max_tokens,
            #         openai_api_key=api_key if api_key else os.getenv("LOCAL_API_KEY"),
            #     )    

            case LlmModel.GEMINI15_FLASH | LlmModel.GEMINI15_PRO | LlmModel.GEMINI20_FLASH:
                return ChatGoogleGenerativeAI(
                    model=model.value,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    google_api_key=api_key if api_key else os.getenv("GOOGLE_API_KEY"),
                )
            case _:
                raise ValueError("Invalid model")

    @staticmethod
    def create_embedding_model(model=LlmModel.GPT4O_MINI) -> BaseEmbedding:
        """
        Creates an embedding model based on the specified LLM
        """
        match model:
            case (
                LlmModel.GPT35 
                | LlmModel.GPT4
                | LlmModel.GPT4O_MINI 
                | LlmModel.GPT4O 
                | LlmModel.GEMINI15_PRO 
                | LlmModel.GEMINI15_FLASH 
                | LlmModel.GEMINI20_FLASH
                | LlmModel.QUASARALPHA
                | LlmModel.GEMINI23_PRO_EXP
                | LlmModel.DEEPSEEKV3
                | LlmModel.DEEPSEEKR1
                | LlmModel.DEEPSEEKR1_ZERO
                | LlmModel.LLAMA4_MAVERICK
                | LlmModel.LLAMA4_SCOUT
		| LlmModel.QWEN3_235B_INSTRUCT
		| LlmModel.GEMMA3_27B
		| LlmModel.GEMINI31_PRO
                # LlmModel.QWEN7B
            ):
                return OpenAIEmbedding(
                    model_name=OpenAIEmbeddingModelType.TEXT_EMBED_ADA_002,
                    api_key=os.getenv("OPENAI_API_KEY"),
                )
            # case LlmModel.GEMINI15_PRO | LlmModel.GEMINI15_FLASH | LlmModel.GEMINI20_FLASH:
            #     return GeminiEmbedding(
            #         model_name="models/embedding-001",
            #         api_key=os.getenv("GOOGLE_API_KEY"),
            #     )
            case _:
                raise ValueError("Invalid model")


