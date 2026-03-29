from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.models import Base


def init_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    return session()
