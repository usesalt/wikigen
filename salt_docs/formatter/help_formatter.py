"""
Enhanced help formatting for Salt Docs CLI.
Provides colored, structured help output with icons and tree structure.
"""

from ..metadata.project import PROJECT_NAME, DESCRIPTION, HOMEPAGE_URL, CLI_ENTRY_POINT
from ..metadata.version import __version__
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

    LOGO = "🧂"
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
    print()

    # Print header
    print(f"{HelpColors.WHITE}{PROJECT_NAME.upper()} v{__version__}{HelpColors.RESET}")
    print(f"{HelpColors.MEDIUM_GRAY}{HelpIcons.INFO} {DESCRIPTION}{HelpColors.RESET}")
    print()

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
        f"{HelpColors.LIGHT_GRAY}├─ {HelpColors.MEDIUM_GRAY}{CLI_ENTRY_POINT} [-h] (--repo REPO | --dir DIR) [OPTIONS...]{HelpColors.RESET}"
    )
    print()


def _print_source_section():
    """Print source options section."""
    print(
        f"{HelpColors.LIGHT_GRAY}┌─ {HelpColors.WHITE}{HelpIcons.SOURCE} SOURCE (Choose One){HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}├─ {HelpColors.MEDIUM_GRAY}--repo REPO{HelpColors.DARK_GRAY}           {HelpIcons.INFO} URL of the public GitHub repository{HelpColors.RESET}"
    )
    print(
        f"{HelpColors.LIGHT_GRAY}└─ {HelpColors.MEDIUM_GRAY}--dir DIR{HelpColors.DARK_GRAY}             {HelpIcons.INFO} Path to local directory{HelpColors.RESET}"
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
            "Language for the generated tutorial (default: from config)",
        ),
        ("--no-cache", "Disable LLM response caching (default: caching enabled)"),
        (
            "--max-abstractions N",
            "Maximum number of abstractions to identify (default: from config)",
        ),
    ]

    for i, (option, description) in enumerate(options):
        is_last = i == len(options) - 1
        prefix = f"{HelpColors.LIGHT_GRAY}{'└─' if is_last else '├─'}{HelpColors.RESET}"
        print(
            f"{prefix} {HelpColors.MEDIUM_GRAY}{option:<20}{HelpColors.DARK_GRAY} {HelpIcons.INFO} {description}{HelpColors.RESET}"
        )

    print()


def _print_subcommands_section():
    """Print subcommands section."""
    print(
        f"{HelpColors.LIGHT_GRAY}┌─ {HelpColors.WHITE}{HelpIcons.SUBCOMMANDS} SUBCOMMANDS{HelpColors.RESET}"
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
        f"{CLI_ENTRY_POINT} init",
        f"{CLI_ENTRY_POINT} config show",
        f'{CLI_ENTRY_POINT} config update-gemini-key "your-key"',
        f"{CLI_ENTRY_POINT} --repo https://github.com/user/repo",
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
