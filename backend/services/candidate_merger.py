"""
Candidate profile merging service with intelligent field-level merge logic.

This module provides a service for merging duplicate candidate profiles by
intelligently combining data from two resume records using configurable
merge strategies. It handles conflict resolution, data deduplication,
and creates comprehensive merge/undo data for audit trails.

The candidate merger supports:
- Multiple merge strategies (most_recent, most_complete, prefer_primary)
- Field-level merge logic for all resume data types
- Automatic conflict detection and resolution
- Skill and education deduplication
- Undo data generation for reversible merges
- Graceful handling of missing or incomplete data

Merge strategies:
- most_recent: Prefer data from the most recently updated resume
- most_complete: Prefer data with more complete information
- prefer_primary: Always prefer primary resume data when conflicts occur
- custom: Use field-specific rules for granular control

Example:
    >>> from backend.services.candidate_merger import CandidateMerger
    >>> merger = CandidateMerger(db_session)
    >>> result = await merger.merge_candidates(
    ...     primary_resume_id="uuid-1",
    ...     duplicate_resume_id="uuid-2",
    ...     strategy="most_complete"
    ... )
    >>> print(result["conflicts_resolved"])
    5
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.resume import Resume
from models.resume_analysis import ResumeAnalysis

logger = logging.getLogger(__name__)


class MergeStrategy:
    """Merge strategy constants for candidate profile merging."""

    MOST_RECENT = "most_recent"
    MOST_COMPLETE = "most_complete"
    PREFER_PRIMARY = "prefer_primary"
    CUSTOM = "custom"

    @classmethod
    def is_valid(cls, strategy: str) -> bool:
        """Check if the given strategy is valid."""
        return strategy in [
            cls.MOST_RECENT,
            cls.MOST_COMPLETE,
            cls.PREFER_PRIMARY,
            cls.CUSTOM,
        ]


@dataclass
class MergeResult:
    """
    Result of a candidate merge operation.

    Attributes:
        merged_data: The merged candidate data
        undo_data: Data needed to reverse the merge
        conflicts_detected: List of fields that had conflicting values
        conflicts_resolved: Number of conflicts that were resolved
        merge_strategy_used: The strategy used for merging
        metadata: Additional metadata about the merge operation
    """

    merged_data: Dict[str, Any]
    undo_data: Dict[str, Any]
    conflicts_detected: List[str]
    conflicts_resolved: int
    merge_strategy_used: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "merged_data": self.merged_data,
            "undo_data": self.undo_data,
            "conflicts_detected": self.conflicts_detected,
            "conflicts_resolved": self.conflicts_resolved,
            "merge_strategy_used": self.merge_strategy_used,
            "metadata": self.metadata,
        }


class CandidateMerger:
    """
    Service for intelligently merging duplicate candidate profiles.

    This service provides field-level merge logic that combines data from
    two candidate profiles (primary and duplicate) using configurable strategies.
    It handles conflict detection, data deduplication, and generates comprehensive
    merge history for audit and undo operations.

    Attributes:
        db: AsyncSession for database operations
        default_strategy: Default merge strategy to use

    Example:
        >>> merger = CandidateMerger(db_session)
        >>> result = await merger.merge_candidates(
        ...     primary_resume_id="uuid-1",
        ...     duplicate_resume_id="uuid-2",
        ...     strategy="most_complete"
        ... )
        >>> print(f"Resolved {result.conflicts_resolved} conflicts")
    """

    def __init__(
        self,
        db: AsyncSession,
        default_strategy: str = MergeStrategy.MOST_COMPLETE,
    ) -> None:
        """
        Initialize the candidate merger service.

        Args:
            db: AsyncSession for database operations
            default_strategy: Default merge strategy (defaults to most_complete)

        Raises:
            ValueError: If default_strategy is not valid
        """
        if not MergeStrategy.is_valid(default_strategy):
            raise ValueError(
                f"Invalid merge strategy: {default_strategy}. "
                f"Must be one of: {MergeStrategy.MOST_RECENT}, "
                f"{MergeStrategy.MOST_COMPLETE}, {MergeStrategy.PREFER_PRIMARY}"
            )

        self.db = db
        self.default_strategy = default_strategy

        logger.info(
            f"CandidateMerger initialized with strategy={default_strategy}"
        )

    async def merge_candidates(
        self,
        primary_resume_id: str,
        duplicate_resume_id: str,
        strategy: Optional[str] = None,
        field_overrides: Optional[Dict[str, Any]] = None,
    ) -> MergeResult:
        """
        Merge two candidate profiles with intelligent field-level logic.

        This method loads both candidate profiles, analyzes their data,
        and merges them using the specified strategy. It detects conflicts,
        resolves them intelligently, and generates undo data.

        Args:
            primary_resume_id: UUID of the primary resume to keep
            duplicate_resume_id: UUID of the duplicate resume to merge from
            strategy: Merge strategy to use (defaults to instance default)
            field_overrides: Optional dict of field values to explicitly set

        Returns:
            MergeResult containing merged data, undo data, and conflict info

        Raises:
            ValueError: If resume IDs are invalid or the same
            LookupError: If either resume is not found in the database
            RuntimeError: If merge operation fails

        Examples:
            >>> result = await merger.merge_candidates(
            ...     primary_resume_id="uuid-1",
            ...     duplicate_resume_id="uuid-2",
            ...     strategy="most_complete",
            ...     field_overrides={"status": "REVIEWED"}
            ... )
            >>> print(result.conflicts_resolved)
            3
        """
        # Validate inputs
        if not primary_resume_id or not duplicate_resume_id:
            raise ValueError("Both primary_resume_id and duplicate_resume_id are required")

        if primary_resume_id == duplicate_resume_id:
            raise ValueError("Cannot merge a resume with itself")

        strategy = strategy or self.default_strategy
        if not MergeStrategy.is_valid(strategy):
            raise ValueError(f"Invalid merge strategy: {strategy}")

        field_overrides = field_overrides or {}

        logger.info(
            f"Starting merge: primary={primary_resume_id}, "
            f"duplicate={duplicate_resume_id}, strategy={strategy}"
        )

        # Load both resumes and their analyses
        primary_resume, primary_analysis = await self._load_resume_with_analysis(
            primary_resume_id
        )
        duplicate_resume, duplicate_analysis = await self._load_resume_with_analysis(
            duplicate_resume_id
        )

        if not primary_resume:
            raise LookupError(f"Primary resume not found: {primary_resume_id}")
        if not duplicate_resume:
            raise LookupError(f"Duplicate resume not found: {duplicate_resume_id}")

        # Verify resumes belong to same organization
        if primary_resume.organization_id != duplicate_resume.organization_id:
            raise ValueError("Cannot merge resumes from different organizations")

        # Build data structures for merging
        primary_data = self._build_candidate_data(primary_resume, primary_analysis)
        duplicate_data = self._build_candidate_data(duplicate_resume, duplicate_analysis)

        # Perform field-level merge
        merged_data, conflicts_detected = self._merge_fields(
            primary_data, duplicate_data, strategy, field_overrides
        )

        # Generate undo data
        undo_data = self._generate_undo_data(
            primary_resume, primary_analysis, duplicate_resume, duplicate_analysis
        )

        # Build result metadata
        metadata = {
            "primary_resume_id": str(primary_resume_id),
            "duplicate_resume_id": str(duplicate_resume_id),
            "primary_filename": primary_resume.filename,
            "duplicate_filename": duplicate_resume.filename,
            "primary_updated_at": primary_resume.updated_at.isoformat() if primary_resume.updated_at else None,
            "duplicate_updated_at": duplicate_resume.updated_at.isoformat() if duplicate_resume.updated_at else None,
            "merge_timestamp": datetime.utcnow().isoformat(),
            "field_overrides_applied": list(field_overrides.keys()),
        }

        result = MergeResult(
            merged_data=merged_data,
            undo_data=undo_data,
            conflicts_detected=conflicts_detected,
            conflicts_resolved=len(conflicts_detected),
            merge_strategy_used=strategy,
            metadata=metadata,
        )

        logger.info(
            f"Merge completed: primary={primary_resume_id}, "
            f"duplicate={duplicate_resume_id}, conflicts={len(conflicts_detected)}"
        )

        return result

    async def _load_resume_with_analysis(
        self, resume_id: str
    ) -> Tuple[Optional[Resume], Optional[ResumeAnalysis]]:
        """
        Load resume and its analysis from database.

        Args:
            resume_id: UUID of the resume to load

        Returns:
            Tuple of (Resume, ResumeAnalysis) or (None, None) if not found
        """
        try:
            # Load resume
            resume_stmt = select(Resume).where(Resume.id == resume_id)
            resume_result = await self.db.execute(resume_stmt)
            resume = resume_result.scalar_one_or_none()

            if not resume:
                return None, None

            # Load analysis
            analysis_stmt = select(ResumeAnalysis).where(
                ResumeAnalysis.resume_id == resume_id
            )
            analysis_result = await self.db.execute(analysis_stmt)
            analysis = analysis_result.scalar_one_or_none()

            return resume, analysis

        except Exception as e:
            logger.error(f"Error loading resume {resume_id}: {e}")
            raise RuntimeError(f"Failed to load resume: {e}")

    def _build_candidate_data(
        self, resume: Resume, analysis: Optional[ResumeAnalysis]
    ) -> Dict[str, Any]:
        """
        Build a unified data structure from resume and analysis.

        Args:
            resume: Resume model instance
            analysis: ResumeAnalysis model instance (may be None)

        Returns:
            Dictionary containing all candidate data
        """
        data = {
            # Resume metadata
            "resume_id": str(resume.id),
            "organization_id": resume.organization_id,
            "vacancy_id": resume.vacancy_id,
            "filename": resume.filename,
            "file_path": resume.file_path,
            "content_type": resume.content_type,
            "status": resume.status.value if resume.status else None,
            "raw_text": resume.raw_text,
            "language": resume.language,
            "error_message": resume.error_message,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
            "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
        }

        # Add analysis data if available
        if analysis:
            data.update({
                "analysis_id": str(analysis.id),
                "skills": analysis.skills or [],
                "keywords": analysis.keywords or [],
                "entities": analysis.entities or {},
                "total_experience_months": analysis.total_experience_months,
                "education": analysis.education or [],
                "contact_info": analysis.contact_info or {},
                "grammar_issues": analysis.grammar_issues or [],
                "warnings": analysis.warnings or [],
                "quality_score": analysis.quality_score,
                "processing_time_seconds": analysis.processing_time_seconds,
                "analyzer_version": analysis.analyzer_version,
            })
        else:
            # Provide empty defaults if no analysis
            data.update({
                "analysis_id": None,
                "skills": [],
                "keywords": [],
                "entities": {},
                "total_experience_months": None,
                "education": [],
                "contact_info": {},
                "grammar_issues": [],
                "warnings": [],
                "quality_score": None,
                "processing_time_seconds": None,
                "analyzer_version": None,
            })

        return data

    def _merge_fields(
        self,
        primary_data: Dict[str, Any],
        duplicate_data: Dict[str, Any],
        strategy: str,
        field_overrides: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Perform field-level merge with conflict detection.

        Args:
            primary_data: Data from primary resume
            duplicate_data: Data from duplicate resume
            strategy: Merge strategy to use
            field_overrides: Fields to explicitly override

        Returns:
            Tuple of (merged_data, conflicts_detected)
        """
        merged = {}
        conflicts = []

        # Start with primary data as base
        merged.update(primary_data)

        # Merge simple fields
        for field in ["language", "vacancy_id", "error_message"]:
            value, conflict = self._merge_simple_field(
                field, primary_data, duplicate_data, strategy
            )
            merged[field] = value
            if conflict:
                conflicts.append(field)

        # Merge text fields (prefer longer/more complete)
        for field in ["raw_text"]:
            value, conflict = self._merge_text_field(
                field, primary_data, duplicate_data, strategy
            )
            merged[field] = value
            if conflict:
                conflicts.append(field)

        # Merge numeric fields (prefer higher/more recent)
        for field in ["total_experience_months", "quality_score"]:
            value, conflict = self._merge_numeric_field(
                field, primary_data, duplicate_data, strategy
            )
            merged[field] = value
            if conflict:
                conflicts.append(field)

        # Merge contact info (combine and deduplicate)
        contact_info, contact_conflicts = self._merge_contact_info(
            primary_data.get("contact_info", {}),
            duplicate_data.get("contact_info", {}),
            strategy,
        )
        merged["contact_info"] = contact_info
        conflicts.extend(contact_conflicts)

        # Merge skills (deduplicate and combine)
        merged["skills"] = self._merge_skills(
            primary_data.get("skills", []),
            duplicate_data.get("skills", []),
        )

        # Merge keywords (deduplicate)
        merged["keywords"] = self._merge_keywords(
            primary_data.get("keywords", []),
            duplicate_data.get("keywords", []),
        )

        # Merge education (deduplicate)
        merged["education"] = self._merge_education(
            primary_data.get("education", []),
            duplicate_data.get("education", []),
        )

        # Merge entities (combine dicts)
        merged["entities"] = self._merge_entities(
            primary_data.get("entities", {}),
            duplicate_data.get("entities", {}),
        )

        # Merge warnings and grammar issues (combine)
        merged["warnings"] = list(set(
            primary_data.get("warnings", []) + duplicate_data.get("warnings", [])
        ))
        merged["grammar_issues"] = list(set(
            primary_data.get("grammar_issues", []) + duplicate_data.get("grammar_issues", [])
        ))

        # Apply field overrides
        for field, value in field_overrides.items():
            merged[field] = value
            logger.debug(f"Applied field override: {field}={value}")

        # Prefer most recent timestamps
        merged["updated_at"] = self._get_most_recent_timestamp(
            primary_data.get("updated_at"),
            duplicate_data.get("updated_at"),
        )

        return merged, conflicts

    def _merge_simple_field(
        self,
        field: str,
        primary_data: Dict[str, Any],
        duplicate_data: Dict[str, Any],
        strategy: str,
    ) -> Tuple[Any, bool]:
        """
        Merge a simple field using the specified strategy.

        Args:
            field: Field name to merge
            primary_data: Primary candidate data
            duplicate_data: Duplicate candidate data
            strategy: Merge strategy

        Returns:
            Tuple of (merged_value, conflict_detected)
        """
        primary_value = primary_data.get(field)
        duplicate_value = duplicate_data.get(field)

        # If values are the same or duplicate is empty, no conflict
        if primary_value == duplicate_value or not duplicate_value:
            return primary_value, False

        # If primary is empty, use duplicate
        if not primary_value:
            return duplicate_value, False

        # Values differ - handle based on strategy
        conflict = True

        if strategy == MergeStrategy.PREFER_PRIMARY:
            return primary_value, conflict
        elif strategy == MergeStrategy.MOST_RECENT:
            # Use updated_at to determine recency
            if self._is_more_recent(
                primary_data.get("updated_at"),
                duplicate_data.get("updated_at"),
            ):
                return primary_value, conflict
            else:
                return duplicate_value, conflict
        elif strategy == MergeStrategy.MOST_COMPLETE:
            # Prefer non-null, longer values
            if len(str(primary_value)) >= len(str(duplicate_value)):
                return primary_value, conflict
            else:
                return duplicate_value, conflict
        else:
            # Default to primary
            return primary_value, conflict

    def _merge_text_field(
        self,
        field: str,
        primary_data: Dict[str, Any],
        duplicate_data: Dict[str, Any],
        strategy: str,
    ) -> Tuple[Optional[str], bool]:
        """
        Merge text fields, preferring longer/more complete text.

        Args:
            field: Field name to merge
            primary_data: Primary candidate data
            duplicate_data: Duplicate candidate data
            strategy: Merge strategy

        Returns:
            Tuple of (merged_value, conflict_detected)
        """
        primary_value = primary_data.get(field)
        duplicate_value = duplicate_data.get(field)

        # If values are the same or one is empty, no conflict
        if primary_value == duplicate_value:
            return primary_value, False

        if not duplicate_value:
            return primary_value, False

        if not primary_value:
            return duplicate_value, False

        # Values differ - prefer longer text (more complete)
        conflict = True

        if strategy == MergeStrategy.PREFER_PRIMARY:
            return primary_value, conflict
        elif strategy == MergeStrategy.MOST_COMPLETE:
            if len(primary_value) >= len(duplicate_value):
                return primary_value, conflict
            else:
                return duplicate_value, conflict
        else:
            # Most recent or default
            if self._is_more_recent(
                primary_data.get("updated_at"),
                duplicate_data.get("updated_at"),
            ):
                return primary_value, conflict
            else:
                return duplicate_value, conflict

    def _merge_numeric_field(
        self,
        field: str,
        primary_data: Dict[str, Any],
        duplicate_data: Dict[str, Any],
        strategy: str,
    ) -> Tuple[Optional[int], bool]:
        """
        Merge numeric fields, preferring higher values.

        Args:
            field: Field name to merge
            primary_data: Primary candidate data
            duplicate_data: Duplicate candidate data
            strategy: Merge strategy

        Returns:
            Tuple of (merged_value, conflict_detected)
        """
        primary_value = primary_data.get(field)
        duplicate_value = duplicate_data.get(field)

        # If values are the same or one is None, no conflict
        if primary_value == duplicate_value:
            return primary_value, False

        if duplicate_value is None:
            return primary_value, False

        if primary_value is None:
            return duplicate_value, False

        # Values differ
        conflict = True

        if strategy == MergeStrategy.PREFER_PRIMARY:
            return primary_value, conflict
        elif strategy == MergeStrategy.MOST_COMPLETE:
            # Prefer higher value (more experience/better quality)
            return max(primary_value, duplicate_value), conflict
        else:
            # Most recent or default
            if self._is_more_recent(
                primary_data.get("updated_at"),
                duplicate_data.get("updated_at"),
            ):
                return primary_value, conflict
            else:
                return duplicate_value, conflict

    def _merge_contact_info(
        self,
        primary_contact: Dict[str, Any],
        duplicate_contact: Dict[str, Any],
        strategy: str,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Merge contact information, combining and deduplicating.

        Args:
            primary_contact: Primary contact info dict
            duplicate_contact: Duplicate contact info dict
            strategy: Merge strategy

        Returns:
            Tuple of (merged_contact_info, conflicts_detected)
        """
        merged = {}
        conflicts = []

        # Combine all keys from both contacts
        all_keys = set(primary_contact.keys()) | set(duplicate_contact.keys())

        for key in all_keys:
            primary_value = primary_contact.get(key)
            duplicate_value = duplicate_contact.get(key)

            if primary_value == duplicate_value or not duplicate_value:
                merged[key] = primary_value
            elif not primary_value:
                merged[key] = duplicate_value
            else:
                # Conflict - values differ
                conflicts.append(f"contact_info.{key}")
                if strategy == MergeStrategy.PREFER_PRIMARY:
                    merged[key] = primary_value
                else:
                    # For contact info, prefer non-empty, longer values
                    if len(str(primary_value)) >= len(str(duplicate_value)):
                        merged[key] = primary_value
                    else:
                        merged[key] = duplicate_value

        return merged, conflicts

    def _merge_skills(
        self,
        primary_skills: List[Dict[str, Any]],
        duplicate_skills: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge skills lists, deduplicating by skill name.

        Args:
            primary_skills: Skills from primary resume
            duplicate_skills: Skills from duplicate resume

        Returns:
            Merged and deduplicated skills list
        """
        # Use dict to deduplicate by skill name (case-insensitive)
        skills_dict = {}

        for skill in primary_skills:
            if isinstance(skill, dict) and "name" in skill:
                key = skill["name"].lower()
                skills_dict[key] = skill
            elif isinstance(skill, str):
                # Handle string skills
                key = skill.lower()
                skills_dict[key] = {"name": skill}

        for skill in duplicate_skills:
            if isinstance(skill, dict) and "name" in skill:
                key = skill["name"].lower()
                if key not in skills_dict:
                    skills_dict[key] = skill
                else:
                    # Merge confidence scores (use max)
                    existing = skills_dict[key]
                    if "confidence" in skill and "confidence" in existing:
                        existing["confidence"] = max(
                            existing["confidence"], skill["confidence"]
                        )
            elif isinstance(skill, str):
                key = skill.lower()
                if key not in skills_dict:
                    skills_dict[key] = {"name": skill}

        return list(skills_dict.values())

    def _merge_keywords(
        self,
        primary_keywords: List[Any],
        duplicate_keywords: List[Any],
    ) -> List[Any]:
        """
        Merge keywords lists, deduplicating.

        Args:
            primary_keywords: Keywords from primary resume
            duplicate_keywords: Keywords from duplicate resume

        Returns:
            Merged and deduplicated keywords list
        """
        # Simple deduplication for keywords
        all_keywords = primary_keywords + duplicate_keywords
        if not all_keywords:
            return []

        # Handle both string and dict keywords
        seen = set()
        merged = []

        for keyword in all_keywords:
            if isinstance(keyword, dict):
                key = keyword.get("keyword", "").lower()
            else:
                key = str(keyword).lower()

            if key and key not in seen:
                seen.add(key)
                merged.append(keyword)

        return merged

    def _merge_education(
        self,
        primary_education: List[Dict[str, Any]],
        duplicate_education: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge education lists, deduplicating by institution and degree.

        Args:
            primary_education: Education from primary resume
            duplicate_education: Education from duplicate resume

        Returns:
            Merged and deduplicated education list
        """
        # Use tuple of (institution, degree) as key for deduplication
        education_dict = {}

        for edu in primary_education:
            if isinstance(edu, dict):
                institution = edu.get("institution", "").lower()
                degree = edu.get("degree", "").lower()
                key = (institution, degree)
                education_dict[key] = edu

        for edu in duplicate_education:
            if isinstance(edu, dict):
                institution = edu.get("institution", "").lower()
                degree = edu.get("degree", "").lower()
                key = (institution, degree)
                if key not in education_dict and (institution or degree):
                    education_dict[key] = edu

        return list(education_dict.values())

    def _merge_entities(
        self,
        primary_entities: Dict[str, Any],
        duplicate_entities: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge entity dictionaries, combining lists.

        Args:
            primary_entities: Entities from primary resume
            duplicate_entities: Entities from duplicate resume

        Returns:
            Merged entities dictionary
        """
        merged = {}

        # Combine all keys
        all_keys = set(primary_entities.keys()) | set(duplicate_entities.keys())

        for key in all_keys:
            primary_value = primary_entities.get(key, [])
            duplicate_value = duplicate_entities.get(key, [])

            # If both are lists, combine and deduplicate
            if isinstance(primary_value, list) and isinstance(duplicate_value, list):
                merged[key] = list(set(primary_value + duplicate_value))
            elif isinstance(primary_value, list):
                merged[key] = primary_value
            elif isinstance(duplicate_value, list):
                merged[key] = duplicate_value
            else:
                # Not lists, prefer primary
                merged[key] = primary_value or duplicate_value

        return merged

    def _is_more_recent(
        self,
        timestamp1: Optional[str],
        timestamp2: Optional[str],
    ) -> bool:
        """
        Compare two timestamps to determine which is more recent.

        Args:
            timestamp1: First timestamp (ISO format string)
            timestamp2: Second timestamp (ISO format string)

        Returns:
            True if timestamp1 is more recent than timestamp2
        """
        if not timestamp1:
            return False
        if not timestamp2:
            return True

        try:
            dt1 = datetime.fromisoformat(timestamp1.replace("Z", "+00:00"))
            dt2 = datetime.fromisoformat(timestamp2.replace("Z", "+00:00"))
            return dt1 > dt2
        except Exception as e:
            logger.warning(f"Error comparing timestamps: {e}")
            return True  # Default to first timestamp

    def _get_most_recent_timestamp(
        self,
        timestamp1: Optional[str],
        timestamp2: Optional[str],
    ) -> Optional[str]:
        """
        Get the most recent of two timestamps.

        Args:
            timestamp1: First timestamp (ISO format string)
            timestamp2: Second timestamp (ISO format string)

        Returns:
            The most recent timestamp
        """
        if not timestamp1:
            return timestamp2
        if not timestamp2:
            return timestamp1

        return timestamp1 if self._is_more_recent(timestamp1, timestamp2) else timestamp2

    def _generate_undo_data(
        self,
        primary_resume: Resume,
        primary_analysis: Optional[ResumeAnalysis],
        duplicate_resume: Resume,
        duplicate_analysis: Optional[ResumeAnalysis],
    ) -> Dict[str, Any]:
        """
        Generate data needed to undo/reverse a merge operation.

        Args:
            primary_resume: Primary resume instance
            primary_analysis: Primary analysis instance
            duplicate_resume: Duplicate resume instance
            duplicate_analysis: Duplicate analysis instance

        Returns:
            Dictionary containing undo data
        """
        undo_data = {
            "primary_resume": {
                "id": str(primary_resume.id),
                "organization_id": primary_resume.organization_id,
                "vacancy_id": primary_resume.vacancy_id,
                "filename": primary_resume.filename,
                "file_path": primary_resume.file_path,
                "content_type": primary_resume.content_type,
                "status": primary_resume.status.value if primary_resume.status else None,
                "raw_text": primary_resume.raw_text,
                "language": primary_resume.language,
                "error_message": primary_resume.error_message,
            },
            "duplicate_resume": {
                "id": str(duplicate_resume.id),
                "organization_id": duplicate_resume.organization_id,
                "vacancy_id": duplicate_resume.vacancy_id,
                "filename": duplicate_resume.filename,
                "file_path": duplicate_resume.file_path,
                "content_type": duplicate_resume.content_type,
                "status": duplicate_resume.status.value if duplicate_resume.status else None,
                "raw_text": duplicate_resume.raw_text,
                "language": duplicate_resume.language,
                "error_message": duplicate_resume.error_message,
            },
        }

        # Add analysis data if available
        if primary_analysis:
            undo_data["primary_analysis"] = {
                "skills": primary_analysis.skills,
                "keywords": primary_analysis.keywords,
                "entities": primary_analysis.entities,
                "total_experience_months": primary_analysis.total_experience_months,
                "education": primary_analysis.education,
                "contact_info": primary_analysis.contact_info,
                "quality_score": primary_analysis.quality_score,
            }

        if duplicate_analysis:
            undo_data["duplicate_analysis"] = {
                "skills": duplicate_analysis.skills,
                "keywords": duplicate_analysis.keywords,
                "entities": duplicate_analysis.entities,
                "total_experience_months": duplicate_analysis.total_experience_months,
                "education": duplicate_analysis.education,
                "contact_info": duplicate_analysis.contact_info,
                "quality_score": duplicate_analysis.quality_score,
            }

        return undo_data


def get_candidate_merger(db: AsyncSession) -> CandidateMerger:
    """
    Get a CandidateMerger instance.

    This is a convenience function for creating a merger instance
    with default settings.

    Args:
        db: AsyncSession for database operations

    Returns:
        CandidateMerger instance

    Example:
        >>> merger = get_candidate_merger(db_session)
        >>> result = await merger.merge_candidates(...)
    """
    return CandidateMerger(db)
