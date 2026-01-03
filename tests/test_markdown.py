"""Tests for odocs.markdown module."""

from pathlib import Path

import pytest

from odocs.markdown import MarkdownGenerator, get_output_path
from odocs.models import CommandHelp


class TestMarkdownGenerator:
    """Tests for MarkdownGenerator class."""

    @pytest.fixture
    def generator(self) -> MarkdownGenerator:
        """Create a MarkdownGenerator instance."""
        return MarkdownGenerator(include_timestamp=False)

    def test_default_includes_timestamp(self) -> None:
        """Test that timestamp is included by default."""
        generator = MarkdownGenerator()
        assert generator.include_timestamp is True

    def test_disable_timestamp(self) -> None:
        """Test disabling timestamp."""
        generator = MarkdownGenerator(include_timestamp=False)
        assert generator.include_timestamp is False

    def test_markdown_structure(
        self, generator: MarkdownGenerator, simple_command: CommandHelp
    ) -> None:
        """Test complete markdown output structure."""
        md = generator.generate(simple_command)
        assert "# app Documentation" in md
        assert "Total commands documented: 1" in md
        assert "## Table of Contents" in md
        assert "## app" in md

    def test_markdown_with_timestamp(self, simple_command: CommandHelp) -> None:
        """Test markdown includes timestamp when enabled."""
        generator = MarkdownGenerator(include_timestamp=True)
        md = generator.generate(simple_command)
        assert "Generated on:" in md


class TestGenerateToc:
    """Tests for TOC generation."""

    @pytest.fixture
    def generator(self) -> MarkdownGenerator:
        """Create a MarkdownGenerator instance."""
        return MarkdownGenerator(include_timestamp=False)

    def test_single_command_toc(
        self, generator: MarkdownGenerator, simple_command: CommandHelp
    ) -> None:
        """Test TOC for single command."""
        toc = generator._generate_toc(simple_command)
        assert "[app](#app)" in toc

    def test_nested_toc(
        self, generator: MarkdownGenerator, nested_command: CommandHelp
    ) -> None:
        """Test TOC for nested commands."""
        toc = generator._generate_toc(nested_command)
        assert "[app](#app)" in toc
        assert "[app sub](#app-sub)" in toc
        # Check indentation
        lines = toc.split("\n")
        assert lines[0].startswith("- ")
        assert lines[1].startswith("  ")  # Indented for subcommand

    def test_deeply_nested_toc(
        self, generator: MarkdownGenerator, deeply_nested_command: CommandHelp
    ) -> None:
        """Test TOC for deeply nested commands."""
        toc = generator._generate_toc(deeply_nested_command)
        lines = toc.split("\n")
        # Check increasing indentation
        for i, line in enumerate(lines):
            expected_indent = "  " * i
            assert line.startswith(expected_indent + "- ")


class TestGenerateSections:
    """Tests for section generation."""

    @pytest.fixture
    def generator(self) -> MarkdownGenerator:
        """Create a MarkdownGenerator instance."""
        return MarkdownGenerator(include_timestamp=False)

    def test_single_command_section(
        self, generator: MarkdownGenerator, simple_command: CommandHelp
    ) -> None:
        """Test section generation for single command."""
        section = generator._generate_sections(simple_command)
        assert "## app" in section
        assert "app --help" in section
        assert simple_command.help_output in section

    def test_nested_command_sections(
        self, generator: MarkdownGenerator, nested_command: CommandHelp
    ) -> None:
        """Test section generation with nested commands."""
        section = generator._generate_sections(nested_command)
        assert "## app" in section
        assert "### app sub" in section
        assert "#### app sub leaf1" in section
        assert "#### app sub leaf2" in section

    def test_heading_level_cap(self, generator: MarkdownGenerator) -> None:
        """Test that heading levels are capped at 6."""
        # Create deeply nested command
        cmd = CommandHelp(name="deep", full_command=["deep"], help_output="help")
        for i in range(10):
            cmd = CommandHelp(
                name=f"l{i}",
                full_command=[f"l{i}"],
                help_output="help",
                subcommands=[cmd],
            )

        section = generator._generate_sections(cmd)
        # Should never have more than 6 #
        assert "#######" not in section


class TestGetOutputPath:
    """Tests for get_output_path function."""

    def test_default_filename(self) -> None:
        """Test default filename generation."""
        result = get_output_path("myapp", None)
        assert result == Path("myapp-help.md")

    def test_custom_output(self) -> None:
        """Test custom output path."""
        custom = Path("/tmp/custom.md")
        result = get_output_path("myapp", custom)
        assert result == custom

    def test_command_path_extraction(self) -> None:
        """Test filename extraction from command path."""
        result = get_output_path("/usr/bin/myapp", None)
        assert result == Path("myapp-help.md")

    def test_relative_path_command(self) -> None:
        """Test filename extraction from relative path."""
        result = get_output_path("./bin/myapp", None)
        assert result == Path("myapp-help.md")
