#!/usr/bin/env python3
"""
Manual LLM Provider Integration Testing Script

This script tests the InterviewQuestionGenerator with each configured LLM provider.
It makes actual API calls and verifies that questions are generated correctly.

Usage:
  1. Set up API keys in environment or backend/.env file:
     - OPENAI_API_KEY for OpenAI
     - ANTHROPIC_API_KEY for Anthropic
     - GOOGLE_API_KEY for Google
     - ZAI_API_KEY for Z.ai

  2. Run from backend directory:
     python test_llm_providers.py

  3. To test specific providers:
     python test_llm_providers.py --providers openai anthropic
     python test_llm_providers.py --providers all

Options:
  --providers: Comma-separated list of providers to test (openai,anthropic,google,zai,all)
  --verbose: Show detailed question output
  --save: Save results to JSON file

Example:
  python test_llm_providers.py --providers openai,anthropic --verbose --save results.json
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analyzers.interview_question_generator import (
    InterviewQuestionGenerator,
    LLMProvider,
)


# Sample resume and job data for testing
SAMPLE_RESUME = """
John Doe
Senior Python Developer

Experience:
- Senior Python Developer at Tech Corp (2020-Present)
  - Developed RESTful APIs using FastAPI and Django
  - Worked with PostgreSQL and Redis databases
  - Led a team of 3 developers
  - Implemented CI/CD pipelines with Jenkins

- Python Developer at Startup Inc (2018-2020)
  - Built web applications using Django and Flask
  - Integrated with third-party APIs (Stripe, AWS S3)
  - Implemented unit tests with pytest
  - Optimized database queries reducing response time by 40%

Skills:
- Programming: Python, JavaScript, SQL, TypeScript
- Frameworks: Django, FastAPI, Flask, React
- Databases: PostgreSQL, MongoDB, Redis
- Tools: Docker, Kubernetes, Git, AWS, Jenkins
- Concepts: REST APIs, Microservices, CI/CD

Education:
- BS Computer Science, University of Technology (2018)
- AWS Certified Developer Associate (2022)
"""

SAMPLE_JOB_TITLE = "Senior Python Developer"

SAMPLE_JOB_DESCRIPTION = """
We are looking for a Senior Python Developer to join our growing team.

Position Overview:
You will be responsible for designing and implementing scalable backend services,
mentoring junior developers, and collaborating with our frontend team to deliver
high-quality software solutions.

Requirements:
- 5+ years of professional Python development experience
- Strong experience with Django or FastAPI frameworks
- Experience with relational databases (PostgreSQL preferred)
- Knowledge of RESTful API design and microservices architecture
- Experience with cloud platforms (AWS/GCP)
- Team leadership or mentoring experience
- Familiarity with containerization (Docker/Kubernetes)
- Understanding of CI/CD best practices

Responsibilities:
- Design and implement robust backend services
- Write clean, maintainable, and well-tested code
- Mentor junior developers and conduct code reviews
- Collaborate with cross-functional teams
- Optimize application performance and scalability
- Participate in architectural decisions

Benefits:
- Competitive salary and equity
- Remote work flexibility
- Professional development budget
- Health insurance
"""

SAMPLE_REQUIRED_SKILLS = [
    "Python", "Django", "FastAPI", "PostgreSQL", "AWS",
    "REST APIs", "Microservices", "Docker", "Git", "CI/CD"
]

SAMPLE_CANDIDATE_SKILLS = [
    "Python", "JavaScript", "Django", "FastAPI", "Flask",
    "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes",
    "Git", "AWS", "Jenkins", "REST APIs", "Microservices"
]

SAMPLE_SKILL_GAPS = ["Team Leadership", "Kubernetes"]


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def has_api_key(provider: str) -> bool:
    """Check if API key is configured for a provider."""
    env_keys = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "zai": "ZAI_API_KEY",
    }
    return bool(os.getenv(env_keys.get(provider, "")))


def verify_question_structure(question: Dict[str, Any], category: str) -> bool:
    """
    Verify that a question has the correct structure.

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["id", "text", "category", "difficulty", "skills", "rationale"]

    for field in required_fields:
        if field not in question:
            print_error(f"{category} question missing field: {field}")
            return False

    # Verify field types
    if not isinstance(question["text"], str) or len(question["text"]) == 0:
        print_error(f"{category} question has invalid text field")
        return False

    if not isinstance(question["skills"], list):
        print_error(f"{category} question has invalid skills field")
        return False

    if question["difficulty"] not in ["beginner", "intermediate", "advanced"]:
        print_error(f"{category} question has invalid difficulty: {question['difficulty']}")
        return False

    return True


def display_questions(questions: List[Dict[str, Any]], category: str, verbose: bool = False) -> None:
    """
    Display questions in a formatted way.

    Args:
        questions: List of question dictionaries
        category: Category name for display
        verbose: Whether to show full details
    """
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{category.upper()} QUESTIONS ({len(questions)}){Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'─' * 80}{Colors.ENDC}")

    for i, question in enumerate(questions, 1):
        print(f"\n{Colors.BOLD}Q{i}: {question['text'][:80]}...{Colors.ENDC}" if len(question['text']) > 80 else f"\n{Colors.BOLD}Q{i}: {question['text']}{Colors.ENDC}")
        print(f"  Difficulty: {question['difficulty']} | Skills: {', '.join(question['skills'][:5])}")

        if verbose:
            print(f"  ID: {question['id']}")
            print(f"  Rationale: {question['rationale'][:100]}...")
            if question.get('expected_answers'):
                print(f"  Expected Answers: {', '.join(question['expected_answers'][:3])}")
            if question.get('follow_up_suggestions'):
                print(f"  Follow-ups: {', '.join(question['follow_up_suggestions'][:2])}")


async def test_provider(
    provider: str,
    model: str,
    verbose: bool = False,
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Test a single LLM provider.

    Args:
        provider: Provider name
        model: Model name
        verbose: Whether to show detailed output
        save_path: Optional path to save results

    Returns:
        Test results dictionary
    """
    print_header(f"Testing {provider.upper()} Provider")

    results = {
        "provider": provider,
        "model": model,
        "success": False,
        "error": None,
        "total_questions": 0,
        "categories": {},
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        print_info(f"Initializing {provider.upper()} generator with model: {model}")

        generator = InterviewQuestionGenerator(
            provider=LLMProvider(provider),
            model=model
        )

        print_info("Generating interview questions...")
        print_info("This may take 10-30 seconds depending on the provider...")

        start_time = datetime.utcnow()

        result = await generator.generate_questions(
            resume_text=SAMPLE_RESUME,
            job_title=SAMPLE_JOB_TITLE,
            job_description=SAMPLE_JOB_DESCRIPTION,
            required_skills=SAMPLE_REQUIRED_SKILLS,
            candidate_skills=SAMPLE_CANDIDATE_SKILLS,
            skill_gaps=SAMPLE_SKILL_GAPS,
            seniority_level="senior"
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print_success(f"Questions generated in {duration:.2f} seconds")

        # Convert to dictionaries for easier handling
        technical_questions = [q.to_dict() for q in result.technical_questions]
        behavioral_questions = [q.to_dict() for q in result.behavioral_questions]
        situational_questions = [q.to_dict() for q in result.situational_questions]
        skill_verification_questions = [q.to_dict() for q in result.skill_verification_questions]

        # Verify structure
        all_valid = True
        for question in technical_questions:
            if not verify_question_structure(question, "Technical"):
                all_valid = False

        for question in behavioral_questions:
            if not verify_question_structure(question, "Behavioral"):
                all_valid = False

        for question in situational_questions:
            if not verify_question_structure(question, "Situational"):
                all_valid = False

        for question in skill_verification_questions:
            if not verify_question_structure(question, "Skill Verification"):
                all_valid = False

        if not all_valid:
            raise ValueError("Some questions have invalid structure")

        # Update results
        results["success"] = True
        results["total_questions"] = len(result.questions)
        results["categories"] = {
            "technical": len(technical_questions),
            "behavioral": len(behavioral_questions),
            "situational": len(situational_questions),
            "skill_verification": len(skill_verification_questions),
        }
        results["areas_to_probe"] = result.areas_to_probe
        results["skill_gaps_to_address"] = result.skill_gaps_to_address
        results["interview_tips"] = result.interview_tips
        results["duration_seconds"] = duration

        # Display summary
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}GENERATION SUCCESSFUL{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{'=' * 80}{Colors.ENDC}\n")

        print(f"{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  Total Questions: {len(result.questions)}")
        print(f"  Technical Questions: {len(technical_questions)}")
        print(f"  Behavioral Questions: {len(behavioral_questions)}")
        print(f"  Situational Questions: {len(situational_questions)}")
        print(f"  Skill Verification Questions: {len(skill_verification_questions)}")
        print(f"  Areas to Probe: {len(result.areas_to_probe)}")
        print(f"  Skill Gaps to Address: {len(result.skill_gaps_to_address)}")
        print(f"  Interview Tips: {len(result.interview_tips)}")
        print(f"  Generation Time: {duration:.2f} seconds")

        # Display questions
        if verbose:
            display_questions(technical_questions, "Technical", verbose)
            display_questions(behavioral_questions, "Behavioral", verbose)
            display_questions(situational_questions, "Situational", verbose)
            display_questions(skill_verification_questions, "Skill Verification", verbose)

            if result.areas_to_probe:
                print(f"\n{Colors.BOLD}AREAS TO PROBE:{Colors.ENDC}")
                for area in result.areas_to_probe[:5]:
                    print(f"  • {area}")

            if result.skill_gaps_to_address:
                print(f"\n{Colors.BOLD}SKILL GAPS TO ADDRESS:{Colors.ENDC}")
                for gap in result.skill_gaps_to_address[:5]:
                    print(f"  • {gap}")

            if result.interview_tips:
                print(f"\n{Colors.BOLD}INTERVIEW TIPS:{Colors.ENDC}")
                for tip in result.interview_tips[:5]:
                    print(f"  • {tip}")

        # Save results if requested
        if save_path:
            output_data = {
                "metadata": {
                    "provider": provider,
                    "model": model,
                    "generated_at": result.generated_at,
                    "duration_seconds": duration,
                },
                "questions": {
                    "technical": technical_questions,
                    "behavioral": behavioral_questions,
                    "situational": situational_questions,
                    "skill_verification": skill_verification_questions,
                },
                "areas_to_probe": result.areas_to_probe,
                "skill_gaps_to_address": result.skill_gaps_to_address,
                "interview_tips": result.interview_tips,
            }

            file_path = Path(save_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print_success(f"Results saved to: {file_path}")

        print_success(f"{provider.upper()} provider test PASSED")

    except Exception as e:
        results["error"] = str(e)
        print_error(f"{provider.upper()} provider test FAILED: {e}")
        import traceback
        if verbose:
            traceback.print_exc()

    return results


async def main():
    """Main testing function."""
    parser = argparse.ArgumentParser(
        description="Test LLM provider integration for interview question generation"
    )
    parser.add_argument(
        "--providers",
        type=str,
        default="all",
        help="Comma-separated list of providers to test (openai,anthropic,google,zai,all)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed question output"
    )
    parser.add_argument(
        "--save",
        type=str,
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    print_header("LLM Provider Integration Testing")

    # Determine which providers to test
    if args.providers.lower() == "all":
        providers_to_test = ["openai", "anthropic", "google", "zai"]
    else:
        providers_to_test = [p.strip().lower() for p in args.providers.split(",")]

    # Provider configurations
    provider_configs = {
        "openai": ("gpt-4o-mini", "OpenAI"),
        "anthropic": ("claude-3-5-sonnet-20241022", "Anthropic"),
        "google": ("gemini-1.5-flash", "Google"),
        "zai": ("gpt-4o-mini", "Z.ai"),
    }

    # Check API keys
    print_info("Checking API keys...")
    available_providers = []
    missing_providers = []

    for provider in providers_to_test:
        if provider not in provider_configs:
            print_warning(f"Unknown provider: {provider}")
            continue

        if has_api_key(provider):
            available_providers.append(provider)
            print_success(f"{provider_configs[provider][1]} API key found")
        else:
            missing_providers.append(provider)
            print_error(f"{provider_configs[provider][1]} API key not found (set {provider.upper()}_API_KEY)")

    if not available_providers:
        print_error("\nNo API keys configured. Please set at least one of:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - GOOGLE_API_KEY")
        print("  - ZAI_API_KEY")
        return

    if missing_providers:
        print_warning(f"\nSkipping providers with missing API keys: {', '.join(missing_providers)}")

    print(f"\n{Colors.BOLD}Testing {len(available_providers)} provider(s): {', '.join(available_providers)}{Colors.ENDC}")

    # Run tests
    all_results = []

    for provider in available_providers:
        model, name = provider_configs[provider]

        # Determine save path for this provider
        save_path = None
        if args.save:
            base_path = Path(args.save).stem
            ext = Path(args.save).suffix
            save_path = f"{base_path}_{provider}{ext}"

        result = await test_provider(provider, model, args.verbose, save_path)
        all_results.append(result)

    # Print final summary
    print_header("TEST SUMMARY")

    successful = sum(1 for r in all_results if r["success"])
    failed = len(all_results) - successful

    print(f"{Colors.BOLD}Total Tests: {len(all_results)}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Passed: {successful}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {failed}{Colors.ENDC}\n")

    for result in all_results:
        status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if result["success"] else f"{Colors.FAIL}FAIL{Colors.ENDC}"
        print(f"{result['provider'].upper():15} {status}", end="")
        if result["success"]:
            duration = result.get("duration_seconds", 0)
            questions = result["total_questions"]
            print(f" - {questions} questions in {duration:.2f}s")
        else:
            error = result.get("error", "Unknown error")[:50]
            print(f" - {error}")

    # Final verdict
    if failed == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}All tests PASSED!{Colors.ENDC}")
        print_success("LLM integration is working correctly for all tested providers")
        return 0
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Some tests FAILED{Colors.ENDC}")
        print_error("Please check the error messages above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
