"""Data models for odocs."""

from dataclasses import dataclass, field


@dataclass
class CommandHelp:
    """Represents help information for a command.

    Attributes:
        name: The command name (last part of the command).
        full_command: List of command parts forming the full command path.
        help_output: The raw help text output from running --help.
        subcommands: List of nested CommandHelp for subcommands.
    """

    name: str
    full_command: list[str]
    help_output: str
    subcommands: list["CommandHelp"] = field(default_factory=list)

    @property
    def full_command_str(self) -> str:
        """Return the full command as a space-separated string."""
        return " ".join(self.full_command)

    def count_all(self) -> int:
        """Count total number of commands including all subcommands."""
        count = 1  # Count self
        for subcmd in self.subcommands:
            count += subcmd.count_all()
        return count
