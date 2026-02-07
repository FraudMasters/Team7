"""
AgentHR CLI - Resume commands.

This module provides commands for uploading and managing resumes via the CLI.
"""
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console

from ..cli import APIError, ConfigError, get_api_client

console = Console()

resume_app = typer.Typer(
    name="resume",
    help="Resume management commands",
    add_completion=False,
)


@resume_app.command("upload")
def upload_resume(
    file_path: str = typer.Argument(
        ...,
        help="Path to the resume file (PDF or DOCX)",
        exists=True,
    ),
    vacancy_id: Optional[str] = typer.Option(
        None,
        "--vacancy-id",
        help="Associate resume with a specific vacancy ID",
    ),
):
    """
    Upload a resume file for analysis.

    The resume will be processed and analyzed for candidate matching.

    Examples:
        Upload a resume:
            agenthr resume upload my_resume.pdf

        Upload and associate with vacancy:
            agenthr resume upload my_resume.pdf --vacancy-id 123e4567-e89b-12d3-a456-426614174000
    """
    try:
        # Get API client
        client = get_api_client()

        # Validate file exists and get its extension
        path = Path(file_path)
        if not path.is_file():
            console.print(f"[red]✗[/red] File not found: {file_path}")
            raise typer.Exit(1)

        # Validate file type
        allowed_extensions = {".pdf", ".docx", ".doc"}
        if path.suffix.lower() not in allowed_extensions:
            console.print(f"[red]✗[/red] Invalid file type: {path.suffix}")
            console.print(f"Allowed types: {', '.join(allowed_extensions)}")
            raise typer.Exit(1)

        # Prepare multipart upload
        console.print(f"[dim]Uploading {file_path}...[/dim]")

        with open(path, "rb") as f:
            files = {"file": (path.name, f, "application/octet-stream")}
            data = {}
            if vacancy_id:
                data["vacancy_id"] = vacancy_id

            # Make upload request
            response = client.post(
                "/api/resumes/upload",
                files=files,
                data=data if data else None,
            )

        # Check for errors
        if response.status_code not in (200, 201):
            console.print(f"[red]✗[/red] Upload failed: {response.status_code}")
            try:
                error_data = response.json()
                console.print(f"[red]  {error_data.get('detail', 'Unknown error')}[/red]")
            except Exception:
                console.print(f"[red]  {response.text}[/red]")
            raise typer.Exit(1)

        # Parse response
        result = response.json()

        # Display success message
        console.print("[green]✓[/green] Resume uploaded successfully")
        console.print(f"  [dim]ID:[/dim] {result.get('id')}")
        console.print(f"  [dim]Filename:[/dim] {result.get('filename')}")
        console.print(f"  [dim]Status:[/dim] {result.get('status')}")

        if vacancy_id:
            console.print(f"  [dim]Associated with vacancy:[/dim] {vacancy_id}")

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]✗[/red] API error: {e}")
        raise typer.Exit(1)
    except httpx.TimeoutException:
        console.print("[red]✗[/red] Request timed out. Try again later.")
        raise typer.Exit(1)
    except httpx.ConnectError:
        console.print("[red]✗[/red] Could not connect to API server.")
        console.print(f"[dim]  Check your API URL configuration[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        raise typer.Exit(1)


@resume_app.command("list")
def list_resumes(
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum number of resumes to display",
    ),
    status_filter: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (pending, processing, completed, failed)",
    ),
):
    """
    List all uploaded resumes.

    Examples:
        List recent resumes:
            agenthr resume list

        List only completed resumes:
            agenthr resume list --status completed

        Show more results:
            agenthr resume list --limit 50
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {"limit": limit}
        if status_filter:
            params["status"] = status_filter

        # Make request
        response = client.get("/api/resumes", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to list resumes: {response.status_code}")
            raise typer.Exit(1)

        data = response.json()
        resumes = data.get("items", data.get("resumes", []))

        if not resumes:
            console.print("[yellow]No resumes found[/yellow]")
            return

        # Display table
        from ..cli import format_table

        columns = ["ID", "Filename", "Status", "Uploaded"]
        rows = []
        for resume in resumes:
            resume_id = resume.get("id", "")
            # Show short ID (first 8 chars)
            short_id = resume_id[:8] if resume_id else "N/A"
            filename = resume.get("filename", "unknown")[:30]
            status = resume.get("status", "unknown")
            created_at = resume.get("created_at", "")[:10]  # Just the date
            rows.append([short_id, filename, status, created_at])

        table = format_table(columns, rows, title=f"Resumes ({len(resumes)})")
        console.print(table)

        # Show pagination info if available
        total = data.get("total", len(resumes))
        if total > limit:
            console.print(f"\n[dim]Showing {len(resumes)} of {total} total resumes[/dim]")

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@resume_app.command("get")
def get_resume(
    resume_id: str = typer.Argument(
        ...,
        help="Resume ID (UUID)",
    ),
):
    """
    Get details of a specific resume.

    Examples:
        Get resume details:
            agenthr resume get 123e4567-e89b-12d3-a456-426614174000
    """
    try:
        client = get_api_client()

        response = client.get(f"/api/resumes/{resume_id}")

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get resume: {response.status_code}")
            raise typer.Exit(1)

        resume = response.json()

        # Display resume details
        console.print(f"[bold]Resume Details[/bold]")
        console.print(f"  [dim]ID:[/dim] {resume.get('id')}")
        console.print(f"  [dim]Filename:[/dim] {resume.get('filename')}")
        console.print(f"  [dim]Status:[/dim] {resume.get('status')}")
        console.print(f"  [dim]Content Type:[/dim] {resume.get('content_type')}")
        console.print(f"  [dim]Created:[/dim] {resume.get('created_at')}")
        console.print(f"  [dim]Updated:[/dim] {resume.get('updated_at')}")

        # Show parsed data if available
        if resume.get("parsed_data"):
            console.print(f"\n[bold]Parsed Data:[/bold]")
            parsed = resume["parsed_data"]
            if parsed.get("name"):
                console.print(f"  [dim]Name:[/dim] {parsed['name']}")
            if parsed.get("email"):
                console.print(f"  [dim]Email:[/dim] {parsed['email']}")
            if parsed.get("phone"):
                console.print(f"  [dim]Phone:[/dim] {parsed['phone']}")
            if parsed.get("skills"):
                console.print(f"  [dim]Skills:[/dim] {', '.join(parsed['skills'])}")

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)
