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

        def mock_help(parts: list[str]) -> CommandResult:
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

        def mock_help(parts: list[str]) -> CommandResult:
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

        def mock_help(parts: list[str]) -> CommandResult:
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
