import json
from tempfile import SpooledTemporaryFile
from typing import List

import pytest
from sqlalchemy import delete

from backend.src.constants import LlmModel, RagTechnique, Technique
from backend.src.models import (
    Chat,
    Message,
    MessageRole,
    ReasoningStep,
    Session,
    User,
)
from backend.src.services.ask import ChatService
from backend.src.services.chat import (
    create_chat,
    get_chats_by_user,
    get_reasoning_steps_by_message,
)
from backend.src.services.etl import insert_data
from backend.src.services.file import get_files_by_chat
from backend.src.services.task import create_task, get_task_by_id
from backend.src.services.user import create_user, get_user_by_id
from common import File

# pylint: disable=consider-using-with


def create_file_from_pdf(pdf_file_path: str) -> File:
    """
    Create a File model from the given PDF file.
    """
    with open(pdf_file_path, "rb") as pdf_file:
        # Create a SpooledTemporaryFile and write the PDF content into it
        spooled_temp_file = SpooledTemporaryFile()
        spooled_temp_file.write(pdf_file.read())

        # Important: Reset the file pointer to the beginning of the file
        spooled_temp_file.seek(0)
        file_name = pdf_file_path.split("/")[-1]
        file_model = File(name=file_name, content=spooled_temp_file)
        return file_model


async def setup_data(prompt_technique: Technique, rag_technique: RagTechnique) -> Chat:
    """Setup util method"""
    user = await create_user("integrationtester@email.com")
    task = await create_task(
        user_id=user.id,
        task_name="Integration test task",
        task_description="Integration testing description",
        initial_system_prompt="Think carefully before answering the question",
        llm_model=LlmModel.GPT4O,
        prompting_technique=prompt_technique,
    )
    chat = await create_chat(user.id, task.id, rag_technique)
    file = create_file_from_pdf(
        "backend/tests_integration/documents/Glaucoma _ National Eye Institute.pdf"
    )
    await insert_data(
        chat_id=chat.id,
        files=[file],
        technique=rag_technique,
        model=LlmModel.GPT4O,
    )
    return chat


async def tear_down(user_id, chat_id, task_id, message_id) -> None:
    """Tear down the setup data"""
    # Delete user afterwards
    async with Session.begin() as session:
        stmt = delete(User).where(User.id == user_id)
        await session.execute(stmt)
    assert (await get_chats_by_user(user_id))[1] == 0
    assert len(await get_files_by_chat(chat_id)) == 0
    assert len(await get_reasoning_steps_by_message(message_id)) == 0
    assert await get_user_by_id(user_id) is None
    assert await get_task_by_id(task_id) is None


@pytest.mark.asyncio
async def test_prompt_rag_integration():
    """Test Prompt + RAG techniques combination integration"""
    for prompt_technique in [
        Technique.NONE,
        Technique.COT,
        Technique.TOT,
        Technique.GOT,
    ]:
        for rag_technique in [
            RagTechnique.VECTOR
        ]:  # Remove GRAPH because it is prone to server issue
            chat = await setup_data(prompt_technique, rag_technique)
            user_id = chat.user_id
            chat_id = chat.id
            task_id = chat.task_id
            try:
                response = await ChatService().get_response(
                    chat_id,
                    "What is glaucoma?",
                    [],
                    prompt_technique,
                    LlmModel.GPT4O_MINI,
                    rag_technique,
                )
                message_id = response.id
                assert isinstance(response, Message), "Response must be of type Message"
                assert isinstance(response.content, str), "Content must be of type str"
                assert response.role == MessageRole.ASSISTANT, "Role must be assistant"
                assert response.chat_id == chat_id
                reasoning_steps = await get_reasoning_steps_by_message(message_id)
                verify_reasoning_steps(prompt_technique, reasoning_steps)
            finally:
                await tear_down(user_id, chat_id, task_id, message_id)


def verify_reasoning_steps(
    prompting_technique: Technique, reasoning_steps: List[ReasoningStep]
):
    """Verify reasoning steps created correctly"""
    match prompting_technique:
        case Technique.NONE:
            assert len(reasoning_steps) == 1
            assert reasoning_steps[0].name == "GENERATE"
            content = json.loads(reasoning_steps[0].content)
            assert isinstance(content, List)
            assert len(content) == 1

        case Technique.COT:
            assert len(reasoning_steps) == 3
            for reasoning_step in reasoning_steps:
                assert reasoning_step.name == "GENERATE"
                content = json.loads(reasoning_step.content)
                assert isinstance(content, List)
                assert len(content) == 1

        case Technique.TOT:
            assert len(reasoning_steps) == 4
            for i, reasoning_step in enumerate(reasoning_steps):
                name = reasoning_step.name
                content = json.loads(reasoning_step.content)
                assert isinstance(content, List)
                if (i % 2) == 0:
                    assert name == "GENERATE"
                    assert len(content) == 5
                else:
                    assert name == "VOTE"
                    assert len(content) == 1

        case Technique.GOT:
            assert len(reasoning_steps) == 6
            for i, reasoning_step in enumerate(reasoning_steps):
                name = reasoning_step.name
                content = json.loads(reasoning_step.content)
                assert isinstance(content, List)
                if (i % 3) == 0:
                    assert name == "GENERATE"
                    assert len(content) == 5
                elif (i % 3) == 1:
                    assert name == "AGGREGATE"
                    assert len(content) == 2
                else:
                    assert name == "VOTE"
                    assert len(content) == 1
