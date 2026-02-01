#!/usr/bin/env python3
"""
Seed preset weight profiles for matching algorithms.
Creates Technical, Creative, and Executive preset profiles if they don't exist.
"""
import asyncio
import sys
import os
import uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_maker
from models.matching_weights_profile import MatchingWeightsProfile
from sqlalchemy import select


# Preset profiles configuration
PRESET_PROFILES = [
    {
        "name": "Technical",
        "description": "Keyword-heavy matching for technical roles. Ensures candidates have exact skill requirements. Best for: Software engineers, DevOps, data scientists, QA engineers.",
        "keyword_weight": 0.60,
        "tfidf_weight": 0.25,
        "vector_weight": 0.15,
        "preset_type": "technical",
    },
    {
        "name": "Creative",
        "description": "Vector similarity-heavy matching for creative roles. Finds candidates with relevant conceptual experience. Best for: Designers, content creators, marketing roles, UX researchers.",
        "keyword_weight": 0.15,
        "tfidf_weight": 0.25,
        "vector_weight": 0.60,
        "preset_type": "creative",
    },
    {
        "name": "Executive",
        "description": "Balanced matching for executive and leadership roles. Combines precise skills, contextual understanding, and semantic similarity. Best for: C-level executives, directors, senior managers.",
        "keyword_weight": 0.34,
        "tfidf_weight": 0.33,
        "vector_weight": 0.33,
        "preset_type": "executive",
    },
    {
        "name": "Balanced",
        "description": "Balanced matching for general roles. Equal weight across all matching algorithms. Best for: General positions, when unsure of which profile to use.",
        "keyword_weight": 0.33,
        "tfidf_weight": 0.34,
        "vector_weight": 0.33,
        "preset_type": "balanced",
    },
]


async def seed_profiles():
    """Seed preset weight profiles."""
    print("=" * 60)
    print("SEEDING PRESET WEIGHT PROFILES")
    print("=" * 60)
    print()

    async with async_session_maker() as db:
        created_count = 0
        skipped_count = 0

        for preset in PRESET_PROFILES:
            preset_type = preset["preset_type"]

            # Check if profile already exists
            existing = await db.execute(
                select(MatchingWeightsProfile).where(
                    MatchingWeightsProfile.is_preset == True,
                    MatchingWeightsProfile.preset_type == preset_type,
                )
            )
            existing_profile = existing.scalar_one_or_none()

            if existing_profile:
                print(f"  ✓ Skipped: {preset['name']} profile (already exists)")
                skipped_count += 1
            else:
                # Create new preset profile
                profile = MatchingWeightsProfile(
                    id=uuid.uuid4(),
                    organization_id="system",  # System-wide presets
                    name=preset["name"],
                    description=preset["description"],
                    keyword_weight=preset["keyword_weight"],
                    tfidf_weight=preset["tfidf_weight"],
                    vector_weight=preset["vector_weight"],
                    is_default=False,  # Not default by default
                    is_preset=True,
                    preset_type=preset["preset_type"],
                    created_by=None,  # System-created
                )
                db.add(profile)
                await db.flush()

                print(f"  + Created: {preset['name']} profile")
                print(f"    Keyword: {preset['keyword_weight']:.0%}")
                print(f"    TF-IDF:  {preset['tfidf_weight']:.0%}")
                print(f"    Vector:  {preset['vector_weight']:.0%}")
                print()
                created_count += 1

        await db.commit()

        print("=" * 60)
        print(f"COMPLETE: {created_count} created, {skipped_count} skipped")
        print("=" * 60)


async def list_profiles():
    """List all preset profiles."""
    print("\nCurrent preset profiles:")
    print("-" * 60)

    async with async_session_maker() as db:
        result = await db.execute(
            select(MatchingWeightsProfile)
            .where(MatchingWeightsProfile.is_preset == True)
            .order_by(MatchingWeightsProfile.preset_type)
        )
        profiles = result.scalars().all()

        if profiles:
            for profile in profiles:
                print(f"\n{profile.name} ({profile.preset_type})")
                print(f"  Description: {profile.description}")
                print(f"  Weights: Keyword={profile.keyword_weight:.0%}, "
                      f"TF-IDF={profile.tfidf_weight:.0%}, "
                      f"Vector={profile.vector_weight:.0%}")
                print(f"  Default: {profile.is_default}")
        else:
            print("  No preset profiles found")


async def main():
    """Main function."""
    await seed_profiles()
    await list_profiles()


if __name__ == "__main__":
    asyncio.run(main())
