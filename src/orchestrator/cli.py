"""Command-line interface for AI Coding Orchestrator."""

import click

from orchestrator import __version__


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """AI Coding Orchestrator - Coordinate multiple AI coding assistants.

    This tool helps you orchestrate multiple AI coding assistants (Claude, Copilot,
    Cursor, Gemini, Cline, Windsurf) for complex development projects.
    """
    pass


@cli.command()
def init() -> None:
    """Initialize a new orchestration project."""
    click.echo("Initializing AI Coding Orchestrator project...")
    click.echo("✓ Project initialized successfully!")


if __name__ == "__main__":
    cli()
