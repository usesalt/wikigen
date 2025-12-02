![Salt Docs](assets/saltdocs.jpg)


## SALT DOCS

[![PyPI](https://img.shields.io/badge/pypi-v0.2.4-blue)](https://pypi.org/project/salt-docs/) [![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/) [![Downloads](https://img.shields.io/badge/downloads-3k+-brightgreen)](https://pypi.org/project/salt-docs/) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE) [![GitHub](https://img.shields.io/badge/github-usesalt%2Fsalt--docs-red)](https://github.com/usesalt/salt-docs)



**Salt Docs** is a compact, human-readable documentation generator for codebases that minimizes tokens and makes structure easy for models to follow.  
It's intended for **LLM input** as a drop-in, lossless representation of your existing codebase.


## Installation

### Option 1: Install from PyPI
```bash
pip install salt-docs
```

### Option 2: Install from source
```bash
git clone https://github.com/usesalt/salt-docs.git
cd salt-docs
pip install -e .
```

## Quick Start

### 1. Initial Setup
Run the setup wizard to configure your API keys and preferences:

```bash
salt-docs init
```

### 2. Generate Documentation

#### Analyze GitHub repository
```bash
salt-docs run https://github.com/username/repo
```

#### Analyze local directory
```bash
salt-docs run /path/to/your/codebase
```

#### With custom options
```bash
salt-docs run https://github.com/username/repo --output /custom/path --language spanish --max-abstractions 10
```

## Configuration

Salt Docs stores configuration in a per-user config file and uses your system's keyring for secure API key storage.

- macOS/Linux: `~/.config/saltdocs/config.json` (or `$XDG_CONFIG_HOME/saltdocs/config.json`)
- Windows: `%APPDATA%\saltdocs\config.json`

### Configuration Options
- `llm_provider`: LLM provider to use (gemini, openai, anthropic, openrouter, ollama) - default: gemini
- `llm_model`: Model name to use (e.g., "gemini-2.5-flash", "gpt-4o-mini", "claude-3-5-sonnet-20241022") - default: gemini-2.5-flash
- `output_dir`: Default output directory
- `language`: Default language for generated docs
- `max_abstractions`: Default number of abstractions to identify
- `max_file_size`: Maximum file size in bytes
- `use_cache`: Enable/disable LLM response caching
- `include_patterns`: Default file patterns to include
- `exclude_patterns`: Default file patterns to exclude
- `ollama_base_url`: Custom Ollama base URL (optional, default: http://localhost:11434)

### Managing Configuration

#### View Current Configuration
```bash
salt-docs config show
```

#### Update API Keys
```bash
# Update API key for any provider (interactive)
salt-docs config update-api-key gemini
salt-docs config update-api-key openai
salt-docs config update-api-key anthropic
salt-docs config update-api-key openrouter

# Legacy command (still works, redirects to update-api-key)
salt-docs config update-gemini-key

# Update GitHub token (interactive)
salt-docs config update-github-token

# Update GitHub token directly
salt-docs config update-github-token "your-token-here"
```

#### Update Other Settings
```bash
# Change LLM provider
salt-docs config set llm-provider openai

# Change LLM model
salt-docs config set llm-model gpt-4o-mini

# Change default language
salt-docs config set language spanish

# Change max abstractions
salt-docs config set max_abstractions 15

# Disable caching
salt-docs config set use_cache false

# Update output directory
salt-docs config set output_dir /custom/path
```

---
## CI/CD Integration

Salt Docs can automatically generate and update documentation in your CI/CD pipeline. Perfect for keeping docs in sync with code changes!

### Quick Setup for GitHub Actions

1. **Add workflow file** to `.github/workflows/salt-docs.yml`:

```yaml
name: Salt Docs

on:
  push:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install salt-docs
      - run: salt-docs run . --ci --output-path docs/
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      - uses: peter-evans/create-pull-request@v6
        with:
          commit-message: 'docs: updated documentation for new changes'
          branch: salt-docs/update-${{ github.run_number }}
          title: 'Update Documentation'
```

2. **Add your LLM API key** to GitHub Secrets:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Add `GEMINI_API_KEY` (or `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)

3. **Push to main** - Documentation will be automatically generated and a PR will be created!

### CI-Specific Flags

- `--ci` - Enable CI mode (non-interactive, better error messages)
- `--output-path <path>` - Custom output directory (e.g., `docs/`, `documentation/`)
- `--update` - Merge with existing docs instead of overwriting
- `--check-changes` - Exit with code 1 if docs changed, 0 if unchanged

### Learn More

See the complete [CI/CD Integration Guide](docs/ci-cd-integration.md) for:
- Advanced configuration options
- Multiple LLM provider setup
- Troubleshooting tips
- Best practices
- Future integrations (Confluence, Notion, etc.)

---
## MCP Server Setup

Salt Docs includes an MCP (Model Context Protocol) server that exposes your generated documentation to AI assistants in IDEs like Cursor, Continue.dev, and Claude Desktop.

### MCP Tools Available

The MCP server provides these tools:
- `list_docs` - List all available documentation files
- `get_docs` - Fetch the full content of a documentation file (by resource name or absolute path)
- `search_docs` - Full-text search across documentation (paths, names, and resource names)
- `index_directories` - Index directories for fast searching

### Setup Instructions

#### Cursor

1. Open or create your MCP configuration file:
   - **macOS/Linux**: `~/.cursor/mcp.json`
   - **Windows**: `%APPDATA%\Cursor\mcp.json`

2. Add the salt-docs server configuration:

```json
{
  "mcpServers": {
    "salt-docs": {
      "command": "salt-docs",
      "args": ["mcp"]
    }
  }
}
```

3. Restart Cursor to load the MCP server.

4. The AI assistant in Cursor can now access your documentation using tools like:
   - "What documentation do we have?"
   - "Get me the documentation for 'SALT project"
   - "Read the README documentation"

#### Claude Desktop

1. Open or create your Claude configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add the salt-docs server configuration:

```json
{
  "mcpServers": {
    "salt-docs": {
      "command": "salt-docs",
      "args": ["mcp"]
    }
  }
}
```

3. Restart Claude Desktop to load the MCP server.

#### Troubleshooting

- **Command not found**: Make sure `salt-docs` is in your PATH. You can verify by running `salt-docs --version` in your terminal.
- **Server not starting**: Ensure you've run `salt-docs init` and have generated at least one documentation project.
- **No docs found**: The MCP server discovers docs from your configured `output_dir`. Run `salt-docs config show` to check your output directory.

### Testing the MCP Server

You can test the MCP server directly:

```bash
salt-docs mcp
```

This will start the server in stdio mode (for MCP clients). To test locally, you can use the test scripts in the `tests/` directory.

## LLM Provider Support

Salt Docs supports multiple LLM providers, allowing you to choose the best option for your needs:

### Supported Providers

1. **Google Gemini** (default)
   - Recommended models: gemini-2.5-pro, gemini-2.5-flash, gemini-1.5-pro, gemini-1.5-flash
   - API key required: Yes (GEMINI_API_KEY)

2. **OpenAI**
   - Recommended models: gpt-4o-mini, gpt-4.1-mini, gpt-5-mini, gpt-5-nano
   - API key required: Yes (OPENAI_API_KEY)
   - Supports o1 models with reasoning capabilities

3. **Anthropic Claude**
   - Recommended models: claude-3-5-sonnet, claude-3-5-haiku, claude-3-7-sonnet (with extended thinking), claude-3-opus
   - API key required: Yes (ANTHROPIC_API_KEY)

4. **OpenRouter**
   - Recommended models: google/gemini-2.5-flash:free, meta-llama/llama-3.1-8b-instruct:free, openai/gpt-4o-mini, anthropic/claude-3.5-sonnet
   - API key required: Yes (OPENROUTER_API_KEY)
   - Access multiple models through a single API

5. **Ollama (Local)**
   - Recommended models: llama3.2, llama3.1, mistral, codellama, phi3
   - API key required: No (runs locally)
   - Default URL: http://localhost:11434
   - Perfect for privacy-sensitive projects or offline usage

### Switching Providers

You can switch between providers at any time:

```bash
# Switch to OpenAI
salt-docs config set llm-provider openai
salt-docs config set llm-model gpt-4o-mini
salt-docs config update-api-key openai

# Switch to Ollama (local)
salt-docs config set llm-provider ollama
salt-docs config set llm-model llama3.2
# No API key needed for Ollama!
```

## CLI Options

### Required
- `run` - GitHub repo URL, current open directory or local directory path
- `--repo` or `--dir` - GitHub repo URL or local directory path (depricated)

### Optional
- `-n, --name` - Project name (derived from repo/directory if omitted)
- `-t, --token` - GitHub personal access token
- `-o, --output` - Output directory (overrides config default)
- `-i, --include` - File patterns to include (e.g., "*.py", "*.js")
- `-e, --exclude` - File patterns to exclude (e.g., "tests/*", "docs/*")
- `-s, --max-size` - Maximum file size in bytes (default: 100KB)
- `--language` - Language for generated docs (default: "english")
- `--no-cache` - Disable LLM response caching
- `--max-abstractions` - Maximum number of abstractions to identify (default: 10)