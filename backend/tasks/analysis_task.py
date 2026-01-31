"""
Async resume analysis task with progress tracking.

This module provides Celery tasks for asynchronous resume analysis with
real-time progress updates. It integrates all ML/NLP analyzers and provides
status tracking throughout the analysis process.
"""
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded


def convert_numpy_types(obj: Any) -> Any:
    """
    Convert numpy types to Python native types for JSON serialization.

    This recursively converts numpy arrays, scalars, and other numpy types
    to their Python equivalents.

    Args:
        obj: Object to convert

    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

# Add parent directory to path to import from data_extractor service
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "data_extractor"))

from analyzers import (
    extract_resume_keywords_hf as extract_resume_keywords,
    extract_resume_entities,
    check_grammar_resume,
    calculate_total_experience,
    format_experience_summary,
    detect_resume_errors,
    extract_work_experience,
)
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Directory where uploaded resumes are stored
UPLOAD_DIR = Path("data/uploads")


def find_resume_file(resume_id: str) -> Path:
    """
    Find the resume file by ID.

    Args:
        resume_id: Unique identifier of the resume

    Returns:
        Path to the resume file

    Raises:
        FileNotFoundError: If resume file is not found
    """
    # Try common file extensions
    for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
        file_path = UPLOAD_DIR / f"{resume_id}{ext}"
        if file_path.exists():
            return file_path

    # If not found, raise error
    raise FileNotFoundError(f"Resume file with ID '{resume_id}' not found")


def extract_text_from_file(file_path: Path) -> str:
    """
    Extract text from resume file (PDF or DOCX).

    Args:
        file_path: Path to the resume file

    Returns:
        Extracted text content

    Raises:
        ValueError: If text extraction fails or returns empty text
    """
    try:
        # Import extraction functions
        from services.data_extractor.extract import extract_text_from_pdf, extract_text_from_docx

        file_ext = file_path.suffix.lower()

        if file_ext == ".pdf":
            result = extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            result = extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        # Check for extraction errors
        if result.get("error"):
            raise ValueError(f"Text extraction failed: {result['error']}")

        text = result.get("text", "")
        if not text or len(text.strip()) < 10:
            raise ValueError(
                "Extracted text is too short or empty. The file may be corrupted or scanned."
            )

        logger.info(f"Extracted {len(text)} characters from {file_path.name}")
        return text

    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}", exc_info=True)
        raise


def analyze_resume_core(
    resume_id: str,
    check_grammar: bool = True,
    extract_experience: bool = True,
    detect_errors: bool = True,
) -> Dict[str, Any]:
    """
    Core resume analysis logic without Celery dependencies.

    This function can be called directly or wrapped in a Celery task.

    Args:
        resume_id: Unique identifier of the resume to analyze
        check_grammar: Whether to perform grammar checking
        extract_experience: Whether to calculate experience
        detect_errors: Whether to detect resume errors

    Returns:
        Dictionary containing analysis results
    """
    start_time = time.time()

    try:
        logger.info(f"Starting core resume analysis for resume_id: {resume_id}")

        # Step 1: Find and extract text
        try:
            file_path = find_resume_file(resume_id)
        except FileNotFoundError as e:
            return {
                "resume_id": resume_id,
                "status": "failed",
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Extract text
        try:
            resume_text = extract_text_from_file(file_path)
        except ValueError as e:
            return {
                "resume_id": resume_id,
                "status": "failed",
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Detect language
        from langdetect import detect
        try:
            lang_code = detect(resume_text[:1000])
            detected_language = 'ru' if lang_code == 'ru' else 'en' if lang_code == 'en' else lang_code
        except:
            detected_language = "en"

        # Extract keywords and entities
        keywords_result = extract_resume_keywords(resume_text, language=detected_language)
        keywords = keywords_result.get("all_keywords") or keywords_result.get("keywords", [])

        entities_result = extract_resume_entities(resume_text)
        language = entities_result.get("language", detected_language)
        entities = entities_result.get("technical_skills", [])

        # Optional analysis
        grammar_result = None
        experience_result = None
        errors_result = None

        if check_grammar:
            try:
                grammar_result = check_grammar_resume(resume_text)
            except Exception as e:
                logger.warning(f"Grammar checking failed: {e}")

        if extract_experience:
            try:
                # First extract structured experience entries from resume text
                extracted = extract_work_experience(resume_text, language=detected_language, min_confidence=0.2)

                if extracted.get("experiences"):
                    # Convert extracted experiences to format expected by calculator
                    experience_entries = []
                    for exp in extracted["experiences"]:
                        entry = {
                            "start": exp.get("start"),
                            "end": exp.get("end"),
                            "company": exp.get("company"),
                            "position": exp.get("title"),
                            "description": exp.get("description"),
                        }
                        experience_entries.append(entry)

                    # Calculate total experience from structured entries
                    calc_result = calculate_total_experience(experience_entries)
                    experience_months = calc_result.get("total_months", 0)

                    experience_result = {
                        "total_months": experience_months,
                        "total_years": round(experience_months / 12, 1) if experience_months else 0,
                        "total_years_formatted": format_experience_summary(calc_result),
                        "entries": extracted["experiences"],
                        "entry_count": extracted["total_count"],
                    }
                else:
                    # No structured experiences found, return zero
                    experience_result = {
                        "total_months": 0,
                        "total_years": 0,
                        "total_years_formatted": "No experience data found",
                        "entries": None,
                        "entry_count": 0,
                    }
                    if extracted.get("error"):
                        logger.warning(f"Experience extraction error: {extracted['error']}")

            except Exception as e:
                logger.warning(f"Experience calculation failed: {e}")
                experience_result = {
                    "total_months": 0,
                    "total_years": 0,
                    "total_years_formatted": "Experience calculation failed",
                    "entries": None,
                    "entry_count": 0,
                }

        if detect_errors:
            try:
                errors_result = detect_resume_errors(resume_text)
            except Exception as e:
                logger.warning(f"Error detection failed: {e}")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "resume_id": resume_id,
            "status": "completed",
            "language": language,
            "keywords": keywords_result,
            "entities": {"technical_skills": entities},
            "grammar": grammar_result,
            "experience": experience_result,
            "errors": errors_result,
            "processing_time_ms": processing_time_ms,
        }

        # Convert numpy types to Python native types for JSON serialization
        result = convert_numpy_types(result)

        logger.info(f"Resume core analysis completed in {processing_time_ms}ms")
        return result

    except Exception as e:
        logger.error(f"Unexpected error in resume core analysis: {e}", exc_info=True)
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.analysis_task.analyze_resume_async",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def analyze_resume_async(
    self,
    resume_id: str,
    check_grammar: bool = True,
    extract_experience: bool = True,
    detect_errors: bool = True,
) -> Dict[str, Any]:
    """
    Asynchronously analyze a resume with progress tracking.

    This is a Celery wrapper around analyze_resume_core that provides
    progress updates via Celery's update_state mechanism.

    Args:
        self: Celery task instance (bind=True)
        resume_id: Unique identifier of the resume to analyze
        check_grammar: Whether to perform grammar checking
        extract_experience: Whether to calculate experience
        detect_errors: Whether to detect resume errors

    Returns:
        Dictionary containing analysis results
    """
    total_steps = 3

    try:
        # Step 1: Finding resume
        progress = {
            "current": 1,
            "total": total_steps,
            "percentage": 33,
            "status": "finding_resume",
            "message": "Locating resume file...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        # Step 2: Analyzing
        progress = {
            "current": 2,
            "total": total_steps,
            "percentage": 66,
            "status": "analyzing",
            "message": "Analyzing resume...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        # Call core analysis function
        result = analyze_resume_core(
            resume_id=resume_id,
            check_grammar=check_grammar,
            extract_experience=extract_experience,
            detect_errors=detect_errors,
        )

        # Step 3: Complete
        progress = {
            "current": 3,
            "total": total_steps,
            "percentage": 100,
            "status": "complete",
            "message": "Analysis complete",
        }
        self.update_state(state="PROGRESS", meta=progress)

        return result

    except Exception as e:
        logger.error(f"Unexpected error in resume analysis: {e}", exc_info=True)
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": 0,
        }


@shared_task(
    name="tasks.analysis_task.batch_analyze_resumes",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
)
def batch_analyze_resumes(
    self,
    resume_ids: List[str],
    check_grammar: bool = True,
    extract_experience: bool = True,
) -> Dict[str, Any]:
    """
    Asynchronously analyze multiple resumes in batch.

    This task processes multiple resumes sequentially, tracking progress
    across the entire batch. Useful for analyzing multiple resumes at once.

    Args:
        self: Celery task instance (bind=True)
        resume_ids: List of resume identifiers to analyze
        check_grammar: Whether to perform grammar checking (default: True)
        extract_experience: Whether to calculate experience (default: True)

    Returns:
        Dictionary containing batch analysis results:
        - total_resumes: Total number of resumes to process
        - successful: Number of successfully analyzed resumes
        - failed: Number of failed analyses
        - results: List of individual analysis results

    Example:
        >>> from tasks import batch_analyze_resumes
        >>> task = batch_analyze_resumes.delay(["abc123", "def456"])
        >>> result = task.get()
        >>> print(result['successful'])
        2
    """
    logger.info(f"Starting batch analysis for {len(resume_ids)} resumes")

    results = []
    successful = 0
    failed = 0

    for i, resume_id in enumerate(resume_ids):
        logger.info(f"Processing resume {i + 1}/{len(resume_ids)}: {resume_id}")

        # Update progress for batch (safe - ignore if task_id is not available)
        try:
            progress = {
                "current": i + 1,
                "total": len(resume_ids),
                "percentage": int((i + 1) / len(resume_ids) * 100),
                "status": "processing_batch",
                "message": f"Analyzing resume {i + 1}/{len(resume_ids)}...",
            }
            self.update_state(state="PROGRESS", meta=progress)
        except (ValueError, AttributeError):
            # Task might not have a valid ID (e.g., when called as subtask)
            pass

        # Analyze individual resume
        try:
            # Call the core analysis function directly (not as Celery task)
            result = analyze_resume_core(
                resume_id=resume_id,
                check_grammar=check_grammar,
                extract_experience=extract_experience,
                detect_errors=True,
            )
            results.append(result)

            if result.get("status") == "completed":
                successful += 1
            else:
                failed += 1

        except Exception as e:
            logger.error(f"Failed to analyze resume {resume_id}: {e}", exc_info=True)
            results.append({
                "resume_id": resume_id,
                "status": "failed",
                "error": str(e),
            })
            failed += 1

    logger.info(f"Batch analysis completed: {successful} successful, {failed} failed")

    return {
        "total_resumes": len(resume_ids),
        "successful": successful,
        "failed": failed,
        "results": results,
    }
