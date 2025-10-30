# Salt Docs CLI

Wiki's for nerds, by nerds

## How it works

```mermaid
flowchart TD
    subgraph Sources["Input Sources"]
        GH[GitHub Repository]
        Local[Local Directory]
    end
    
    subgraph Pipeline["Processing Pipeline"]
        Crawl[Crawl Files<br/>Extract code structure]
        Analyze[Analyze Structure<br/>Parse modules & classes]
        Identify[Identify Abstractions<br/>LLM-powered analysis]
        Generate[Generate Documentation<br/>Create markdown content]
    end
    
    subgraph Output["Documentation"]
        Docs[Markdown Files<br/>Organized wiki structure]
    end
    
    subgraph MCP["MCP Server"]
        Server[MCP Server<br/>Exposes docs as tools]
        Tools["Tools:<br/>• list_docs<br/>• doc_id<br/>• get_docs"]
    end
    
    subgraph Consumers["AI Assistants"]
        Cursor[Cursor]
        Claude[Claude Desktop]
        Continue[Continue.dev]
    end
    
    Sources --> Crawl
    Crawl --> Analyze
    Analyze --> Identify
    Identify --> Generate
    Generate --> Docs
    Docs --> Server
    Server --> Tools
    Tools --> Cursor
    Tools --> Claude
    Tools --> Continue
    
    style Sources fill:#e1f5ff
    style Pipeline fill:#fff4e1
    style Output fill:#e8f5e9
    style MCP fill:#f3e5f5
    style Consumers fill:#fce4ec
```

## Installation

### Option 1: Install from PyPI
```bash
pip install salt-docs
```

### Option 2: Install from source
```bash
git clone https://github.com/itsjustmithun/salt-docs-cli.git
cd salt-docs-cli
pip install -e .
```

## Quick Start

### 1. Initial Setup
Run the setup wizard to configure your API keys and preferences:

```bash
salt-docs init
```

This will:
- Prompt for your Gemini API key
- Optionally ask for GitHub token (for private repos)
- Set default output location (`~/Documents/Salt Docs`)
- Configure other preferences

### 2. Generate Documentation

#### Analyze GitHub repository
```bash
salt-docs --repo https://github.com/username/repo
```

#### Analyze local directory
```bash
salt-docs --dir /path/to/your/codebase
```

#### With custom options
```bash
salt-docs --repo https://github.com/username/repo --output /custom/path --language spanish --max-abstractions 15
```

## Configuration

Salt Docs stores configuration in `~/Documents/Salt Docs/.salt/config.json` and uses your system's keyring for secure API key storage.

### Configuration Options
- `output_dir`: Default output directory
- `language`: Default language for generated docs
- `max_abstractions`: Default number of abstractions to identify
- `max_file_size`: Maximum file size in bytes
- `use_cache`: Enable/disable LLM response caching
- `include_patterns`: Default file patterns to include
- `exclude_patterns`: Default file patterns to exclude

### Managing Configuration

#### View Current Configuration
```bash
salt-docs config show
```

#### Update API Keys
```bash
# Update Gemini API key (interactive)
salt-docs config update-gemini-key

# Update Gemini API key directly
salt-docs config update-gemini-key "your-api-key-here"

# Update GitHub token (interactive)
salt-docs config update-github-token

# Update GitHub token directly
salt-docs config update-github-token "your-token-here"
```

#### Update Other Settings
```bash
# Change default language
salt-docs config set language spanish

# Change max abstractions
salt-docs config set max_abstractions 15

# Disable caching
salt-docs config set use_cache false

# Update output directory
salt-docs config set output_dir /custom/path
```

## MCP Server Setup

Salt Docs includes an MCP (Model Context Protocol) server that exposes your generated documentation to AI assistants in IDEs like Cursor, Continue.dev, and Claude Desktop.

### MCP Tools Available

The MCP server provides three tools:
- `list_docs` - List all available documentation files
- `doc_id` - Get the ID/path for a specific documentation resource
- `get_docs` - Fetch the full content of a documentation file

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

## CLI Options

### Required
- `--repo` or `--dir` - GitHub repo URL or local directory path

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