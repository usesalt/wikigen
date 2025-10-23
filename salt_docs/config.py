"""
Configuration management for Salt Docs.
Handles loading, saving, and merging configuration with CLI arguments.
"""

import os
import json
import sys
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
    from .metadata.logo import print_logo

    print_logo()
    print()  # Blank line for spacing

    # Create directories
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Welcome to Salt Docs! Let's set up your configuration")
    print(f"Configuration will be saved to (Default): {CONFIG_FILE}")
    print(f"Default output directory: {DEFAULT_OUTPUT_DIR}\n")

    # Collect API keys
    gemini_key = input("Enter your Gemini API key: ").strip()
    if not gemini_key:
        print("✘ Gemini API key is required!")
        sys.exit(1)

    github_token = input("Enter GitHub token (optional, press Enter to skip): ").strip()

    # Store in keyring if available, otherwise save to config
    keyring_available = KEYRING_AVAILABLE
    if keyring_available:
        try:
            keyring.set_password("salt-docs", "gemini_api_key", gemini_key)
            if github_token:
                keyring.set_password("salt-docs", "github_token", github_token)
            print("✓ API keys saved securely using keyring")
        except Exception as e:
            print(f"⚠ Keyring failed ({e}), saving to config file")
            keyring_available = False

    if not keyring_available:
        print("⚠ Keyring not available, saving to config file (less secure)")

    # Collect other preferences
    output_dir = input(f"Default output directory [{DEFAULT_OUTPUT_DIR}]: ").strip()
    if not output_dir:
        output_dir = str(DEFAULT_OUTPUT_DIR)

    language = input("Default language [english]: ").strip()
    if not language:
        language = "english"

    max_abstractions = input("Default max abstractions [10]: ").strip()
    if not max_abstractions:
        max_abstractions = 10
    else:
        try:
            max_abstractions = int(max_abstractions)
        except ValueError:
            max_abstractions = 10

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

    print(f"\n✓ Configuration saved to {CONFIG_FILE}")
    print(f"✓ Default output location: {output_dir}")
    print("\nYou can now run: salt-docs --repo <url>")


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
        except Exception as e:
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

    # Try config first
    api_key = config.get("gemini_api_key")
    if api_key:
        return api_key

    # Fallback to environment variable
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    return None


def get_github_token() -> Optional[str]:
    """Get GitHub token from config or environment."""
    config = load_config()

    # Try config first
    token = config.get("github_token")
    if token:
        return token

    # Fallback to environment variable
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token

    return None
