"""ASCII logo for Salt Docs CLI."""

from .project import ORGANIZATION


def print_logo():
    """Print the Salt Docs ASCII logo with grayscale colors."""
    # ANSI color codes
    WHITE = "\033[38;5;255m"
    GRAY = "\033[38;5;245m"
    RESET = "\033[0m"

    logo = f"""{WHITE}
██╗   ██╗      ███████╗ ███████╗ ██╗   ████████╗
  ██║   ██║    ██╔════╝ ██╔══██║ ██║   ╚══██╔══╝
    ██║   ██║  ███████╗ ███████║ ██║      ██║
  ██║   ██║    ╚════██║ ██╔══██║ ██║      ██║
██║   ██║      ███████║ ██║  ██║ ███████╗ ██║       
╚═╝   ╚═╝      ╚══════╝ ╚═╝  ╚═╝ ╚══════╝ ╚═╝
{RESET}
{GRAY}BUILT WITH ♥ BY {ORGANIZATION}{RESET}
"""
    print(logo)
