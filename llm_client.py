"""Provider-agnostic LLM client factory.

DeepSeek and OpenAI speak the same OpenAI-style chat.completions API; Claude
(Anthropic) has a different request/response shape. Callers should use
complete() rather than calling the client directly — it hides that
difference behind one interface: system prompt + message history in,
response text out. Add a new provider by adding an entry to PROVIDERS and,
if its API isn't OpenAI-compatible, a branch in complete().
"""

import os

import anthropic
from openai import OpenAI

PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
    },
    "openai": {
        "base_url": None,  # OpenAI SDK default
        "api_key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "anthropic": {
        "api_key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-opus-5",
    },
}


def _provider_name(provider: str | None = None) -> str:
    return provider or os.getenv("LLM_PROVIDER", "deepseek")


def _provider_config(provider: str | None = None) -> dict:
    provider = _provider_name(provider)
    try:
        return PROVIDERS[provider]
    except KeyError:
        raise ValueError(f"Unknown LLM_PROVIDER {provider!r}. Known providers: {list(PROVIDERS)}") from None


def get_client(provider: str | None = None):
    provider = _provider_name(provider)
    config = _provider_config(provider)
    api_key = os.getenv(config["api_key_env"])

    if provider == "anthropic":
        return anthropic.Anthropic(api_key=api_key)
    return OpenAI(api_key=api_key, base_url=config["base_url"])


def default_model(provider: str | None = None) -> str:
    return _provider_config(provider)["default_model"]


def complete(client, model: str, system_prompt: str, messages: list[dict], max_tokens: int = 1024) -> str:
    """Send a chat request and return the reply text, regardless of provider."""
    if isinstance(client, anthropic.Anthropic):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return next((block.text for block in response.content if block.type == "text"), "")

    completion = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )
    return completion.choices[0].message.content or ""
