import asyncio
import subprocess
import sys

from backend.src.models.message import MessageRole
from backend.src.services.chat import add_message_to_chat, create_chat
from backend.src.services.task import create_task
from backend.src.services.user import (
    create_user,
    delete_user_by_id,
    get_user_by_email,
)

# Constant for test user email
TEST_USER_EMAIL = "testuser@mail.com"


async def setup_chat(user_id, task_id):
    """Setup a chat with messages"""
    chat = await create_chat(user_id, task_id)
    await add_message_to_chat(chat.id, "Test Message")
    await add_message_to_chat(chat.id, "Test Response", MessageRole.ASSISTANT)
    return chat


async def setup():
    """Setup the test environment"""
    user = await get_user_by_email(TEST_USER_EMAIL)
    if not user:
        user = await create_user(TEST_USER_EMAIL)
    test_task = await create_task(
        user.id, "Test Task", "Test Task Description", "Test Prompt"
    )
    await setup_chat(user.id, test_task.id)
    await setup_chat(user.id, test_task.id)
    return user


async def clean_up(user_id):
    """Clean up the test environment"""
    await delete_user_by_id(user_id)


async def run_test():
    """Run the test"""
    user = await setup()
    # Run the test
    try:
        process = subprocess.Popen(
            ["pytest", "test_ui/"] + sys.argv[1:],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for line in process.stdout:
            print(line, end="")

        _, stderr = process.communicate()

        if stderr:
            print(f"Error message: {stderr}")

        exit_code = process.returncode
    # pylint: disable=broad-exception-caught
    except Exception as e:
        if isinstance(e, KeyboardInterrupt):
            process.terminate()
        print(f"Error: {e}")
        exit_code = 1
    finally:
        await clean_up(user.id)
    # pylint: enable=broad-exception-caught

    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(run_test()))
