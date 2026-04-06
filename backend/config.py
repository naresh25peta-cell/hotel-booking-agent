from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    All project settings loaded from .env file
    Pydantic validates all values automatically!
    """

    # ── Azure OpenAI ──────────────────────
    AZURE_OPENAI_KEY        : str
    AZURE_OPENAI_ENDPOINT   : str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_DEPLOYMENT : str

    # ── Database ──────────────────────────
    DATABASE_URL: str = "sqlite:///./hotel_booking.db"

    # ── API ───────────────────────────────
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_URL : str = "http://127.0.0.1:8000"

    # ── Langfuse ──────────────────────────
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST      : str = "https://cloud.langfuse.com"
    LANGFUSE_BASE_URL  : str = "https://cloud.langfuse.com"  # newer SDK uses this name

    # ── Auth / JWT ────────────────────────
    JWT_SECRET_KEY     : str = "change-me-in-production-use-a-strong-random-key"
    JWT_ALGORITHM      : str = "HS256"
    JWT_EXPIRE_MINUTES : int = 1440  # 24 hours

    class Config:
        env_file = ".env"

# single instance used everywhere
settings = Settings()