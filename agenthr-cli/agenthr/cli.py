"""
AgentHR CLI - Main entry point.

This module provides the main CLI application using typer for command-line
interface. It includes configuration management and command routing.
"""
import logging
import os
from pathlib import Path
from typing import Optional

import httpx
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Load environment variables from .env file if present
load_dotenv()

app = typer.Typer(
    name="agenthr",
    help="AgentHR CLI - AI-powered resume analysis and candidate ranking",
    add_completion=False,
)

console = Console()

# Global state for API configuration
_state = {
    "api_url": os.getenv("AGENTHR_API_URL", "http://localhost:8000"),
    "api_key": os.getenv("AGENTHR_API_KEY", ""),
    "timeout": int(os.getenv("AGENTHR_TIMEOUT", "30")),
}


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


class APIError(Exception):
    """Raised when API request fails."""

    pass


def get_api_client() -> httpx.Client:
    """
    Get an HTTP client configured for API requests.

    Returns:
        httpx.Client: Configured HTTP client with API key headers

    Raises:
        ConfigError: If API key is not configured
    """
    api_key = _state.get("api_key", "")
    if not api_key:
        raise ConfigError(
            "API key not configured. Set AGENTHR_API_KEY environment variable "
            "or run: agenthr config set api-key YOUR_KEY"
        )

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }

    return httpx.Client(
        base_url=_state["api_url"],
        headers=headers,
        timeout=_state["timeout"],
    )


def format_table(columns: list[str], rows: list[list[str]], title: Optional[str] = None) -> Table:
    """
    Format data as a Rich table.

    Args:
        columns: Column headers
        rows: Table rows
        title: Optional table title

    Returns:
        Table: Formatted Rich table
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for column in columns:
        table.add_column(column)

    for row in rows:
        table.add_row(*row)

    return table


@app.command()
def version():
    """Show AgentHR CLI version."""
    from agenthr import __version__

    console.print(f"AgentHR CLI version {__version__}")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set configuration value"),
    set_value: Optional[str] = typer.Option(None, "--value", help="Configuration value"),
):
    """
    Manage CLI configuration.

    Set API key:
        agenthr config set --set api-key --value YOUR_KEY

    Set API URL:
        agenthr config set --set api-url --value http://localhost:8000

    Show configuration:
        agenthr config --show
    """
    if show:
        console.print("[bold]Current Configuration:[/bold]")
        console.print(f"API URL: {_state['api_url']}")
        console.print(f"API Key: {'*' * 20 if _state['api_key'] else '(not set)'}")
        console.print(f"Timeout: {_state['timeout']}s")
        return

    if set_key and set_value:
        if set_key == "api-key":
            _state["api_key"] = set_value
            console.print("[green]✓[/green] API key updated")
        elif set_key == "api-url":
            _state["api_url"] = set_value
            console.print("[green]✓[/green] API URL updated")
        elif set_key == "timeout":
            try:
                _state["timeout"] = int(set_value)
                console.print("[green]✓[/green] Timeout updated")
            except ValueError:
                console.print("[red]✗[/red] Timeout must be a number")
                raise typer.Exit(1)
        else:
            console.print(f"[red]✗[/red] Unknown configuration key: {set_key}")
            console.print("Valid keys: api-key, api-url, timeout")
            raise typer.Exit(1)
        return

    # Show help if no options provided
    typer.echo(ctx=typer.get_context(config))


@app.callback()
def main(
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        envvar="AGENTHR_API_URL",
        help="AgentHR API base URL",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="AGENTHR_API_KEY",
        help="AgentHR API key for authentication",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """
    AgentHR CLI - AI-powered resume analysis and candidate ranking system.

    Use --help after any command to see more details.
    """
    # Update global state from command-line options
    if api_url is not None:
        _state["api_url"] = api_url
    if api_key is not None:
        _state["api_key"] = api_key

    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Silence httpx logging unless verbose
    if not verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)


# Import and register command modules
from agenthr.commands import analytics, resume, vacancy

app.add_typer(resume.resume_app, name="resume")
app.add_typer(vacancy.vacancy_app, name="vacancy")
app.add_typer(analytics.analytics_app, name="analytics")

# Additional command modules will be added in subsequent subtasks
# from agenthr.commands import candidate
# app.add_typer(candidate.candidate_app, name="candidate")


if __name__ == "__main__":
    app()
