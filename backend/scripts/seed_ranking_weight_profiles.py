#!/usr/bin/env python3
"""
Seed preset ranking weight profiles for ranking algorithm.
Creates Technical, Sales, Executive, and Balanced preset profiles if they don't exist.
"""
import asyncio
import sys
import os
import uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_maker
from models.ranking_weights_profile import RankingWeightProfile
from sqlalchemy import select


# Preset profiles configuration
PRESET_PROFILES = [
    {
        "name": "Technical",
        "description": "Optimized for technical roles - prioritizes skills match, keyword matching, and education. Best for: Software engineers, DevOps, data scientists, QA engineers.",
        "preset_type": "technical",
        "overall_match_score_weight": 0.15,
        "keyword_score_weight": 0.15,
        "tfidf_score_weight": 0.10,
        "vector_score_weight": 0.08,
        "skills_match_ratio_weight": 0.25,
        "experience_months_weight": 0.05,
        "experience_relevance_weight": 0.10,
        "education_level_weight": 0.08,
        "recent_experience_weight": 0.02,
        "skill_rarity_weight": 0.01,
        "title_similarity_weight": 0.01,
        "freshness_score_weight": 0.00,
        "completeness_score_weight": 0.00,
    },
    {
        "name": "Sales",
        "description": "Optimized for sales roles - prioritizes title similarity, experience relevance, and recent activity. Best for: Sales representatives, account executives, business development, customer success.",
        "preset_type": "sales",
        "overall_match_score_weight": 0.12,
        "keyword_score_weight": 0.08,
        "tfidf_score_weight": 0.06,
        "vector_score_weight": 0.05,
        "skills_match_ratio_weight": 0.10,
        "experience_months_weight": 0.12,
        "experience_relevance_weight": 0.20,
        "education_level_weight": 0.05,
        "recent_experience_weight": 0.10,
        "skill_rarity_weight": 0.02,
        "title_similarity_weight": 0.08,
        "freshness_score_weight": 0.01,
        "completeness_score_weight": 0.01,
    },
    {
        "name": "Executive",
        "description": "Optimized for executive/leadership roles - prioritizes experience, education, and title similarity. Best for: C-level executives, VPs, directors, senior managers.",
        "preset_type": "executive",
        "overall_match_score_weight": 0.10,
        "keyword_score_weight": 0.05,
        "tfidf_score_weight": 0.05,
        "vector_score_weight": 0.05,
        "skills_match_ratio_weight": 0.08,
        "experience_months_weight": 0.20,
        "experience_relevance_weight": 0.22,
        "education_level_weight": 0.12,
        "recent_experience_weight": 0.05,
        "skill_rarity_weight": 0.01,
        "title_similarity_weight": 0.06,
        "freshness_score_weight": 0.00,
        "completeness_score_weight": 0.01,
    },
    {
        "name": "Balanced",
        "description": "Equal consideration of all ranking factors for general-purpose hiring. Best for: General positions, when unsure of which profile to use.",
        "preset_type": "balanced",
        "overall_match_score_weight": 0.077,
        "keyword_score_weight": 0.077,
        "tfidf_score_weight": 0.077,
        "vector_score_weight": 0.077,
        "skills_match_ratio_weight": 0.077,
        "experience_months_weight": 0.077,
        "experience_relevance_weight": 0.077,
        "education_level_weight": 0.077,
        "recent_experience_weight": 0.077,
        "skill_rarity_weight": 0.077,
        "title_similarity_weight": 0.077,
        "freshness_score_weight": 0.077,
        "completeness_score_weight": 0.076,
    },
]


async def seed_profiles():
    """Seed preset ranking weight profiles."""
    print("=" * 60)
    print("SEEDING PRESET RANKING WEIGHT PROFILES")
    print("=" * 60)
    print()

    async with async_session_maker() as db:
        created_count = 0
        skipped_count = 0

        for preset in PRESET_PROFILES:
            preset_type = preset["preset_type"]

            # Check if profile already exists
            existing = await db.execute(
                select(RankingWeightProfile).where(
                    RankingWeightProfile.is_preset == True,
                    RankingWeightProfile.preset_type == preset_type,
                )
            )
            existing_profile = existing.scalar_one_or_none()

            if existing_profile:
                print(f"  ✓ Skipped: {preset['name']} profile (already exists)")
                skipped_count += 1
            else:
                # Create new preset profile
                profile = RankingWeightProfile(
                    id=uuid.uuid4(),
                    organization_id="system",  # System-wide presets
                    name=preset["name"],
                    description=preset["description"],
                    is_preset=True,
                    preset_type=preset["preset_type"],
                    is_active=True,
                    overall_match_score_weight=preset["overall_match_score_weight"],
                    keyword_score_weight=preset["keyword_score_weight"],
                    tfidf_score_weight=preset["tfidf_score_weight"],
                    vector_score_weight=preset["vector_score_weight"],
                    skills_match_ratio_weight=preset["skills_match_ratio_weight"],
                    experience_months_weight=preset["experience_months_weight"],
                    experience_relevance_weight=preset["experience_relevance_weight"],
                    education_level_weight=preset["education_level_weight"],
                    recent_experience_weight=preset["recent_experience_weight"],
                    skill_rarity_weight=preset["skill_rarity_weight"],
                    title_similarity_weight=preset["title_similarity_weight"],
                    freshness_score_weight=preset["freshness_score_weight"],
                    completeness_score_weight=preset["completeness_score_weight"],
                    created_by=None,  # System-created
                )
                db.add(profile)
                await db.flush()

                print(f"  + Created: {preset['name']} profile")
                print(f"    Skills Match: {preset['skills_match_ratio_weight']:.0%}")
                print(f"    Overall Match: {preset['overall_match_score_weight']:.0%}")
                print(f"    Experience Relevance: {preset['experience_relevance_weight']:.0%}")
                print()
                created_count += 1

        await db.commit()

        print("=" * 60)
        print(f"COMPLETE: {created_count} created, {skipped_count} skipped")
        print("=" * 60)


async def list_profiles():
    """List all preset profiles."""
    print("\nCurrent preset ranking weight profiles:")
    print("-" * 60)

    async with async_session_maker() as db:
        result = await db.execute(
            select(RankingWeightProfile)
            .where(RankingWeightProfile.is_preset == True)
            .order_by(RankingWeightProfile.preset_type)
        )
        profiles = result.scalars().all()

        if profiles:
            for profile in profiles:
                print(f"\n{profile.name} ({profile.preset_type})")
                print(f"  Description: {profile.description}")
                print(f"  Top Weights:")
                print(f"    - Skills Match: {profile.skills_match_ratio_weight:.0%}")
                print(f"    - Overall Match: {profile.overall_match_score_weight:.0%}")
                print(f"    - Experience Relevance: {profile.experience_relevance_weight:.0%}")
                print(f"    - Keyword: {profile.keyword_score_weight:.0%}")
                print(f"  Active: {profile.is_active}")
        else:
            print("  No preset ranking weight profiles found")


async def main():
    """Main function."""
    await seed_profiles()
    await list_profiles()


if __name__ == "__main__":
    asyncio.run(main())
