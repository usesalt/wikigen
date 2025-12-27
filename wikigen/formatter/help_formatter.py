"""
Enhanced help formatting for WikiGen CLI.
Provides colored, structured help output with icons and tree structure.
"""

from ..metadata.project import HOMEPAGE_URL, CLI_ENTRY_POINT
from ..metadata.logo import print_logo


class HelpColors:
    """ANSI 256-color codes for help formatting."""

    WHITE = "\033[38;5;255m"  # Headers, important text
    LIGHT_GRAY = "\033[38;5;250m"  # Tree structure lines
    MEDIUM_GRAY = "\033[38;5;245m"  # Descriptions, labels
    DARK_GRAY = "\033[38;5;240m"  # Subtle details
    RESET = "\033[0m"


class HelpIcons:
    """Unicode icons for help sections."""

    INFO = "◆"
    USAGE = "◎"
    SOURCE = "◎"
    OPTIONS = "⚙"
    SUBCOMMANDS = "⚙"
    EXAMPLES = "◆"
    MORE_INFO = "◆"
    ARROW = "→"
    CHECK = "✓"


class HelpTree:
    """Tree structure characters for help formatting."""

    START = "┌─"  # Start of section
    MIDDLE = "├─"  # Middle items
    END = "└─"  # Last item
    VERTICAL = "│"  # Vertical line
    SPACE = "   "  # Space for indentation


def print_enhanced_help():
    """Print enhanced help with logo, colors, and structure."""
    # Print logo
    print_logo()

    # Print structured help sections
    _print_usage_section()
    _print_source_section()
    _print_options_section()
    _print_subcommands_section()
    _print_examples_section()
    _print_more_info_section()


def _print_usage_section():
    """Print usage section."""
    print(
        f"{HelpColors.LIGHT_GRAY}┌─ {HelpColors.WHITE}{HelpIcons.USAGE} USAGE{HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}└─ {HelpColors.MEDIUM_GRAY}{CLI_ENTRY_POINT} [-h] run [url|path] [OPTIONS...]{HelpColors.RESET}"
    )
    print()


def _print_source_section():
    """Print source options section."""
    print(
        f"{HelpColors.LIGHT_GRAY}┌─ {HelpColors.WHITE}{HelpIcons.SOURCE} SOURCE{HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}├─ {HelpColors.MEDIUM_GRAY}{CLI_ENTRY_POINT} run [url|path]{HelpColors.DARK_GRAY}    {HelpIcons.INFO} Generate documentation (auto-detects URL or path){HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}│  {HelpColors.DARK_GRAY}                            {HelpIcons.INFO} url: GitHub repository URL (e.g., https://github.com/user/repo){HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}│  {HelpColors.DARK_GRAY}                            {HelpIcons.INFO} path: Local directory path (e.g., /path/to/project){HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}└─ {HelpColors.DARK_GRAY}                            {HelpIcons.INFO} (no argument): Current directory{HelpColors.RESET}"
    )
    print()


def _print_options_section():
    """Print options section."""
    print(
        f"{HelpColors.LIGHT_GRAY}┌─ {HelpColors.WHITE}{HelpIcons.OPTIONS} OPTIONS{HelpColors.RESET}"
    )

    options = [
        ("-h, --help", "Show this help message and exit"),
        (
            "-n, --name NAME",
            "Project name (optional, derived from repo/directory if omitted)",
        ),
        (
            "-t, --token TOKEN",
            "GitHub personal access token (optional, reads from GITHUB_TOKEN env var)",
        ),
        ("-o, --output OUTPUT", "Base directory for output (default: from config)"),
        ("-i, --include PATTERN", "Include file patterns (e.g. '*.py' '*.js')"),
        ("-e, --exclude PATTERN", "Exclude file patterns (e.g. 'tests/*' 'docs/*')"),
        ("-s, --max-size SIZE", "Maximum file size in bytes (default: from config)"),
        (
            "--language LANG",
            "Language for the generated wiki (default: from config)",
        ),
        ("--no-cache", "Disable LLM response caching (default: caching enabled)"),
        (
            "--max-abstractions N",
            "Maximum number of abstractions to identify (default: from config)",
        ),
        (
            "--mode MODE",
            "Documentation mode: minimal or comprehensive (default: from config)",
        ),
        ("--ci", "Enable CI mode (non-interactive, uses defaults)"),
        (
            "--update",
            "Update existing documentation instead of overwriting",
        ),
        (
            "--output-path PATH",
            "Custom output path for documentation",
        ),
        (
            "--check-changes",
            "Exit with code 1 if docs changed (for CI checks)",
        ),
    ]

    for i, (option, description) in enumerate(options):
        is_last = i == len(options) - 1
        prefix = f"{HelpColors.LIGHT_GRAY}{'└─' if is_last else '├─'}{HelpColors.RESET}"
        print(
            f"{prefix} {HelpColors.MEDIUM_GRAY}{option:<25}{HelpColors.DARK_GRAY} {HelpIcons.INFO} {description}{HelpColors.RESET}"
        )

    print()


def _print_subcommands_section():
    """Print subcommands section."""
    print(
        f"{HelpColors.LIGHT_GRAY}┌─ {HelpColors.WHITE}{HelpIcons.SUBCOMMANDS} SUBCOMMANDS{HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}├─ {HelpColors.MEDIUM_GRAY}run [url|path]{HelpColors.DARK_GRAY}        {HelpIcons.INFO} Generate documentation (auto-detects URL or path){HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}├─ {HelpColors.MEDIUM_GRAY}init{HelpColors.DARK_GRAY}                  {HelpIcons.INFO} Set up configuration{HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}└─ {HelpColors.MEDIUM_GRAY}config <command>{HelpColors.DARK_GRAY}      {HelpIcons.INFO} Manage configuration{HelpColors.RESET}"
    )
    print()


def _print_examples_section():
    """Print examples section."""
    print(
        f"{HelpColors.LIGHT_GRAY}┌─ {HelpColors.WHITE}{HelpIcons.EXAMPLES} EXAMPLES{HelpColors.RESET}"
    )

    examples = [
        f"{CLI_ENTRY_POINT} run                                    {HelpIcons.INFO}  Current directory",
        f"{CLI_ENTRY_POINT} run https://github.com/user/repo       {HelpIcons.INFO}  GitHub repo",
        f"{CLI_ENTRY_POINT} run /path/to/project                   {HelpIcons.INFO}  Local directory",
        f"{CLI_ENTRY_POINT} init",
        f"{CLI_ENTRY_POINT} config show",
        f'{CLI_ENTRY_POINT} config update-gemini-key "your-key"',
    ]

    for i, example in enumerate(examples):
        is_last = i == len(examples) - 1
        prefix = f"{HelpColors.LIGHT_GRAY}{'└─' if is_last else '├─'}{HelpColors.RESET}"
        print(f"{prefix} {HelpColors.MEDIUM_GRAY}{example}{HelpColors.RESET}")

    print()


def _print_more_info_section():
    """Print more info section."""
    print(
        f"{HelpColors.LIGHT_GRAY}┌─ {HelpColors.WHITE}{HelpIcons.MORE_INFO} MORE INFO{HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}└─ {HelpColors.MEDIUM_GRAY}Visit: {HelpColors.WHITE}{HOMEPAGE_URL}{HelpColors.RESET}"
    )
