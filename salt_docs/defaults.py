"""
Default configuration values for Salt Docs.
"""

# Default file patterns for inclusion
DEFAULT_INCLUDE_PATTERNS = {
    "*.py",
    "*.js",
    "*.jsx",
    "*.ts",
    "*.tsx",
    "*.go",
    "*.java",
    "*.pyi",
    "*.pyx",
    "*.c",
    "*.cc",
    "*.cpp",
    "*.h",
    "*.md",
    "*.rst",
    "*Dockerfile",
    "*Makefile",
    "*.yaml",
    "*.yml",
}

# Default file patterns for exclusion
DEFAULT_EXCLUDE_PATTERNS = {
    "assets/*",
    "data/*",
    "images/*",
    "public/*",
    "static/*",
    "temp/*",
    "*docs/*",
    "*venv/*",
    "*.venv/*",
    "*test*",
    "*tests/*",
    "*examples/*",
    "v1/*",
    "*dist/*",
    "*build/*",
    "*experimental/*",
    "*deprecated/*",
    "*misc/*",
    "*legacy/*",
    ".git/*",
    ".github/*",
    ".next/*",
    ".vscode/*",
    "*obj/*",
    "*bin/*",
    "*node_modules/*",
    "*.log",
}

# Default configuration values
DEFAULT_CONFIG = {
    "output_dir": "~/Documents/Salt Docs",
    "language": "english",
    "max_abstractions": 10,
    "max_file_size": 100000,
    "use_cache": True,
    "include_patterns": list(DEFAULT_INCLUDE_PATTERNS),
    "exclude_patterns": list(DEFAULT_EXCLUDE_PATTERNS),
    "last_update_check": None,  # Timestamp of last update check (None means never checked)
    "llm_provider": "gemini",
    "llm_model": "gemini-2.5-flash",
    "documentation_mode": "minimal",
}
