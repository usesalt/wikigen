"""
Project metadata for Salt Docs.
Single source of truth for project information.
"""

import datetime

# Project info
PROJECT_NAME = "salt-docs"
AUTHOR_NAME = "Mithun Ramesh"
ORGANIZATION = "USESALT.CO"
DESCRIPTION = "Wiki's for nerds, by nerds"

# Repository info
REPOSITORY_URL = "https://github.com/usesalt/salt-docs"
HOMEPAGE_URL = "https://usesalt.co"
ISSUES_URL = "https://github.com/usesalt/salt-docs/issues"

# Dynamic values
CURRENT_YEAR = datetime.datetime.now().year
COPYRIGHT_TEXT = f"Copyright (c) {CURRENT_YEAR} {AUTHOR_NAME}"

# Python requirements
MIN_PYTHON_VERSION = "3.12"

# Package info
PACKAGE_NAME = "salt-docs"
CLI_ENTRY_POINT = "salt-docs"
