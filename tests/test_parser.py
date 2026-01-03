"""Tests for odocs.parser module."""

import pytest

from odocs.parser import HelpParser


class TestHelpParser:
    """Tests for HelpParser class."""

    @pytest.fixture
    def parser(self) -> HelpParser:
        """Create a HelpParser instance."""
        return HelpParser()

    def test_parse_standard_commands_section(self, parser: HelpParser) -> None:
        """Test parsing standard Commands: section."""
        help_output = """
Usage: tool [OPTIONS] COMMAND

Commands:
  init     Initialize something
  build    Build the project
  test     Run tests

Options:
  --help   Show help
"""
        result = parser.parse_subcommands(help_output)
        assert result == ["init", "build", "test"]

    def test_parse_commands_without_colon(self, parser: HelpParser) -> None:
        """Test parsing Commands section without colon."""
        help_output = """
Usage: tool [OPTIONS]

Commands
  add      Add item
  remove   Remove item
"""
        result = parser.parse_subcommands(help_output)
        assert result == ["add", "remove"]

    def test_parse_subcommands_section(self, parser: HelpParser) -> None:
        """Test parsing Subcommands: section."""
        help_output = """
Subcommands:
  start    Start service
  stop     Stop service
"""
        result = parser.parse_subcommands(help_output)
        assert result == ["start", "stop"]

    def test_parse_empty_help(self, parser: HelpParser) -> None:
        """Test parsing help with no commands."""
        help_output = """
Usage: simple-tool [OPTIONS]

Options:
  --version  Show version
  --help     Show help
"""
        result = parser.parse_subcommands(help_output)
        assert result == []

    def test_parse_uv_style_help(
        self, parser: HelpParser, uv_style_help_output: str
    ) -> None:
        """Test parsing uv-style help output."""
        result = parser.parse_subcommands(uv_style_help_output)
        assert "run" in result
        assert "init" in result
        assert "add" in result
        assert "sync" in result
        assert "help" in result

    def test_skip_common_words(self, parser: HelpParser) -> None:
        """Test that common non-command words are skipped."""
        help_output = """
Commands:
  Use this tool wisely
  See documentation for more
  actual-cmd   A real command
"""
        result = parser.parse_subcommands(help_output)
        # "Use" and "See" should be skipped
        assert "actual-cmd" in result
        assert "Use" not in result
        assert "See" not in result

    def test_parse_hyphenated_commands(self, parser: HelpParser) -> None:
        """Test parsing commands with hyphens."""
        help_output = """
Commands:
  my-command     Do something
  another-one    Do another thing
"""
        result = parser.parse_subcommands(help_output)
        assert result == ["my-command", "another-one"]

    def test_stops_at_options_section(self, parser: HelpParser) -> None:
        """Test that parsing stops at Options section."""
        help_output = """
Commands:
  init     Initialize
  build    Build

Options:
  -h, --help   Show help
"""
        result = parser.parse_subcommands(help_output)
        assert result == ["init", "build"]

    def test_stops_at_dash_prefix(self, parser: HelpParser) -> None:
        """Test that parsing stops at lines starting with dash."""
        help_output = """
Commands:
  init     Initialize
  -v       This is not a command
"""
        result = parser.parse_subcommands(help_output)
        assert result == ["init"]
        assert "-v" not in result


class TestHelpParserPrivateMethods:
    """Tests for HelpParser private methods."""

    @pytest.fixture
    def parser(self) -> HelpParser:
        """Create a HelpParser instance."""
        return HelpParser()

    def test_is_section_end_empty_line(self, parser: HelpParser) -> None:
        """Test _is_section_end with empty line."""
        assert parser._is_section_end("") is False

    def test_is_section_end_new_section(self, parser: HelpParser) -> None:
        """Test _is_section_end with new section header."""
        assert parser._is_section_end("Options:") is True
        assert parser._is_section_end("Global options:") is True

    def test_is_section_end_dash_prefix(self, parser: HelpParser) -> None:
        """Test _is_section_end with dash prefix."""
        assert parser._is_section_end("-h, --help") is True

    def test_extract_command_name_valid(self, parser: HelpParser) -> None:
        """Test _extract_command_name with valid command."""
        assert parser._extract_command_name("  init     Initialize") == "init"

    def test_extract_command_name_skip_word(self, parser: HelpParser) -> None:
        """Test _extract_command_name skips common words."""
        assert parser._extract_command_name("  Use this tool") is None

    def test_extract_command_name_no_match(self, parser: HelpParser) -> None:
        """Test _extract_command_name with no match."""
        assert parser._extract_command_name("") is None
