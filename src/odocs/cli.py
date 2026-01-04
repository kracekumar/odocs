"""CLI entry point for odocs."""

import sys
from pathlib import Path

# Allow running as script: python src/odocs/cli.py
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer

from odocs.discovery import CommandDiscovery
from odocs.markdown import MarkdownGenerator, get_output_path
from odocs.models import CommandHelp
from odocs.parser import HelpParser
from odocs.runner import CommandRunner

app = typer.Typer(
    help="Capture command --help output recursively and save as markdown."
)


@app.command()
def main(
    command: str = typer.Argument(
        ...,
        help="Command or path to executable to get help for.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output markdown file path. Defaults to <command>-help.md",
    ),
    max_depth: int = typer.Option(
        5,
        "--max-depth",
        "-m",
        help="Maximum depth for subcommand discovery.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show progress during discovery.",
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Timeout in seconds for each command.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Print parsed subcommands, options, and flags to stdout.",
    ),
) -> None:
    """Recursively capture --help output of a command and all subcommands.

    Examples:
        odocs uv
        odocs git -o git-docs.md
        odocs docker --max-depth 3
        odocs git --debug
    """
    typer.echo(f"Discovering commands for: {command}")

    # Set up discovery with optional verbose callback
    def on_discover(cmd: str, depth: int) -> None:
        if verbose:
            typer.echo(f"{'  ' * depth}Discovering: {cmd}")

    runner = CommandRunner(timeout=timeout)
    discovery = CommandDiscovery(
        runner=runner,
        max_depth=max_depth,
        on_discover=on_discover,
    )

    cmd_help = discovery.discover(command)

    if not cmd_help:
        typer.echo(f"Error: Could not get help for '{command}'", err=True)
        raise typer.Exit(1)

    total = cmd_help.count_all()
    typer.echo(f"Found {total} command(s)")

    if debug:
        # Print debug output to stdout
        _print_debug_output(cmd_help)
    else:
        # Generate markdown
        generator = MarkdownGenerator()
        markdown_content = generator.generate(cmd_help)

        # Write output
        output_file = get_output_path(command, output)
        output_file.write_text(markdown_content)
        typer.echo(f"Documentation saved to: {output_file}")


def _print_debug_output(cmd_help: CommandHelp, indent: int = 0) -> None:
    """Print debug information for a command and its subcommands.

    Args:
        cmd_help: CommandHelp to print debug info for.
        indent: Current indentation level.
    """
    parser = HelpParser()
    prefix = "  " * indent

    # Print command header
    typer.echo(f"\n{prefix}{'=' * 60}")
    typer.echo(f"{prefix}Command: {cmd_help.full_command_str}")
    typer.echo(f"{prefix}{'=' * 60}")

    # Parse the help output
    parsed = parser.parse_all(cmd_help.help_output)

    # Print subcommands
    if parsed.subcommands:
        typer.echo(f"{prefix}Subcommands ({len(parsed.subcommands)}):")
        for subcmd in parsed.subcommands:
            typer.echo(f"{prefix}  - {subcmd}")
    else:
        typer.echo(f"{prefix}Subcommands: (none)")

    # Print flags
    flags = parsed.flags
    if flags:
        typer.echo(f"{prefix}Flags ({len(flags)}):")
        for flag in flags:
            parts = []
            if flag.short:
                parts.append(flag.short)
            if flag.long:
                parts.append(flag.long)
            name = ", ".join(parts)
            desc = f"  {flag.description}" if flag.description else ""
            typer.echo(f"{prefix}  - {name}{desc}")
    else:
        typer.echo(f"{prefix}Flags: (none)")

    # Print options (with values)
    options = parsed.valued_options
    if options:
        typer.echo(f"{prefix}Options ({len(options)}):")
        for opt in options:
            parts = []
            if opt.short:
                parts.append(opt.short)
            if opt.long:
                parts.append(opt.long)
            name = ", ".join(parts)
            arg = f" {opt.argument}" if opt.argument else ""
            desc = f"  {opt.description}" if opt.description else ""
            typer.echo(f"{prefix}  - {name}{arg}{desc}")
    else:
        typer.echo(f"{prefix}Options: (none)")

    # Recurse into subcommands
    for subcmd in cmd_help.subcommands:
        _print_debug_output(subcmd, indent + 1)


def run() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    run()
