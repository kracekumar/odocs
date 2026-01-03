# CLAUDE.md

## Project Overview

odocs is a CLI tool that generates markdown documentation from command `--help` output. It recursively discovers subcommands and creates a single comprehensive markdown file with a table of contents.

## Tech Stack

- Python 3.14+
- Typer for CLI framework
- uv for package management

## Common Commands

```bash
# Install dependencies
uv sync

# Run the CLI
uv run odocs <command> [options]

# Run tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .
```

## Code Style

- All functions must have type annotations
- All public functions must have docstrings
- Follow PEP 8 conventions
- Use `pathlib.Path` for file paths

## Development Guidelines

- **Always run tests before completing any task**: `uv run pytest`
- All new features must include tests
- Tests go in the `tests/` directory, matching the source module structure
- Use pytest fixtures and parametrize for test organization
- Mock external commands in tests using `unittest.mock.patch`

## Project Structure

```
odocs/
├── src/odocs/           # Main package
│   ├── __init__.py
│   ├── cli.py           # CLI entry point
│   ├── models.py        # CommandHelp dataclass
│   ├── runner.py        # Command execution
│   ├── parser.py        # Help output parsing
│   ├── discovery.py     # Recursive command discovery
│   └── markdown.py      # Markdown generation
├── tests/               # Test suite
│   ├── conftest.py      # Shared fixtures
│   ├── test_cli.py
│   ├── test_models.py
│   ├── test_runner.py
│   ├── test_parser.py
│   ├── test_discovery.py
│   └── test_markdown.py
├── pyproject.toml       # Project configuration
└── CLAUDE.md            # This file
```

## Key Classes

- `CommandHelp` - Data model for command help information
- `CommandRunner` - Executes commands and captures output
- `HelpParser` - Parses help output to extract subcommands
- `CommandDiscovery` - Recursively discovers commands and subcommands
- `MarkdownGenerator` - Generates markdown documentation
