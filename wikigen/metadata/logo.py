"""ASCII logo for WikiGen CLI."""

from .project import DESCRIPTION
from .version import get_version


def print_logo():
    """Print the WikiGen ASCII logo with simple gray colors."""
    # Simple colors that work well on both light and dark backgrounds
    LOGO_COLOR = "\033[38;5;240m"  # Medium gray - visible everywhere
    ATTRIB_COLOR = "\033[38;5;245m"  # Light gray
    RESET = "\033[0m"

    version = get_version()
    logo = f"""
{ATTRIB_COLOR}INTRODUCING
{RESET}{LOGO_COLOR}
██╗   ██╗      ██╗    ██╗ ██╗ ██╗  ██╗ ██╗  ██████╗  ███████╗ ███╗   ██╗
  ██║   ██║    ██║    ██║ ██║ ██║ ██╔╝ ██║ ██╔════╝  ██╔════╝ ████╗  ██║
    ██║   ██║  ██║ █╗ ██║ ██║ █████╔╝  ██║ ██║  ███╗ ██████╗  ██╔██╗ ██║
  ██║   ██║    ██║███╗██║ ██║ ██╔═██╗  ██║ ██║   ██║ ██╔══╝   ██║╚██╗██║
██║   ██║      ╚███╔███╔╝ ██║ ██║  ██╗ ██║ ╚██████╔╝ ███████╗ ██║ ╚████║
╚═╝   ╚═╝       ╚══╝╚══╝  ╚═╝ ╚═╝  ╚═╝ ╚═╝  ╚═════╝  ╚══════╝ ╚═╝  ╚═══╝
{RESET}
{ATTRIB_COLOR}{DESCRIPTION} ♥ {RESET}
{ATTRIB_COLOR}v{version}{RESET}
"""
    print(logo)
