#!/usr/bin/env python3
"""
AgentHR Python Quickstart Example

This example demonstrates how to:
1. Authenticate with the AgentHR API
2. Upload a resume
3. Create a job vacancy
4. Find matching candidates
5. Move candidates through the hiring pipeline

Requirements:
    pip install httpx pydantic

Usage:
    python python_quickstart.py --help
    python python_quickstart.py upload-resume --file resume.pdf
    python python_quickstart.py create-vacancy --title "Senior Developer"
    python python_quickstart.py find-matches --vacancy-id <id>
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


class AgentHRClient:
    """
    Simple Python client for the AgentHR API.

    This client demonstrates best practices for:
    - API key authentication
    - Error handling
    - Request/response handling
    - File uploads
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ):
        """
        Initialize the AgentHR client.

        Args:
            api_key: AgentHR API key (defaults to AGENTHR_API_KEY env var)
            base_url: Base URL of the AgentHR API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("AGENTHR_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set AGENTHR_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Create HTTP client with default headers
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=timeout,
        )

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle API response with proper error handling.

        Args:
            response: HTTP response object

        Returns:
            Response data as dictionary

        Raises:
            AgentHRAPIError: On API errors
        """
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_detail = e.response.json().get("detail", error_detail)
            except Exception:
                pass

            raise AgentHRAPIError(
                f"API request failed: {e.response.status_code} - {error_detail}"
            ) from e
        except httpx.RequestError as e:
            raise AgentHRAPIError(f"Request failed: {e}") from e

    # ===== Authentication =====

    def verify_api_key(self) -> Dict[str, Any]:
        """
        Verify that the API key is valid.

        Returns:
            API key details
        """
        response = self.client.get("/api/api-keys/me")
        return self._handle_response(response)

    # ===== Resume Operations =====

    def upload_resume(
        self,
        file_path: str,
        vacancy_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a resume file for parsing and analysis.

        Args:
            file_path: Path to the resume file (PDF, DOCX, or DOC)
            vacancy_id: Optional vacancy ID to associate with the resume

        Returns:
            Uploaded resume details including parsed data
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        # Validate file type
        valid_extensions = {".pdf", ".docx", ".doc"}
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(
                f"Invalid file type: {path.suffix}. "
                f"Supported types: {', '.join(valid_extensions)}"
            )

        # Prepare multipart upload
        files = {"file": (path.name, path.open("rb"))}
        data = {}
        if vacancy_id:
            data["vacancy_id"] = vacancy_id

        response = self.client.post(
            "/api/resumes/upload",
            files=files,
            data=data,
        )
        return self._handle_response(response)

    def list_resumes(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List all resumes with optional filtering.

        Args:
            limit: Maximum number of results
            offset: Pagination offset
            status: Filter by status (e.g., 'processing', 'completed', 'failed')

        Returns:
            List of resumes with pagination info
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        response = self.client.get("/api/resumes", params=params)
        return self._handle_response(response)

    def get_resume(self, resume_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a resume.

        Args:
            resume_id: Resume UUID

        Returns:
            Resume details including parsed data
        """
        response = self.client.get(f"/api/resumes/{resume_id}")
        return self._handle_response(response)

    # ===== Vacancy Operations =====

    def create_vacancy(
        self,
        title: str,
        description: str,
        required_skills: List[str],
        min_experience: Optional[int] = None,
        location: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new job vacancy.

        Args:
            title: Job title
            description: Job description
            required_skills: List of required skills
            min_experience: Minimum years of experience
            location: Job location
            salary_min: Minimum salary
            salary_max: Maximum salary

        Returns:
            Created vacancy details
        """
        payload = {
            "title": title,
            "description": description,
            "required_skills": required_skills,
        }

        # Add optional fields
        if min_experience is not None:
            payload["min_experience"] = min_experience
        if location:
            payload["location"] = location
        if salary_min is not None:
            payload["salary_min"] = salary_min
        if salary_max is not None:
            payload["salary_max"] = salary_max

        response = self.client.post("/api/vacancies", json=payload)
        return self._handle_response(response)

    def list_vacancies(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List all job vacancies.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of vacancies with pagination info
        """
        params = {"limit": limit, "offset": offset}
        response = self.client.get("/api/vacancies", params=params)
        return self._handle_response(response)

    def get_vacancy(self, vacancy_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a vacancy.

        Args:
            vacancy_id: Vacancy UUID

        Returns:
            Vacancy details
        """
        response = self.client.get(f"/api/vacancies/{vacancy_id}")
        return self._handle_response(response)

    # ===== Candidate Operations =====

    def list_candidates(
        self,
        vacancy_id: Optional[str] = None,
        stage: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List candidates with optional filtering.

        Args:
            vacancy_id: Filter by vacancy ID
            stage: Filter by workflow stage
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of candidates with pagination info
        """
        params = {"limit": limit, "offset": offset}
        if vacancy_id:
            params["vacancy_id"] = vacancy_id
        if stage:
            params["stage"] = stage

        response = self.client.get("/api/candidates", params=params)
        return self._handle_response(response)

    def move_candidate(
        self,
        candidate_id: str,
        stage_id: str,
        vacancy_id: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Move a candidate to a different workflow stage.

        Args:
            candidate_id: Candidate (resume) UUID
            stage_id: Target stage ID (e.g., 'screening', 'interview')
            vacancy_id: Vacancy UUID
            notes: Optional notes about the move

        Returns:
            Move operation result
        """
        payload = {
            "stage_id": stage_id,
            "vacancy_id": vacancy_id,
        }
        if notes:
            payload["notes"] = notes

        response = self.client.put(
            f"/api/candidates/{candidate_id}/stage",
            json=payload,
        )
        return self._handle_response(response)

    # ===== Matching Operations =====

    def find_matches(
        self,
        vacancy_id: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Find candidates matching a vacancy using AI-powered ranking.

        Args:
            vacancy_id: Vacancy UUID
            limit: Maximum number of matches to return

        Returns:
            List of ranked candidate matches
        """
        params = {"limit": limit}
        response = self.client.get(
            f"/api/vacancies/{vacancy_id}/matches",
            params=params,
        )
        return self._handle_response(response)

    def rank_candidate(
        self,
        vacancy_id: str,
        resume_id: str,
    ) -> Dict[str, Any]:
        """
        Get AI-powered ranking score for a candidate against a vacancy.

        Args:
            vacancy_id: Vacancy UUID
            resume_id: Resume UUID

        Returns:
            Ranking results with score and explanation
        """
        response = self.client.post(
            "/api/ranking/rank",
            params={
                "vacancy_id": vacancy_id,
                "resume_id": resume_id,
            },
        )
        return self._handle_response(response)

    # ===== Analytics Operations =====

    def get_key_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get key recruitment metrics.

        Args:
            start_date: Start date (ISO 8601 format)
            end_date: End date (ISO 8601 format)

        Returns:
            Key metrics including time-to-hire, conversion rates
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = self.client.get("/api/analytics/key-metrics", params=params)
        return self._handle_response(response)


class AgentHRAPIError(Exception):
    """Exception raised for API errors."""

    pass


# ===== CLI Interface =====

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AgentHR Python Quickstart Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify API key
  python python_quickstart.py verify

  # Upload a resume
  python python_quickstart.py upload-resume --file resume.pdf

  # Create a vacancy
  python python_quickstart.py create-vacancy \\
    --title "Senior Python Developer" \\
    --skills "Python, FastAPI, PostgreSQL" \\
    --description "We are looking for..."

  # List all vacancies
  python python_quickstart.py list-vacancies

  # Find matching candidates
  python python_quickstart.py find-matches --vacancy-id <uuid>

  # Move a candidate
  python python_quickstart.py move-candidate \\
    --candidate-id <uuid> \\
    --stage interview \\
    --vacancy-id <uuid>
        """,
    )

    parser.add_argument(
        "--api-key",
        help="AgentHR API key (defaults to AGENTHR_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the AgentHR API (default: http://localhost:8000)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Verify command
    subparsers.add_parser("verify", help="Verify API key")

    # Upload resume command
    upload_parser = subparsers.add_parser("upload-resume", help="Upload a resume file")
    upload_parser.add_argument("--file", required=True, help="Path to resume file")
    upload_parser.add_argument("--vacancy-id", help="Optional vacancy ID")

    # List resumes command
    list_resumes_parser = subparsers.add_parser("list-resumes", help="List all resumes")
    list_resumes_parser.add_argument("--limit", type=int, default=50, help="Max results")
    list_resumes_parser.add_argument("--status", help="Filter by status")

    # Create vacancy command
    vacancy_parser = subparsers.add_parser("create-vacancy", help="Create a job vacancy")
    vacancy_parser.add_argument("--title", required=True, help="Job title")
    vacancy_parser.add_argument(
        "--skills",
        required=True,
        help="Comma-separated required skills",
    )
    vacancy_parser.add_argument(
        "--description",
        required=True,
        help="Job description",
    )
    vacancy_parser.add_argument("--location", help="Job location")
    vacancy_parser.add_argument(
        "--min-experience",
        type=int,
        help="Minimum years of experience",
    )

    # List vacancies command
    list_vacancies_parser = subparsers.add_parser(
        "list-vacancies",
        help="List all vacancies",
    )
    list_vacancies_parser.add_argument("--limit", type=int, default=50)

    # Find matches command
    matches_parser = subparsers.add_parser(
        "find-matches",
        help="Find candidates matching a vacancy",
    )
    matches_parser.add_argument("--vacancy-id", required=True, help="Vacancy UUID")
    matches_parser.add_argument("--limit", type=int, default=10)

    # Move candidate command
    move_parser = subparsers.add_parser(
        "move-candidate",
        help="Move candidate to a new stage",
    )
    move_parser.add_argument("--candidate-id", required=True, help="Candidate UUID")
    move_parser.add_argument("--stage", required=True, help="Target stage ID")
    move_parser.add_argument("--vacancy-id", required=True, help="Vacancy UUID")
    move_parser.add_argument("--notes", help="Optional notes")

    # Metrics command
    metrics_parser = subparsers.add_parser(
        "metrics",
        help="Get key recruitment metrics",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Create client
    try:
        with AgentHRClient(
            api_key=args.api_key,
            base_url=args.base_url,
        ) as client:
            # Execute command
            if args.command == "verify":
                result = client.verify_api_key()
                print("API Key verified successfully!")
                print(f"Key: {result.get('key_prefix', 'N/A')}***")

            elif args.command == "upload-resume":
                result = client.upload_resume(
                    file_path=args.file,
                    vacancy_id=args.vacancy_id,
                )
                print("Resume uploaded successfully!")
                print(f"ID: {result.get('id')}")
                print(f"Filename: {result.get('filename')}")
                if result.get("parsed_data"):
                    data = result["parsed_data"]
                    print(f"Name: {data.get('name', 'N/A')}")
                    print(f"Email: {data.get('email', 'N/A')}")
                    print(f"Skills: {', '.join(data.get('skills', []))}")

            elif args.command == "list-resumes":
                result = client.list_resumes(
                    limit=args.limit,
                    status=args.status,
                )
                resumes = result.get("items", [])
                print(f"\nTotal resumes: {result.get('total', 0)}\n")
                for resume in resumes:
                    print(f"  {resume['id'][:8]}... | {resume['filename']} | {resume.get('status', 'N/A')}")

            elif args.command == "create-vacancy":
                skills = [s.strip() for s in args.skills.split(",")]
                result = client.create_vacancy(
                    title=args.title,
                    description=args.description,
                    required_skills=skills,
                    location=args.location,
                    min_experience=args.min_experience,
                )
                print("Vacancy created successfully!")
                print(f"ID: {result.get('id')}")
                print(f"Title: {result.get('title')}")

            elif args.command == "list-vacancies":
                result = client.list_vacancies(limit=args.limit)
                vacancies = result.get("items", [])
                print(f"\nTotal vacancies: {result.get('total', 0)}\n")
                for vacancy in vacancies:
                    skills = vacancy.get("required_skills", [])[:3]
                    skills_str = ", ".join(skills)
                    if len(vacancy.get("required_skills", [])) > 3:
                        skills_str += "..."
                    print(f"  {vacancy['id'][:8]}... | {vacancy['title']} | {skills_str}")

            elif args.command == "find-matches":
                result = client.find_matches(
                    vacancy_id=args.vacancy_id,
                    limit=args.limit,
                )
                matches = result.get("matches", [])
                print(f"\nFound {len(matches)} matches:\n")
                for match in matches:
                    print(f"  Score: {match.get('score', 0):.1%}")
                    print(f"  Name: {match.get('name', 'N/A')}")
                    print(f"  Skills: {', '.join(match.get('skills', [])[:5])}")
                    print()

            elif args.command == "move-candidate":
                result = client.move_candidate(
                    candidate_id=args.candidate_id,
                    stage_id=args.stage,
                    vacancy_id=args.vacancy_id,
                    notes=args.notes,
                )
                print("Candidate moved successfully!")
                print(f"Previous stage: {result.get('previous_stage', 'N/A')}")
                print(f"New stage: {result.get('new_stage', 'N/A')}")

            elif args.command == "metrics":
                result = client.get_key_metrics()
                print("Key Recruitment Metrics:")
                print(f"  Time to Hire: {result.get('time_to_hire_days', 'N/A')} days")
                print(f"  Resumes Processed: {result.get('resumes_processed', 0)}")
                print(f"  Match Rate: {result.get('match_rate', 0):.1%}")

    except AgentHRAPIError as e:
        print(f"API Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
