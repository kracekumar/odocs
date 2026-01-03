"""CLI entry point for odocs."""

from pathlib import Path

import typer

from .discovery import CommandDiscovery
from .markdown import MarkdownGenerator, get_output_path
from .runner import CommandRunner

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
        "-d",
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
) -> None:
    """Recursively capture --help output of a command and all subcommands.

    Examples:
        odocs uv
        odocs git -o git-docs.md
        odocs docker --max-depth 3
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

    # Generate markdown
    generator = MarkdownGenerator()
    markdown_content = generator.generate(cmd_help)

    # Write output
    output_file = get_output_path(command, output)
    output_file.write_text(markdown_content)
    typer.echo(f"Documentation saved to: {output_file}")


def run() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    run()
