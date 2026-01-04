"""Recursive command discovery."""

from typing import Callable

from odocs.models import CommandHelp
from odocs.parser import HelpParser
from odocs.runner import CommandRunner


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
        return self._discover_recursive(
            command_parts=[command],
            current_depth=0,
            root_command=command,
            use_help_subcommand=False,
        )

    def _discover_recursive(
        self,
        command_parts: list[str],
        current_depth: int,
        root_command: str,
        use_help_subcommand: bool,
    ) -> CommandHelp | None:
        """Recursively discover command and subcommands.

        Args:
            command_parts: List of command parts forming the command.
            current_depth: Current recursion depth.
            root_command: The root command name (for help subcommand pattern).
            use_help_subcommand: Whether to use "help <subcommand>" pattern.

        Returns:
            CommandHelp with nested subcommands, or None on error.
        """
        if current_depth > self.max_depth:
            return None

        full_cmd = " ".join(command_parts)

        if self.on_discover:
            self.on_discover(full_cmd, current_depth)

        # For root command or when not using help subcommand pattern
        is_root = len(command_parts) == 1
        result = self.runner.run_help(
            command_parts,
            use_help_subcommand=use_help_subcommand and not is_root,
            root_command=root_command,
        )

        if not result.success:
            return None

        cmd_help = CommandHelp(
            name=command_parts[-1],
            full_command=command_parts.copy(),
            help_output=result.output,
        )

        # Find subcommands
        subcommand_names = self.parser.parse_subcommands(result.output)

        # Detect if this command uses "help <subcommand>" pattern
        # by checking if "help" is listed as a subcommand
        if is_root and "help" in subcommand_names:
            use_help_subcommand = True
            # Remove "help" from subcommands to avoid recursing into it
            subcommand_names = [s for s in subcommand_names if s != "help"]

        for subcmd_name in subcommand_names:
            subcmd_parts = command_parts + [subcmd_name]
            subcmd_help = self._discover_recursive(
                subcmd_parts,
                current_depth=current_depth + 1,
                root_command=root_command,
                use_help_subcommand=use_help_subcommand,
            )
            if subcmd_help:
                cmd_help.subcommands.append(subcmd_help)

        return cmd_help
