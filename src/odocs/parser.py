"""Help output parsing utilities."""

import re


class HelpParser:
    """Parses command help output to extract subcommands."""

    # Words that commonly appear in help text but aren't commands
    SKIP_WORDS = frozenset({"use", "see", "for", "the", "and", "options", "usage"})

    # Patterns that indicate start of commands section
    COMMANDS_SECTION_PATTERN = re.compile(
        r"^(Commands|Subcommands|Available commands):?\s*$",
        re.IGNORECASE,
    )

    # Pattern to match command names
    COMMAND_NAME_PATTERN = re.compile(r"^\s*([a-zA-Z][\w-]*)\s")

    def parse_subcommands(self, help_output: str) -> list[str]:
        """Extract subcommand names from help output.

        Args:
            help_output: The raw help text from a command.

        Returns:
            List of subcommand names found in the help text.
        """
        subcommands = []
        in_commands_section = False

        for line in help_output.split("\n"):
            stripped = line.strip()

            # Detect start of commands section
            if self.COMMANDS_SECTION_PATTERN.match(stripped):
                in_commands_section = True
                continue

            if in_commands_section:
                # Check for end of section
                if self._is_section_end(stripped):
                    in_commands_section = False
                    continue

                # Skip empty lines
                if not stripped:
                    continue

                # Try to extract command name
                command = self._extract_command_name(line)
                if command:
                    subcommands.append(command)

        return subcommands

    def _is_section_end(self, line: str) -> bool:
        """Check if line indicates end of commands section.

        Args:
            line: Stripped line to check.

        Returns:
            True if this line ends the commands section.
        """
        if not line:
            return False

        # New section header (ends with colon, starts with capital)
        if line.endswith(":") and line[0].isupper() and line != "Commands:":
            return True

        # Options section markers
        if line.startswith(("-", "╭", "╰")):
            return True

        return False

    def _extract_command_name(self, line: str) -> str | None:
        """Extract command name from a line.

        Args:
            line: Line that may contain a command definition.

        Returns:
            Command name if found, None otherwise.
        """
        match = self.COMMAND_NAME_PATTERN.match(line)
        if match:
            cmd_name = match.group(1)
            if cmd_name.lower() not in self.SKIP_WORDS:
                return cmd_name
        return None
