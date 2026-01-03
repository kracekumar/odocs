"""Shared fixtures for odocs tests."""

import pytest
from typer.testing import CliRunner

from odocs.models import CommandHelp


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a CLI test runner."""
    return CliRunner()


@pytest.fixture
def simple_command() -> CommandHelp:
    """Create a simple command with no subcommands."""
    return CommandHelp(
        name="app",
        full_command=["app"],
        help_output="Simple app help",
    )


@pytest.fixture
def nested_command() -> CommandHelp:
    """Create a command with nested subcommands."""
    leaf1 = CommandHelp(
        name="leaf1",
        full_command=["app", "sub", "leaf1"],
        help_output="Leaf 1 help",
    )
    leaf2 = CommandHelp(
        name="leaf2",
        full_command=["app", "sub", "leaf2"],
        help_output="Leaf 2 help",
    )
    sub = CommandHelp(
        name="sub",
        full_command=["app", "sub"],
        help_output="Sub command help",
        subcommands=[leaf1, leaf2],
    )
    return CommandHelp(
        name="app",
        full_command=["app"],
        help_output="App root help",
        subcommands=[sub],
    )


@pytest.fixture
def deeply_nested_command() -> CommandHelp:
    """Create a command with 5 levels of nesting."""
    level5 = CommandHelp(
        name="level5",
        full_command=["app", "l1", "l2", "l3", "l4", "level5"],
        help_output="Level 5 help",
    )
    level4 = CommandHelp(
        name="l4",
        full_command=["app", "l1", "l2", "l3", "l4"],
        help_output="Level 4 help",
        subcommands=[level5],
    )
    level3 = CommandHelp(
        name="l3",
        full_command=["app", "l1", "l2", "l3"],
        help_output="Level 3 help",
        subcommands=[level4],
    )
    level2 = CommandHelp(
        name="l2",
        full_command=["app", "l1", "l2"],
        help_output="Level 2 help",
        subcommands=[level3],
    )
    level1 = CommandHelp(
        name="l1",
        full_command=["app", "l1"],
        help_output="Level 1 help",
        subcommands=[level2],
    )
    return CommandHelp(
        name="app",
        full_command=["app"],
        help_output="Root help",
        subcommands=[level1],
    )


@pytest.fixture
def standard_help_output() -> str:
    """Standard CLI help output format."""
    return """
Usage: tool [OPTIONS] COMMAND

A sample tool for testing.

Commands:
  init     Initialize something
  build    Build the project
  test     Run tests

Options:
  --help   Show help
  --version  Show version
"""


@pytest.fixture
def uv_style_help_output() -> str:
    """UV-style help output format."""
    return """
An extremely fast Python package manager.

Usage: uv [OPTIONS] <COMMAND>

Commands:
  run      Run a command or script
  init     Create a new project
  add      Add dependencies to the project
  remove   Remove dependencies from the project
  sync     Update the project's environment
  lock     Update the project's lockfile
  export   Export the project's lockfile to an alternate format
  tree     Display the project's dependency tree
  tool     Run and install commands provided by Python packages
  python   Manage Python versions and installations
  pip      Manage Python packages with a pip-compatible interface
  venv     Create a virtual environment
  build    Build Python packages into source distributions and wheels
  publish  Upload distributions to an index
  cache    Manage uv's cache
  self     Manage the uv executable
  version  Display uv's version
  help     Display documentation for a command

Cache options:
  -n, --no-cache  Avoid reading from or writing to the cache

Global options:
  -q, --quiet    Do not print any output
  -v, --verbose  Use verbose output
"""


@pytest.fixture
def git_style_help_output() -> str:
    """Git-style help output format."""
    return """
usage: git [-v | --version] [-h | --help] [-C <path>] [-c <name>=<value>]

These are common Git commands used in various situations:

start a working area (see also: git help tutorial)
   clone     Clone a repository into a new directory
   init      Create an empty Git repository or reinitialize an existing one

work on the current change (see also: git help everyday)
   add       Add file contents to the index
   mv        Move or rename a file, a directory, or a symlink
   restore   Restore working tree files
   rm        Remove files from the working tree and from the index

examine the history and state (see also: git help revisions)
   bisect    Use binary search to find the commit that introduced a bug
   diff      Show changes between commits
   grep      Print lines matching a pattern
   log       Show commit logs
   show      Show various types of objects
   status    Show the working tree status
"""
