import os
import logging
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Configure logging
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(
    log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log"
)

# Set up logger
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent propagation to root logger
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)


def get_cache_file_path() -> Path:
    """Get the cache file path in the WikiGen directory."""
    try:
        from ..config import DEFAULT_OUTPUT_DIR

        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_OUTPUT_DIR / "llm_cache.json"
    except ImportError:
        # Fallback to current directory if config module not available
        return Path("llm_cache.json")


def _call_gemini(prompt: str, model: str, api_key: str) -> str:
    """Call Google Gemini API."""
    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=[prompt])
    return response.text


def _call_openai(prompt: str, model: str, api_key: str) -> str:
    """Call OpenAI API."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    # Check if model is o1 family (requires special format)
    if model.startswith("o1"):
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "text"},
            reasoning_effort="medium",
            store=False,
        )
        return r.choices[0].message.content
    else:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.choices[0].message.content


def _call_anthropic(prompt: str, model: str, api_key: str) -> str:
    """Call Anthropic Claude API."""
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)

    # Check if model supports extended thinking
    thinking_enabled = "sonnet" in model.lower() and "7" in model

    if thinking_enabled:
        response = client.messages.create(
            model=model,
            max_tokens=21000,
            thinking={"type": "enabled", "budget_tokens": 20000},
            messages=[{"role": "user", "content": prompt}],
        )
        # Extended thinking returns content[1].text (the final answer)
        if len(response.content) > 1:
            return response.content[1].text
        return response.content[0].text
    else:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text


def _call_openrouter(prompt: str, model: str, api_key: str) -> str:
    """Call OpenRouter API."""
    import requests

    headers = {"Authorization": f"Bearer {api_key}"}

    data = {"model": model, "messages": [{"role": "user", "content": prompt}]}

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
    )

    if response.status_code != 200:
        error_msg = f"OpenRouter API call failed with status {response.status_code}: {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)

    try:
        response_text = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        error_msg = (
            f"Failed to parse OpenRouter response: {e}; Response: {response.text}"
        )
        logger.error(error_msg)
        raise Exception(error_msg)

    return response_text


def _call_ollama(prompt: str, model: str, api_key: str = None) -> str:
    """Call Ollama API (local LLM)."""
    import requests
    from ..config import load_config

    config = load_config()
    base_url = config.get("ollama_base_url") or os.getenv(
        "OLLAMA_BASE_URL", "http://localhost:11434"
    )

    url = f"{base_url}/api/generate"

    data = {"model": model, "prompt": prompt, "stream": False}

    try:
        response = requests.post(url, json=data, timeout=300)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API call failed: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)


def _save_cache(cache: dict, cache_file: Path) -> None:
    """Save cache to file using atomic write."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=cache_file.parent,
            delete=False,
            suffix=".tmp",
        ) as tmp_file:
            json.dump(cache, tmp_file, indent=2)
            tmp_path = Path(tmp_file.name)

        tmp_path.replace(cache_file)
    except (IOError, OSError, PermissionError) as e:
        logger.error(f"Failed to save cache: {e}")
        if tmp_path is not None:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors


def call_llm(prompt: str, use_cache: bool = True, api_key: str = None) -> str:
    """Call LLM API based on configured provider."""
    # Log the prompt
    logger.info(f"PROMPT: {prompt}")

    # Load cache once if enabled
    cache = {}
    cache_file = None
    if use_cache:
        cache_file = get_cache_file_path()
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, IOError, OSError) as e:
                logger.warning(f"Failed to load cache, starting with empty cache: {e}")

        # Return from cache if exists
        if prompt in cache:
            logger.info(f"RESPONSE: {cache[prompt]}")
            return cache[prompt]

    # Get provider and model from config
    try:
        from ..config import get_llm_provider, get_llm_model, get_api_key
        from .llm_providers import requires_api_key, get_provider_info

        provider = get_llm_provider()
        model = get_llm_model()

        # Get API key if required
        if not api_key:
            if requires_api_key(provider):
                api_key = get_api_key()
                if not api_key:
                    from ..metadata import CLI_ENTRY_POINT

                    provider_info = get_provider_info(provider)
                    api_key_env = provider_info.get("api_key_env", "")
                    raise ValueError(
                        f"{api_key_env} not found. Please run '{CLI_ENTRY_POINT} init' to configure your API key, "
                        f"or set the {api_key_env} environment variable."
                    )
            else:
                api_key = None  # Ollama doesn't need API key
    except ImportError:
        # Fallback to Gemini if config module not available
        provider = "gemini"
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY not found. Please configure your API key or set the GEMINI_API_KEY environment variable."
                )

    # Route to provider-specific implementation
    try:
        if provider == "gemini":
            response_text = _call_gemini(prompt, model, api_key)
        elif provider == "openai":
            response_text = _call_openai(prompt, model, api_key)
        elif provider == "anthropic":
            response_text = _call_anthropic(prompt, model, api_key)
        elif provider == "openrouter":
            response_text = _call_openrouter(prompt, model, api_key)
        elif provider == "ollama":
            response_text = _call_ollama(prompt, model, api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    except Exception as e:
        logger.error(f"Provider {provider} call failed: {e}")
        raise

    # Log the response
    logger.info(f"RESPONSE: {response_text}")

    # Update cache if enabled
    if use_cache and cache_file:
        cache[prompt] = response_text
        _save_cache(cache, cache_file)

    return response_text


if __name__ == "__main__":
    test_prompt = "Hello, how are you?"

    # First call - should hit the API
    print("Making call...")
    response1 = call_llm(test_prompt, use_cache=False)
    print(f"Response: {response1}")
