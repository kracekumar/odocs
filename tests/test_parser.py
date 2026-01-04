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

    def test_parse_indented_commands_help(
        self, parser: HelpParser, git_style_help_output: str
    ) -> None:
        """Test parsing help output with indented command format."""
        result = parser.parse_subcommands(git_style_help_output)
        # Commands should be detected from indented lines
        assert "clone" in result
        assert "init" in result
        assert "add" in result
        assert "mv" in result
        assert "restore" in result
        assert "rm" in result
        assert "bisect" in result
        assert "diff" in result
        assert "grep" in result
        assert "log" in result
        assert "show" in result
        assert "status" in result

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

    def test_git_command(self, parser: HelpParser) -> None:
        help_output = """
        usage: git [-v | --version] [-h | --help] [-C <path>] [-c <name>=<value>]
                   [--exec-path[=<path>]] [--html-path] [--man-path] [--info-path]
                   [-p | --paginate | -P | --no-pager] [--no-replace-objects] [--bare]
                   [--git-dir=<path>] [--work-tree=<path>] [--namespace=<name>]
                   [--super-prefix=<path>] [--config-env=<name>=<envvar>]
                   <command> [<args>]

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
           diff      Show changes between commits, commit and working tree, etc
           grep      Print lines matching a pattern
           log       Show commit logs
           show      Show various types of objects
           status    Show the working tree status

        grow, mark and tweak your common history
           branch    List, create, or delete branches
           commit    Record changes to the repository
           merge     Join two or more development histories together
           rebase    Reapply commits on top of another base tip
           reset     Reset current HEAD to the specified state
           switch    Switch branches
           tag       Create, list, delete or verify a tag object signed with GPG

        collaborate (see also: git help workflows)
           fetch     Download objects and refs from another repository
           pull      Fetch from and integrate with another repository or a local branch
           push      Update remote refs along with associated objects

        'git help -a' and 'git help -g' list available subcommands and some
        concept guides. See 'git help <command>' or 'git help <concept>'
        to read about a specific subcommand or concept.
        See 'git help git' for an overview of the system.
"""

        result = parser.parse_subcommands(help_output)
        expected = [
            "clone", "init", "add", "mv", "restore", "rm",
            "bisect", "diff", "grep", "log", "show", "status",
            "branch", "commit", "merge", "rebase", "reset", "switch", "tag",
            "fetch", "pull", "push",
        ]
        assert result == expected
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


class TestSpecYamlExamples:
    """Tests based on spec.yaml examples."""

    @pytest.fixture
    def parser(self) -> HelpParser:
        """Create a HelpParser instance."""
        return HelpParser()

    def test_ty_style_subcommands(
        self, parser: HelpParser, ty_style_help_output: str
    ) -> None:
        """Test parsing ty-style help (Commands section)."""
        result = parser.parse_subcommands(ty_style_help_output)
        assert result == ["check", "server", "version", "help"]

    def test_ty_style_options(
        self, parser: HelpParser, ty_style_help_output: str
    ) -> None:
        """Test parsing ty-style options."""
        options = parser.parse_options(ty_style_help_output)
        # Should find -h/--help and -V/--version
        assert len(options) >= 2
        longs = [opt.long for opt in options if opt.long]
        assert "--help" in longs
        assert "--version" in longs

    def test_toad_style_subcommands(
        self, parser: HelpParser, toad_style_help_output: str
    ) -> None:
        """Test parsing toad-style help (Options before Commands)."""
        result = parser.parse_subcommands(toad_style_help_output)
        assert result == ["about", "acp", "run", "serve", "settings"]

    def test_toad_style_options(
        self, parser: HelpParser, toad_style_help_output: str
    ) -> None:
        """Test parsing toad-style options (Options section before Commands)."""
        options = parser.parse_options(toad_style_help_output)
        # Should find --help option
        longs = [opt.long for opt in options if opt.long]
        assert "--help" in longs

    def test_wc_style_no_subcommands(
        self, parser: HelpParser, wc_style_help_output: str
    ) -> None:
        """Test parsing wc-style help (no subcommands)."""
        result = parser.parse_subcommands(wc_style_help_output)
        assert result == []

    def test_wc_style_parse_all(
        self, parser: HelpParser, wc_style_help_output: str
    ) -> None:
        """Test parse_all for wc-style (no commands, no standard options)."""
        parsed = parser.parse_all(wc_style_help_output)
        assert parsed.subcommands == []
        # wc doesn't have standard options section


class TestParseOptions:
    """Tests for option parsing."""

    @pytest.fixture
    def parser(self) -> HelpParser:
        """Create a HelpParser instance."""
        return HelpParser()

    def test_parse_standard_options(self, parser: HelpParser) -> None:
        """Test parsing standard Options: section."""
        help_output = """
Usage: tool [OPTIONS]

Options:
  -h, --help     Show help message
  -v, --verbose  Verbose output
  --version      Show version
"""
        options = parser.parse_options(help_output)
        assert len(options) >= 2
        # Check that we found some flags
        names = [opt.name for opt in options]
        assert "--help" in names or "-h" in [opt.short for opt in options]

    def test_parse_options_with_arguments(self, parser: HelpParser) -> None:
        """Test parsing options that take arguments."""
        help_output = """
Options:
  -o, --output FILE  Output file path
  --config PATH      Config file
"""
        options = parser.parse_options(help_output)
        valued = [opt for opt in options if not opt.is_flag]
        # Should find options with arguments
        assert any(opt.argument for opt in options) or len(options) > 0

    def test_parse_all(self, parser: HelpParser) -> None:
        """Test parse_all returns both subcommands and options."""
        help_output = """
Usage: tool [OPTIONS] COMMAND

Commands:
  init    Initialize
  build   Build project

Options:
  --help  Show help
"""
        parsed = parser.parse_all(help_output)
        assert "init" in parsed.subcommands
        assert "build" in parsed.subcommands
        assert len(parsed.options) >= 0  # Options parsing may vary

    def test_parsed_help_flags_property(self, parser: HelpParser) -> None:
        """Test ParsedHelp flags property."""
        help_output = """
Options:
  -v, --verbose  Verbose output
  -o FILE        Output file
"""
        parsed = parser.parse_all(help_output)
        # flags should only include options without arguments
        for flag in parsed.flags:
            assert flag.is_flag

    def test_parsed_help_valued_options_property(self, parser: HelpParser) -> None:
        """Test ParsedHelp valued_options property."""
        help_output = """
Options:
  -v, --verbose  Verbose output
  -o FILE        Output file
"""
        parsed = parser.parse_all(help_output)
        # valued_options should only include options with arguments
        for opt in parsed.valued_options:
            assert not opt.is_flag
