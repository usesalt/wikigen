"""
Configuration management for WikiGen.
Handles loading, saving, and merging configuration with CLI arguments.
"""

import os
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from .defaults import DEFAULT_CONFIG


def _get_platform_config_base() -> Path:
    """
    Return the OS-appropriate user config base directory.

    - macOS: ~/Library/Application Support
    - Windows: %APPDATA%
    - Linux/other: $XDG_CONFIG_HOME or ~/.config
    """
    home = Path.home()
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        return Path(appdata) if appdata else home / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        # Follow XDG-style on macOS per project preference
        xdg = os.environ.get("XDG_CONFIG_HOME")
        return Path(xdg) if xdg else home / ".config"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        return Path(xdg) if xdg else home / ".config"


def _get_new_config_dir() -> Path:
    """Return the new config directory for wikigen under the platform base."""
    return _get_platform_config_base() / "wikigen"


def _get_legacy_config_dir() -> Path:
    """Return the previous Documents-based config directory (for migration)."""
    return Path.home() / "Documents" / "WikiGen" / ".salt"


# Configuration paths
CONFIG_DIR = _get_new_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "WikiGen"


def _migrate_legacy_config_if_needed() -> None:
    """
    If a legacy config exists in the old Documents path and the new config
    doesn't exist yet, migrate the file and directory.
    """
    legacy_dir = _get_legacy_config_dir()
    legacy_file = legacy_dir / "config.json"
    if CONFIG_FILE.exists():
        return
    if legacy_file.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            # Copy then remove legacy to be safe
            with open(legacy_file, "r", encoding="utf-8") as f:
                data = f.read()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(data)
            # best-effort cleanup of empty legacy dir
            try:
                legacy_file.unlink(missing_ok=True)
            except Exception:
                pass
            try:
                # remove legacy dir if empty
                legacy_dir.rmdir()
            except Exception:
                pass
        except Exception:
            # Ignore migration errors — user can re-init
            pass


def init_config() -> None:
    """Interactive setup wizard for init command."""
    import getpass

    from .formatter.init_formatter import (
        print_init_header,
        print_section_start,
        print_input_prompt,
        print_init_complete,
    )
    from .formatter.output_formatter import Colors, Icons, Tree
    from .utils.llm_providers import (
        get_provider_list,
        get_display_name,
        get_recommended_models,
        get_provider_info,
        requires_api_key,
    )

    # Create directories
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print_init_header()

    # LLM Provider Selection section
    print_section_start("LLM Provider", Icons.INFO)

    # Show provider list
    providers = get_provider_list()
    print(
        f"{Colors.LIGHT_GRAY}{Tree.VERTICAL}  {Colors.LIGHT_GRAY}{Tree.MIDDLE} "
        f"{Colors.MEDIUM_GRAY}Available providers:{Colors.RESET}"
    )
    for i, provider_id in enumerate(providers, 1):
        display_name = get_display_name(provider_id)
        print(
            f"{Colors.LIGHT_GRAY}{Tree.VERTICAL}  {Colors.LIGHT_GRAY}{Tree.VERTICAL}  "
            f"{Colors.MEDIUM_GRAY}{i}) {display_name}{Colors.RESET}"
        )

    # Provider selection
    print_input_prompt(
        "Select LLM provider (enter number)", Icons.ANALYZING, is_required=True
    )
    provider_choice = input().strip()

    try:
        provider_index = int(provider_choice) - 1
        if provider_index < 0 or provider_index >= len(providers):
            print(f"✘ Invalid provider selection: {provider_choice}")
            sys.exit(1)
        llm_provider = providers[provider_index]
    except ValueError:
        print(f"✘ Invalid provider selection: {provider_choice}")
        sys.exit(1)

    provider_info = get_provider_info(llm_provider)
    provider_display = get_display_name(llm_provider)

    # Model Selection
    print_section_start("Model Selection", Icons.INFO)

    # Show recommended models
    recommended_models = get_recommended_models(llm_provider)
    print(
        f"{Colors.LIGHT_GRAY}{Tree.VERTICAL}  {Colors.LIGHT_GRAY}{Tree.MIDDLE} "
        f"{Colors.MEDIUM_GRAY}Recommended models for {provider_display}:{Colors.RESET}"
    )
    for i, model in enumerate(recommended_models, 1):
        print(
            f"{Colors.LIGHT_GRAY}{Tree.VERTICAL}  {Colors.LIGHT_GRAY}{Tree.VERTICAL}  "
            f"{Colors.MEDIUM_GRAY}{i}) {model}{Colors.RESET}"
        )
    print(
        f"{Colors.LIGHT_GRAY}{Tree.VERTICAL}  {Colors.LIGHT_GRAY}{Tree.VERTICAL}  "
        f"{Colors.MEDIUM_GRAY}{len(recommended_models) + 1}) Enter custom model name{Colors.RESET}"
    )

    print_input_prompt(
        f"Select model for {provider_display} (enter number or custom name)",
        Icons.ANALYZING,
        is_required=True,
    )
    model_choice = input().strip()

    # Parse model selection
    try:
        model_index = int(model_choice) - 1
        if model_index == len(recommended_models):
            # Custom model
            print_input_prompt(
                "Enter custom model name", Icons.CONFIG, is_required=True
            )
            llm_model = input().strip()
            if not llm_model:
                print("✘ Model name cannot be empty!")
                sys.exit(1)
        elif 0 <= model_index < len(recommended_models):
            llm_model = recommended_models[model_index]
        else:
            print(f"✘ Invalid model selection: {model_choice}")
            sys.exit(1)
    except ValueError:
        # Custom model name entered directly
        llm_model = model_choice

    # API Keys section
    print_section_start("API Keys", Icons.INFO)

    # Get API key if required
    api_key = None
    custom_url = None
    if requires_api_key(llm_provider):
        env_var = provider_info.get("api_key_env")
        key_name = env_var or f"{provider_display} API Key"

        print_input_prompt(key_name, Icons.ANALYZING, is_required=True)
        api_key = getpass.getpass().strip()
        if not api_key:
            print(f"✘ {key_name} is required!")
            sys.exit(1)
    else:
        # Ollama - just show base URL
        base_url = provider_info.get("base_url", "http://localhost:11434")
        print_input_prompt(
            "Ollama Base URL", Icons.CONFIG, is_required=False, default_value=base_url
        )
        custom_url = input().strip()
        # For Ollama, use default if empty
        if not custom_url:
            custom_url = base_url

    # GitHub Token
    print_input_prompt(
        "GitHub Token", Icons.ANALYZING, is_required=False, default_value="skip"
    )
    github_token = input().strip()

    # Store in keyring if available, otherwise save to config
    keyring_available = KEYRING_AVAILABLE
    if keyring_available:
        try:
            if api_key:
                keyring.set_password("wikigen", provider_info["keyring_key"], api_key)
            if github_token:
                keyring.set_password("wikigen", "github_token", github_token)
        except (OSError, RuntimeError, AttributeError):
            keyring_available = False

    # Preferences section
    print_section_start("Preferences", Icons.INFO)

    # Output Directory
    print_input_prompt(
        "Output Directory",
        Icons.CONFIG,
        is_required=False,
        default_value=str(DEFAULT_OUTPUT_DIR),
    )
    output_dir = input().strip()
    if not output_dir:
        output_dir = str(DEFAULT_OUTPUT_DIR)

    # Language
    print_input_prompt(
        "Language", Icons.CONFIG, is_required=False, default_value="english"
    )
    language = input().strip()
    if not language:
        language = "english"

    # Max Abstractions
    print_input_prompt(
        "Max Abstractions", Icons.CONFIG, is_required=False, default_value="5"
    )
    max_abstractions_input = input().strip()
    if not max_abstractions_input:
        max_abstractions = 5
    else:
        try:
            max_abstractions = int(max_abstractions_input)
        except ValueError:
            max_abstractions = 5

    # Documentation Mode
    print_input_prompt(
        "Documentation Mode (minimal/comprehensive)",
        Icons.CONFIG,
        is_required=False,
        default_value="minimal",
    )
    documentation_mode_input = input().strip().lower()
    if not documentation_mode_input:
        documentation_mode = "minimal"
    elif documentation_mode_input in ["minimal", "comprehensive"]:
        documentation_mode = documentation_mode_input
    else:
        print(f"⚠ Warning: Invalid mode '{documentation_mode_input}'. Using 'minimal'.")
        documentation_mode = "minimal"

    # Build configuration
    config = {
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "output_dir": output_dir,
        "language": language,
        "max_abstractions": max_abstractions,
        "max_file_size": DEFAULT_CONFIG["max_file_size"],
        "use_cache": DEFAULT_CONFIG["use_cache"],
        "include_patterns": DEFAULT_CONFIG["include_patterns"],
        "exclude_patterns": DEFAULT_CONFIG["exclude_patterns"],
        "documentation_mode": documentation_mode,
    }

    # Store Ollama base URL if custom
    if llm_provider == "ollama" and custom_url and custom_url != base_url:
        config["ollama_base_url"] = custom_url

    # Add API keys to config if keyring not available
    if not keyring_available:
        if api_key:
            config[provider_info["keyring_key"]] = api_key
        if github_token:
            config["github_token"] = github_token

    # Save configuration
    save_config(config)

    # Print completion message
    print_init_complete(CONFIG_FILE, output_dir, keyring_available)


def load_config() -> Dict[str, Any]:
    """Load configuration from file and keyring."""
    config = DEFAULT_CONFIG.copy()

    # Attempt migration from legacy location
    _migrate_legacy_config_if_needed()

    # Load from file if it exists
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                config.update(file_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠ Warning: Could not load config file: {e}")

    # Load API keys from keyring if available
    # Load all provider API keys dynamically
    if KEYRING_AVAILABLE:
        try:
            from .utils.llm_providers import LLM_PROVIDERS

            for provider_id, provider_info in LLM_PROVIDERS.items():
                keyring_key = provider_info.get("keyring_key")
                if keyring_key:
                    api_key = keyring.get_password("wikigen", keyring_key)
                    if api_key:
                        config[keyring_key] = api_key

            github_token = keyring.get_password("wikigen", "github_token")
            if github_token:
                config["github_token"] = github_token
        except (OSError, RuntimeError, AttributeError) as e:
            print(f"⚠ Warning: Could not load from keyring: {e}")

    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Don't save API keys to file if keyring is available
    config_to_save = config.copy()
    if KEYRING_AVAILABLE:
        # Remove all provider API keys from config file
        from .utils.llm_providers import LLM_PROVIDERS

        for provider_info in LLM_PROVIDERS.values():
            keyring_key = provider_info.get("keyring_key")
            if keyring_key:
                config_to_save.pop(keyring_key, None)
        config_to_save.pop("github_token", None)

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_to_save, f, indent=2)
    except IOError as e:
        print(f"✘ Error saving config: {e}")
        sys.exit(1)


def merge_config_with_args(config: Dict[str, Any], args) -> Dict[str, Any]:
    """Merge configuration with CLI arguments (CLI takes precedence)."""
    merged = config.copy()

    # Map argparse attributes to config keys
    arg_mapping = {
        "output": "output_dir",
        "language": "language",
        "max_abstractions": "max_abstractions",
        "max_size": "max_file_size",
        "no_cache": "use_cache",  # Note: inverted logic
        "include": "include_patterns",
        "exclude": "exclude_patterns",
        "token": "github_token",
        "mode": "documentation_mode",
    }

    for arg_name, config_key in arg_mapping.items():
        if hasattr(args, arg_name):
            value = getattr(args, arg_name)
            if arg_name == "no_cache":
                # For store_true flags, only override if explicitly provided (True)
                # Invert the logic: no_cache=True means use_cache=False
                if value is True:
                    merged[config_key] = False
            elif value is not None:
                if arg_name in ["include", "exclude"]:
                    # Convert to list if it's a set
                    if isinstance(value, set):
                        merged[config_key] = list(value)
                    else:
                        merged[config_key] = value
                else:
                    merged[config_key] = value

    return merged


def check_config_exists() -> bool:
    """Check if configuration file exists."""
    return CONFIG_FILE.exists()


def get_llm_provider() -> str:
    """Get LLM provider from config, defaulting to gemini."""
    config = load_config()
    return config.get("llm_provider", "gemini")


def get_llm_model() -> str:
    """Get LLM model from config, defaulting to gemini-2.5-flash."""
    config = load_config()
    return config.get("llm_model", "gemini-2.5-flash")


def get_api_key() -> Optional[str]:
    """Get API key from config or environment based on current provider."""
    from .utils.llm_providers import get_provider_info, requires_api_key

    config = load_config()
    provider = get_llm_provider()

    # Check if provider requires API key
    if not requires_api_key(provider):
        return None

    provider_info = get_provider_info(provider)
    keyring_key = provider_info.get("keyring_key")
    env_var = provider_info.get("api_key_env")

    # Try keyring first, then env var
    api_key = None
    if keyring_key and KEYRING_AVAILABLE:
        try:
            api_key = keyring.get_password("wikigen", keyring_key)
        except (OSError, RuntimeError, AttributeError):
            pass

    if not api_key:
        # Try config file fallback
        api_key = config.get(keyring_key or "")

    if not api_key and env_var:
        # Fallback to environment variable
        api_key = os.getenv(env_var)

    return api_key


def get_github_token() -> Optional[str]:
    """Get GitHub token from config or environment."""
    config = load_config()
    return config.get("github_token") or os.getenv("GITHUB_TOKEN")


def should_check_for_updates() -> bool:
    """
    Check if 24 hours have passed since last update check.

    Returns:
        True if update check should be performed, False otherwise
    """
    config = load_config()
    last_check = config.get("last_update_check")

    # If never checked, return True
    if last_check is None:
        return True

    # Check if 24 hours (86400 seconds) have passed
    current_time = time.time()
    time_since_last_check = current_time - last_check

    return time_since_last_check >= 86400


def update_last_check_timestamp() -> None:
    """Update the last update check timestamp to current time."""
    config = load_config()
    config["last_update_check"] = time.time()
    save_config(config)


def get_output_dir() -> Path:
    """
    Get the output directory from config or use default.

    Returns:
        Path to the output directory
    """
    try:
        config = load_config()
        output_dir_str = config.get("output_dir")
        if output_dir_str:
            return Path(output_dir_str).expanduser()
    except Exception:
        # If config loading fails, fallback to default
        pass

    return DEFAULT_OUTPUT_DIR
