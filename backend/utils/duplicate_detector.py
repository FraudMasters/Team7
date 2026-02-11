"""
Duplicate detection utilities for identifying duplicate resume uploads.

This module provides functions for detecting duplicate resume files using
content-based hashing (SHA-256) and optional fuzzy matching for near-duplicates.
This helps prevent processing the same resume multiple times and allows
recruiters to review potential duplicates during bulk upload operations.

Security considerations:
- Uses SHA-256 for cryptographic hash of file content
- Hash comparison prevents timing attacks
- Organization-scoped duplicate detection for multi-tenancy
"""
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Similarity threshold for fuzzy matching (0.0 to 1.0)
# Files with similarity >= this threshold are considered near-duplicates
FUZZY_MATCH_THRESHOLD = 0.95


@dataclass
class DuplicateMatch:
    """
    Data class representing a detected duplicate match.

    Attributes:
        is_duplicate: Whether the file is a duplicate
        content_hash: SHA-256 hash of the file content
        original_resume_id: ID of the original resume (if duplicate)
        original_filename: Filename of the original resume (if duplicate)
        similarity_score: Similarity score for near-duplicates (1.0 for exact)
        match_type: Type of match ('exact', 'fuzzy', or None)
    """
    is_duplicate: bool
    content_hash: str
    original_resume_id: Optional[str] = None
    original_filename: Optional[str] = None
    similarity_score: float = 0.0
    match_type: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_duplicate": self.is_duplicate,
            "content_hash": self.content_hash,
            "original_resume_id": self.original_resume_id,
            "original_filename": self.original_filename,
            "similarity_score": self.similarity_score,
            "match_type": self.match_type,
        }


def compute_content_hash(file_content: bytes) -> str:
    """
    Compute SHA-256 hash of file content for duplicate detection.

    This function generates a cryptographic hash of the file content that
    can be used to uniquely identify identical files regardless of filename.

    Args:
        file_content: The raw bytes of the file to hash

    Returns:
        Hexadecimal SHA-256 hash string (64 characters)

    Raises:
        ValueError: If file_content is empty or None

    Examples:
        >>> content = b"%PDF-1.4 sample resume content"
        >>> hash_value = compute_content_hash(content)
        >>> len(hash_value)
        64
        >>> # Same content produces same hash
        >>> compute_content_hash(b"test") == compute_content_hash(b"test")
        True
        >>> # Different content produces different hash
        >>> compute_content_hash(b"test1") == compute_content_hash(b"test2")
        False
    """
    if not file_content:
        raise ValueError("File content cannot be empty or None")

    return hashlib.sha256(file_content).hexdigest()


def compute_content_hash_from_file(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file by reading from disk.

    This is a convenience function for hashing files that are already stored
    on disk, useful for comparing new uploads against existing stored files.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal SHA-256 hash string (64 characters)

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is empty or path is invalid
        IOError: If the file cannot be read

    Examples:
        >>> hash_value = compute_content_hash_from_file("/path/to/resume.pdf")
        >>> len(hash_value)
        64
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    sha256_hash = hashlib.sha256()

    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for file {file_path}: {e}")
        raise IOError(f"Failed to read file: {e}")


def compare_hashes(hash1: str, hash2: str) -> bool:
    """
    Compare two content hashes using constant-time comparison.

    This function uses a constant-time comparison to prevent timing attacks
    when comparing hashes, which is important for security-sensitive operations.

    Args:
        hash1: First hash to compare
        hash2: Second hash to compare

    Returns:
        True if hashes are equal, False otherwise

    Examples:
        >>> hash1 = compute_content_hash(b"test")
        >>> hash2 = compute_content_hash(b"test")
        >>> compare_hashes(hash1, hash2)
        True
        >>> hash3 = compute_content_hash(b"different")
        >>> compare_hashes(hash1, hash3)
        False
    """
    if not hash1 or not hash2:
        return False

    if len(hash1) != len(hash2):
        return False

    # Use hmac.compare_digest for constant-time comparison
    # This prevents timing attacks that could reveal hash information
    try:
        import hmac
        return hmac.compare_digest(hash1, hash2)
    except Exception:
        # Fallback to regular comparison if hmac is unavailable
        return hash1 == hash2


async def detect_duplicate(
    file_content: bytes,
    organization_id: str,
    db_session: AsyncSession,
    current_resume_id: Optional[str] = None,
    batch_job_id: Optional[str] = None,
    check_file_system: bool = True,
) -> DuplicateMatch:
    """
    Detect if a file is a duplicate of an existing resume.

    This function checks if the given file content matches any existing
    resume in the organization by comparing content hashes. It first checks
    the DuplicateResume table for known duplicates, then optionally checks
    the file system for files with matching content.

    Args:
        file_content: Raw bytes of the file to check
        organization_id: ID of the organization to scope the check
        db_session: Async database session for queries
        current_resume_id: Optional ID of current resume (to exclude from check)
        batch_job_id: Optional batch job ID for tracking detection
        check_file_system: Whether to check stored files (default: True)

    Returns:
        DuplicateMatch object with detection results

    Raises:
        ValueError: If file_content is empty or organization_id is invalid

    Examples:
        >>> # Check if a file is a duplicate
        >>> result = await detect_duplicate(
        ...     file_content=b"resume content",
        ...     organization_id="org-123",
        ...     db_session=db
        ... )
        >>> if result.is_duplicate:
        ...     print(f"Duplicate of resume {result.original_resume_id}")
    """
    try:
        # Validate inputs
        if not file_content:
            logger.warning("Empty file content provided for duplicate detection")
            return DuplicateMatch(
                is_duplicate=False,
                content_hash="",
                match_type=None,
            )

        if not organization_id:
            raise ValueError("organization_id is required")

        # Compute content hash
        content_hash = compute_content_hash(file_content)
        logger.debug(f"Computed content hash: {content_hash[:16]}...")

        # Import models here to avoid circular imports
        from models.duplicate_resume import DuplicateResume
        from models.resume import Resume

        # Check DuplicateResume table for known duplicates
        stmt = (
            select(DuplicateResume)
            .where(DuplicateResume.content_hash == content_hash)
            .where(DuplicateResume.organization_id == organization_id)
            .order_by(DuplicateResume.detection_timestamp.desc())
            .limit(1)
        )
        result = await db_session.execute(stmt)
        existing_duplicate = result.scalar_one_or_none()

        if existing_duplicate:
            logger.info(
                f"Found duplicate record: hash={content_hash[:16]}..., "
                f"original_id={existing_duplicate.original_resume_id}"
            )
            return DuplicateMatch(
                is_duplicate=True,
                content_hash=content_hash,
                original_resume_id=existing_duplicate.original_resume_id,
                similarity_score=1.0,
                match_type="exact",
            )

        # Check Resume table for files with matching content
        if check_file_system:
            # Get all resumes for this organization
            stmt = (
                select(Resume)
                .where(Resume.organization_id == organization_id)
                .where(Resume.status != "FAILED")
            )

            if current_resume_id:
                stmt = stmt.where(Resume.id != current_resume_id)

            result = await db_session.execute(stmt)
            resumes = result.scalars().all()

            # Check each resume's file content
            for resume in resumes:
                try:
                    if not resume.file_path:
                        continue

                    file_path = Path(resume.file_path)
                    if not file_path.exists():
                        logger.debug(f"Resume file not found: {file_path}")
                        continue

                    # Compute hash of stored file
                    stored_hash = compute_content_hash_from_file(file_path)

                    if compare_hashes(content_hash, stored_hash):
                        logger.info(
                            f"Found duplicate file: new_hash={content_hash[:16]}... "
                            f"matches resume {resume.id}"
                        )
                        return DuplicateMatch(
                            is_duplicate=True,
                            content_hash=content_hash,
                            original_resume_id=str(resume.id),
                            original_filename=resume.filename,
                            similarity_score=1.0,
                            match_type="exact",
                        )

                except Exception as e:
                    logger.warning(f"Error checking resume {resume.id}: {e}")
                    continue

        # No duplicate found
        logger.debug(f"No duplicate found for hash: {content_hash[:16]}...")
        return DuplicateMatch(
            is_duplicate=False,
            content_hash=content_hash,
            match_type=None,
        )

    except ValueError as e:
        logger.error(f"Invalid input for duplicate detection: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during duplicate detection: {e}")
        # Return non-duplicate on error to avoid blocking uploads
        return DuplicateMatch(
            is_duplicate=False,
            content_hash=compute_content_hash(file_content) if file_content else "",
            match_type=None,
        )


async def batch_detect_duplicates(
    files: List[Dict],
    organization_id: str,
    db_session: AsyncSession,
    batch_job_id: Optional[str] = None,
) -> Dict[str, DuplicateMatch]:
    """
    Detect duplicates for multiple files in a batch.

    This is an optimized function for checking multiple files at once,
    useful during bulk upload operations to identify all duplicates
    before processing.

    Args:
        files: List of file dictionaries, each with 'content' (bytes) and
               optionally 'filename' (str)
        organization_id: ID of the organization to scope the check
        db_session: Async database session for queries
        batch_job_id: Optional batch job ID for tracking

    Returns:
        Dictionary mapping file indices to DuplicateMatch results

    Examples:
        >>> files = [
        ...     {"content": b"resume1", "filename": "resume1.pdf"},
        ...     {"content": b"resume2", "filename": "resume2.pdf"},
        ... ]
        >>> results = await batch_detect_duplicates(files, "org-123", db)
        >>> for idx, match in results.items():
        ...     if match.is_duplicate:
        ...         print(f"File {idx} is a duplicate")
    """
    results: Dict[str, DuplicateMatch] = {}

    if not files:
        return results

    # Pre-compute all content hashes
    content_hashes: Dict[int, str] = {}
    for idx, file_info in enumerate(files):
        content = file_info.get("content")
        if content:
            try:
                content_hashes[idx] = compute_content_hash(content)
            except ValueError:
                logger.warning(f"Empty content for file at index {idx}")

    if not content_hashes:
        return results

    # Import models here to avoid circular imports
    from models.duplicate_resume import DuplicateResume

    # Batch check DuplicateResume table
    hash_list = list(set(content_hashes.values()))
    stmt = (
        select(DuplicateResume)
        .where(DuplicateResume.content_hash.in_(hash_list))
        .where(DuplicateResume.organization_id == organization_id)
    )
    result = await db_session.execute(stmt)
    existing_duplicates = result.scalars().all()

    # Create lookup by content hash
    duplicate_lookup: Dict[str, DuplicateResume] = {}
    for dup in existing_duplicates:
        if dup.content_hash not in duplicate_lookup:
            duplicate_lookup[dup.content_hash] = dup

    # Build results for each file
    for idx, content_hash in content_hashes.items():
        if content_hash in duplicate_lookup:
            dup = duplicate_lookup[content_hash]
            results[idx] = DuplicateMatch(
                is_duplicate=True,
                content_hash=content_hash,
                original_resume_id=dup.original_resume_id,
                similarity_score=1.0,
                match_type="exact",
            )
        else:
            results[idx] = DuplicateMatch(
                is_duplicate=False,
                content_hash=content_hash,
                match_type=None,
            )

    return results


def compute_text_similarity(text1: str, text2: str) -> float:
    """
    Compute similarity between two text strings for fuzzy duplicate detection.

    This function uses a simple similarity metric based on common n-grams.
    For more sophisticated fuzzy matching, consider using libraries like
    fuzzywuzzy or rapidfuzz.

    Args:
        text1: First text to compare
        text2: Second text to compare

    Returns:
        Similarity score between 0.0 and 1.0

    Examples:
        >>> compute_text_similarity("hello world", "hello world")
        1.0
        >>> score = compute_text_similarity("hello world", "hello earth")
        >>> 0.0 <= score <= 1.0
        True
    """
    if not text1 or not text2:
        return 0.0

    if text1 == text2:
        return 1.0

    # Normalize texts
    text1_lower = text1.lower().strip()
    text2_lower = text2.lower().strip()

    if text1_lower == text2_lower:
        return 1.0

    # Simple n-gram based similarity
    def get_ngrams(text: str, n: int = 3) -> set:
        """Extract character n-grams from text."""
        text = text.lower()
        return {text[i:i+n] for i in range(len(text) - n + 1)}

    try:
        ngrams1 = get_ngrams(text1_lower)
        ngrams2 = get_ngrams(text2_lower)

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = ngrams1 & ngrams2
        union = ngrams1 | ngrams2

        similarity = len(intersection) / len(union) if union else 0.0
        return round(similarity, 4)

    except Exception as e:
        logger.warning(f"Error computing text similarity: {e}")
        return 0.0


async def detect_near_duplicate(
    file_content: bytes,
    extracted_text: str,
    organization_id: str,
    db_session: AsyncSession,
    threshold: float = FUZZY_MATCH_THRESHOLD,
) -> DuplicateMatch:
    """
    Detect if a file is a near-duplicate using fuzzy text matching.

    This function compares the extracted text content of resumes to find
    near-duplicates that may have minor differences (formatting, whitespace,
    small edits). Useful for detecting resumes that have been slightly
    modified but are essentially the same.

    Args:
        file_content: Raw bytes of the file to check
        extracted_text: Extracted text content from the resume
        organization_id: ID of the organization to scope the check
        db_session: Async database session for queries
        threshold: Minimum similarity score to consider as duplicate (0.0-1.0)

    Returns:
        DuplicateMatch object with detection results

    Examples:
        >>> result = await detect_near_duplicate(
        ...     file_content=b"resume content",
        ...     extracted_text="John Doe\\nSoftware Engineer\\n...",
        ...     organization_id="org-123",
        ...     db_session=db,
        ...     threshold=0.95
        ... )
        >>> if result.is_duplicate:
        ...     print(f"Near-duplicate found: {result.similarity_score}")
    """
    try:
        # First check for exact duplicates
        exact_match = await detect_duplicate(
            file_content=file_content,
            organization_id=organization_id,
            db_session=db_session,
            check_file_system=True,
        )

        if exact_match.is_duplicate:
            return exact_match

        # If no exact match, check for fuzzy matches
        if not extracted_text:
            return DuplicateMatch(
                is_duplicate=False,
                content_hash=compute_content_hash(file_content),
                match_type=None,
            )

        from models.resume import Resume

        # Get resumes with raw_text for comparison
        stmt = (
            select(Resume)
            .where(Resume.organization_id == organization_id)
            .where(Resume.raw_text.isnot(None))
            .where(Resume.status != "FAILED")
        )

        result = await db_session.execute(stmt)
        resumes = result.scalars().all()

        best_match: Optional[Resume] = None
        best_similarity = 0.0

        for resume in resumes:
            if not resume.raw_text:
                continue

            similarity = compute_text_similarity(extracted_text, resume.raw_text)

            if similarity >= threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = resume

        if best_match and best_similarity >= threshold:
            logger.info(
                f"Found near-duplicate: similarity={best_similarity:.4f}, "
                f"original_id={best_match.id}"
            )
            return DuplicateMatch(
                is_duplicate=True,
                content_hash=compute_content_hash(file_content),
                original_resume_id=str(best_match.id),
                original_filename=best_match.filename,
                similarity_score=best_similarity,
                match_type="fuzzy",
            )

        return DuplicateMatch(
            is_duplicate=False,
            content_hash=compute_content_hash(file_content),
            similarity_score=best_similarity if best_similarity > 0 else 0.0,
            match_type=None,
        )

    except Exception as e:
        logger.error(f"Error during near-duplicate detection: {e}")
        return DuplicateMatch(
            is_duplicate=False,
            content_hash=compute_content_hash(file_content) if file_content else "",
            match_type=None,
        )


async def record_duplicate(
    original_resume_id: str,
    duplicate_resume_id: str,
    content_hash: str,
    organization_id: str,
    db_session: AsyncSession,
    batch_job_id: Optional[str] = None,
    match_type: str = "exact",
    similarity_score: float = 1.0,
) -> bool:
    """
    Record a duplicate detection in the database.

    This function creates a DuplicateResume record to track detected
    duplicates for future reference and reporting.

    Args:
        original_resume_id: ID of the original/first resume
        duplicate_resume_id: ID of the newly detected duplicate
        content_hash: SHA-256 hash of the duplicate content
        organization_id: ID of the organization
        db_session: Async database session
        batch_job_id: Optional batch job ID where duplicate was detected
        match_type: Type of match ('exact' or 'fuzzy')
        similarity_score: Similarity score for fuzzy matches

    Returns:
        True if record was created successfully, False otherwise

    Examples:
        >>> success = await record_duplicate(
        ...     original_resume_id="resume-1",
        ...     duplicate_resume_id="resume-2",
        ...     content_hash="abc123...",
        ...     organization_id="org-123",
        ...     db_session=db
        ... )
    """
    try:
        from models.duplicate_resume import DuplicateResume

        duplicate_record = DuplicateResume(
            organization_id=organization_id,
            original_resume_id=original_resume_id,
            duplicate_resume_id=duplicate_resume_id,
            content_hash=content_hash,
            batch_job_id=batch_job_id,
            detection_timestamp=datetime.now(timezone.utc),
        )

        db_session.add(duplicate_record)
        await db_session.flush()

        logger.info(
            f"Recorded duplicate: original={original_resume_id}, "
            f"duplicate={duplicate_resume_id}, type={match_type}, "
            f"similarity={similarity_score:.4f}"
        )
        return True

    except Exception as e:
        logger.error(f"Error recording duplicate: {e}")
        return False
