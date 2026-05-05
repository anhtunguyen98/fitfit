from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    ai_base_url: str = "http://localhost:8001/v1"
    ai_model: str = "qwen3"
    ai_timeout: int = 120
    database_url: str = "sqlite:///./overfit.db"
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings(
    ai_base_url=os.getenv("AI_BASE_URL", "http://localhost:8001/v1"),
    ai_model=os.getenv("AI_MODEL", "qwen3"),
    ai_timeout=int(os.getenv("AI_TIMEOUT", "120")),
    database_url=os.getenv("DATABASE_URL", "sqlite:///./overfit.db"),
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8000")),
)
