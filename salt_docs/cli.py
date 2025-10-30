"""
CLI entry point for Salt Docs.
"""

import sys
import argparse
import time

from .config import (
    init_config,
    load_config,
    merge_config_with_args,
    check_config_exists,
    save_config,
    should_check_for_updates,
    update_last_check_timestamp,
)
from .defaults import DEFAULT_INCLUDE_PATTERNS, DEFAULT_EXCLUDE_PATTERNS
from .flows.flow import create_tutorial_flow
from .formatter.output_formatter import (
    print_header,
    print_info,
    print_final_success,
    print_error_missing_api_key,
    print_error_invalid_api_key,
    print_error_rate_limit,
    print_error_network,
    print_error_general,
    print_update_notification,
)
from .metadata.logo import print_logo
from .metadata import DESCRIPTION, CLI_ENTRY_POINT
from .metadata.version import get_version
from .formatter.help_formatter import print_enhanced_help
from .utils.version_check import check_for_update


def main():
    """Main CLI entry point."""
    # Handle 'init' subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_config()
        return

    # Handle 'config' subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "config":
        handle_config_command()
        return
    
    # Handle 'mcp' subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        from .mcp.server import run_mcp_server
        run_mcp_server()
        return

    # Check if config exists, if not, prompt user to run init
    if not check_config_exists():
        print("✘ Salt Docs is not configured yet.")
        print(
            f"Please run '{CLI_ENTRY_POINT} init' to set up your configuration first."
        )
        sys.exit(1)

    # Load saved configuration
    config = load_config()

    # Parse arguments with enhanced help
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use our custom one
    )

    # Add custom help option
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show enhanced help message and exit"
    )

    # Add version option
    parser.add_argument(
        "-v", "--version", action="version", version=f"salt-docs {get_version()}"
    )

    # Create mutually exclusive group for source
    source_group = parser.add_mutually_exclusive_group(required=False)
    source_group.add_argument("--repo", help="URL of the public GitHub repository.")
    source_group.add_argument("--dir", help="Path to local directory.")

    parser.add_argument(
        "-n",
        "--name",
        help="Project name (optional, derived from repo/directory if omitted).",
    )
    parser.add_argument(
        "-t",
        "--token",
        help="GitHub personal access token (optional, reads from GITHUB_TOKEN env var if not provided).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=config.get("output_dir", "output"),
        help="Base directory for output (default: from config).",
    )
    parser.add_argument(
        "-i",
        "--include",
        nargs="+",
        help="Include file patterns (e.g. '*.py' '*.js'). Defaults to common code files if not specified.",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        help="Exclude file patterns (e.g. 'tests/*' 'docs/*'). Defaults to test/build directories if not specified.",
    )
    parser.add_argument(
        "-s",
        "--max-size",
        type=int,
        default=config.get("max_file_size", 100000),
        help="Maximum file size in bytes (default: from config).",
    )
    # Add language parameter for multi-language support
    parser.add_argument(
        "--language",
        default=config.get("language", "english"),
        help="Language for the generated tutorial (default: from config)",
    )
    # Add use_cache parameter to control LLM caching
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable LLM response caching (default: caching enabled)",
    )
    # Add max_abstraction_num parameter to control the number of abstractions
    parser.add_argument(
        "--max-abstractions",
        type=int,
        default=config.get("max_abstractions", 10),
        help="Maximum number of abstractions to identify (default: from config)",
    )

    args = parser.parse_args()

    # Handle help display
    if args.help:
        print_enhanced_help()
        sys.exit(0)

    # Validate that either --repo or --dir is provided
    if not args.repo and not args.dir:
        print("Error: One of --repo or --dir is required.")
        print("Use --help for more information.")
        sys.exit(1)

    # Get GitHub token from argument, config, or environment variable
    github_token = None
    if args.repo:
        github_token = (
            args.token or config.get("github_token") or sys.environ.get("GITHUB_TOKEN")
        )
        if not github_token:
            print(
                "⚠ Warning: No GitHub token provided.\n"
                "  • For public repos: Optional, but you may hit rate limits (60 requests/hour)\n"
                "  • For private repos: Required for access\n"
                f"  • To add a token: Run '{CLI_ENTRY_POINT} config update-github-token'"
            )

    # Merge config with CLI args (CLI takes precedence)
    final_config = merge_config_with_args(config, args)

    # Initialize the shared dictionary with inputs
    shared = {
        "repo_url": args.repo,
        "local_dir": args.dir,
        "project_name": args.name,  # Can be None, FetchRepo will derive it
        "github_token": github_token,
        "output_dir": final_config[
            "output_dir"
        ],  # Base directory for CombineTutorial output
        # Add include/exclude patterns and max file size
        "include_patterns": (
            set(final_config["include_patterns"])
            if final_config.get("include_patterns")
            else DEFAULT_INCLUDE_PATTERNS
        ),
        "exclude_patterns": (
            set(final_config["exclude_patterns"])
            if final_config.get("exclude_patterns")
            else DEFAULT_EXCLUDE_PATTERNS
        ),
        "max_file_size": final_config["max_file_size"],
        # Add language for multi-language support
        "language": final_config["language"],
        # Add use_cache flag (inverse of no-cache flag)
        "use_cache": final_config["use_cache"],
        # Add max_abstraction_num parameter
        "max_abstraction_num": final_config["max_abstractions"],
        # Outputs will be populated by the nodes
        "files": [],
        "abstractions": [],
        "relationships": {},
        "component_order": [],
        "components": [],
        "final_output_dir": None,
    }

    # Display logo and starting message with repository/directory and language
    print_logo()
    print()  # Blank line for spacing
    print_header()  # Version will be read from pyproject.toml
    print_info("Repository", args.repo or args.dir)
    print_info("Language", final_config["language"].capitalize())
    print_info("LLM caching", "Enabled" if final_config["use_cache"] else "Disabled")

    # Create the flow instance
    tutorial_flow = create_tutorial_flow()

    # Run the flow
    start_time = time.time()
    try:
        tutorial_flow.run(shared)
        total_time = time.time() - start_time

        # Print final success message
        print_final_success(
            "Success! Documents generated", total_time, shared["final_output_dir"]
        )

        # Check for updates (non-blocking, only if 24 hours have passed)
        _check_for_updates_quietly()
    except ValueError as e:
        # Handle missing/invalid API key
        if "GEMINI_API_KEY not found" in str(e):
            print_error_missing_api_key()
        else:
            print_error_general(e)
        sys.exit(1)
    except (ValueError, IOError, OSError, ConnectionError, TimeoutError) as e:
        # Check error type and show appropriate message
        error_str = str(e).lower()
        if (
            "401" in error_str
            or "unauthorized" in error_str
            or "invalid api key" in error_str
        ):
            print_error_invalid_api_key()
        elif "rate limit" in error_str or "429" in error_str:
            print_error_rate_limit()
        elif (
            "connection" in error_str
            or "timeout" in error_str
            or "network" in error_str
        ):
            print_error_network()
        else:
            print_error_general(e)
        sys.exit(1)


def _check_for_updates_quietly():
    """
    Check for updates in the background without blocking the CLI.
    Only checks if 24 hours have passed since last check.
    Silently fails on any errors to not interrupt user workflow.
    """
    try:
        # Only check if 24 hours have passed
        if not should_check_for_updates():
            return

        current_version = get_version()
        latest_version = check_for_update(current_version, timeout=5.0)

        # Update timestamp after attempting check (prevents excessive API calls)
        # Even if network fails, we update to avoid retrying immediately
        update_last_check_timestamp()

        # If update is available, show notification
        if latest_version:
            print_update_notification(current_version, latest_version)
    except Exception:
        # Silently fail - don't interrupt user workflow
        # Catch all exceptions to ensure update checks never break the CLI
        pass


def handle_config_command():
    """Handle salt-docs config commands."""
    if len(sys.argv) < 3:
        print("Usage: salt-docs config <command>")
        print("Commands:")
        print("  show                    - Show current configuration")
        print("  set <key> <value>       - Set a configuration value")
        print(
            "  update-gemini-key [key] - Update Gemini API key (interactive if no key provided)"
        )
        print(
            "  update-github-token [token] - Update GitHub token (interactive if no token provided)"
        )
        return

    command = sys.argv[2]

    if command == "show":
        show_config()
    elif command == "set":
        if len(sys.argv) < 5:
            print("Usage: salt-docs config set <key> <value>")
            print("Example: salt-docs config set language spanish")
            return
        key = sys.argv[3]
        value = sys.argv[4]
        set_config_value(key, value)
    elif command == "update-gemini-key":
        if len(sys.argv) > 3:
            # Key provided as argument
            new_key = sys.argv[3]
            update_gemini_key_direct(new_key)
        else:
            # Interactive mode
            update_gemini_key()
    elif command == "update-github-token":
        if len(sys.argv) > 3:
            # Token provided as argument
            new_token = sys.argv[3]
            update_github_token_direct(new_token)
        else:
            # Interactive mode
            update_github_token()
    else:
        print(f"Unknown command: {command}")
        print("Run 'salt-docs config' to see available commands")


def show_config():
    """Show current configuration."""
    if not check_config_exists():
        print(f"✘ No configuration found. Run '{CLI_ENTRY_POINT} init' first.")
        return

    config = load_config()
    print(" Current Salt Docs Configuration:")
    print(f"  Output Directory: {config.get('output_dir', 'Not set')}")
    print(f"  Language: {config.get('language', 'Not set')}")
    print(f"  Max Abstractions: {config.get('max_abstractions', 'Not set')}")
    print(f"  Max File Size: {config.get('max_file_size', 'Not set')}")
    print(f"  Use Cache: {config.get('use_cache', 'Not set')}")

    # Check if API keys are available
    try:
        from .config import get_api_key, get_github_token

        gemini_key = get_api_key()
        github_token = get_github_token()
        print(f"  Gemini API Key: {'✓ Set' if gemini_key else '✘ Not set'}")
        print(f"  GitHub Token: {'✓ Set' if github_token else '✘ Not set'}")
    except (IOError, OSError, ValueError, ImportError) as e:
        print(f"  Gemini API Key:  Unable to check ({e})")
        print(f"  GitHub Token:  Unable to check ({e})")


def set_config_value(key, value):
    """Set a configuration value."""
    if not check_config_exists():
        print(f"✘ No configuration found. Run '{CLI_ENTRY_POINT} init' first.")
        return

    config = load_config()

    # Handle different value types
    if key in ["max_abstractions", "max_file_size"]:
        try:
            value = int(value)
        except ValueError:
            print(f"✘ {key} must be a number")
            return
    elif key == "use_cache":
        value = value.lower() in ["true", "1", "yes", "on"]
    elif key in ["include_patterns", "exclude_patterns"]:
        value = [pattern.strip() for pattern in value.split(",")]

    config[key] = value
    save_config(config)
    print(f"✓ Updated {key} to {value}")


def _update_secret(
    secret_key: str,
    secret_value: str,
    display_name: str,
    allow_empty: bool = False,
) -> None:
    """
    Common function to update a secret in keyring or config file.

    Args:
        secret_key: The keyring service/key name and config key (e.g., "gemini_api_key")
        secret_value: The secret value to store (empty string removes it if allow_empty=True)
        display_name: Human-readable name for messages (e.g., "Gemini API key")
        allow_empty: If True, empty value removes the secret; if False, empty is invalid
    """
    try:
        import keyring

        KEYRING_AVAILABLE = True
    except ImportError:
        KEYRING_AVAILABLE = False

    if KEYRING_AVAILABLE:
        try:
            if secret_value:
                keyring.set_password("salt-docs", secret_key, secret_value)
                print(f"✓ {display_name} updated securely in keyring")
                return
            elif allow_empty:
                keyring.delete_password("salt-docs", secret_key)
                print(f"✓ {display_name} removed from keyring")
                return
            else:
                print(f"✘ {display_name} cannot be empty")
                return
        except (OSError, RuntimeError, AttributeError) as e:
            print(f"✘ Failed to update keyring: {e}")
            # Fall through to config file fallback

    # Fallback to config file if keyring not available or failed
    print("⚠ Keyring not available, updating config file (less secure)")
    config = load_config()
    if secret_value:
        config[secret_key] = secret_value
        save_config(config)
        print(f"✓ {display_name} updated in config file")
    elif allow_empty:
        config.pop(secret_key, None)
        save_config(config)
        print(f"✓ {display_name} removed from config file")
    else:
        print(f"✘ {display_name} cannot be empty")


def update_gemini_key():
    """Update Gemini API key (interactive)."""
    import getpass

    print("+ Update Gemini API Key")
    new_key = getpass.getpass("Enter new Gemini API key: ").strip()

    if not new_key:
        print("✘ API key cannot be empty")
        return

    update_gemini_key_direct(new_key)


def update_gemini_key_direct(new_key: str) -> None:
    """Update Gemini API key directly."""
    if not new_key:
        print("✘ API key cannot be empty")
        return

    _update_secret("gemini_api_key", new_key, "Gemini API key", allow_empty=False)


def update_github_token():
    """Update GitHub token (interactive)."""
    import getpass

    print("+ Update GitHub Token")
    new_token = getpass.getpass(
        "Enter new GitHub token (or press Enter to remove): "
    ).strip()

    update_github_token_direct(new_token)


def update_github_token_direct(new_token: str) -> None:
    """Update GitHub token directly."""
    _update_secret("github_token", new_token, "GitHub token", allow_empty=True)


if __name__ == "__main__":
    main()
