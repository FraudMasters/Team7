"""
Industry classification endpoints.

This module provides endpoints for classifying job postings into industries
based on job title and description using keyword matching and ML-based scoring.
"""
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# Define supported industries
INDUSTRIES = [
    "healthcare",
    "finance",
    "marketing",
    "manufacturing",
    "sales",
    "design",
    "technology",  # Fallback for tech-related jobs
]


class ClassifyRequest(BaseModel):
    """Request model for industry classification."""

    title: str = Field(..., description="Job title", min_length=1, max_length=500)
    description: str = Field(..., description="Job description", min_length=1, max_length=10000)


class IndustryMatch(BaseModel):
    """Industry match result."""

    industry: str = Field(..., description="Industry name")
    confidence: float = Field(..., description="Confidence score (0-1)")


class ClassifyResponse(BaseModel):
    """Response model for industry classification."""

    industry: str = Field(..., description="Detected industry")
    confidence: float = Field(..., description="Confidence score (0-1)")
    all_matches: List[IndustryMatch] = Field(..., description="All industry matches ranked by confidence")
    keywords_matched: Dict[str, List[str]] = Field(..., description="Keywords matched per industry")


class IndustryClassifier:
    """
    Industry classifier using keyword matching and scoring.

    Uses industry taxonomy data to classify job postings into industries
    based on keyword frequency and relevance scoring.
    """

    def __init__(self):
        """Initialize classifier with industry keywords."""
        self.industry_keywords: Dict[str, List[str]] = {}
        self.industry_titles: Dict[str, List[str]] = {}
        self._load_industry_data()

    def _load_industry_data(self):
        """Load industry keywords from taxonomy files."""
        taxonomy_dir = Path(__file__).parent.parent / "data" / "industry_taxonomies"

        for industry in INDUSTRIES:
            if industry == "technology":
                # Technology uses a different set of keywords
                self.industry_keywords[industry] = self._get_tech_keywords()
                self.industry_titles[industry] = self._get_tech_titles()
                continue

            taxonomy_file = taxonomy_dir / f"{industry}_taxonomy.json"

            if taxonomy_file.exists():
                try:
                    with open(taxonomy_file, "r") as f:
                        taxonomy_data = json.load(f)

                    # Extract all skill variants as keywords
                    keywords = set()
                    for category, skills in taxonomy_data.items():
                        for skill_name, variants in skills.items():
                            keywords.add(skill_name.lower())
                            if isinstance(variants, list):
                                keywords.update(v.lower() for v in variants)
                            else:
                                keywords.add(variants.lower())

                    self.industry_keywords[industry] = list(keywords)

                    # Extract common job titles
                    self.industry_titles[industry] = self._get_industry_titles(industry)

                    logger.info(f"Loaded {len(keywords)} keywords for {industry}")
                except Exception as e:
                    logger.error(f"Error loading {industry} taxonomy: {e}")
                    self.industry_keywords[industry] = []
                    self.industry_titles[industry] = []
            else:
                logger.warning(f"Taxonomy file not found: {taxonomy_file}")
                self.industry_keywords[industry] = []
                self.industry_titles[industry] = []

    def _get_industry_titles(self, industry: str) -> List[str]:
        """Get common job titles for an industry."""
        titles_map = {
            "healthcare": [
                "nurse", "rn", "registered nurse", "doctor", "physician",
                "surgeon", "medical", "healthcare", "health", "patient care",
                "clinical", "pharmacist", "therapist", "dentist", "veterinarian",
            ],
            "finance": [
                "accountant", "financial analyst", "cfo", "finance manager",
                "investment banker", "financial advisor", "actuary", "auditor",
                "tax", "banking", "controller", "treasurer",
            ],
            "marketing": [
                "marketing manager", "digital marketing", "seo", "content marketer",
                "brand manager", "social media", "marketing coordinator", "cmo",
                "advertising", "public relations", "copywriter", "growth hacker",
            ],
            "manufacturing": [
                "production manager", "manufacturing engineer", "plant manager",
                "quality control", "assembly", "machinist", "operator",
                "production supervisor", "lean manufacturing", "process engineer",
            ],
            "sales": [
                "sales representative", "account executive", "sales manager",
                "business development", "sales director", "vp sales", "account manager",
                "inside sales", "field sales", "sales engineer",
            ],
            "design": [
                "ux designer", "ui designer", "graphic designer", "product designer",
                "visual designer", "art director", "creative director", "design lead",
                "web designer", "illustrator", "designer",
            ],
            "technology": [
                "software engineer", "developer", "programmer", "full stack",
                "frontend", "backend", "devops", "sre", "data scientist",
                "machine learning", "qa engineer", "mobile developer",
            ],
        }
        return titles_map.get(industry, [])

    def _get_tech_keywords(self) -> List[str]:
        """Get technology-related keywords."""
        return [
            # Programming languages
            "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php",
            "go", "rust", "swift", "kotlin", "scala", "r", "matlab",
            # Frameworks
            "react", "angular", "vue", "django", "flask", "spring", "express",
            "rails", "laravel", "fastapi", "next.js", "nuxt",
            # Databases
            "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "terraform",
            "jenkins", "ansible", "linux", "git",
            # Data & ML
            "machine learning", "data science", "ai", "deep learning", "nlp",
            "tensorflow", "pytorch", "pandas", "numpy", "spark", "hadoop",
            # Other
            "api", "rest", "graphql", "microservices", "agile", "scrum",
        ]

    def _get_tech_titles(self) -> List[str]:
        """Get technology job titles."""
        return self._get_industry_titles("technology")

    def classify(self, title: str, description: str) -> Dict:
        """
        Classify a job posting into industry.

        Args:
            title: Job title
            description: Job description

        Returns:
            Dictionary with classification results
        """
        # Combine title and description, weight title higher
        text = f"{title.lower()} {title.lower()} {description.lower()}"

        # Tokenize into words
        words = set(text.split())

        # Score each industry
        scores = {}
        keywords_matched = {}

        for industry in INDUSTRIES:
            # Check title matches (higher weight)
            title_score = 0
            for job_title in self.industry_titles.get(industry, []):
                if job_title in title.lower():
                    title_score += 10

            # Check keyword matches
            industry_keywords = self.industry_keywords.get(industry, [])
            matched = [kw for kw in industry_keywords if kw in words or any(kw in word for word in words)]

            keyword_score = len(matched)

            # Normalize by keyword count to avoid bias toward industries with more keywords
            if industry_keywords:
                normalized_score = (keyword_score / len(industry_keywords)) * 100
            else:
                normalized_score = 0

            # Combine scores
            total_score = title_score * 5 + normalized_score * 2
            scores[industry] = total_score

            if matched:
                keywords_matched[industry] = matched[:10]  # Top 10 matches

        # Convert scores to confidence (0-1)
        max_score = max(scores.values()) if scores.values() else 0
        if max_score > 0:
            confidences = {
                industry: min(score / max_score, 1.0)
                for industry, score in scores.items()
            }
        else:
            # Default to technology if no matches
            confidences = {industry: 0.0 for industry in INDUSTRIES}
            confidences["technology"] = 0.3

        # Sort by confidence
        sorted_matches = sorted(
            [{"industry": ind, "confidence": conf} for ind, conf in confidences.items()],
            key=lambda x: x["confidence"],
            reverse=True,
        )

        # Get top match
        top_match = sorted_matches[0]

        return {
            "industry": top_match["industry"],
            "confidence": round(top_match["confidence"], 2),
            "all_matches": sorted_matches,
            "keywords_matched": keywords_matched,
        }


# Initialize classifier singleton
classifier = IndustryClassifier()


@router.post(
    "/classify",
    response_model=ClassifyResponse,
    tags=["Industry Classifier"],
)
async def classify_industry(request: ClassifyRequest) -> JSONResponse:
    """
    Classify job posting into industry.

    This endpoint analyzes job title and description to determine which industry
    the job belongs to using keyword matching and ML-based scoring. Returns the
    detected industry with confidence score and all ranked matches.

    Args:
        request: Classification request with title and description

    Returns:
        JSON response with detected industry, confidence, and match details

    Raises:
        HTTPException(500): If classification fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/industry-classifier/classify",
        ...     json={
        ...         "title": "Senior Registered Nurse",
        ...         "description": "Looking for an experienced RN with ICU experience..."
        ...     }
        ... )
        >>> response.json()
        {
            "industry": "healthcare",
            "confidence": 0.95,
            "all_matches": [
                {"industry": "healthcare", "confidence": 0.95},
                {"industry": "technology", "confidence": 0.12},
                ...
            ],
            "keywords_matched": {
                "healthcare": ["rn", "patient", "care", "clinical", ...]
            }
        }
    """
    try:
        logger.info(f"Classifying job - title: {request.title[:50]}...")

        # Perform classification
        result = classifier.classify(request.title, request.description)

        logger.info(f"Classified as {result['industry']} with confidence {result['confidence']}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result,
        )

    except Exception as e:
        logger.error(f"Error classifying industry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify industry: {str(e)}",
        ) from e


@router.get(
    "/industries",
    tags=["Industry Classifier"],
)
async def list_industries() -> JSONResponse:
    """
    List all supported industries.

    Returns a list of all industries that the classifier can detect.

    Returns:
        JSON response with list of supported industries

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/industry-classifier/industries")
        >>> response.json()
        {
            "industries": [
                "healthcare",
                "finance",
                "marketing",
                "manufacturing",
                "sales",
                "design",
                "technology"
            ]
        }
    """
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"industries": INDUSTRIES},
        )
    except Exception as e:
        logger.error(f"Error listing industries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list industries: {str(e)}",
        ) from e
