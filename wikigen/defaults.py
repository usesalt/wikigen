"""
Default configuration values for WikiGen.
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
    "output_dir": "~/Documents/WikiGen",
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
    # Semantic search configuration
    "semantic_search_enabled": True,
    "chunk_size": 1000,  # tokens (increased for better context)
    "chunk_overlap": 200,  # tokens (reduced overlap to avoid tiny fragments)
    "embedding_model": "all-MiniLM-L6-v2",  # lightweight, fast
    "max_chunks_per_file": 5,  # limit chunks returned per file
}
