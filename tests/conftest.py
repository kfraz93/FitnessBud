import pytest
from core.config import Settings
from dotenv import load_dotenv

load_dotenv(dotenv_path='./.env.test', override=True)

@pytest.fixture(scope="session")
def mock_settings():
    """Provides the Settings object initialized with .env.test variables."""
    return Settings()