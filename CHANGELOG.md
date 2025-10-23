# Changelog

All notable changes to this project will be documented in this file.

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
