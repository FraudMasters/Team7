"""
LinkedIn profile synchronization tasks for async profile data fetching and updating.

This module provides Celery tasks for synchronizing LinkedIn profile data,
including fetching profile data from LinkedIn API, storing it in the database,
and handling periodic updates to keep profile information current.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from difflib import SequenceMatcher

from config import get_settings
from database import async_session_maker
from models.linkedin_profile import LinkedInProfile, LinkedInProfileStatus
from services.linkedin_service import LinkedInService, LinkedInAPIError, LinkedInRateLimitError, LinkedInAuthError

logger = logging.getLogger(__name__)
settings = get_settings()

# Path to skill taxonomy file
SKILL_TAXONOMY_FILE = Path(__file__).parent.parent / "models" / "skill_synonyms.json"


async def get_linkedin_access_token(user_id: UUID) -> Optional[str]:
    """
    Retrieve LinkedIn access token for a user.

    This function queries the database for the user's LinkedIn access token.
    The token should be stored securely (encrypted) after OAuth flow completion.

    Args:
        user_id: UUID of the user/recruiter

    Returns:
        Access token string, or None if not found

    Example:
        >>> from uuid import UUID
        >>> user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        >>> token = await get_linkedin_access_token(user_id)
        >>> isinstance(token, str)
        True
    """
    # Note: This is a placeholder for access token retrieval
    # In a real implementation, you would:
    # 1. Query User or LinkedInConnection model for the access token
    # 2. Decrypt the token if encrypted
    # 3. Check if token is expired and refresh if necessary

    async with async_session_maker() as session:
        # Placeholder: Query user's LinkedIn access token
        # from models import LinkedInConnection
        # connection = await session.execute(
        #     select(LinkedInConnection).where(
        #         and_(
        #             LinkedInConnection.user_id == user_id,
        #             LinkedInConnection.is_active == True
        #         )
        #     )
        # )
        # token = connection.scalar_one_or_none()
        # return token.access_token if token else None

        logger.debug(f"Retrieving LinkedIn access token for user: {user_id}")
        return None  # Placeholder


async def save_linkedin_profile(
    profile_data: Dict[str, Any],
    user_id: UUID,
) -> Optional[LinkedInProfile]:
    """
    Save or update LinkedIn profile in database.

    This function creates a new LinkedInProfile record or updates an existing one
    with the provided profile data. It also updates the status and last_synced_at timestamp.

    Args:
        profile_data: Dictionary containing LinkedIn profile data from API
        user_id: UUID of the user who initiated the sync

    Returns:
        Saved or updated LinkedInProfile instance, or None if save fails

    Example:
        >>> profile_data = {
        ...     "id": "abc123",
        ...     "first_name": "John",
        ...     "last_name": "Doe",
        ...     "headline": "Software Engineer"
        ... }
        >>> profile = await save_linkedin_profile(profile_data, user_id)
        >>> profile.status
        <LinkedInProfileStatus.COMPLETED>
    """
    try:
        async with async_session_maker() as session:
            # Check if profile already exists
            from sqlalchemy import select

            linkedin_id = profile_data.get("id")
            if not linkedin_id:
                logger.error("Profile data missing required 'id' field")
                return None

            # Query existing profile
            result = await session.execute(
                select(LinkedInProfile).where(
                    LinkedInProfile.linkedin_id == linkedin_id
                )
            )
            existing_profile = result.scalar_one_or_none()

            if existing_profile:
                # Update existing profile
                logger.info(f"Updating existing LinkedIn profile: {linkedin_id}")

                existing_profile.first_name = profile_data.get("first_name")
                existing_profile.last_name = profile_data.get("last_name")
                existing_profile.headline = profile_data.get("headline")
                existing_profile.location = profile_data.get("location")
                existing_profile.email = profile_data.get("email")
                existing_profile.phone = profile_data.get("phone")
                existing_profile.profile_picture_url = profile_data.get("profile_picture")
                existing_profile.skills = {"skills": profile_data.get("skills", [])}
                existing_profile.experience = {"positions": profile_data.get("positions", [])}
                existing_profile.education = {"education": profile_data.get("education", [])}
                existing_profile.raw_profile_data = profile_data.get("raw_data", {})
                existing_profile.status = LinkedInProfileStatus.SYNCED
                existing_profile.last_synced_at = datetime.utcnow().isoformat()
                existing_profile.error_message = None

                profile = existing_profile
            else:
                # Create new profile
                logger.info(f"Creating new LinkedIn profile: {linkedin_id}")

                profile = LinkedInProfile(
                    linkedin_id=linkedin_id,
                    linkedin_url=f"https://www.linkedin.com/in/{linkedin_id}",
                    first_name=profile_data.get("first_name"),
                    last_name=profile_data.get("last_name"),
                    headline=profile_data.get("headline"),
                    location=profile_data.get("location"),
                    email=profile_data.get("email"),
                    phone=profile_data.get("phone"),
                    profile_picture_url=profile_data.get("profile_picture"),
                    skills={"skills": profile_data.get("skills", [])},
                    experience={"positions": profile_data.get("positions", [])},
                    education={"education": profile_data.get("education", [])},
                    raw_profile_data=profile_data.get("raw_data", {}),
                    status=LinkedInProfileStatus.COMPLETED,
                    last_synced_at=datetime.utcnow().isoformat(),
                )

                session.add(profile)

            await session.commit()
            await session.refresh(profile)

            logger.info(f"LinkedIn profile saved successfully: {profile.id}")
            return profile

    except Exception as e:
        logger.error(f"Failed to save LinkedIn profile: {e}", exc_info=True)
        return None


async def mark_profile_failed(
    linkedin_id: str,
    error_message: str,
) -> None:
    """
    Mark a LinkedIn profile as failed and store error message.

    This function updates the profile status to FAILED and stores the
    error message for troubleshooting.

    Args:
        linkedin_id: LinkedIn profile ID
        error_message: Error message describing the failure

    Example:
        >>> await mark_profile_failed("abc123", "Rate limit exceeded")
    """
    try:
        async with async_session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(LinkedInProfile).where(
                    LinkedInProfile.linkedin_id == linkedin_id
                )
            )
            profile = result.scalar_one_or_none()

            if profile:
                profile.status = LinkedInProfileStatus.FAILED
                profile.error_message = error_message[:500]  # Limit error message length
                await session.commit()
                logger.info(f"Marked profile {linkedin_id} as failed: {error_message}")

    except Exception as e:
        logger.error(f"Failed to mark profile as failed: {e}", exc_info=True)


@shared_task(
    name="tasks.linkedin_sync.sync_linkedin_profile",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def sync_linkedin_profile(
    self,
    linkedin_profile_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Synchronize LinkedIn profile data from LinkedIn API.

    This Celery task handles the complete workflow of synchronizing a LinkedIn profile:
    1. Retrieve user's LinkedIn access token
    2. Initialize LinkedIn API client
    3. Fetch profile data from LinkedIn API
    4. Store or update profile in database
    5. Update profile status and metadata
    6. Handle errors with appropriate retry logic

    Task Workflow:
    1. Query user's LinkedIn access token from database
    2. Initialize LinkedInService with access token
    3. Call LinkedInService.get_profile() to fetch profile data
    4. Save/update LinkedInProfile record in database
    5. Return success/failure status with metadata

    Retry Logic:
    - Max retries: 3
    - Retry delay: 5 minutes (300 seconds)
    - Retries on: Network errors, rate limit errors (429), temporary API errors
    - No retry on: Authentication errors (401), invalid profile IDs

    Args:
        self: Celery task instance (bind=True)
        linkedin_profile_id: LinkedIn profile ID or member URN
        user_id: UUID of user who initiated the sync (as string)

    Returns:
        Dictionary containing sync results:
        - linkedin_profile_id: LinkedIn profile ID
        - status: Task status (completed/failed/pending_retry)
        - profile_db_id: Database ID of created/updated profile
        - first_name: Profile first name
        - last_name: Profile last name
        - headline: Profile headline
        - synced_at: ISO timestamp of sync
        - processing_time_ms: Total processing time
        - error: Error message (if failed)
        - retry_attempt: Current retry attempt number

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For unexpected errors

    Example:
        >>> from tasks.linkedin_sync import sync_linkedin_profile
        >>> task = sync_linkedin_profile.delay("abc-123", "user-uuid-456")
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    total_steps = 4
    current_step = 0
    retry_attempt = self.request.retries

    try:
        logger.info(
            f"Starting LinkedIn profile sync for ID: {linkedin_profile_id}, "
            f"user: {user_id}, attempt: {retry_attempt}"
        )

        # Step 1: Retrieve access token
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "retrieving_token",
            "message": "Retrieving LinkedIn access token...",
            "retry_attempt": retry_attempt,
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Retrieving access token")

        # Import asyncio to run async functions
        import asyncio

        # Get access token for user
        user_uuid = UUID(user_id)
        access_token = asyncio.run(get_linkedin_access_token(user_uuid))

        if not access_token:
            logger.error(f"No LinkedIn access token found for user: {user_id}")
            return {
                "linkedin_profile_id": linkedin_profile_id,
                "status": "failed",
                "error": "No LinkedIn access token found. Please connect your LinkedIn account.",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "retry_attempt": retry_attempt,
            }

        logger.info("Access token retrieved successfully")

        # Step 2: Initialize LinkedIn service and fetch profile
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "fetching_profile",
            "message": "Fetching profile data from LinkedIn API...",
            "retry_attempt": retry_attempt,
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Fetching profile data")

        # Initialize LinkedIn service
        linkedin_service = LinkedInService(access_token=access_token)

        # Fetch profile data from LinkedIn API
        profile_data = asyncio.run(
            linkedin_service.get_profile(profile_id=linkedin_profile_id)
        )

        logger.info(
            f"Profile data fetched: {profile_data.get('first_name', '')} "
            f"{profile_data.get('last_name', '')}"
        )

        # Step 3: Save profile to database
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "saving_profile",
            "message": "Saving profile data to database...",
            "retry_attempt": retry_attempt,
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Saving profile")

        # Save or update profile in database
        profile = asyncio.run(
            save_linkedin_profile(profile_data, user_uuid)
        )

        if not profile:
            logger.error("Failed to save profile to database")
            return {
                "linkedin_profile_id": linkedin_profile_id,
                "status": "failed",
                "error": "Failed to save profile to database",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "retry_attempt": retry_attempt,
            }

        logger.info(f"Profile saved successfully: {profile.id}")

        # Step 4: Finalize sync
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "finalizing",
            "message": "Finalizing profile synchronization...",
            "retry_attempt": retry_attempt,
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Finalizing")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        synced_at = datetime.utcnow().isoformat()

        result = {
            "linkedin_profile_id": linkedin_profile_id,
            "status": "completed",
            "profile_db_id": str(profile.id),
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "headline": profile.headline,
            "synced_at": synced_at,
            "processing_time_ms": processing_time_ms,
            "retry_attempt": retry_attempt,
        }

        logger.info(
            f"LinkedIn profile sync completed: {linkedin_profile_id}, "
            f"{profile.first_name} {profile.last_name}, "
            f"time: {processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        # Mark profile as failed due to timeout
        import asyncio
        asyncio.run(mark_profile_failed(
            linkedin_profile_id,
            f"Profile sync exceeded maximum time limit (attempt {retry_attempt})"
        ))
        return {
            "linkedin_profile_id": linkedin_profile_id,
            "status": "failed",
            "error": "Profile sync exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "retry_attempt": retry_attempt,
        }

    except LinkedInRateLimitError as e:
        logger.error(f"LinkedIn rate limit error: {e}")
        # Mark profile as failed due to rate limit
        import asyncio
        asyncio.run(mark_profile_failed(
            linkedin_profile_id,
            f"LinkedIn API rate limit exceeded: {str(e)[:200]}"
        ))
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=300 * (2 ** retry_attempt))

    except LinkedInAuthError as e:
        logger.error(f"LinkedIn authentication error: {e}")
        # Mark profile as failed - don't retry auth errors
        import asyncio
        asyncio.run(mark_profile_failed(
            linkedin_profile_id,
            f"LinkedIn authentication failed: {str(e)[:200]}"
        ))
        return {
            "linkedin_profile_id": linkedin_profile_id,
            "status": "failed",
            "error": f"LinkedIn authentication failed: {str(e)}",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "retry_attempt": retry_attempt,
        }

    except LinkedInAPIError as e:
        logger.error(f"LinkedIn API error: {e}")
        # Mark profile as failed
        import asyncio
        asyncio.run(mark_profile_failed(
            linkedin_profile_id,
            f"LinkedIn API error: {str(e)[:200]}"
        ))
        # Retry for temporary API errors
        if retry_attempt < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** retry_attempt))
        return {
            "linkedin_profile_id": linkedin_profile_id,
            "status": "failed",
            "error": f"LinkedIn API error: {str(e)}",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "retry_attempt": retry_attempt,
        }

    except Exception as e:
        logger.error(f"Unexpected error in LinkedIn profile sync: {e}", exc_info=True)
        # Mark profile as failed
        import asyncio
        asyncio.run(mark_profile_failed(
            linkedin_profile_id,
            f"Unexpected error: {str(e)[:200]}"
        ))
        return {
            "linkedin_profile_id": linkedin_profile_id,
            "status": "failed",
            "error": f"Unexpected error: {str(e)}",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "retry_attempt": retry_attempt,
        }



def load_skill_taxonomy() -> Dict[str, Dict[str, List[str]]]:
    """
    Load skill taxonomy from JSON file.

    Returns a dictionary organizing skills by category, with each skill
    having a canonical name and list of synonyms/variations.

    The taxonomy file structure organizes skills into categories like:
    - databases (SQL, PostgreSQL, MongoDB, etc.)
    - programming_languages (Java, JavaScript, Python, etc.)
    - web_frameworks (React, Angular, Django, etc.)
    - devops (Docker, Kubernetes, CI/CD, etc.)
    And more...

    Returns:
        Dictionary mapping categories to skills and their synonyms

    Example:
        >>> taxonomy = load_skill_taxonomy()
        >>> taxonomy["databases"]["PostgreSQL"]
        ["PostgreSQL", "Postgres", "Postgres SQL"]
    """
    try:
        with open(SKILL_TAXONOMY_FILE, "r", encoding="utf-8") as f:
            taxonomy_data = json.load(f)

        logger.info(f"Loaded skill taxonomy with {len(taxonomy_data)} categories")
        return taxonomy_data

    except FileNotFoundError:
        logger.warning(f"Skill taxonomy file not found: {SKILL_TAXONOMY_FILE}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing skill taxonomy JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading skill taxonomy: {e}", exc_info=True)
        return {}


def normalize_skill_name(skill: str) -> str:
    """
    Normalize a skill name for consistent comparison.

    Removes extra whitespace, converts to lowercase, handles
    common variations in capitalization and spacing, and removes
    special characters that do not affect meaning.

    Args:
        skill: The skill name to normalize

    Returns:
        Normalized skill name

    Example:
        >>> normalize_skill_name("  React JS  ")
        "react js"
    """
    # Remove extra whitespace and convert to lowercase
    normalized = " ".join(skill.strip().lower().split())

    # Remove common punctuation that does not affect meaning
    # Keep: letters, numbers, spaces, dots, plus, hash
    normalized = "".join(c for c in normalized if c.isalnum() or c in " .+#")

    return normalized


def calculate_fuzzy_similarity(skill1: str, skill2: str) -> float:
    """
    Calculate fuzzy similarity between two skill names.

    Uses SequenceMatcher to determine how similar two strings are,
    useful for detecting typos and minor variations in skill names.

    Args:
        skill1: First skill name
        skill2: Second skill name

    Returns:
        Similarity score between 0.0 and 1.0

    Example:
        >>> calculate_fuzzy_similarity("React", "ReactJS")
        0.75
    """
    norm1 = normalize_skill_name(skill1)
    norm2 = normalize_skill_name(skill2)

    return SequenceMatcher(None, norm1, norm2).ratio()


def find_canonical_skill(
    linkedin_skill: str,
    taxonomy: Dict[str, Dict[str, List[str]]],
    fuzzy_threshold: float = 0.75
) -> Optional[Tuple[str, str, float]]:
    """
    Find the canonical skill name and category for a LinkedIn skill.

    Searches through the taxonomy to find if a LinkedIn skill matches
    any canonical skill or its synonyms. Uses both exact matching and
    fuzzy matching for robust mapping.

    Args:
        linkedin_skill: Skill name from LinkedIn profile
        taxonomy: Skill taxonomy dictionary
        fuzzy_threshold: Minimum similarity score for fuzzy matching (0.0-1.0)

    Returns:
        Tuple of (category, canonical_skill, confidence) or None if no match found
        - category: The skill category (e.g., "databases", "programming_languages")
        - canonical_skill: The canonical name for the skill
        - confidence: Match confidence (1.0 for exact, <1.0 for fuzzy)

    Example:
        >>> taxonomy = load_skill_taxonomy()
        >>> find_canonical_skill("ReactJS", taxonomy)
        ("web_frameworks", "React", 1.0)
        >>> find_canonical_skill("React.js", taxonomy)
        ("web_frameworks", "React", 1.0)
        >>> find_canonical_skill("ReactJS Framework", taxonomy)
        ("web_frameworks", "React", 0.85)
    """
    normalized_linkedin = normalize_skill_name(linkedin_skill)

    # Search for exact or synonym match
    for category, skills in taxonomy.items():
        if not isinstance(skills, dict):
            continue

        for canonical_name, synonyms_list in skills.items():
            if not isinstance(synonyms_list, list):
                continue

            # Check canonical name
            normalized_canonical = normalize_skill_name(canonical_name)
            if normalized_canonical == normalized_linkedin:
                return (category, canonical_name, 1.0)

            # Check all synonyms
            for synonym in synonyms_list:
                normalized_synonym = normalize_skill_name(synonym)
                if normalized_synonym == normalized_linkedin:
                    return (category, canonical_name, 1.0)

    # If no exact match, try fuzzy matching
    best_match = None
    best_similarity = 0.0

    for category, skills in taxonomy.items():
        if not isinstance(skills, dict):
            continue

        for canonical_name, synonyms_list in skills.items():
            if not isinstance(synonyms_list, list):
                continue

            # Check canonical name similarity
            canonical_similarity = calculate_fuzzy_similarity(linkedin_skill, canonical_name)
            if canonical_similarity > best_similarity and canonical_similarity >= fuzzy_threshold:
                best_similarity = canonical_similarity
                best_match = (category, canonical_name, round(canonical_similarity, 2))

            # Check synonym similarity
            for synonym in synonyms_list:
                synonym_similarity = calculate_fuzzy_similarity(linkedin_skill, synonym)
                if synonym_similarity > best_similarity and synonym_similarity >= fuzzy_threshold:
                    best_similarity = synonym_similarity
                    best_match = (category, canonical_name, round(synonym_similarity, 2))

    return best_match


def map_linkedin_skills_to_taxonomy(
    linkedin_skills: List[str],
    fuzzy_threshold: float = 0.75,
    min_confidence: float = 0.6
) -> Dict[str, Any]:
    """
    Map LinkedIn skills to internal skill taxonomy.

    This function takes a list of skills extracted from a LinkedIn profile
    and maps them to the canonical skill taxonomy used by the application.
    It uses both exact matching (for synonyms and variations) and fuzzy
    matching (for typos and minor variations).

    Mapping Strategy:
    1. Exact match: LinkedIn skill exactly matches canonical name or synonym (confidence: 1.0)
    2. Fuzzy match: LinkedIn skill is similar to canonical name (confidence: 0.6-0.99)
    3. Unmapped: LinkedIn skill does not match any known skill (confidence: 0.0)

    Args:
        linkedin_skills: List of skill names from LinkedIn profile
        fuzzy_threshold: Minimum similarity score for fuzzy matching (default: 0.75)
        min_confidence: Minimum confidence threshold to include a skill (default: 0.6)

    Returns:
        Dictionary containing:
        - mapped_skills: List of successfully mapped skills with metadata
        - unmapped_skills: List of skills that could not be mapped
        - statistics: Mapping statistics (total, mapped, unmapped, mapping_rate)
        - categories: Dictionary of skills grouped by category

        Each mapped skill contains:
        - original: Original skill name from LinkedIn
        - canonical: Canonical skill name from taxonomy
        - category: Skill category
        - confidence: Match confidence (0.0-1.0)

    Example:
        >>> result = map_linkedin_skills_to_taxonomy([
        ...     "ReactJS",
        ...     "Postgres",
        ...     "AWS Lambda",
        ...     "Unknown Framework"
        ... ])
        >>> result["statistics"]["mapping_rate"]
        0.75
        >>> result["mapped_skills"][0]
        {
            "original": "ReactJS",
            "canonical": "React",
            "category": "web_frameworks",
            "confidence": 1.0
        }
    """
    if not linkedin_skills:
        return {
            "mapped_skills": [],
            "unmapped_skills": [],
            "statistics": {
                "total": 0,
                "mapped": 0,
                "unmapped": 0,
                "mapping_rate": 0.0
            },
            "categories": {}
        }

    # Load skill taxonomy
    taxonomy = load_skill_taxonomy()

    if not taxonomy:
        logger.warning("Skill taxonomy not available, returning all skills as unmapped")
        return {
            "mapped_skills": [],
            "unmapped_skills": linkedin_skills,
            "statistics": {
                "total": len(linkedin_skills),
                "mapped": 0,
                "unmapped": len(linkedin_skills),
                "mapping_rate": 0.0
            },
            "categories": {}
        }

    mapped_skills = []
    unmapped_skills = []
    skills_by_category: Dict[str, List[Dict[str, Any]]] = {}

    # Map each LinkedIn skill to taxonomy
    for linkedin_skill in linkedin_skills:
        if not linkedin_skill or not isinstance(linkedin_skill, str):
            continue

        # Find canonical skill
        match_result = find_canonical_skill(
            linkedin_skill,
            taxonomy,
            fuzzy_threshold=fuzzy_threshold
        )

        if match_result and match_result[2] >= min_confidence:
            category, canonical_name, confidence = match_result

            mapped_skill = {
                "original": linkedin_skill,
                "canonical": canonical_name,
                "category": category,
                "confidence": confidence
            }

            mapped_skills.append(mapped_skill)

            # Group by category
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(mapped_skill)

            logger.debug(
                f"Mapped skill {linkedin_skill} to {canonical_name} "
                f"in category {category} (confidence: {confidence})"
            )
        else:
            unmapped_skills.append(linkedin_skill)
            logger.debug(f"Could not map skill {linkedin_skill} to taxonomy")

    # Calculate statistics
    total_skills = len(linkedin_skills)
    mapped_count = len(mapped_skills)
    unmapped_count = len(unmapped_skills)
    mapping_rate = round(mapped_count / total_skills, 2) if total_skills > 0 else 0.0

    result = {
        "mapped_skills": mapped_skills,
        "unmapped_skills": unmapped_skills,
        "statistics": {
            "total": total_skills,
            "mapped": mapped_count,
            "unmapped": unmapped_count,
            "mapping_rate": mapping_rate
        },
        "categories": skills_by_category
    }

    logger.info(
        f"Skill mapping complete: {mapped_count}/{total_skills} skills mapped "
        f"({mapping_rate * 100:.1f}% mapping rate)"
    )

    return result

