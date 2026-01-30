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

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

# Add parent directory to path to import from data_extractor service
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "data_extractor"))

from analyzers import (
    extract_resume_keywords_hf as extract_resume_keywords,
    extract_resume_entities,
    check_grammar_resume,
    calculate_total_experience,
    format_experience_summary,
    detect_resume_errors,
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

    This task performs comprehensive resume analysis including:
    - Keyword extraction (KeyBERT)
    - Named entity recognition (SpaCy)
    - Grammar and spelling checking (LanguageTool)
    - Experience calculation
    - Error detection

    The task provides progress updates throughout the analysis process,
    allowing clients to monitor the status of long-running analyses.

    Args:
        self: Celery task instance (bind=True)
        resume_id: Unique identifier of the resume to analyze
        check_grammar: Whether to perform grammar checking (default: True)
        extract_experience: Whether to calculate experience (default: True)
        detect_errors: Whether to detect resume errors (default: True)

    Returns:
        Dictionary containing complete analysis results:
        - resume_id: Resume identifier
        - status: Final analysis status
        - language: Detected language (en, ru)
        - keywords: Keyword extraction results
        - entities: Named entity recognition results
        - grammar: Grammar checking results (if enabled)
        - experience: Experience calculation results (if enabled)
        - errors: Detected resume errors (if enabled)
        - processing_time_ms: Total processing time

    Raises:
        FileNotFoundError: If resume file is not found
        ValueError: If text extraction fails
        SoftTimeLimitExceeded: If task exceeds time limit

    Example:
        >>> from tasks import analyze_resume_async
        >>> task = analyze_resume_async.delay("abc123")
        >>> # Can check task.status for 'PROGRESS' updates
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    total_steps = 5
    current_step = 0

    try:
        logger.info(f"Starting async resume analysis for resume_id: {resume_id}")

        # Step 1: Find resume file
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "finding_resume",
            "message": "Locating resume file...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Finding resume file")

        try:
            file_path = find_resume_file(resume_id)
        except FileNotFoundError as e:
            logger.error(f"Resume file not found: {e}")
            return {
                "resume_id": resume_id,
                "status": "failed",
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 2: Extract text from file
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "extracting_text",
            "message": "Extracting text from resume file...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Extracting text")

        try:
            resume_text = extract_text_from_file(file_path)
        except ValueError as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                "resume_id": resume_id,
                "status": "failed",
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 3: Extract keywords and entities
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "extracting_keywords",
            "message": "Extracting keywords and entities...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Keyword extraction")

        try:
            # Detect language first for model selection
            from langdetect import detect
            try:
                lang_code = detect(resume_text[:1000])
                # Map to our language format
                if lang_code == 'ru':
                    detected_language = 'ru'
                elif lang_code == 'en':
                    detected_language = 'en'
                else:
                    detected_language = lang_code
            except:
                detected_language = "en"

            logger.info(f"Detected language: {detected_language}")

            # Extract keywords with language-aware model selection
            keywords_result = extract_resume_keywords(resume_text, language=detected_language)

            # Extract named entities
            entities_result = extract_resume_entities(resume_text)

            # Use detected language for entities result
            language = entities_result.get("language", detected_language)

        except Exception as e:
            logger.error(f"Keyword/entity extraction failed: {e}", exc_info=True)
            language = "unknown"
            keywords_result = {"keywords": [], "keyphrases": [], "scores": []}
            entities_result = {
                "organizations": [],
                "dates": [],
                "persons": [],
                "locations": [],
                "technical_skills": [],
                "language": "unknown",
            }

        # Step 4: Run optional analysis (grammar, experience, errors)
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "analyzing_content",
            "message": "Analyzing grammar, experience, and errors...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Content analysis")

        grammar_result = None
        experience_result = None
        errors_result = None

        # Grammar checking
        if check_grammar:
            try:
                grammar_result = check_grammar_resume(resume_text)
                logger.info(f"Grammar checking completed: {grammar_result.get('total_errors', 0)} errors found")
            except Exception as e:
                logger.warning(f"Grammar checking failed: {e}", exc_info=True)
                grammar_result = None

        # Experience calculation
        if extract_experience:
            try:
                experience_months = calculate_total_experience(resume_text)
                experience_result = {
                    "total_months": experience_months,
                    "total_years": round(experience_months / 12, 1),
                    "total_years_formatted": format_experience_summary(experience_months),
                }
                logger.info(f"Experience calculation completed: {experience_result['total_years_formatted']}")
            except Exception as e:
                logger.warning(f"Experience calculation failed: {e}", exc_info=True)
                experience_result = None

        # Error detection
        if detect_errors:
            try:
                errors_result = detect_resume_errors(resume_text)
                logger.info(f"Error detection completed: {len(errors_result)} errors detected")
            except Exception as e:
                logger.warning(f"Error detection failed: {e}", exc_info=True)
                errors_result = None

        # Step 5: Compile results
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "compiling_results",
            "message": "Compiling analysis results...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Compiling results")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "resume_id": resume_id,
            "status": "completed",
            "language": language,
            "keywords": keywords_result,
            "entities": entities_result,
            "grammar": grammar_result,
            "experience": experience_result,
            "errors": errors_result,
            "processing_time_ms": processing_time_ms,
        }

        logger.info(f"Resume analysis completed successfully in {processing_time_ms}ms")

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": "Analysis exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Unexpected error in resume analysis: {e}", exc_info=True)
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
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
        # Update progress for batch
        progress = {
            "current": i + 1,
            "total": len(resume_ids),
            "percentage": int((i + 1) / len(resume_ids) * 100),
            "status": "processing_batch",
            "message": f"Analyzing resume {i + 1}/{len(resume_ids)}...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        logger.info(f"Processing resume {i + 1}/{len(resume_ids)}: {resume_id}")

        # Analyze individual resume
        try:
            result = analyze_resume_async(
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
