import asyncio
from typing import List

from langchain_core.messages import BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI


async def query(llm: BaseChatModel, messages: List[BaseMessage], n=1) -> List[str]:
    """
    Generate responses for the query via LLM agent
    """
    if isinstance(llm, ChatGoogleGenerativeAI):
        # Gemini does not support multiple generations
        # Generate n times instead
        tasks = [llm.agenerate([messages]) for _ in range(n)]
        responses = await asyncio.gather(*tasks)
        return [response.generations[0][0].text for response in responses]

    # Use the agenerate method to specify `n`
    response = await llm.agenerate([messages], n=n)
    return [generation.text for generation in response.generations[0]]
