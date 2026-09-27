"""Factory pattern for initializing LLMs across different model providers."""

from typing import Optional, Any
from common.config import settings


def get_llm(
    provider: str = "openai",
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs: Any,
) -> Any:
    """Instantiate and return a Chat model based on provider and parameters.
    
    Supported providers:
    - 'openai' (default: gpt-4o-mini / gpt-4o)
    - 'anthropic' (default: claude-3-5-sonnet-latest)
    - 'google' (default: gemini-1.5-pro / gemini-2.0-flash)
    """
    provider_lower = provider.lower()

    if provider_lower == "openai":
        from langchain_openai import ChatOpenAI
        model = model_name or "gpt-4o-mini"
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY,
            **kwargs,
        )
    elif provider_lower == "anthropic":
        from langchain_anthropic import ChatAnthropic
        model = model_name or "claude-3-5-sonnet-20241022"
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=settings.ANTHROPIC_API_KEY,
            **kwargs,
        )
    elif provider_lower in ("google", "gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = model_name or "gemini-1.5-pro"
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=settings.GOOGLE_API_KEY,
            **kwargs,
        )
    else:
        raise ValueError(
            f"Unsupported provider: '{provider}'. Choose from ['openai', 'anthropic', 'google']."
        )
