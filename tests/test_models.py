"""Tests for odocs.models module."""

import pytest

from odocs.models import CommandHelp


class TestCommandHelp:
    """Tests for CommandHelp dataclass."""

    def test_create_command_help(self) -> None:
        """Test creating CommandHelp instance."""
        cmd = CommandHelp(
            name="test",
            full_command=["app", "test"],
            help_output="Test help output",
        )
        assert cmd.name == "test"
        assert cmd.full_command == ["app", "test"]
        assert cmd.help_output == "Test help output"
        assert cmd.subcommands == []

    def test_command_help_with_subcommands(self) -> None:
        """Test CommandHelp with nested subcommands."""
        subcmd = CommandHelp(
            name="sub",
            full_command=["app", "sub"],
            help_output="Sub help",
        )
        cmd = CommandHelp(
            name="app",
            full_command=["app"],
            help_output="App help",
            subcommands=[subcmd],
        )
        assert len(cmd.subcommands) == 1
        assert cmd.subcommands[0].name == "sub"

    def test_full_command_str(self) -> None:
        """Test full_command_str property."""
        cmd = CommandHelp(
            name="sub",
            full_command=["app", "sub"],
            help_output="help",
        )
        assert cmd.full_command_str == "app sub"

    def test_full_command_str_single(self) -> None:
        """Test full_command_str for single command."""
        cmd = CommandHelp(
            name="app",
            full_command=["app"],
            help_output="help",
        )
        assert cmd.full_command_str == "app"


class TestCountAll:
    """Tests for CommandHelp.count_all method."""

    def test_single_command(self, simple_command: CommandHelp) -> None:
        """Test counting single command."""
        assert simple_command.count_all() == 1

    def test_nested_commands(self, nested_command: CommandHelp) -> None:
        """Test counting nested commands."""
        # root + sub + leaf1 + leaf2 = 4
        assert nested_command.count_all() == 4

    def test_deeply_nested_commands(self, deeply_nested_command: CommandHelp) -> None:
        """Test counting deeply nested commands."""
        # root + 5 levels = 6
        assert deeply_nested_command.count_all() == 6
