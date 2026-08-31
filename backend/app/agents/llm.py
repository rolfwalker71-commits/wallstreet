from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.services.usage import record_usage, usage_from_message


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


def invoke_llm(llm: ChatOpenAI, messages, *, purpose: str):
    msg = llm.invoke(messages)
    prompt, completion = usage_from_message(msg)
    model = getattr(llm, "model_name", None) or str(getattr(llm, "model", "unknown"))
    record_usage(purpose, model, prompt, completion)
    return msg
