"""
AgentHR CLI - Vacancy commands.

This module provides commands for creating and managing job vacancies via the CLI.
"""
from typing import Optional

import httpx
import typer
from rich.console import Console

from ..cli import APIError, ConfigError, get_api_client

console = Console()

vacancy_app = typer.Typer(
    name="vacancy",
    help="Vacancy management commands",
    add_completion=False,
)


@vacancy_app.command("create")
def create_vacancy(
    title: str = typer.Option(
        ...,
        "--title",
        "-t",
        help="Job title",
    ),
    description: str = typer.Option(
        ...,
        "--description",
        "-d",
        help="Job description and responsibilities",
    ),
    required_skills: str = typer.Option(
        ...,
        "--skills",
        "-s",
        help="Required skills (comma-separated)",
    ),
    min_experience: Optional[int] = typer.Option(
        None,
        "--min-experience",
        "-e",
        help="Minimum experience in months",
    ),
    additional_skills: Optional[str] = typer.Option(
        None,
        "--additional-skills",
        "-a",
        help="Additional/preferred skills (comma-separated)",
    ),
    industry: Optional[str] = typer.Option(
        None,
        "--industry",
        help="Industry sector",
    ),
    work_format: Optional[str] = typer.Option(
        None,
        "--work-format",
        help="Work format (remote, office, hybrid)",
    ),
    location: Optional[str] = typer.Option(
        None,
        "--location",
        "-l",
        help="Job location",
    ),
    salary_min: Optional[int] = typer.Option(
        None,
        "--salary-min",
        help="Minimum salary",
    ),
    salary_max: Optional[int] = typer.Option(
        None,
        "--salary-max",
        help="Maximum salary",
    ),
    english_level: Optional[str] = typer.Option(
        None,
        "--english-level",
        help="Required English level",
    ),
    employment_type: Optional[str] = typer.Option(
        None,
        "--employment-type",
        help="Employment type (full-time, part-time, contract)",
    ),
):
    """
    Create a new job vacancy.

    Examples:
        Create a basic vacancy:
            agenthr vacancy create --title "Senior Developer" --description "Build amazing software" --skills "Python,React"

        Create a detailed vacancy:
            agenthr vacancy create --title "Senior Developer" --description "Build amazing software" --skills "Python,React" --min-experience 36 --work-format remote --salary-min 80000
    """
    try:
        # Get API client
        client = get_api_client()

        # Parse comma-separated skills
        skills_list = [s.strip() for s in required_skills.split(",")]
        additional_skills_list = []
        if additional_skills:
            additional_skills_list = [s.strip() for s in additional_skills.split(",")]

        # Build request payload
        payload = {
            "title": title,
            "description": description,
            "required_skills": skills_list,
        }

        # Add optional fields
        if min_experience is not None:
            payload["min_experience_months"] = min_experience
        if additional_skills_list:
            payload["additional_requirements"] = additional_skills_list
        if industry:
            payload["industry"] = industry
        if work_format:
            payload["work_format"] = work_format
        if location:
            payload["location"] = location
        if salary_min is not None:
            payload["salary_min"] = salary_min
        if salary_max is not None:
            payload["salary_max"] = salary_max
        if english_level:
            payload["english_level"] = english_level
        if employment_type:
            payload["employment_type"] = employment_type

        # Make request
        console.print("[dim]Creating vacancy...[/dim]")
        response = client.post("/api/vacancies/", json=payload)

        # Check for errors
        if response.status_code != 201:
            console.print(f"[red]✗[/red] Failed to create vacancy: {response.status_code}")
            try:
                error_data = response.json()
                console.print(f"[red]  {error_data.get('detail', 'Unknown error')}[/red]")
            except Exception:
                console.print(f"[red]  {response.text}[/red]")
            raise typer.Exit(1)

        # Parse response
        result = response.json()

        # Display success message
        console.print("[green]✓[/green] Vacancy created successfully")
        console.print(f"  [dim]ID:[/dim] {result.get('id')}")
        console.print(f"  [dim]Title:[/dim] {result.get('title')}")
        console.print(f"  [dim]Skills:[/dim] {', '.join(result.get('required_skills', []))}")

        if result.get('location'):
            console.print(f"  [dim]Location:[/dim] {result.get('location')}")
        if result.get('work_format'):
            console.print(f"  [dim]Work Format:[/dim] {result.get('work_format')}")

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


@vacancy_app.command("list")
def list_vacancies(
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum number of vacancies to display",
    ),
):
    """
    List all job vacancies.

    Examples:
        List recent vacancies:
            agenthr vacancy list

        Show more results:
            agenthr vacancy list --limit 50
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {"limit": limit, "skip": 0}

        # Make request
        response = client.get("/api/vacancies/", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to list vacancies: {response.status_code}")
            raise typer.Exit(1)

        vacancies = response.json()

        if not vacancies:
            console.print("[yellow]No vacancies found[/yellow]")
            return

        # Display table
        from ..cli import format_table

        columns = ["ID", "Title", "Location", "Work Format", "Skills", "Created"]
        rows = []
        for vacancy in vacancies:
            vacancy_id = vacancy.get("id", "")
            # Show short ID (first 8 chars)
            short_id = vacancy_id[:8] if vacancy_id else "N/A"
            title = vacancy.get("title", "unknown")[:30]
            location = vacancy.get("location", "")[:20] or "-"
            work_format = vacancy.get("work_format", "-")[:15]
            skills = ", ".join(vacancy.get("required_skills", [])[:3])
            if len(vacancy.get("required_skills", [])) > 3:
                skills += "+"
            created_at = vacancy.get("created_at", "")[:10]  # Just the date
            rows.append([short_id, title, location, work_format, skills, created_at])

        table = format_table(columns, rows, title=f"Vacancies ({len(vacancies)})")
        console.print(table)

        # Show count
        console.print(f"\n[dim]Showing {len(vacancies)} vacancies[/dim]")

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@vacancy_app.command("get")
def get_vacancy(
    vacancy_id: str = typer.Argument(
        ...,
        help="Vacancy ID (UUID)",
    ),
):
    """
    Get details of a specific vacancy.

    Examples:
        Get vacancy details:
            agenthr vacancy get 123e4567-e89b-12d3-a456-426614174000
    """
    try:
        client = get_api_client()

        response = client.get(f"/api/vacancies/{vacancy_id}")

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get vacancy: {response.status_code}")
            raise typer.Exit(1)

        vacancy = response.json()

        # Display vacancy details
        console.print(f"[bold]Vacancy Details[/bold]")
        console.print(f"  [dim]ID:[/dim] {vacancy.get('id')}")
        console.print(f"  [dim]Title:[/dim] {vacancy.get('title')}")
        console.print(f"  [dim]Description:[/dim] {vacancy.get('description')[:100]}...")
        console.print(f"  [dim]Status:[/dim] Active")
        console.print(f"  [dim]Created:[/dim] {vacancy.get('created_at')}")
        console.print(f"  [dim]Updated:[/dim] {vacancy.get('updated_at')}")

        # Show skills
        if vacancy.get("required_skills"):
            console.print(f"\n[bold]Required Skills:[/bold]")
            for skill in vacancy["required_skills"]:
                console.print(f"  • {skill}")

        # Show additional requirements
        if vacancy.get("additional_requirements"):
            console.print(f"\n[bold]Additional Requirements:[/bold]")
            for req in vacancy["additional_requirements"]:
                console.print(f"  • {req}")

        # Show job details
        console.print(f"\n[bold]Job Details:[/bold]")
        if vacancy.get("location"):
            console.print(f"  [dim]Location:[/dim] {vacancy['location']}")
        if vacancy.get("work_format"):
            console.print(f"  [dim]Work Format:[/dim] {vacancy['work_format']}")
        if vacancy.get("employment_type"):
            console.print(f"  [dim]Employment Type:[/dim] {vacancy['employment_type']}")
        if vacancy.get("min_experience_months"):
            exp_years = vacancy["min_experience_months"] // 12
            console.print(f"  [dim]Min Experience:[/dim] {exp_years}+ years")
        if vacancy.get("english_level"):
            console.print(f"  [dim]English Level:[/dim] {vacancy['english_level']}")

        # Show salary
        if vacancy.get("salary_min") or vacancy.get("salary_max"):
            salary_range = []
            if vacancy.get("salary_min"):
                salary_range.append(f"${vacancy['salary_min']:,}")
            if vacancy.get("salary_max"):
                salary_range.append(f"${vacancy['salary_max']:,}")
            console.print(f"  [dim]Salary Range:[/dim] {' - '.join(salary_range)}")

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)
