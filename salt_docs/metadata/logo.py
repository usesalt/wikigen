"""ASCII logo for Salt Docs CLI."""

from .project import ORGANIZATION


def print_logo():
    """Print the Salt Docs ASCII logo with simple gray colors."""
    # Simple colors that work well on both light and dark backgrounds
    LOGO_COLOR = "\033[38;5;240m"  # Medium gray - visible everywhere
    ATTRIB_COLOR = "\033[38;5;245m"  # Light gray
    RESET = "\033[0m"

    logo = f"""{LOGO_COLOR}
██╗   ██╗      ███████╗ ███████╗ ██╗   ████████╗
  ██║   ██║    ██╔════╝ ██╔══██║ ██║   ╚══██╔══╝
    ██║   ██║  ███████╗ ███████║ ██║      ██║
  ██║   ██║    ╚════██║ ██╔══██║ ██║      ██║
██║   ██║      ███████║ ██║  ██║ ███████╗ ██║
╚═╝   ╚═╝      ╚══════╝ ╚═╝  ╚═╝ ╚══════╝ ╚═╝
{RESET}
{ATTRIB_COLOR}COOKED WITH LOT OF ♥ BY MITHUN{RESET}
"""
    print(logo)
