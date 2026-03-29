import os

import dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .base import Base
from .chat import Chat
from .feedback import Feedback
from .file import File
from .message import Message, MessageRole
from .reasoning_step import ReasoningStep
from .task import Task
from .user import User

dotenv.load_dotenv()

DEVELOPMENT = os.getenv("APP_ENV") == "development"


engine = create_async_engine(
    os.getenv("DB_CONNECTION"),
    echo=DEVELOPMENT,
    echo_pool=DEVELOPMENT,
    pool_recycle=3 * 60 * 60,  # 3 hours
    pool_pre_ping=True,
)

Session = async_sessionmaker(engine, expire_on_commit=False)
