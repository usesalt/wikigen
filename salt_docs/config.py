"""
Configuration management for Salt Docs.
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

# Configuration paths
CONFIG_DIR = Path.home() / "Documents" / "Salt Docs" / ".salt"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "Salt Docs"


def init_config() -> None:
    """Interactive setup wizard for init command."""
    from .formatter.init_formatter import (
        print_init_header,
        print_section_start,
        print_input_prompt,
        print_init_complete,
    )
    from .formatter.output_formatter import Icons

    # Create directories
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print_init_header()

    # API Keys section
    print_section_start("API Keys", Icons.INFO)

    # Gemini API Key
    print_input_prompt("Gemini API Key", Icons.ANALYZING, is_required=True)
    gemini_key = input().strip()
    if not gemini_key:
        print("✘ Gemini API key is required!")
        sys.exit(1)

    # GitHub Token
    print_input_prompt(
        "GitHub Token", Icons.ANALYZING, is_required=False, default_value="skip"
    )
    github_token = input().strip()

    # Store in keyring if available, otherwise save to config
    keyring_available = KEYRING_AVAILABLE
    if keyring_available:
        try:
            keyring.set_password("salt-docs", "gemini_api_key", gemini_key)
            if github_token:
                keyring.set_password("salt-docs", "github_token", github_token)
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

    # Build configuration
    config = {
        "output_dir": output_dir,
        "language": language,
        "max_abstractions": max_abstractions,
        "max_file_size": DEFAULT_CONFIG["max_file_size"],
        "use_cache": DEFAULT_CONFIG["use_cache"],
        "include_patterns": DEFAULT_CONFIG["include_patterns"],
        "exclude_patterns": DEFAULT_CONFIG["exclude_patterns"],
    }

    # Add API keys to config if keyring not available
    if not keyring_available:
        config["gemini_api_key"] = gemini_key
        if github_token:
            config["github_token"] = github_token

    # Save configuration
    save_config(config)

    # Print completion message
    print_init_complete(CONFIG_FILE, output_dir, keyring_available)


def load_config() -> Dict[str, Any]:
    """Load configuration from file and keyring."""
    config = DEFAULT_CONFIG.copy()

    # Load from file if it exists
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                config.update(file_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠ Warning: Could not load config file: {e}")

    # Load API keys from keyring if available
    if KEYRING_AVAILABLE:
        try:
            gemini_key = keyring.get_password("salt-docs", "gemini_api_key")
            if gemini_key:
                config["gemini_api_key"] = gemini_key

            github_token = keyring.get_password("salt-docs", "github_token")
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
        config_to_save.pop("gemini_api_key", None)
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
    }

    for arg_name, config_key in arg_mapping.items():
        if hasattr(args, arg_name):
            value = getattr(args, arg_name)
            if value is not None:
                if arg_name == "no_cache":
                    # Invert the logic: no_cache=True means use_cache=False
                    merged[config_key] = not value
                elif arg_name in ["include", "exclude"]:
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


def get_api_key() -> Optional[str]:
    """Get API key from config or environment."""
    config = load_config()
    return config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")


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
