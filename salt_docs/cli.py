"""
CLI entry point for Salt Docs.
"""

import sys
import argparse
import time
from pathlib import Path

# Add the parent directory to the path so we can import from the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from .config import (
    init_config,
    load_config,
    merge_config_with_args,
    check_config_exists,
    save_config,
)
from .defaults import DEFAULT_INCLUDE_PATTERNS, DEFAULT_EXCLUDE_PATTERNS
from .flows.flow import create_tutorial_flow
from .formatter.output_formatter import print_header, print_info, print_final_success
from .metadata.logo import print_logo
from .metadata import DESCRIPTION, CLI_ENTRY_POINT
from .formatter.help_formatter import print_enhanced_help


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
                "Warning: No GitHub token provided. You might hit rate limits for public repositories."
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
        "chapter_order": [],
        "chapters": [],
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
    tutorial_flow.run(shared)
    total_time = time.time() - start_time

    # Print final success message
    print_final_success(
        "Success! Documents generated", total_time, shared["final_output_dir"]
    )


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
    except Exception as e:
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


def update_gemini_key():
    """Update Gemini API key (interactive)."""
    import getpass

    try:
        import keyring

        KEYRING_AVAILABLE = True
    except ImportError:
        KEYRING_AVAILABLE = False

    print(" Update Gemini API Key")
    new_key = getpass.getpass("Enter new Gemini API key: ").strip()

    if not new_key:
        print("✘ API key cannot be empty")
        return

    update_gemini_key_direct(new_key)


def update_gemini_key_direct(new_key):
    """Update Gemini API key directly."""
    try:
        import keyring

        KEYRING_AVAILABLE = True
    except ImportError:
        KEYRING_AVAILABLE = False

    if not new_key:
        print("✘ API key cannot be empty")
        return

    if KEYRING_AVAILABLE:
        try:
            keyring.set_password("salt-docs", "gemini_api_key", new_key)
            print("✓ Gemini API key updated securely in keyring")
        except Exception as e:
            print(f"✘ Failed to update keyring: {e}")
    else:
        print("⚠ Keyring not available, updating config file (less secure)")
        config = load_config()
        config["gemini_api_key"] = new_key
        save_config(config)
        print("✓ Gemini API key updated in config file")


def update_github_token():
    """Update GitHub token (interactive)."""
    import getpass

    try:
        import keyring

        KEYRING_AVAILABLE = True
    except ImportError:
        KEYRING_AVAILABLE = False

    print("+ Update GitHub Token")
    new_token = getpass.getpass(
        "Enter new GitHub token (or press Enter to remove): "
    ).strip()

    update_github_token_direct(new_token)


def update_github_token_direct(new_token):
    """Update GitHub token directly."""
    try:
        import keyring

        KEYRING_AVAILABLE = True
    except ImportError:
        KEYRING_AVAILABLE = False

    if KEYRING_AVAILABLE:
        try:
            if new_token:
                keyring.set_password("salt-docs", "github_token", new_token)
                print("✓ GitHub token updated securely in keyring")
            else:
                keyring.delete_password("salt-docs", "github_token")
                print("✓ GitHub token removed from keyring")
        except Exception as e:
            print(f"✘ Failed to update keyring: {e}")
    else:
        print("⚠ Keyring not available, updating config file (less secure)")
        config = load_config()
        if new_token:
            config["github_token"] = new_token
        else:
            config.pop("github_token", None)
        save_config(config)
        print("✓ GitHub token updated in config file")


if __name__ == "__main__":
    main()
