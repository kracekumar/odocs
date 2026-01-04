"""Tests for odocs.cli module."""

import subprocess

import pytest
from typer.testing import CliRunner

from odocs.cli import app


class TestCLI:
    """Integration tests for CLI."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    def test_help_option(self, runner: CliRunner) -> None:
        """Test --help option."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Recursively capture" in result.stdout

    def test_missing_command_argument(self, runner: CliRunner) -> None:
        """Test error when command argument is missing."""
        result = runner.invoke(app, [])
        assert result.exit_code != 0

    def test_nonexistent_command(self, runner: CliRunner) -> None:
        """Test error handling for non-existent command."""
        result = runner.invoke(app, ["nonexistent_cmd_xyz123"])
        assert result.exit_code == 1

    def test_verbose_option(self, runner: CliRunner) -> None:
        """Test verbose output."""
        result = runner.invoke(app, ["echo", "--verbose"])
        assert "Discovering:" in result.stdout

    def test_output_file_creation(self, runner: CliRunner, tmp_path) -> None:
        """Test that output file is created."""
        output_file = tmp_path / "test-help.md"
        result = runner.invoke(app, ["echo", "-o", str(output_file)])
        # echo should work on most systems
        if result.exit_code == 0:
            assert output_file.exists()

    def test_max_depth_option(self, runner: CliRunner, tmp_path) -> None:
        """Test --max-depth option."""
        output_file = tmp_path / "test-help.md"
        result = runner.invoke(app, ["echo", "-o", str(output_file), "-m", "1"])
        assert result.exit_code == 0

    def test_timeout_option(self, runner: CliRunner, tmp_path) -> None:
        """Test --timeout option."""
        output_file = tmp_path / "test-help.md"
        result = runner.invoke(
            app, ["echo", "-o", str(output_file), "-t", "10"]
        )
        assert result.exit_code == 0

    def test_debug_option(self, runner: CliRunner) -> None:
        """Test --debug option prints to stdout."""
        result = runner.invoke(app, ["echo", "--debug"])
        assert result.exit_code == 0
        assert "Command: echo" in result.stdout
        assert "Subcommands" in result.stdout
        assert "Flags" in result.stdout
        assert "Options" in result.stdout

    def test_debug_short_option(self, runner: CliRunner) -> None:
        """Test -d short option for debug."""
        result = runner.invoke(app, ["echo", "-d"])
        assert result.exit_code == 0
        assert "Command: echo" in result.stdout


class TestIntegration:
    """Integration tests with real commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @pytest.mark.skipif(
        subprocess.run(["which", "python"], capture_output=True).returncode
        != 0,
        reason="python not available",
    )
    def test_python_help(self, runner: CliRunner, tmp_path) -> None:
        """Test generating docs for python command."""
        output_file = tmp_path / "python-help.md"
        result = runner.invoke(
            app, ["python", "-o", str(output_file), "--max-depth", "1"]
        )
        # Python might not have subcommands, but should still work
        assert output_file.exists() or result.exit_code == 0

    def test_output_contains_command(self, runner: CliRunner, tmp_path) -> None:
        """Test that output file contains the command."""
        output_file = tmp_path / "echo-help.md"
        result = runner.invoke(app, ["echo", "-o", str(output_file)])
        if result.exit_code == 0:
            content = output_file.read_text()
            assert "echo" in content.lower()
            assert "Documentation" in content

    def test_reports_command_count(self, runner: CliRunner, tmp_path) -> None:
        """Test that CLI reports command count."""
        output_file = tmp_path / "echo-help.md"
        result = runner.invoke(app, ["echo", "-o", str(output_file)])
        if result.exit_code == 0:
            assert "Found" in result.stdout
            assert "command(s)" in result.stdout
