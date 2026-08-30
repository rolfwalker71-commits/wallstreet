from langchain_openai import ChatOpenAI

from app.config import get_settings


def get_llm(mini: bool = False) -> ChatOpenAI | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    model = settings.openai_mini_model if mini else settings.openai_model
    return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )