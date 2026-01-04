"""Help output parsing utilities."""

import re
from dataclasses import dataclass, field


@dataclass
class ParsedOption:
    """Represents a parsed option or flag from help output.

    Attributes:
        short: Short form like -h, -v (optional).
        long: Long form like --help, --verbose (optional).
        argument: Argument name if option takes a value (e.g., FILE, PATH).
        description: Description text for the option.
        is_flag: True if this is a boolean flag (no argument).
    """

    short: str | None = None
    long: str | None = None
    argument: str | None = None
    description: str = ""
    is_flag: bool = True

    @property
    def name(self) -> str:
        """Return the primary name (long form preferred)."""
        return self.long or self.short or ""


@dataclass
class ParsedHelp:
    """Complete parsed help output.

    Attributes:
        subcommands: List of subcommand names.
        options: List of parsed options.
        flags: List of parsed flags (boolean options).
    """

    subcommands: list[str] = field(default_factory=list)
    options: list[ParsedOption] = field(default_factory=list)

    @property
    def flags(self) -> list[ParsedOption]:
        """Return only flag options (no argument)."""
        return [opt for opt in self.options if opt.is_flag]

    @property
    def valued_options(self) -> list[ParsedOption]:
        """Return only options that take values."""
        return [opt for opt in self.options if not opt.is_flag]


class HelpParser:
    """Parses command help output to extract subcommands and options."""

    # Words that commonly appear in help text but aren't commands
    SKIP_WORDS = frozenset(
        {"use", "see", "for", "the", "and", "options", "usage"}
    )

    # Patterns that indicate start of commands section
    COMMANDS_SECTION_PATTERN = re.compile(
        r"^(Commands|Subcommands|Available commands):?\s*$",
        re.IGNORECASE,
    )

    # Patterns that indicate start of options section
    OPTIONS_SECTION_PATTERN = re.compile(
        r"^(Options|Flags|Global options|Arguments):?\s*$",
        re.IGNORECASE,
    )

    # Pattern to match command names
    COMMAND_NAME_PATTERN = re.compile(r"^\s*([a-zA-Z][\w-]*)\s")

    # Pattern for indented command lines (2+ leading spaces, command name,
    # 2+ spaces as separator, then description text)
    # This matches formats like:
    #    clone     Clone a repository
    #    my-cmd    Description here
    INDENTED_COMMAND_PATTERN = re.compile(r"^[ ]{2,}([a-zA-Z][\w-]*)\s{2,}\S")

    # Pattern for options: -x, --long-opt [ARG]  description
    # Matches: -h, --help, -o FILE, --output=FILE, etc.
    OPTION_PATTERN = re.compile(
        r"^\s*"
        r"(?:(-[a-zA-Z]),?\s*)?"  # Optional short form: -x
        r"(--[a-zA-Z][\w-]*)?"  # Optional long form: --long
        r"(?:[=\s]([A-Z_][\w_]*))?"  # Optional argument: FILE, PATH
        r"\s{2,}(.+)?$"  # Description (2+ spaces then text)
    )

    def parse_subcommands(self, help_output: str) -> list[str]:
        """Extract subcommand names from help output.

        Args:
            help_output: The raw help text from a command.

        Returns:
            List of subcommand names found in the help text.
        """
        # Try standard Commands: section parsing first
        subcommands = self._parse_standard_commands(help_output)

        # If no commands found, try indented command format
        if not subcommands:
            subcommands = self._parse_indented_commands(help_output)

        return subcommands

    def parse_options(self, help_output: str) -> list[ParsedOption]:
        """Extract options and flags from help output.

        Args:
            help_output: The raw help text from a command.

        Returns:
            List of ParsedOption objects found in the help text.
        """
        options = []
        in_options_section = False

        for line in help_output.split("\n"):
            stripped = line.strip()

            # Detect start of options section
            if self.OPTIONS_SECTION_PATTERN.match(stripped):
                in_options_section = True
                continue

            # Check for section end
            if in_options_section and self._is_options_section_end(stripped):
                in_options_section = False
                continue

            if in_options_section and stripped:
                option = self._parse_option_line(line)
                if option:
                    options.append(option)

        # If no options section found, try to find options anywhere
        if not options:
            options = self._parse_inline_options(help_output)

        return options

    def parse_all(self, help_output: str) -> ParsedHelp:
        """Parse all information from help output.

        Args:
            help_output: The raw help text from a command.

        Returns:
            ParsedHelp with subcommands and options.
        """
        return ParsedHelp(
            subcommands=self.parse_subcommands(help_output),
            options=self.parse_options(help_output),
        )

    def _parse_standard_commands(self, help_output: str) -> list[str]:
        """Parse standard Commands: section format.

        Args:
            help_output: The raw help text from a command.

        Returns:
            List of subcommand names found.
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

    def _parse_indented_commands(self, help_output: str) -> list[str]:
        """Parse help output with indented command format.

        Many CLIs list commands with indentation:
               command     Description of the command
               other-cmd   Another description

        Args:
            help_output: The raw help text from a command.

        Returns:
            List of subcommand names found.
        """
        subcommands = []

        for line in help_output.split("\n"):
            match = self.INDENTED_COMMAND_PATTERN.match(line)
            if match:
                cmd_name = match.group(1)
                if cmd_name.lower() not in self.SKIP_WORDS:
                    subcommands.append(cmd_name)

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

    def _is_options_section_end(self, line: str) -> bool:
        """Check if line indicates end of options section.

        Args:
            line: Stripped line to check.

        Returns:
            True if this line ends the options section.
        """
        if not line:
            return False

        # New section header (ends with colon, starts with capital)
        if (
            line.endswith(":")
            and line[0].isupper()
            and not self.OPTIONS_SECTION_PATTERN.match(line)
        ):
            return True

        # Rich box drawing characters indicate section boundaries
        if line.startswith(("╭", "╰")):
            return True

        return False

    def _parse_option_line(self, line: str) -> ParsedOption | None:
        """Parse a single option line.

        Args:
            line: Line that may contain an option definition.

        Returns:
            ParsedOption if found, None otherwise.
        """
        # Try the regex pattern first
        match = self.OPTION_PATTERN.match(line)
        if match:
            short, long_opt, arg, desc = match.groups()
            if short or long_opt:
                return ParsedOption(
                    short=short,
                    long=long_opt,
                    argument=arg,
                    description=(desc or "").strip(),
                    is_flag=arg is None,
                )

        # Fallback: look for -x or --xxx patterns
        stripped = line.strip()
        if stripped.startswith("-"):
            parts = stripped.split(None, 1)
            if parts:
                opt_part = parts[0].rstrip(",")
                desc = parts[1] if len(parts) > 1 else ""

                short = None
                long_opt = None

                if opt_part.startswith("--"):
                    long_opt = opt_part.split("=")[0]
                elif opt_part.startswith("-") and len(opt_part) == 2:
                    short = opt_part

                if short or long_opt:
                    return ParsedOption(
                        short=short,
                        long=long_opt,
                        description=desc.strip(),
                        is_flag=True,
                    )

        return None

    def _parse_inline_options(self, help_output: str) -> list[ParsedOption]:
        """Parse options that appear inline without section headers.

        Args:
            help_output: The raw help text from a command.

        Returns:
            List of ParsedOption objects found.
        """
        options = []

        for line in help_output.split("\n"):
            stripped = line.strip()
            # Look for lines starting with dash that look like options
            if stripped.startswith("-") and "  " in stripped:
                option = self._parse_option_line(line)
                if option:
                    options.append(option)

        return options
