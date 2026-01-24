"""
Resume analysis endpoints integrating all analyzers.

This module provides endpoints for analyzing uploaded resumes using
multiple ML/NLP analyzers including keyword extraction, named entity
recognition, grammar checking, and experience calculation.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add parent directory to path to import from data_extractor service
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "data_extractor"))

from ..analyzers import (
    extract_resume_keywords,
    extract_resume_entities,
    check_grammar_resume,
    calculate_total_experience,
    format_experience_summary,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory where uploaded resumes are stored
UPLOAD_DIR = Path("data/uploads")


class AnalysisRequest(BaseModel):
    """Request model for resume analysis endpoint."""

    resume_id: str = Field(..., description="Unique identifier of the resume to analyze")
    extract_experience: bool = Field(
        default=True, description="Whether to extract and calculate experience information"
    )
    check_grammar: bool = Field(
        default=True, description="Whether to perform grammar and spelling checking"
    )


class KeywordAnalysis(BaseModel):
    """Keyword extraction results."""

    keywords: List[str] = Field(..., description="Extracted keywords")
    keyphrases: List[str] = Field(..., description="Extracted key phrases")
    scores: List[float] = Field(..., description="Confidence scores for each keyword")


class EntityAnalysis(BaseModel):
    """Named entity recognition results."""

    organizations: List[str] = Field(..., description="Extracted organization names")
    dates: List[str] = Field(..., description="Extracted date expressions")
    persons: List[str] = Field(default=[], description="Extracted person names")
    locations: List[str] = Field(default=[], description="Extracted location names")
    technical_skills: List[str] = Field(..., description="Extracted technical skills")


class GrammarError(BaseModel):
    """Individual grammar/spelling error."""

    type: str = Field(..., description="Type of error (grammar, spelling, punctuation, style)")
    severity: str = Field(..., description="Severity level (error, warning)")
    message: str = Field(..., description="Error message")
    context: str = Field(..., description="Text context where error occurs")
    suggestions: List[str] = Field(..., description="Suggested corrections")
    position: Dict[str, int] = Field(..., description="Character position of error")


class GrammarAnalysis(BaseModel):
    """Grammar checking results."""

    total_errors: int = Field(..., description="Total number of errors found")
    errors_by_category: Dict[str, int] = Field(
        ..., description="Breakdown of errors by type"
    )
    errors_by_severity: Dict[str, int] = Field(
        ..., description="Breakdown of errors by severity"
    )
    errors: List[GrammarError] = Field(..., description="List of individual errors")


class ExperienceEntry(BaseModel):
    """Individual work experience entry."""

    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job position/title")
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: Optional[str] = Field(..., description="End date (ISO format) or None if current")
    duration_months: int = Field(..., description="Duration in months")


class ExperienceAnalysis(BaseModel):
    """Experience calculation results."""

    total_months: int = Field(..., description="Total experience in months")
    total_years: float = Field(..., description="Total experience in years")
    total_years_formatted: str = Field(..., description="Human-readable experience summary")
    entries: List[ExperienceEntry] = Field(..., description="Individual experience entries")


class AnalysisResponse(BaseModel):
    """Complete analysis response."""

    resume_id: str = Field(..., description="Resume identifier")
    status: str = Field(..., description="Analysis status")
    language: str = Field(..., description="Detected language (en, ru)")
    keywords: KeywordAnalysis = Field(..., description="Keyword extraction results")
    entities: EntityAnalysis = Field(..., description="Named entity recognition results")
    grammar: Optional[GrammarAnalysis] = Field(
        None, description="Grammar checking results (if enabled)"
    )
    experience: Optional[ExperienceAnalysis] = Field(
        None, description="Experience calculation results (if enabled)"
    )
    processing_time_ms: float = Field(..., description="Analysis processing time in milliseconds")


def find_resume_file(resume_id: str) -> Path:
    """
    Find the resume file by ID.

    Args:
        resume_id: Unique identifier of the resume

    Returns:
        Path to the resume file

    Raises:
        HTTPException: If resume file is not found
    """
    # Try common file extensions
    for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
        file_path = UPLOAD_DIR / f"{resume_id}{ext}"
        if file_path.exists():
            return file_path

    # If not found, raise error
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Resume file with ID '{resume_id}' not found",
    )


def extract_text_from_file(file_path: Path) -> str:
    """
    Extract text from resume file (PDF or DOCX).

    Args:
        file_path: Path to the resume file

    Returns:
        Extracted text content

    Raises:
        HTTPException: If text extraction fails
    """
    try:
        # Import extraction functions
        from extract import extract_text_from_pdf, extract_text_from_docx

        file_ext = file_path.suffix.lower()

        if file_ext == ".pdf":
            result = extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            result = extract_text_from_docx(file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file_ext}",
            )

        # Check for extraction errors
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Text extraction failed: {result['error']}",
            )

        text = result.get("text", "")
        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Extracted text is too short or empty. The file may be corrupted or scanned.",
            )

        logger.info(f"Extracted {len(text)} characters from {file_path.name}")
        return text

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from resume: {str(e)}",
        ) from e


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
)
async def analyze_resume(request: AnalysisRequest) -> JSONResponse:
    """
    Analyze a resume using integrated ML/NLP analyzers.

    This endpoint performs comprehensive resume analysis including:
    - Keyword extraction (KeyBERT)
    - Named entity recognition (SpaCy)
    - Grammar and spelling checking (LanguageTool)
    - Experience calculation

    Args:
        request: Analysis request with resume_id and analysis options

    Returns:
        JSON response with complete analysis results

    Raises:
        HTTPException(404): If resume file is not found
        HTTPException(422): If text extraction fails
        HTTPException(500): If analysis processing fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/resumes/analyze",
        ...     json={"resume_id": "abc123", "check_grammar": True, "extract_experience": True}
        ... )
        >>> response.json()
        {
            "resume_id": "abc123",
            "status": "completed",
            "language": "en",
            "keywords": {...},
            "entities": {...},
            "grammar": {...},
            "experience": {...},
            "processing_time_ms": 1234.56
        }
    """
    import time

    start_time = time.time()

    try:
        logger.info(f"Starting analysis for resume_id: {request.resume_id}")

        # Step 1: Find the resume file
        file_path = find_resume_file(request.resume_id)
        logger.info(f"Found resume file: {file_path}")

        # Step 2: Extract text from file
        resume_text = extract_text_from_file(file_path)

        # Step 3: Detect language from text
        try:
            from langdetect import detect, LangDetectException

            try:
                detected_lang = detect(resume_text)
                # Normalize to supported languages
                language = "ru" if detected_lang == "ru" else "en"
            except LangDetectException:
                logger.warning("Language detection failed, defaulting to English")
                language = "en"
        except ImportError:
            logger.warning("langdetect not installed, defaulting to English")
            language = "en"

        logger.info(f"Detected language: {language}")

        # Step 4: Perform keyword extraction
        logger.info("Performing keyword extraction...")
        keywords_result = extract_resume_keywords(
            resume_text, language=language, top_n=20
        )
        keyword_analysis = KeywordAnalysis(
            keywords=keywords_result.get("keywords", []),
            keyphrases=keywords_result.get("keyphrases", []),
            scores=keywords_result.get("scores", []),
        )

        # Step 5: Perform named entity recognition
        logger.info("Performing named entity recognition...")
        entities_result = extract_resume_entities(resume_text, language=language)
        entity_analysis = EntityAnalysis(
            organizations=entities_result.get("organizations", []),
            dates=entities_result.get("dates", []),
            persons=entities_result.get("persons", []),
            locations=entities_result.get("locations", []),
            technical_skills=entities_result.get("technical_skills", []),
        )

        # Step 6: Grammar checking (optional)
        grammar_analysis = None
        if request.check_grammar:
            logger.info("Performing grammar checking...")
            try:
                grammar_result = check_grammar_resume(resume_text, language=language)

                # Convert grammar errors to response models
                error_models = []
                for error in grammar_result.get("errors", []):
                    error_models.append(
                        GrammarError(
                            type=error.get("type", "unknown"),
                            severity=error.get("severity", "warning"),
                            message=error.get("message", ""),
                            context=error.get("context", ""),
                            suggestions=error.get("suggestions", []),
                            position=error.get("position", {}),
                        )
                    )

                grammar_analysis = GrammarAnalysis(
                    total_errors=grammar_result.get("total_errors", 0),
                    errors_by_category=grammar_result.get("errors_by_category", {}),
                    errors_by_severity=grammar_result.get("errors_by_severity", {}),
                    errors=error_models,
                )

                logger.info(
                    f"Found {grammar_analysis.total_errors} grammar/spelling errors"
                )
            except Exception as e:
                logger.warning(f"Grammar checking failed: {e}")
                # Continue without grammar results rather than failing the entire analysis

        # Step 7: Experience calculation (optional, requires structured data)
        experience_analysis = None
        if request.extract_experience:
            logger.info("Calculating experience...")
            try:
                # Note: Experience calculation requires structured experience data
                # For now, we'll return a placeholder since we don't have parsed experience
                # This will be implemented when we have resume parsing logic
                experience_analysis = ExperienceAnalysis(
                    total_months=0,
                    total_years=0.0,
                    total_years_formatted="Experience calculation requires parsed resume data",
                    entries=[],
                )
            except Exception as e:
                logger.warning(f"Experience calculation failed: {e}")
                # Continue without experience results

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Build response
        response_data = {
            "resume_id": request.resume_id,
            "status": "completed",
            "language": language,
            "keywords": keyword_analysis.model_dump(),
            "entities": entity_analysis.model_dump(),
            "grammar": grammar_analysis.model_dump() if grammar_analysis else None,
            "experience": experience_analysis.model_dump() if experience_analysis else None,
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"Analysis completed for resume_id {request.resume_id} in {processing_time_ms:.2f}ms"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error analyzing resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume: {str(e)}",
        ) from e
