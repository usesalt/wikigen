# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1] - 2025-11-03

### Added
- **Documentation Mode Selection** - Choose between minimal and comprehensive documentation output
  - **Minimal Mode** - Shorter, more direct documentation focused on key facts and intent
  - **Comprehensive Mode** - Full detailed documentation with extensive explanations and examples
- **New CLI Argument**: `--mode` - Override documentation mode for a single run
  - Options: `minimal` or `comprehensive`
  - Example: `salt-docs --repo <url> --mode comprehensive`
- **Configuration Field**: `documentation_mode` - Set default documentation mode in config
  - Default: `minimal`
  - Can be set via `salt-docs config set documentation-mode <mode>`
  - Interactive selection during `salt-docs init` setup wizard
- **Comprehensive Test Suite** - Full test coverage for documentation mode configuration

### Changed
- Documentation generation now adapts prompts based on selected mode
- Minimal mode uses shorter, more concise prompts to reduce token usage
- Comprehensive mode retains original detailed prompts for thorough documentation
- Code formatting with black for consistency

### Improved
- Better control over documentation verbosity and detail level
- Reduced costs for users who prefer concise documentation (minimal mode)
- More flexible documentation generation to match user needs
- Code quality and formatting consistency

## [0.2.0] - 2025-01-29

### Added
- **Multi-Provider LLM Support** - Support for multiple LLM providers beyond Gemini
  - **OpenAI** - Support for GPT models (gpt-4o-mini, o1-mini, o1-preview, etc.)
  - **Anthropic Claude** - Support for Claude models (claude-3-5-sonnet, claude-3-7-sonnet with extended thinking, etc.)
  - **OpenRouter** - Support for accessing multiple models via OpenRouter API
  - **Ollama (Local)** - Support for running local LLMs via Ollama (no API key required)
- **Enhanced Initialization Flow** - Interactive provider and model selection during setup
  - Numbered provider selection (Gemini, OpenAI, Anthropic, OpenRouter, Ollama)
  - Recommended model suggestions for each provider
  - Custom model name entry option
- **Provider-Specific API Key Management** - Secure storage of API keys per provider in keyring
- **New Configuration Fields**:
  - `llm_provider` - Selected LLM provider (default: gemini)
  - `llm_model` - Selected model name (default: gemini-2.5-flash)
  - `ollama_base_url` - Custom Ollama base URL (optional, default: http://localhost:11434)

### Changed
- Initialization flow now includes provider and model selection before API key setup
- API key storage now uses provider-specific keyring keys (e.g., `gemini_api_key`, `openai_api_key`)
- `get_api_key()` now retrieves API key based on configured provider
- Updated config commands:
  - `config set llm-provider <provider>` - Set LLM provider
  - `config set llm-model <model>` - Set LLM model
  - `config update-api-key <provider>` - Update API key for specific provider (replaces `update-gemini-key`)
- Error messages are now provider-agnostic

### Improved
- Backward compatibility: Existing configs default to Gemini if `llm_provider`/`llm_model` not set
- Environment variable fallback still supported for all providers
- Ollama support for local LLM usage without API keys
- Provider-specific model recommendations for cost-effective options

## [0.1.8] - 2025-01-28

### Changed
- **Cross-platform config directory** - Migrated config file location to OS-appropriate directories
  - macOS/Linux: `~/.config/saltdocs/config.json` (or `$XDG_CONFIG_HOME/saltdocs/config.json`)
  - Windows: `%APPDATA%\saltdocs\config.json`
  - Previous location: `~/Documents/Salt Docs/.salt/config.json` (no longer used)

### Improved
- Automatic migration from legacy config location on first load
- Platform-specific config path resolution for better OS conventions
- Updated documentation to reflect new config locations
- Better Windows support with proper `%APPDATA%` usage
- Code formatting with black

## [0.1.7] - 2025-01-28

### Added
- **MCP (Model Context Protocol) Server** - Full MCP server implementation for AI assistant integration
- **Fast Machine-Wide Search** - SQLite FTS5-powered search across indexed markdown files
- **4 MCP Tools**:
  - `list_docs` - List all documentation files from output directory
  - `search_docs` - Fast full-text search across indexed directories
  - `get_docs` - Fetch documentation by resource name or absolute file path
  - `index_directories` - Manually index directories for search
- **MCP Setup Documentation** - Complete setup instructions for Cursor, Claude Desktop, and Continue.dev
- **Comprehensive Test Suite** - Full test coverage for all MCP tools and search functionality
- **Auto-indexing** - Automatically indexes output directory on first search

### Changed
- Renamed `doc_discovery.py` → `output_resources.py` for clearer purpose
- Renamed `file_indexer.py` → `search_index.py` for better organization
- Moved `get_output_dir()` to `config.py` for better code organization
- Consolidated from 6 MCP tools to 4 tools (merged functionality, removed redundancy)
- Enhanced `get_docs()` to accept both resource names and absolute file paths
- Updated README with MCP setup instructions and improved architecture diagram

### Removed
- Removed redundant `doc_id()` tool (functionality merged into `search_docs`)
- Removed redundant `get_file_content()` tool (merged into `get_docs`)
- Cleaned up unused imports across all MCP and test files

### Improved
- Code organization and naming conventions
- Search performance with SQLite FTS5 indexing
- Test coverage and code quality
- Developer experience with better file organization
- AI assistant integration capabilities

## [0.1.6] - 2025-01-28

### Added
- Automatic update notification system
- Users now get notified when newer versions are available on PyPI
- Update checks occur once per day (24-hour interval)
- Notifications appear at the end of successful CLI runs
- Comprehensive test coverage for version checking functionality

### Changed
- Updated version to 0.1.6

### Improved
- User experience with automated update awareness
- Code quality with additional test suite

## [0.1.5] - 2025-01-28

### Changed
- Updated version to 0.1.5
- Fixed code formatting with black formatter
- Improved code quality and consistency

### Improved
- Code formatting and style consistency
- Project maintainability
- Development workflow

## [0.1.4] - 2025-01-25

### Added
- Fallback formatters for improved error handling and robustness
- Enhanced documentation generation with comprehensive component structure
- Improved CLI error handling with graceful fallback mechanisms

### Changed
- Refactored components to components architecture for better organization
- Enhanced output formatting with more robust error handling
- Improved CLI interface with better fallback support

### Improved
- Code organization and maintainability
- Error handling and user experience
- Documentation structure and clarity

## [0.1.3] - 2025-01-23

### Added
- Enhanced init mode with structured tree-based visual design
- Consistent visual language across all CLI commands
- Input masking for sensitive data (API keys) in init mode
- Improved logo visibility on both light and dark terminal backgrounds

### Changed
- Default max abstractions reduced from 10 to 5 for better performance
- Init mode now uses same visual design as repo mode (tree structure, icons, colors)
- Logo colors optimized for universal visibility across terminal themes
- Streamlined init flow with cleaner input prompts and result display

### Improved
- Visual consistency between init and repo modes
- User experience during initial setup
- Code formatting and linting compliance
- Overall CLI design coherence

## [0.1.2] - 2025-01-23

### Added
- Enhanced CLI with beautiful ASCII logo and branding
- Colorized output with icons and progress indicators
- Improved help system with structured formatting and examples
- Multi-language support for generated documentation
- LLM response caching system for better performance
- Comprehensive configuration management with keyring support
- Interactive setup wizard for first-time users
- Advanced file pattern filtering (include/exclude patterns)
- Batch processing for efficient large codebase analysis
- Detailed progress tracking with timing information

### Changed
- Streamlined project structure by removing unnecessary files
- Enhanced user experience with visual feedback and progress indicators
- Improved error handling and retry mechanisms
- Better code organization and separation of concerns
- Simplified metadata management

### Removed
- Unused `import re` from nodes.py
- Unused `get_config_path()` function from config.py
- Unnecessary generation scripts (`generate_license.py`, `generate_pyproject.py`)
- Redundant `scripts/` directory and release script
- Unused metadata README.md

### Improved
- Code quality and maintainability
- Project structure simplicity
- User interface and experience
- Performance with caching and batch processing
- Documentation and help system
- Error handling and robustness

## [0.1.0] - 2025-01-23

### Added
- Initial release of Salt Docs CLI
- AI-powered codebase analysis and documentation generation
- Support for GitHub repositories and local directories
- Configurable API key management with secure keyring storage
- Multiple output formats and language support
- CLI commands for configuration management
- Support for file pattern inclusion/exclusion
- LLM response caching for improved performance

### Features
- `salt-docs init` - Initial setup wizard
- `salt-docs config` - Configuration management
- `salt-docs --repo <url>` - Analyze GitHub repository
- `salt-docs --dir <path>` - Analyze local directory
- Support for Python 3.10+ environments
- Integration with Google Gemini AI
