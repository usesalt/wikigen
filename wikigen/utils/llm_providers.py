"""
LLM Provider Registry

Defines supported LLM providers, their recommended models, and configuration details.
"""

LLM_PROVIDERS = {
    "gemini": {
        "display_name": "Google Gemini",
        "recommended_models": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
        "api_key_env": "GEMINI_API_KEY",
        "keyring_key": "gemini_api_key",
        "requires_api_key": True,
    },
    "openai": {
        "display_name": "OpenAI",
        "recommended_models": [
            "gpt-4o-mini",
            "gpt-4.1-mini",
            "gpt-5-mini",
            "gpt-5-nano",
        ],
        "api_key_env": "OPENAI_API_KEY",
        "keyring_key": "openai_api_key",
        "requires_api_key": True,
    },
    "anthropic": {
        "display_name": "Anthropic Claude",
        "recommended_models": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-7-sonnet-20250219",
            "claude-3-opus-20240229",
        ],
        "api_key_env": "ANTHROPIC_API_KEY",
        "keyring_key": "anthropic_api_key",
        "requires_api_key": True,
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "recommended_models": [
            "google/gemini-2.5-flash:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-sonnet",
        ],
        "api_key_env": "OPENROUTER_API_KEY",
        "keyring_key": "openrouter_api_key",
        "requires_api_key": True,
    },
    "ollama": {
        "display_name": "Ollama (Local)",
        "recommended_models": [
            "llama3.2",
            "llama3.1",
            "mistral",
            "codellama",
            "phi3",
        ],
        "api_key_env": None,
        "keyring_key": None,
        "requires_api_key": False,
        "base_url": "http://localhost:11434",
        "base_url_env": "OLLAMA_BASE_URL",
    },
}


def get_provider_info(provider_id: str) -> dict:
    """Get provider information by provider ID."""
    if provider_id not in LLM_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_id}")
    return LLM_PROVIDERS[provider_id]


def get_recommended_models(provider_id: str) -> list:
    """Get recommended models for a provider."""
    provider_info = get_provider_info(provider_id)
    return provider_info.get("recommended_models", [])


def get_provider_list() -> list:
    """Get list of all provider IDs."""
    return list(LLM_PROVIDERS.keys())


def get_display_name(provider_id: str) -> str:
    """Get display name for a provider."""
    provider_info = get_provider_info(provider_id)
    return provider_info["display_name"]


def requires_api_key(provider_id: str) -> bool:
    """Check if provider requires an API key."""
    provider_info = get_provider_info(provider_id)
    return provider_info.get("requires_api_key", True)
