"""
AgentHR CLI - Analytics commands.

This module provides commands for querying and analyzing recruitment data via the CLI.
"""
from typing import Optional

import httpx
import typer
from rich.console import Console

from ..cli import APIError, ConfigError, get_api_client, format_table

console = Console()

analytics_app = typer.Typer(
    name="analytics",
    help="Analytics and reporting commands",
    add_completion=False,
)


@analytics_app.command("key-metrics")
def get_key_metrics(
    start_date: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start date filter (ISO 8601 format)",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End date filter (ISO 8601 format)",
    ),
):
    """
    Get key recruitment analytics metrics.

    This command provides essential metrics for monitoring recruitment performance,
    including time-to-hire statistics, resume processing metrics, and skill match rates.

    Examples:
        Get key metrics:
            agenthr analytics key-metrics

        Get metrics for a date range:
            agenthr analytics key-metrics --start 2024-01-01 --end 2024-01-31
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Make request
        response = client.get("/api/analytics/key-metrics", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get key metrics: {response.status_code}")
            raise typer.Exit(1)

        data = response.json()

        # Display time-to-hire metrics
        console.print("\n[bold]Time-to-Hire Metrics[/bold]")
        tth = data.get("time_to_hire", {})
        console.print(f"  [dim]Average:[/dim] {tth.get('average_days', 0):.1f} days")
        console.print(f"  [dim]Median:[/dim] {tth.get('median_days', 0):.1f} days")
        console.print(f"  [dim]Range:[/dim] {tth.get('min_days', 0)} - {tth.get('max_days', 0)} days")
        console.print(f"  [dim]25th percentile:[/dim] {tth.get('percentile_25', 0):.1f} days")
        console.print(f"  [dim]75th percentile:[/dim] {tth.get('percentile_75', 0):.1f} days")

        # Display resume metrics
        console.print("\n[bold]Resume Processing Metrics[/bold]")
        resumes = data.get("resumes", {})
        console.print(f"  [dim]Total processed:[/dim] {resumes.get('total_processed', 0)}")
        console.print(f"  [dim]This month:[/dim] {resumes.get('processed_this_month', 0)}")
        console.print(f"  [dim]This week:[/dim] {resumes.get('processed_this_week', 0)}")
        console.print(f"  [dim]Avg rate:[/dim] {resumes.get('processing_rate_avg', 0):.1f} resumes/day")

        # Display match rate metrics
        console.print("\n[bold]Match Rate Metrics[/bold]")
        matches = data.get("match_rates", {})
        console.print(f"  [dim]Overall match rate:[/dim] {matches.get('overall_match_rate', 0):.1%}")
        console.print(f"  [dim]High confidence matches:[/dim] {matches.get('high_confidence_matches', 0)}")
        console.print(f"  [dim]Low confidence matches:[/dim] {matches.get('low_confidence_matches', 0)}")
        console.print(f"  [dim]Avg confidence:[/dim] {matches.get('average_confidence', 0):.1%}")

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@analytics_app.command("quality-metrics")
def get_quality_metrics(
    start_date: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start date filter (ISO 8601 format)",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End date filter (ISO 8601 format)",
    ),
):
    """
    Get ML/NLP model quality metrics.

    This command provides metrics about the quality and performance of the ML/NLP models
    used in resume analysis, including text extraction, NER, keyword extraction, and matching.

    Examples:
        Get quality metrics:
            agenthr analytics quality-metrics

        Get metrics for a date range:
            agenthr analytics quality-metrics --start 2024-01-01 --end 2024-01-31
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Make request
        response = client.get("/api/analytics/quality-metrics", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get quality metrics: {response.status_code}")
            raise typer.Exit(1)

        data = response.json()

        # Display text extraction metrics
        console.print("\n[bold]Text Extraction Metrics[/bold]")
        console.print(f"  [dim]Success rate:[/dim] {data.get('text_extraction_success_rate', 0):.1%}")
        console.print(f"  [dim]Avg extraction time:[/dim] {data.get('avg_extraction_time_seconds', 0):.1f}s")

        # Display NER metrics
        console.print("\n[bold]Named Entity Recognition Metrics[/bold]")
        console.print(f"  [dim]NER accuracy:[/dim] {data.get('ner_accuracy', 0):.1%}")
        console.print(f"  [dim]Avg entities per resume:[/dim] {data.get('entities_per_resume_avg', 0):.1f}")

        # Display keyword metrics
        console.print("\n[bold]Keyword Extraction Metrics[/bold]")
        console.print(f"  [dim]Avg keywords per resume:[/dim] {data.get('avg_keywords_per_resume', 0):.1f}")
        console.print(f"  [dim]Avg keyword relevance:[/dim] {data.get('keyword_relevance_avg', 0):.1%}")

        # Display grammar metrics
        console.print("\n[bold]Grammar Metrics[/bold]")
        console.print(f"  [dim]Grammar error rate:[/dim] {data.get('grammar_error_rate', 0):.1%}")

        # Display matching metrics
        console.print("\n[bold]Matching Metrics[/bold]")
        console.print(f"  [dim]Avg matching confidence:[/dim] {data.get('matching_confidence_avg', 0):.1%}")
        console.print(f"  [dim]Matching precision:[/dim] {data.get('matching_precision', 0):.1%}")
        console.print(f"  [dim]Matching recall:[/dim] {data.get('matching_recall', 0):.1%}")

        # Display performance metrics
        console.print("\n[bold]Performance Metrics[/bold]")
        console.print(f"  [dim]Avg analysis time:[/dim] {data.get('avg_analysis_time_seconds', 0):.1f}s")
        console.print(f"  [dim]Error rate:[/dim] {data.get('error_rate', 0):.1%}")
        console.print(f"  [dim]Total analyzed:[/dim] {data.get('total_analyzed', 0)}")

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@analytics_app.command("funnel")
def get_funnel_metrics(
    start_date: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start date filter (ISO 8601 format)",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End date filter (ISO 8601 format)",
    ),
):
    """
    Get hiring funnel visualization metrics.

    This command provides a visual representation of the hiring funnel, showing
    the number of candidates at each stage and conversion rates between stages.

    Examples:
        Get funnel metrics:
            agenthr analytics funnel

        Get metrics for a date range:
            agenthr analytics funnel --start 2024-01-01 --end 2024-01-31
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Make request
        response = client.get("/api/analytics/funnel", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get funnel metrics: {response.status_code}")
            raise typer.Exit(1)

        data = response.json()

        stages = data.get("stages", [])
        total_candidates = data.get("total_candidates", 0)

        if not stages:
            console.print("[yellow]No funnel data available[/yellow]")
            return

        # Display table
        columns = ["Stage", "Count", "Conv from Prev", "Conv from Start"]
        rows = []
        for stage in stages:
            stage_name = stage.get("stage_name", "unknown")
            count = stage.get("count", 0)

            conv_prev = stage.get("conversion_rate_from_previous")
            conv_prev_str = f"{conv_prev:.1%}" if conv_prev is not None else "N/A"

            conv_start = stage.get("conversion_rate_from_start", 0)
            conv_start_str = f"{conv_start:.1%}"

            rows.append([stage_name, str(count), conv_prev_str, conv_start_str])

        table = format_table(columns, rows, title=f"Hiring Funnel ({total_candidates} total)")
        console.print(table)

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@analytics_app.command("stage-duration")
def get_stage_duration_metrics(
    start_date: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start date filter (ISO 8601 format)",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End date filter (ISO 8601 format)",
    ),
):
    """
    Get stage duration analytics metrics.

    This command provides metrics about how long candidates spend in each hiring stage,
    helping identify bottlenecks in the recruitment process.

    Examples:
        Get stage duration metrics:
            agenthr analytics stage-duration

        Get metrics for a date range:
            agenthr analytics stage-duration --start 2024-01-01 --end 2024-01-31
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Make request
        response = client.get("/api/analytics/stage-duration", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get stage duration metrics: {response.status_code}")
            raise typer.Exit(1)

        data = response.json()

        stages = data.get("stages", [])

        if not stages:
            console.print("[yellow]No stage duration data available[/yellow]")
            return

        # Display table
        columns = ["Stage", "Avg Days", "Median Days", "Min Days", "Max Days", "Candidates"]
        rows = []
        for stage in stages:
            stage_name = stage.get("stage_name", "unknown")
            avg_days = f"{stage.get('average_days', 0):.1f}"
            median_days = f"{stage.get('median_days', 0):.1f}"
            min_days = f"{stage.get('min_days', 0):.1f}"
            max_days = f"{stage.get('max_days', 0):.1f}"
            candidate_count = str(stage.get("candidate_count", 0))

            rows.append([stage_name, avg_days, median_days, min_days, max_days, candidate_count])

        table = format_table(columns, rows, title=f"Stage Duration Metrics ({len(stages)} stages)")
        console.print(table)

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@analytics_app.command("skill-demand")
def get_skill_demand(
    start_date: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start date filter (ISO 8601 format)",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End date filter (ISO 8601 format)",
    ),
    limit: int = typer.Option(
        15,
        "--limit",
        "-l",
        help="Maximum number of skills to display",
    ),
):
    """
    Get skill demand analytics.

    This command provides analytics about the most in-demand skills across job postings,
    helping understand market trends and adjust job requirements accordingly.

    Examples:
        Get skill demand:
            agenthr analytics skill-demand

        Get top 20 skills:
            agenthr analytics skill-demand --limit 20

        Get metrics for a date range:
            agenthr analytics skill-demand --start 2024-01-01 --end 2024-01-31
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Make request
        response = client.get("/api/analytics/skill-demand", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get skill demand: {response.status_code}")
            raise typer.Exit(1)

        data = response.json()

        skills = data.get("skills", [])
        total_postings = data.get("total_postings_analyzed", 0)

        if not skills:
            console.print("[yellow]No skill demand data available[/yellow]")
            return

        # Display table
        columns = ["Skill", "Demand Count", "Demand %", "Trend"]
        rows = []
        for skill in skills:
            skill_name = skill.get("skill_name", "unknown")
            demand_count = str(skill.get("demand_count", 0))
            demand_pct = f"{skill.get('demand_percentage', 0):.1f}%"
            trend = skill.get("trend") or "N/A"

            # Add trend indicator
            if trend == "up":
                trend_str = "[green]↑[/green]"
            elif trend == "down":
                trend_str = "[red]↓[/red]"
            elif trend == "stable":
                trend_str = "[blue]→[/blue]"
            else:
                trend_str = "N/A"

            rows.append([skill_name, demand_count, demand_pct, trend_str])

        table = format_table(columns, rows, title=f"Skill Demand ({total_postings} postings analyzed)")
        console.print(table)

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@analytics_app.command("source-tracking")
def get_source_tracking(
    start_date: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start date filter (ISO 8601 format)",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End date filter (ISO 8601 format)",
    ),
):
    """
    Get candidate source tracking analytics.

    This command provides analytics about where candidates are coming from,
    including sources like referrals, LinkedIn, company website, job boards, etc.

    Examples:
        Get source tracking:
            agenthr analytics source-tracking

        Get metrics for a date range:
            agenthr analytics source-tracking --start 2024-01-01 --end 2024-01-31
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Make request
        response = client.get("/api/analytics/source-tracking", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get source tracking: {response.status_code}")
            raise typer.Exit(1)

        data = response.json()

        sources = data.get("sources", [])
        total_candidates = data.get("total_candidates", 0)

        if not sources:
            console.print("[yellow]No source tracking data available[/yellow]")
            return

        # Display table
        columns = ["Source", "Candidates", "Hired", "Conv Rate"]
        rows = []
        for source in sources:
            source_name = source.get("source", "unknown")
            candidate_count = str(source.get("candidate_count", 0))
            hired_count = str(source.get("hired_count", 0))
            conv_rate = f"{source.get('conversion_rate', 0):.1%}"

            rows.append([source_name, candidate_count, hired_count, conv_rate])

        table = format_table(columns, rows, title=f"Source Tracking ({total_candidates} total candidates)")
        console.print(table)

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@analytics_app.command("recruiter-performance")
def get_recruiter_performance(
    start_date: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start date filter (ISO 8601 format)",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End date filter (ISO 8601 format)",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of recruiters to display",
    ),
):
    """
    Get recruiter performance metrics.

    This command provides performance analytics for individual recruiters,
    including hires, interviews conducted, resumes processed, and placement rates.

    Examples:
        Get recruiter performance:
            agenthr analytics recruiter-performance

        Get top 20 recruiters:
            agenthr analytics recruiter-performance --limit 20

        Get metrics for a date range:
            agenthr analytics recruiter-performance --start 2024-01-01 --end 2024-01-31
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Make request
        response = client.get("/api/analytics/recruiter-performance", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get recruiter performance: {response.status_code}")
            raise typer.Exit(1)

        data = response.json()

        recruiters = data.get("recruiters", [])

        if not recruiters:
            console.print("[yellow]No recruiter performance data available[/yellow]")
            return

        # Display table
        columns = ["Name", "Hires", "Interviews", "Resumes", "Avg TTH", "Placement Rate"]
        rows = []
        for recruiter in recruiters:
            name = recruiter.get("recruiter_name", "unknown")[:25]
            hires = str(recruiter.get("hires", 0))
            interviews = str(recruiter.get("interviews_conducted", 0))
            resumes = str(recruiter.get("resumes_processed", 0))
            avg_tth = f"{recruiter.get('average_time_to_hire_days', 0):.0f}d"
            placement_rate = f"{recruiter.get('placement_rate', 0):.1%}"

            rows.append([name, hires, interviews, resumes, avg_tth, placement_rate])

        table = format_table(columns, rows, title=f"Recruiter Performance ({len(recruiters)} recruiters)")
        console.print(table)

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@analytics_app.command("taxonomy-usage")
def get_taxonomy_usage(
    industry: Optional[str] = typer.Option(
        None,
        "--industry",
        "-i",
        help="Filter by industry",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of taxonomies to display",
    ),
):
    """
    Get taxonomy usage analytics.

    This command provides analytics about industry taxonomy usage,
    including which taxonomies are most used and most effective.

    Examples:
        Get taxonomy usage:
            agenthr analytics taxonomy-usage

        Get usage for a specific industry:
            agenthr analytics taxonomy-usage --industry Technology

        Get top 20 taxonomies:
            agenthr analytics taxonomy-usage --limit 20
    """
    try:
        client = get_api_client()

        # Build query parameters
        params = {"limit": limit}
        if industry:
            params["industry"] = industry

        # Make request
        response = client.get("/api/analytics/taxonomy-usage", params=params)

        if response.status_code != 200:
            console.print(f"[red]✗[/red] Failed to get taxonomy usage: {response.status_code}")
            raise typer.Exit(1)

        data = response.json()

        most_used = data.get("most_used_taxonomies", [])
        most_effective = data.get("most_effective_taxonomies", [])
        total_taxonomies = data.get("total_taxonomies_analyzed", 0)
        industry_filter = data.get("industry_filter")

        if not most_used and not most_effective:
            console.print("[yellow]No taxonomy usage data available[/yellow]")
            return

        # Display filter info
        if industry_filter:
            console.print(f"[dim]Industry filter: {industry_filter}[/dim]\n")
        console.print(f"[dim]Total taxonomies analyzed: {total_taxonomies}[/dim]\n")

        # Display most used taxonomies
        if most_used:
            console.print("[bold]Most Used Taxonomies:[/bold]")
            columns = ["Name", "Usage Count", "Avg Match", "Success Rate", "Candidates"]
            rows = []
            for taxonomy in most_used:
                name = taxonomy.get("taxonomy_name", "unknown")[:30]
                usage_count = str(taxonomy.get("usage_count", 0))
                avg_match = f"{taxonomy.get('avg_match_score', 0):.1f}"
                success_rate = f"{taxonomy.get('success_rate', 0):.1%}"
                candidates = str(taxonomy.get("total_candidates_matched", 0))

                rows.append([name, usage_count, avg_match, success_rate, candidates])

            table = format_table(columns, rows, title="Most Used")
            console.print(table)
            console.print()

        # Display most effective taxonomies
        if most_effective:
            console.print("[bold]Most Effective Taxonomies:[/bold]")
            columns = ["Name", "Usage Count", "Avg Match", "Success Rate", "Candidates"]
            rows = []
            for taxonomy in most_effective:
                name = taxonomy.get("taxonomy_name", "unknown")[:30]
                usage_count = str(taxonomy.get("usage_count", 0))
                avg_match = f"{taxonomy.get('avg_match_score', 0):.1f}"
                success_rate = f"{taxonomy.get('success_rate', 0):.1%}"
                candidates = str(taxonomy.get("total_candidates_matched", 0))

                rows.append([name, usage_count, avg_match, success_rate, candidates])

            table = format_table(columns, rows, title="Most Effective")
            console.print(table)

    except ConfigError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)
