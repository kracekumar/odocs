"""Recursive command discovery."""

from typing import Callable

from .models import CommandHelp
from .parser import HelpParser
from .runner import CommandRunner


class CommandDiscovery:
    """Discovers commands and their subcommands recursively."""

    def __init__(
        self,
        runner: CommandRunner | None = None,
        parser: HelpParser | None = None,
        max_depth: int = 5,
        on_discover: Callable[[str, int], None] | None = None,
    ) -> None:
        """Initialize the discovery service.

        Args:
            runner: CommandRunner instance for executing commands.
            parser: HelpParser instance for parsing help output.
            max_depth: Maximum recursion depth for subcommand discovery.
            on_discover: Optional callback called when discovering a command.
                         Receives (command_string, depth).
        """
        self.runner = runner or CommandRunner()
        self.parser = parser or HelpParser()
        self.max_depth = max_depth
        self.on_discover = on_discover

    def discover(self, command: str) -> CommandHelp | None:
        """Discover a command and all its subcommands.

        Args:
            command: The root command to discover.

        Returns:
            CommandHelp tree or None if command not found.
        """
        return self._discover_recursive([command], current_depth=0)

    def _discover_recursive(
        self,
        command_parts: list[str],
        current_depth: int,
    ) -> CommandHelp | None:
        """Recursively discover command and subcommands.

        Args:
            command_parts: List of command parts forming the command.
            current_depth: Current recursion depth.

        Returns:
            CommandHelp with nested subcommands, or None on error.
        """
        if current_depth > self.max_depth:
            return None

        full_cmd = " ".join(command_parts)

        if self.on_discover:
            self.on_discover(full_cmd, current_depth)

        result = self.runner.run_help(command_parts)

        if not result.success:
            return None

        cmd_help = CommandHelp(
            name=command_parts[-1],
            full_command=command_parts.copy(),
            help_output=result.output,
        )

        # Find and recurse into subcommands
        subcommand_names = self.parser.parse_subcommands(result.output)

        for subcmd_name in subcommand_names:
            subcmd_parts = command_parts + [subcmd_name]
            subcmd_help = self._discover_recursive(
                subcmd_parts,
                current_depth=current_depth + 1,
            )
            if subcmd_help:
                cmd_help.subcommands.append(subcmd_help)

        return cmd_help
