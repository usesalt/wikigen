"""
Project metadata for WikiGen.
Single source of truth for project information.
"""

import datetime

# Project info
PROJECT_NAME = "wikigen"
AUTHOR_NAME = "Mithun Ramesh"
ORGANIZATION = "USEWIKIGEN.CO"
DESCRIPTION = "WIKI'S FOR NERDS, BY NERDS"

# Repository info
REPOSITORY_URL = "https://github.com/usesalt/wikigen"
HOMEPAGE_URL = "https://usesalt.co"
ISSUES_URL = "https://github.com/usesalt/wikigen/issues"

# Dynamic values
CURRENT_YEAR = datetime.datetime.now().year
COPYRIGHT_TEXT = f"Copyright (c) {CURRENT_YEAR} {AUTHOR_NAME}"

# Python requirements
MIN_PYTHON_VERSION = "3.12"

# Package info
PACKAGE_NAME = "wikigen"
CLI_ENTRY_POINT = "wikigen"
