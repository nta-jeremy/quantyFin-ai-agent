from crewai import LLM
from app.core.config import settings

llm = LLM(
    model=settings.LITELLM_MODEL,
    api_key=settings.LITELLM_API_KEY,
    base_url=settings.LITELLM_API_BASE
)
