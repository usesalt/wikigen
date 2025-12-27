"""
Output formatting utilities for WikiGen CLI.
Provides tree-structured output with icons, colors, and timing.
"""


# ANSI 256-color codes (work on both light and dark backgrounds)
class Colors:
    WHITE = "\033[38;5;255m"  # Phase headers, success
    LIGHT_GRAY = "\033[38;5;250m"  # Tree structure
    MEDIUM_GRAY = "\033[38;5;245m"  # Operation text
    DARK_GRAY = "\033[38;5;240m"  # Timing, file sizes
    RESET = "\033[0m"


# Unicode icons for different operations
class Icons:
    # Configuration
    CONFIG = "⚙"
    INFO = "◆"

    # Repository operations
    CRAWLING = "◎"
    DOWNLOAD = "↓"
    SKIP = "○"

    # LLM operations
    PROCESSING = "⟳"
    ANALYZING = "◉"
    ORDERING = "◈"

    # Content generation
    WRITING = "✎"
    GENERATING = "◊"

    # File operations
    CREATING = "▸"

    # Status
    SUCCESS = "✓"
    ERROR = "✗"
    WARNING = "⚠"


# Tree structure characters
class Tree:
    START = "┌─"  # Start of section
    MIDDLE = "├─"  # Middle items
    END = "└─"  # Last item
    VERTICAL = "│"  # Vertical line
    SPACE = "   "  # Space for indentation


class PhaseTracker:
    """Track current phase state for proper tree structure."""

    def __init__(self):
        self.depth = 0
        self.in_phase = False
        self.phase_items = 0

    def start_phase(self):
        """Start a new phase."""
        self.in_phase = True
        self.phase_items = 0
        self.depth = 0

    def end_phase(self):
        """End current phase."""
        self.in_phase = False
        self.depth = 0

    def add_item(self):
        """Add an item to current phase."""
        self.phase_items += 1


# Global tracker instance
_tracker = PhaseTracker()


def format_time(seconds):
    """Format elapsed time as [X.Xs]."""
    return f"[{seconds:.1f}s]"


def format_size(bytes_size):
    """Format file size in human-readable format."""
    if bytes_size < 1024:
        return f"{bytes_size} bytes"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.1f} MB"


def print_header(version=None):
    """Print the CLI header with version and configuration info."""
    if version is None:
        from ..metadata import __version__

        version = __version__

    print(f"{Colors.WHITE}WikiGen {Colors.LIGHT_GRAY}v{version}{Colors.RESET}")


def print_info(label, value):
    """Print configuration information line."""
    print(
        f"{Colors.MEDIUM_GRAY}{Icons.INFO} {label}: {Colors.WHITE}{value}{Colors.RESET}"
    )


def print_phase_start(name, icon):
    """
    Print the start of a new phase (top-level section).
    Example: "┌─ ◎ Repository Crawling"
    """
    _tracker.start_phase()
    print()  # Blank line before phase
    print(f"{Colors.LIGHT_GRAY}{Tree.START} {Colors.WHITE}{icon} {name}{Colors.RESET}")


def print_operation(text, icon=None, indent=1, is_last=False, elapsed_time=None):
    """
    Print an operation within a phase with proper tree structure.

    Args:
        text: Operation description
        icon: Icon to display (optional)
        indent: Indentation level (1 for direct child, 2 for nested)
        is_last: Whether this is the last item at this level
        elapsed_time: Optional elapsed time to display inline
    """
    _tracker.add_item()

    # Build indentation
    prefix_parts = []
    for i in range(indent):
        if i < indent - 1:
            prefix_parts.append(Colors.LIGHT_GRAY + Tree.VERTICAL + "  ")
        else:
            if is_last:
                prefix_parts.append(Colors.LIGHT_GRAY + Tree.END + " ")
            else:
                prefix_parts.append(Colors.LIGHT_GRAY + Tree.MIDDLE + " ")

    prefix = "".join(prefix_parts)

    # Format icon and text
    if icon:
        formatted_text = f"{Colors.MEDIUM_GRAY}{icon} {text}{Colors.RESET}"
    else:
        formatted_text = f"{Colors.MEDIUM_GRAY}{text}{Colors.RESET}"

    # Add timing if provided
    if elapsed_time is not None:
        time_suffix = f" {Colors.DARK_GRAY}[{format_time(elapsed_time)}]{Colors.RESET}"
        formatted_text += time_suffix

    print(f"{prefix}{formatted_text}")


def print_success(text, elapsed_time=None, indent=1):
    """
    Print a success message with optional timing.
    Example: "└─ ✓ Complete (43 files, 85.2 KB) [2.3s]"
    """
    # Build timing suffix
    time_suffix = ""
    if elapsed_time is not None:
        time_suffix = f" {Colors.DARK_GRAY}{format_time(elapsed_time)}{Colors.RESET}"

    # Build prefix
    prefix_parts = []
    for i in range(indent):
        if i < indent - 1:
            prefix_parts.append(Colors.LIGHT_GRAY + Tree.VERTICAL + "  ")
        else:
            prefix_parts.append(Colors.LIGHT_GRAY + Tree.END + " ")

    prefix = "".join(prefix_parts)

    print(f"{prefix}{Colors.WHITE}{Icons.SUCCESS} {text}{time_suffix}{Colors.RESET}")


def print_phase_end():
    """End the current phase (adds vertical connector if needed)."""
    print(f"{Colors.LIGHT_GRAY}{Tree.VERTICAL}{Colors.RESET}")
    _tracker.end_phase()


def print_final_success(message, total_time, output_path):
    """
    Print final success message with total time and output location.
    Example:
    ✓ Success! Documents generated [66.2s total]
    📂 /Users/.../output/
    """
    print()  # Blank line before final message
    print(
        f"{Colors.WHITE}{Icons.SUCCESS} {message} {Colors.DARK_GRAY}{format_time(total_time)} total{Colors.RESET}"
    )
    print(f"{Colors.MEDIUM_GRAY}📂 {Colors.WHITE}{output_path}{Colors.RESET}")


def print_error_missing_api_key(provider_display: str = "API"):
    """Print error message for missing API key."""
    from ..metadata import CLI_ENTRY_POINT

    print()
    print(
        f"{Colors.WHITE}{Icons.ERROR} Error: {provider_display} API key not found{Colors.RESET}"
    )
    print(f"{Colors.MEDIUM_GRAY}  To configure your API key, run:{Colors.RESET}")
    print(
        f"{Colors.WHITE}    {CLI_ENTRY_POINT} config update-api-key <provider>{Colors.RESET}"
    )
    print(
        f"{Colors.MEDIUM_GRAY}  Or set the appropriate API key environment variable{Colors.RESET}"
    )


def print_error_invalid_api_key():
    """Print error message for invalid API key."""
    from ..metadata import CLI_ENTRY_POINT

    print()
    print(
        f"{Colors.WHITE}{Icons.ERROR} Error: Invalid or unauthorized API key{Colors.RESET}"
    )
    print(
        f"{Colors.MEDIUM_GRAY}  Your API key may be invalid or expired.{Colors.RESET}"
    )
    print(f"{Colors.MEDIUM_GRAY}  To update your API key, run:{Colors.RESET}")
    print(
        f"{Colors.WHITE}    {CLI_ENTRY_POINT} config update-api-key <provider>{Colors.RESET}"
    )


def print_error_rate_limit():
    """Print error message for rate limit errors."""
    print()
    print(f"{Colors.WHITE}{Icons.ERROR} Error: Rate limit exceeded{Colors.RESET}")
    print(
        f"{Colors.MEDIUM_GRAY}  You've hit the API rate limit. Please wait and try again.{Colors.RESET}"
    )
    print(
        f"{Colors.MEDIUM_GRAY}  Consider using --no-cache flag to reduce API calls.{Colors.RESET}"
    )


def print_error_network():
    """Print error message for network errors."""
    print()
    print(f"{Colors.WHITE}{Icons.ERROR} Error: Network connection issue{Colors.RESET}")
    print(
        f"{Colors.MEDIUM_GRAY}  Unable to connect to the API. Please check your internet connection.{Colors.RESET}"
    )


def print_error_general(error):
    """Print error message for general/unexpected errors."""
    print()
    print(
        f"{Colors.WHITE}{Icons.ERROR} Error: An unexpected error occurred{Colors.RESET}"
    )
    print(f"{Colors.MEDIUM_GRAY}  {str(error)}{Colors.RESET}")
    print(
        f"{Colors.MEDIUM_GRAY}  Please check your configuration and try again.{Colors.RESET}"
    )


def print_update_notification(current_version: str, latest_version: str):
    """
    Print update notification message at the end of successful execution.

    Args:
        current_version: Currently installed version
        latest_version: Latest available version from PyPI
    """
    print()
    print(
        f"{Colors.WHITE}{Icons.INFO} Update available: "
        f"{Colors.MEDIUM_GRAY}v{current_version}"
        f"{Colors.WHITE} → {Colors.WHITE}v{latest_version}{Colors.RESET}"
    )
    print(
        f"{Colors.MEDIUM_GRAY}  To upgrade, run: {Colors.WHITE}pip install --upgrade wikigen{Colors.RESET}"
    )
