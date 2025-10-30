# Changelog

All notable changes to this project will be documented in this file.

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
