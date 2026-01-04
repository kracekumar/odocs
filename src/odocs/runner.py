"""Command execution utilities."""

import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of running a command.

    Attributes:
        output: The command output (stdout or stderr).
        return_code: The command's exit code.
        success: Whether the command succeeded.
    """

    output: str
    return_code: int

    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.return_code == 0 or not self.output.startswith("Error:")


class CommandRunner:
    """Executes commands and captures their output."""

    def __init__(self, timeout: int = 30) -> None:
        """Initialize the runner.

        Args:
            timeout: Maximum time in seconds to wait for command completion.
        """
        self.timeout = timeout

    def run_help(
        self,
        command_parts: list[str],
        use_help_subcommand: bool = False,
        root_command: str | None = None,
    ) -> CommandResult:
        """Run a command to get its help output.

        Args:
            command_parts: List of command parts (e.g., ["git", "commit"]).
            use_help_subcommand: If True, use "<root> help <subcommand>" pattern
                instead of "<command> --help".
            root_command: The root command for help subcommand pattern.
                Required if use_help_subcommand is True.

        Returns:
            CommandResult with output and return code.
        """
        try:
            if use_help_subcommand and root_command:
                # Use pattern: <root> help <subcommand> [<subsubcommand>...]
                # e.g., "ty help check" instead of "ty check --help"
                subcommand_parts = command_parts[1:]  # Skip root command
                cmd_to_run = [root_command, "help", *subcommand_parts]
            else:
                # Use standard --help flag
                cmd_to_run = [*command_parts, "--help"]

            result = subprocess.run(
                cmd_to_run,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            output = result.stdout if result.stdout else result.stderr
            return CommandResult(output=output, return_code=result.returncode)
        except FileNotFoundError:
            cmd = " ".join(command_parts)
            return CommandResult(
                output=f"Error: Command '{cmd}' not found.",
                return_code=1,
            )
        except subprocess.TimeoutExpired:
            cmd = " ".join(command_parts)
            return CommandResult(
                output=f"Error: Command '{cmd}' help timed out.",
                return_code=1,
            )
