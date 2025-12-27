"""
Init mode formatter for WikiGen CLI.
Provides structured visual output for the configuration setup process.
"""

from .output_formatter import Colors, Icons, Tree
from ..metadata.logo import print_logo


def print_init_header():
    """Print the logo and setup header."""
    print_logo()
    print()  # Blank line for spacing
    print(
        f"{Colors.LIGHT_GRAY}{Tree.START} {Colors.WHITE}{Icons.CONFIG} "
        f"Configuration Setup{Colors.RESET}"
    )


def print_section_start(name, icon):
    """Print the start of a configuration section."""
    print(f"{Colors.LIGHT_GRAY}{Tree.MIDDLE} {Colors.WHITE}{icon} {name}{Colors.RESET}")


def print_input_prompt(label, icon, is_required=True, default_value=None):
    """Print an input prompt with proper tree structure."""
    required_text = " (required)" if is_required else " (optional, press Enter to skip)"
    default_text = f" [{default_value}]" if default_value else ""

    print(
        f"{Colors.LIGHT_GRAY}{Tree.VERTICAL}  {Colors.LIGHT_GRAY}{Tree.MIDDLE} "
        f"{Colors.MEDIUM_GRAY}{icon} {label}{required_text}{default_text}{Colors.RESET}"
    )
    print(
        f"{Colors.LIGHT_GRAY}{Tree.VERTICAL}  {Colors.LIGHT_GRAY}{Tree.VERTICAL}  "
        f"{Colors.MEDIUM_GRAY}→ {Colors.RESET}",
        end="",
    )


def print_init_complete(config_path, output_dir, keyring_available):
    """Print the final completion message."""
    print(
        f"{Colors.LIGHT_GRAY}{Tree.END} {Colors.WHITE}{Icons.SUCCESS} "
        f"Configuration Complete{Colors.RESET}"
    )
    print()
    print(f"{Colors.WHITE}{Icons.SUCCESS} Saved to {config_path}{Colors.RESET}")

    keyring_status = (
        "Enabled (secure storage)"
        if keyring_available
        else "Not available (saved to config file)"
    )
    print(f"{Colors.MEDIUM_GRAY}{Icons.INFO} Keyring: {keyring_status}{Colors.RESET}")
    print(f"{Colors.MEDIUM_GRAY}📂 {Colors.WHITE}{output_dir}{Colors.RESET}")
