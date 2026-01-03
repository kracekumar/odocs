"""Markdown generation utilities."""

from datetime import datetime
from pathlib import Path

from .models import CommandHelp


class MarkdownGenerator:
    """Generates markdown documentation from command help."""

    def __init__(self, include_timestamp: bool = True) -> None:
        """Initialize the generator.

        Args:
            include_timestamp: Whether to include generation timestamp.
        """
        self.include_timestamp = include_timestamp

    def generate(self, cmd_help: CommandHelp) -> str:
        """Generate complete markdown documentation.

        Args:
            cmd_help: Root CommandHelp with all subcommands.

        Returns:
            Complete markdown document as string.
        """
        root_cmd = cmd_help.full_command[0]
        total_commands = cmd_help.count_all()

        # Build document parts
        header = self._generate_header(root_cmd, total_commands)
        toc = self._generate_toc(cmd_help)
        sections = self._generate_sections(cmd_help)

        return f"{header}\n\n## Table of Contents\n\n{toc}\n\n---\n\n{sections}"

    def _generate_header(self, root_cmd: str, total_commands: int) -> str:
        """Generate document header.

        Args:
            root_cmd: Name of the root command.
            total_commands: Total number of documented commands.

        Returns:
            Header markdown string.
        """
        lines = [f"# {root_cmd} Documentation"]

        if self.include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"\nGenerated on: {timestamp}")

        lines.append(f"\nTotal commands documented: {total_commands}")

        return "\n".join(lines)

    def _generate_toc(self, cmd_help: CommandHelp, indent: int = 0) -> str:
        """Generate table of contents.

        Args:
            cmd_help: CommandHelp to generate TOC for.
            indent: Current indentation level.

        Returns:
            TOC markdown string.
        """
        entries = []
        full_cmd = cmd_help.full_command_str
        anchor = full_cmd.replace(" ", "-").lower()
        entries.append(f"{'  ' * indent}- [{full_cmd}](#{anchor})")

        for subcmd in cmd_help.subcommands:
            entries.append(self._generate_toc(subcmd, indent + 1))

        return "\n".join(entries)

    def _generate_sections(self, cmd_help: CommandHelp, level: int = 2) -> str:
        """Generate command documentation sections.

        Args:
            cmd_help: CommandHelp to generate sections for.
            level: Current heading level.

        Returns:
            Sections markdown string.
        """
        full_cmd = cmd_help.full_command_str
        heading = "#" * min(level, 6)

        section = f"""{heading} {full_cmd}

```
{full_cmd} --help
```

```
{cmd_help.help_output}
```

"""

        for subcmd in cmd_help.subcommands:
            section += self._generate_sections(subcmd, level + 1)

        return section


def get_output_path(command: str, output: Path | None) -> Path:
    """Determine the output file path.

    Args:
        command: The command name.
        output: Optional explicit output path.

    Returns:
        Path for the output file.
    """
    if output:
        return output
    cmd_name = Path(command).name
    return Path(f"{cmd_name}-help.md")
