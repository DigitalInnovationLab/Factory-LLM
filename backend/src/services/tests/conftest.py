import pytest
@pytest.fixture(scope="session")
def database_url():
    return "sqlite+aiosqlite:///:memory:"