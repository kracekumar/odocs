"""Tests for odocs.discovery module."""

from unittest.mock import MagicMock

import pytest

from odocs.discovery import CommandDiscovery
from odocs.parser import HelpParser
from odocs.runner import CommandResult, CommandRunner


class TestCommandDiscovery:
    """Tests for CommandDiscovery class."""

    def test_default_dependencies(self) -> None:
        """Test that default dependencies are created."""
        discovery = CommandDiscovery()
        assert discovery.runner is not None
        assert discovery.parser is not None
        assert discovery.max_depth == 5
        assert discovery.on_discover is None

    def test_custom_max_depth(self) -> None:
        """Test custom max_depth."""
        discovery = CommandDiscovery(max_depth=3)
        assert discovery.max_depth == 3

    def test_custom_dependencies(self) -> None:
        """Test injection of custom dependencies."""
        runner = CommandRunner(timeout=60)
        parser = HelpParser()
        discovery = CommandDiscovery(runner=runner, parser=parser)
        assert discovery.runner is runner
        assert discovery.parser is parser

    def test_max_depth_limit(self) -> None:
        """Test that max_depth is respected."""
        runner = MagicMock(spec=CommandRunner)
        runner.run_help.return_value = CommandResult(
            output="Commands:\n  sub  A subcommand",
            return_code=0,
        )

        discovery = CommandDiscovery(runner=runner, max_depth=0)
        result = discovery.discover("app")

        # Should return the root but not recurse into subcommands
        assert result is not None
        # With max_depth=0, current_depth starts at 0, so it processes root
        # but subcommands would be at depth 1 which exceeds max_depth

    def test_command_not_found(self) -> None:
        """Test handling of command not found."""
        runner = MagicMock(spec=CommandRunner)
        runner.run_help.return_value = CommandResult(
            output="Error: Command 'bad' not found.",
            return_code=1,
        )

        discovery = CommandDiscovery(runner=runner)
        result = discovery.discover("bad")
        assert result is None

    def test_recursive_discovery(self) -> None:
        """Test recursive subcommand discovery."""
        runner = MagicMock(spec=CommandRunner)

        def mock_help(
            parts: list[str],
            use_help_subcommand: bool = False,
            root_command: str | None = None,
        ) -> CommandResult:
            cmd = " ".join(parts)
            if cmd == "app":
                return CommandResult(
                    output="Commands:\n  sub  A subcommand",
                    return_code=0,
                )
            elif cmd == "app sub":
                return CommandResult(
                    output="No subcommands here",
                    return_code=0,
                )
            return CommandResult(output="Error", return_code=1)

        runner.run_help.side_effect = mock_help

        discovery = CommandDiscovery(runner=runner, max_depth=5)
        result = discovery.discover("app")

        assert result is not None
        assert result.name == "app"
        assert len(result.subcommands) == 1
        assert result.subcommands[0].name == "sub"

    def test_on_discover_callback(self) -> None:
        """Test that on_discover callback is called."""
        runner = MagicMock(spec=CommandRunner)
        runner.run_help.return_value = CommandResult(
            output="Simple help",
            return_code=0,
        )

        discovered = []

        def on_discover(cmd: str, depth: int) -> None:
            discovered.append((cmd, depth))

        discovery = CommandDiscovery(runner=runner, on_discover=on_discover)
        discovery.discover("myapp")

        assert len(discovered) == 1
        assert discovered[0] == ("myapp", 0)

    def test_deep_recursion(self) -> None:
        """Test discovery with multiple levels of nesting."""
        runner = MagicMock(spec=CommandRunner)

        def mock_help(
            parts: list[str],
            use_help_subcommand: bool = False,
            root_command: str | None = None,
        ) -> CommandResult:
            depth = len(parts) - 1
            if depth < 3:
                return CommandResult(
                    output=f"Commands:\n  level{depth + 1}  Level {depth + 1}",
                    return_code=0,
                )
            return CommandResult(output="Leaf command", return_code=0)

        runner.run_help.side_effect = mock_help

        discovery = CommandDiscovery(runner=runner, max_depth=5)
        result = discovery.discover("app")

        assert result is not None
        # Navigate down the tree
        current = result
        for level in range(3):
            assert len(current.subcommands) == 1
            current = current.subcommands[0]
            assert current.name == f"level{level + 1}"


class TestHelpSubcommandPattern:
    """Tests for commands that use 'help <subcommand>' pattern like ty."""

    def test_detects_help_subcommand_pattern(self) -> None:
        """Test that discovery detects when a command uses help subcommand."""
        runner = MagicMock(spec=CommandRunner)

        # ty-style: has "help" as a subcommand
        ty_help = """An extremely fast Python type checker.

Usage: ty <COMMAND>

Commands:
  check    Check a project for type errors
  server   Start the language server
  version  Display ty's version
  help     Print this message or the help of the given subcommand(s)

Options:
  -h, --help     Print help
  -V, --version  Print version
"""
        # Track all calls with their arguments
        help_calls = []

        def mock_help(
            parts: list[str],
            use_help_subcommand: bool = False,
            root_command: str | None = None,
        ) -> CommandResult:
            help_calls.append({
                "parts": parts,
                "use_help_subcommand": use_help_subcommand,
                "root_command": root_command,
            })
            if parts == ["ty"]:
                return CommandResult(output=ty_help, return_code=0)
            # When use_help_subcommand=True, simulate what runner does:
            # it transforms ["ty", "check"] to ["ty", "help", "check"]
            elif use_help_subcommand and root_command == "ty":
                # Simulate success for subcommands
                return CommandResult(
                    output=f"Help for {parts[-1]}",
                    return_code=0,
                )
            # If called without help subcommand pattern, simulate failure
            elif parts in [["ty", "check"], ["ty", "server"]]:
                return CommandResult(
                    output="Error: unexpected argument",
                    return_code=1,
                )
            return CommandResult(output="", return_code=0)

        runner.run_help.side_effect = mock_help

        discovery = CommandDiscovery(runner=runner, max_depth=1)
        result = discovery.discover("ty")

        assert result is not None
        # Should have discovered subcommands (check, server, version)
        # Note: "help" is excluded from recursion
        assert len(result.subcommands) == 3
        subcommand_names = [s.name for s in result.subcommands]
        assert "check" in subcommand_names
        assert "server" in subcommand_names
        assert "version" in subcommand_names
        assert "help" not in subcommand_names  # Should be excluded

        # Verify that help subcommand pattern was used for subcommands
        subcommand_calls = [
            c for c in help_calls if c["parts"] != ["ty"]
        ]
        for call in subcommand_calls:
            assert call["use_help_subcommand"] is True
            assert call["root_command"] == "ty"


class TestDiscoverRecursiveEdgeCases:
    """Edge case tests for recursive discovery."""

    def test_empty_subcommands(self) -> None:
        """Test command with no subcommands."""
        runner = MagicMock(spec=CommandRunner)
        runner.run_help.return_value = CommandResult(
            output="Usage: app [OPTIONS]\n\nOptions:\n  --help",
            return_code=0,
        )

        discovery = CommandDiscovery(runner=runner)
        result = discovery.discover("app")

        assert result is not None
        assert result.subcommands == []

    def test_failed_subcommand(self) -> None:
        """Test that failed subcommands are not included."""
        runner = MagicMock(spec=CommandRunner)

        def mock_help(
            parts: list[str],
            use_help_subcommand: bool = False,
            root_command: str | None = None,
        ) -> CommandResult:
            if parts == ["app"]:
                return CommandResult(
                    output="Commands:\n  good  Works\n  bad   Fails",
                    return_code=0,
                )
            elif parts == ["app", "good"]:
                return CommandResult(output="Good help", return_code=0)
            else:
                return CommandResult(
                    output="Error: Command not found",
                    return_code=1,
                )

        runner.run_help.side_effect = mock_help

        discovery = CommandDiscovery(runner=runner)
        result = discovery.discover("app")

        assert result is not None
        assert len(result.subcommands) == 1
        assert result.subcommands[0].name == "good"
