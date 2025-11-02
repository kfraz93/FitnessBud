from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide configuration settings.
    Reads environment variables from .env file and environment.
    """
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Core Application Settings
    APP_NAME: str = "FitnessBud API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    VERSION: str = "0.1.0"

    # Database Settings (Async connection string)
    # CRITICAL: Use the PostgreSQL driver (postgresql+asyncpg) and the credentials
    # defined in the docker run command.
    DATABASE_URL: str

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
