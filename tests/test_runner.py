"""Tests for odocs.runner module."""

import subprocess
from unittest.mock import patch

import pytest

from odocs.runner import CommandResult, CommandRunner


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_successful_result(self) -> None:
        """Test successful command result."""
        result = CommandResult(output="Help text", return_code=0)
        assert result.success is True
        assert result.output == "Help text"
        assert result.return_code == 0

    def test_failed_result(self) -> None:
        """Test failed command result."""
        result = CommandResult(output="Error: Command failed", return_code=1)
        assert result.success is False

    def test_nonzero_but_valid_result(self) -> None:
        """Test command with non-zero return but valid output."""
        result = CommandResult(output="Some help output", return_code=1)
        assert result.success is True


class TestCommandRunner:
    """Tests for CommandRunner class."""

    def test_default_timeout(self) -> None:
        """Test default timeout value."""
        runner = CommandRunner()
        assert runner.timeout == 30

    def test_custom_timeout(self) -> None:
        """Test custom timeout value."""
        runner = CommandRunner(timeout=60)
        assert runner.timeout == 60

    def test_successful_command(self) -> None:
        """Test running help on a valid command."""
        runner = CommandRunner()
        result = runner.run_help(["echo"])
        # echo --help should work on most systems
        assert result.return_code == 0 or "echo" in result.output.lower()

    def test_command_not_found(self) -> None:
        """Test running help on non-existent command."""
        runner = CommandRunner()
        result = runner.run_help(["nonexistent_command_xyz"])
        assert result.return_code == 1
        assert "Error:" in result.output
        assert "not found" in result.output

    @patch("odocs.runner.subprocess.run")
    def test_timeout_handling(self, mock_run) -> None:
        """Test handling of command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=30)
        runner = CommandRunner()
        result = runner.run_help(["slow_command"])
        assert result.return_code == 1
        assert "timed out" in result.output

    @patch("odocs.runner.subprocess.run")
    def test_uses_configured_timeout(self, mock_run) -> None:
        """Test that configured timeout is passed to subprocess."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["test", "--help"],
            returncode=0,
            stdout="Help text",
            stderr="",
        )
        runner = CommandRunner(timeout=45)
        runner.run_help(["test"])
        mock_run.assert_called_once()
        assert mock_run.call_args.kwargs["timeout"] == 45
