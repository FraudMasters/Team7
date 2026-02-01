"""
Demographic Inference Analyzer for Bias Detection

This module provides AI-based demographic inference from resume text for fairness monitoring.
It infers:
- Gender from name patterns and pronouns
- Age group from graduation dates and career timeline
- Ethnicity indicators from name patterns (for bias detection)
- Geographic region from location data
- Education level and career stage

IMPORTANT: All inferences are probabilistic estimates used solely for detecting
and mitigating algorithmic bias in the hiring process. Individual predictions are
NOT used for hiring decisions and are stored with privacy protections.
"""
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import DemographicInference, Resume, ResumeAnalysis

logger = logging.getLogger(__name__)


class DemographicAnalyzer:
    """
    Analyze resumes to infer demographic attributes for bias detection.

    Uses probabilistic methods to infer demographic attributes from resume text,
    names, dates, and patterns. All inferences include confidence scores.

    Privacy-First Design:
    - Inferences are used ONLY for aggregate bias analysis
    - Individual predictions are NEVER used in hiring decisions
    - All predictions are probabilistic with documented uncertainty
    - Raw data is retained for audit and re-analysis with improved models
    """

    # Gender name patterns (simplified heuristic - not 100% accurate)
    GENDER_PATTERNS = {
        "male": {
            "first_names": {
                "james", "john", "robert", "michael", "william", "david", "richard",
                "joseph", "thomas", "charles", "christopher", "daniel", "matthew",
                "anthony", "donald", "mark", "paul", "steven", "andrew", "kenneth",
                "joshua", "kevin", "brian", "george", "edward", "ronald", "timothy",
                "jason", "jeffrey", "ryan", "jacob", "gary", "nicholas", "eric",
                "jonathan", "stephen", "larry", "justin", "scott", "brandon", "benjamin",
                "samuel", "frank", "gregory", "raymond", "alexander", "patrick", "jack",
                "dennis", "jerry", "tyler", "aaron", "jose", "adam", "henry", "nathan",
                "douglas", "zachary", "peter", "kyle", "walter", "ethan", "jeremy",
                "harold", "keith", "christian", "roger", "noah", "gerald", "terry",
                "sean", "austin", "arthur", "lawrence", "jesse", "dylan", "bryan",
                "joe", "jordan", "billy", "bruce", "albert", "willie", "gabriel",
                "logan", "alan", "juan", "wayne", "roy", "ralph", "randy", "eugene",
                "vincent", "russell", "louis", "philip", "bobby", "johnny", "bradley",
            },
            "pronouns": {"he", "him", "his", "himself"},
            "honorifics": {"mr", "mr."},
        },
        "female": {
            "first_names": {
                "mary", "patricia", "jennifer", "linda", "elizabeth", "barbara",
                "susan", "jessica", "sarah", "karen", "lisa", "nancy", "betty",
                "margaret", "sandra", "ashley", "kimberly", "emily", "donna",
                "michelle", "dorothy", "carol", "amanda", "melissa", "deborah",
                "stephanie", "rebecca", "sharon", "laura", "cynthia", "kathleen",
                "amy", "shirley", "angela", "helen", "anna", "brenda", "pamela",
                "nicole", "emma", "samantha", "katherine", "christine", "debra",
                "rachel", "catherine", "carolyn", "janet", "ruth", "maria", "heather",
                "diane", "virginia", "julie", "joyce", "victoria", "olivia", "kelly",
                "christina", "lauren", "joan", "evelyn", "judith", "megan", "cheryl",
                "andrea", "hannah", "martha", "jacqueline", "frances", "gloria",
                "ann", "teresa", "kathryn", "sara", "janice", "alice", "madison",
                "doris", "abigail", "julia", "judy", "grace", "denise", "amber",
                "marilyn", "beverly", "danielle", "theresa", "sophia", "marie",
                "diana", "brittany", "natalie", "isabella", "charlotte", "rose",
                "alex", "morgan", "taylor", "tori", "courtney", "ashley", "lindsay",
            },
            "pronouns": {"she", "her", "hers", "herself"},
            "honorifics": {"ms", "mrs", "ms.", "mrs.", "miss"},
        },
    }

    # Ethnicity/race patterns based on name analysis (simplified)
    # This is deliberately coarse-grained and used only for aggregate bias detection
    ETHNICITY_PATTERNS = {
        "asian": {
            "surnames": {
                "lee", "kim", "wang", "zhang", "liu", "chen", "yang", "zhao", "huang",
                "wu", "zhou", "xu", "sun", "tan", "nguyen", "tran", "pham", "le",
                "hoang", "bui", "bao", "cai", "chang", "cho", "choi", "chong",
                "chuang", "feng", "gao", "han", "hou", "jian", "jin", "kang",
                "kuo", "lai", "lin", "ma", "okamoto", "park", "peng", "qian",
                "shi", "song", "su", "tsai", "wang", "wei", "wen", "wu", "xia",
                "xie", "xu", "yan", "yang", "yao", "yuan", "zeng", "zhang", "zhou",
                "zhu", "sato", "suzuki", "takahashi", "tanaka", "watanabe", "ito",
                "yamamoto", "nakamura", "kobayashi", "hayashi", "yamaguchi", "mori",
            },
        },
        "hispanic": {
            "surnames": {
                "garcia", "rodriguez", "martinez", "hernandez", "lopez", "gonzalez",
                "perez", "sanchez", "ramirez", "cruz", "rivera", "torres", "flores",
                "reyes", "gonzales", "ramos", "diaz", "molina", "ruiz", "ortega",
                "guerrero", "vasquez", "castillo", "mendoza", "medina", "riviera",
                "castro", "espinoza", "rangel", "cordova", "munoz", "rios", "reyes",
                "vargas", "dominguez", "herrera", "velasquez", "fuentes", "mora",
                "cortez", "valdez", "aguilar", "miranda", "padilla", "bravo", "delgado",
            },
        },
        "black_african": {
            "surnames": {
                "smith", "johnson", "williams", "brown", "jones", "davis", "jackson",
                "harris", "thomas", "robinson", "white", "clark", "walker", "hall",
                "allen", "young", "king", "wright", "scott", "green", "baker", "adams",
                "nelson", "hill", "moore", "mitchell", "roberts", "carter", "phillips",
                "evans", "turner", "torrence", "parker", "collins", "edwards", "stewart",
                "morris", "murphy", "cook", "rogers", "washington", "jefferson",
            },
        },
    }

    # Geographic region patterns
    REGIONAL_PATTERNS = {
        "usa_northeast": {
            "states": {
                "maine", "new hampshire", "vermont", "massachusetts", "rhode island",
                "connecticut", "new york", "new jersey", "pennsylvania",
            },
            "cities": {"boston", "new york", "philadelphia", "pittsburgh", "hartford"},
        },
        "usa_south": {
            "states": {
                "delaware", "maryland", "virginia", "west virginia", "kentucky",
                "north carolina", "south carolina", "tennessee", "georgia", "alabama",
                "mississippi", "arkansas", "louisiana", "florida", "texas", "oklahoma",
            },
            "cities": {"atlanta", "charlotte", "miami", "dallas", "houston", "nashville", "austin"},
        },
        "usa_midwest": {
            "states": {
                "ohio", "michigan", "indiana", "illinois", "wisconsin", "minnesota",
                "iowa", "missouri", "kansas", "nebraska", "south dakota", "north dakota",
            },
            "cities": {"chicago", "detroit", "minneapolis", "st. louis", "cleveland", "indianapolis"},
        },
        "usa_west": {
            "states": {
                "montana", "idaho", "wyoming", "colorado", "new mexico", "arizona",
                "utah", "nevada", "california", "oregon", "washington", "alaska", "hawaii",
            },
            "cities": {"los angeles", "san francisco", "seattle", "denver", "phoenix", "portland", "san diego"},
        },
        "international": {
            "countries": {
                "canada", "uk", "united kingdom", "england", "scotland", "wales",
                "ireland", "australia", "germany", "france", "spain", "italy",
                "netherlands", "india", "china", "japan", "singapore", "brazil",
                "mexico", "argentina", "south africa", "kenya", "nigeria",
            },
        },
    }

    # Education level patterns
    EDUCATION_PATTERNS = {
        "doctoral": {
            "keywords": {"ph.d", "phd", "doctor", "doctorate", "md", "juris doctor", "jd"},
            "degree_prefixes": {"doctor of", "ph.d in", "phd in"},
        },
        "masters": {
            "keywords": {"master", "m.s", "msc", "m.sc", "mba", "mfa", "mph"},
            "degree_prefixes": {"master of", "ms in", "m.sc in", "mba"},
        },
        "bachelors": {
            "keywords": {"bachelor", "b.s", "b.sc", "ba", "b.a", "bs", "bse", "beng"},
            "degree_prefixes": {"bachelor of", "bs in", "b.sc in", "ba in"},
        },
        "associate": {
            "keywords": {"associate", "a.a", "a.s", "aas"},
            "degree_prefixes": {"associate of", "aa in", "as in"},
        },
        "high_school": {
            "keywords": {"high school", "ged", "diploma", "secondary school"},
            "degree_prefixes": {"high school diploma"},
        },
    }

    # Career stage patterns
    CAREER_STAGE_PATTERNS = {
        "executive": {
            "keywords": {"ceo", "cto", "cfo", "chief", "vp", "vice president", "director",
                        "head of", "president", "executive", "c-level"},
            "min_experience_years": 15,
        },
        "senior": {
            "keywords": {"senior", "sr.", "sr ", "lead", "principal", "staff", "architect"},
            "min_experience_years": 10,
        },
        "mid": {
            "keywords": {"mid-level", "experienced", "developer", "engineer", "manager"},
            "min_experience_years": 5,
        },
        "entry": {
            "keywords": {"junior", "jr.", "jr ", "entry level", "associate", "assistant", "intern"},
            "min_experience_years": 0,
        },
    }

    # Age group calculations based on graduation year
    # Assumes typical graduation ages: High school (18), Bachelor (22), Master (24), PhD (27)
    AGE_GROUPS = {
        "under_25": (0, 24),
        "25_34": (25, 34),
        "35_44": (35, 44),
        "45_54": (45, 54),
        "55_64": (55, 64),
        "65_plus": (65, 100),
    }

    MIN_CONFIDENCE_THRESHOLD = 0.6

    def __init__(self):
        """Initialize the demographic analyzer."""
        self.inference_method = "nlp_heuristic_v1"
        self.inference_version = "1.0.0"

    async def analyze_resume(
        self,
        db: AsyncSession,
        resume_id: UUID,
    ) -> Dict[str, Any]:
        """
        Analyze a resume and infer demographic attributes.

        Args:
            db: Database session
            resume_id: Resume UUID to analyze

        Returns:
            Dictionary with inferred demographics and confidence scores

        Raises:
            ValueError: If resume not found
        """
        import time
        start_time = time.time()

        # Fetch resume
        resume_query = select(Resume).where(Resume.id == resume_id)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        # Get resume analysis if available
        analysis_query = select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        # Prepare text for analysis
        raw_text = resume.raw_text or ""
        analysis_text = ""
        if analysis:
            if analysis.raw_text:
                analysis_text = analysis.raw_text
            elif analysis.skills:
                analysis_text = " ".join(analysis.skills)

        full_text = f"{raw_text} {analysis_text}".lower()

        # Extract name from resume
        name = self._extract_name(resume, analysis)

        # Infer demographic attributes
        inferences = self._infer_demographics(full_text, name, analysis)

        # Check if confidence threshold is met
        confidence_threshold_met = all(
            inferences.get(f"{attr}_confidence", 0) >= self.MIN_CONFIDENCE_THRESHOLD
            for attr in ["gender", "age", "ethnicity", "geographic"]
        )

        processing_time = time.time() - start_time

        # Create or update DemographicInference record
        existing_query = select(DemographicInference).where(
            DemographicInference.resume_id == resume_id
        )
        existing_result = await db.execute(existing_query)
        existing_inference = existing_result.scalar_one_or_none()

        if existing_inference:
            # Update existing
            existing_inference.inferred_gender = inferences.get("gender")
            existing_inference.gender_confidence = inferences.get("gender_confidence")
            existing_inference.inferred_age_group = inferences.get("age_group")
            existing_inference.age_confidence = inferences.get("age_confidence")
            existing_inference.inferred_ethnicity = inferences.get("ethnicity")
            existing_inference.ethnicity_confidence = inferences.get("ethnicity_confidence")
            existing_inference.inferred_geographic_region = inferences.get("geographic_region")
            existing_inference.geographic_confidence = inferences.get("geographic_confidence")
            existing_inference.inferred_education_level = inferences.get("education_level")
            existing_inference.education_confidence = inferences.get("education_confidence")
            existing_inference.inferred_career_stage = inferences.get("career_stage")
            existing_inference.career_stage_confidence = inferences.get("career_stage_confidence")
            existing_inference.raw_features = inferences.get("raw_features")
            existing_inference.alternative_predictions = inferences.get("alternative_predictions")
            existing_inference.bias_indicators = inferences.get("bias_indicators")
            existing_inference.inference_method = self.inference_method
            existing_inference.inference_version = self.inference_version
            existing_inference.processing_time_seconds = processing_time
            existing_inference.confidence_threshold_met = confidence_threshold_met
            existing_inference.requires_review = not confidence_threshold_met

            inference_id = existing_inference.id
        else:
            # Create new
            new_inference = DemographicInference(
                resume_id=resume_id,
                analysis_id=analysis.id if analysis else None,
                inferred_gender=inferences.get("gender"),
                gender_confidence=inferences.get("gender_confidence"),
                inferred_age_group=inferences.get("age_group"),
                age_confidence=inferences.get("age_confidence"),
                inferred_ethnicity=inferences.get("ethnicity"),
                ethnicity_confidence=inferences.get("ethnicity_confidence"),
                inferred_geographic_region=inferences.get("geographic_region"),
                geographic_confidence=inferences.get("geographic_confidence"),
                inferred_education_level=inferences.get("education_level"),
                education_confidence=inferences.get("education_confidence"),
                inferred_career_stage=inferences.get("career_stage"),
                career_stage_confidence=inferences.get("career_stage_confidence"),
                raw_features=inferences.get("raw_features"),
                alternative_predictions=inferences.get("alternative_predictions"),
                bias_indicators=inferences.get("bias_indicators"),
                inference_method=self.inference_method,
                inference_version=self.inference_version,
                processing_time_seconds=processing_time,
                confidence_threshold_met=confidence_threshold_met,
                requires_review=not confidence_threshold_met,
                review_status="pending" if not confidence_threshold_met else None,
            )
            db.add(new_inference)
            await db.flush()
            inference_id = new_inference.id

        await db.commit()

        logger.info(f"Demographic analysis complete for resume {resume_id}: {inferences.get('gender')} {inferences.get('age_group')}")

        return {
            "inference_id": str(inference_id),
            "resume_id": str(resume_id),
            **inferences,
            "confidence_threshold_met": confidence_threshold_met,
            "requires_review": not confidence_threshold_met,
            "processing_time_seconds": processing_time,
        }

    def _infer_demographics(
        self, text: str, name: Optional[str], analysis: Optional[ResumeAnalysis]
    ) -> Dict[str, Any]:
        """
        Infer all demographic attributes from text.

        Args:
            text: Full resume text (lowercase)
            name: Extracted name
            analysis: ResumeAnalysis object

        Returns:
            Dictionary with all inferred attributes and confidences
        """
        raw_features = {}
        alternative_predictions = {}
        bias_indicators = []

        # Infer gender
        gender, gender_confidence, gender_features = self._infer_gender(text, name)
        raw_features["gender"] = gender_features
        if gender_features.get("alternative_prediction"):
            alternative_predictions["gender"] = gender_features["alternative_prediction"]

        # Infer age group
        age_group, age_confidence, age_features = self._infer_age_group(text, analysis)
        raw_features["age"] = age_features

        # Infer ethnicity
        ethnicity, ethnicity_confidence, ethnicity_features = self._infer_ethnicity(name, text)
        raw_features["ethnicity"] = ethnicity_features
        if ethnicity_features.get("alternative_prediction"):
            alternative_predictions["ethnicity"] = ethnicity_features["alternative_prediction"]

        # Infer geographic region
        geo_region, geo_confidence, geo_features = self._infer_geographic_region(text)
        raw_features["geographic"] = geo_features

        # Infer education level
        edu_level, edu_confidence, edu_features = self._infer_education_level(text)
        raw_features["education"] = edu_features

        # Infer career stage
        career_stage, career_confidence, career_features = self._infer_career_stage(text, analysis)
        raw_features["career_stage"] = career_features

        # Check for bias indicators
        bias_indicators = self._check_bias_indicators(text)

        return {
            "gender": gender,
            "gender_confidence": gender_confidence,
            "age_group": age_group,
            "age_confidence": age_confidence,
            "ethnicity": ethnicity,
            "ethnicity_confidence": ethnicity_confidence,
            "geographic_region": geo_region,
            "geographic_confidence": geo_confidence,
            "education_level": edu_level,
            "education_confidence": edu_confidence,
            "career_stage": career_stage,
            "career_stage_confidence": career_confidence,
            "raw_features": raw_features,
            "alternative_predictions": alternative_predictions if alternative_predictions else None,
            "bias_indicators": bias_indicators if bias_indicators else None,
        }

    def _extract_name(
        self, resume: Resume, analysis: Optional[ResumeAnalysis]
    ) -> Optional[str]:
        """
        Extract candidate name from resume.

        Args:
            resume: Resume object
            analysis: ResumeAnalysis object

        Returns:
            Extracted name or None
        """
        # Try to get from analysis
        if analysis and analysis.raw_text:
            # Simple heuristic: first line of resume often contains name
            lines = analysis.raw_text.strip().split("\n")
            if lines:
                first_line = lines[0].strip()
                # Remove common non-name elements
                first_line = re.sub(r"resume|cv|curriculum vitae", "", first_line, flags=re.IGNORECASE)
                if len(first_line.split()) <= 4:  # Name is typically 2-4 words
                    return first_line

        # Try to get from raw text
        if resume.raw_text:
            lines = resume.raw_text.strip().split("\n")
            if lines:
                first_line = lines[0].strip()
                first_line = re.sub(r"resume|cv|curriculum vitae", "", first_line, flags=re.IGNORECASE)
                if len(first_line.split()) <= 4:
                    return first_line

        return None

    def _infer_gender(self, text: str, name: Optional[str]) -> Tuple[Optional[str, float, Dict]]:
        """
        Infer gender from name and pronouns.

        Returns:
            Tuple of (gender, confidence, features)
        """
        features = {
            "first_name_match": None,
            "pronoun_count": 0,
            "honorific_count": 0,
            "name_used": False,
        }

        scores = {"male": 0.0, "female": 0.0, "non_binary": 0.0}

        # Check pronouns
        for gender, patterns in self.GENDER_PATTERNS.items():
            pronouns = patterns.get("pronouns", set())
            count = sum(1 for pronoun in pronouns if f" {pronoun} " in f" {text} ")
            features["pronoun_count"] += count
            scores[gender] += count * 0.4  # Pronouns are strong indicators

        # Check name if available
        if name:
            name_lower = name.lower().split()[0]  # First name only
            features["name_used"] = True

            for gender, patterns in self.GENDER_PATTERNS.items():
                first_names = patterns.get("first_names", set())
                if name_lower in first_names:
                    scores[gender] += 0.5  # Name match is strong indicator
                    features["first_name_match"] = gender

        # Check honorifics
        for gender, patterns in self.GENDER_PATTERNS.items():
            honorifics = patterns.get("honorifics", set())
            count = sum(1 for honorific in honorifics if f"{honorific} " in text)
            features["honorific_count"] += count
            scores[gender] += count * 0.3

        # Normalize scores
        total_score = sum(scores.values())
        if total_score == 0:
            return None, 0.0, features

        # Normalize to 0-1
        max_score = max(scores.values())
        normalized_scores = {k: v / max_score for k, v in scores.items()}

        # Get best match
        best_gender = max(normalized_scores, key=normalized_scores.get)
        best_score = normalized_scores[best_gender]

        # Adjust confidence based on strength of evidence
        confidence = min(best_score * 1.2, 1.0)  # Boost slightly but cap at 1.0

        # Alternative prediction (second best)
        sorted_scores = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[1][1] > 0.3:
            features["alternative_prediction"] = {
                "value": sorted_scores[1][0],
                "confidence": sorted_scores[1][1],
            }

        # Detect non-binary indicators
        non_binary_indicators = {"they", "them", "their", "themself", "mx", "mx."}
        nb_count = sum(1 for indicator in non_binary_indicators if f" {indicator} " in f" {text} ")
        if nb_count > 0:
            scores["non_binary"] += nb_count * 0.3
            if scores["non_binary"] > scores["male"] and scores["non_binary"] > scores["female"]:
                return "non_binary", min(scores["non_binary"] / max(scores["male"], scores["female"], 1.0), 1.0), features

        return best_gender, confidence, features

    def _infer_age_group(
        self, text: str, analysis: Optional[ResumeAnalysis]
    ) -> Tuple[Optional[str, float, Dict]]:
        """
        Infer age group from graduation dates and experience.

        Returns:
            Tuple of (age_group, confidence, features)
        """
        features = {
            "graduation_years": [],
            "estimated_graduation_year": None,
            "experience_years": 0,
        }

        # Look for graduation years
        year_pattern = r"\b(19|20)\d{2}\b"
        years_found = re.findall(year_pattern, text)
        graduation_years = []

        # Filter likely graduation years (1950-2025)
        current_year = datetime.now().year
        for year_match in years_found:
            year = int(year_match)
            if 1950 <= year <= current_year:
                # Check if it's near education keywords
                context_pattern = rf"(\w+\s+){{0,5}}{year}\b"
                for match in re.finditer(context_pattern, text):
                    context = match.group().lower()
                    if any(edu in context for edu in ["university", "college", "school", "degree", "ba ", "bs ", "ms ", "phd"]):
                        graduation_years.append(year)
                        break

        features["graduation_years"] = list(set(graduation_years))

        # Get experience years if available
        experience_years = 0
        if analysis and analysis.raw_data:
            exp_data = analysis.raw_data.get("experience", {})
            if isinstance(exp_data, dict):
                experience_years = exp_data.get("total_months", 0) / 12
            elif isinstance(exp_data, (int, float)):
                experience_years = exp_data / 12 if exp_data > 12 else 0
        features["experience_years"] = experience_years

        # Estimate age
        estimated_age = None
        estimated_grad_year = None

        if graduation_years:
            # Use most recent graduation year
            estimated_grad_year = max(graduation_years)
            features["estimated_graduation_year"] = estimated_grad_year

            # Estimate graduation age (22 for bachelor's, adjust higher for advanced degrees)
            grad_age = 22
            text_lower = text.lower()
            if any(adv in text_lower for adv in ["master", "m.s", "mba", "msc"]):
                grad_age = 24
            elif any(adv in text_lower for adv in ["ph.d", "phd", "doctor", "doctorate"]):
                grad_age = 27

            estimated_age = grad_age + (current_year - estimated_grad_year)

        # Also estimate from experience
        age_from_experience = None
        if experience_years > 0:
            # Assume career starts at ~22
            age_from_experience = 22 + experience_years

        # Combine estimates
        if estimated_age and age_from_experience:
            # Average both estimates
            final_age = (estimated_age + age_from_experience) / 2
            confidence = 0.8
        elif estimated_age:
            final_age = estimated_age
            confidence = 0.7
        elif age_from_experience:
            final_age = age_from_experience
            confidence = 0.6
        else:
            return None, 0.0, features

        # Map to age group
        for group, (min_age, max_age) in self.AGE_GROUPS.items():
            if min_age <= final_age <= max_age:
                return group, confidence, features

        return "35_44", 0.5, features  # Default fallback

    def _infer_ethnicity(self, name: Optional[str], text: str) -> Tuple[Optional[str, float, Dict]]:
        """
        Infer ethnicity from surname patterns.

        Returns:
            Tuple of (ethnicity, confidence, features)
        """
        features = {
            "surname": None,
            "pattern_matches": [],
        }

        if not name:
            return None, 0.0, features

        # Extract surname (last word of name)
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            return None, 0.0, features

        surname = name_parts[-1].lower().strip(",")
        features["surname"] = surname

        # Check against ethnicity patterns
        scores = {}
        for ethnicity, patterns in self.ETHNICITY_PATTERNS.items():
            surnames = patterns.get("surnames", set())
            if surname in surnames:
                scores[ethnicity] = 0.8  # Strong match
                features["pattern_matches"].append(ethnicity)
            elif surname.lower().startswith(tuple(s[:3] for s in surnames)):
                # Partial match (first 3 chars)
                scores[ethnicity] = 0.4  # Weak match
                features["pattern_matches"].append(f"{ethnicity} (partial)")

        if not scores:
            return None, 0.0, features

        # Get best match
        best_ethnicity = max(scores, key=scores.get)
        best_score = scores[best_ethnicity]

        # Alternative prediction
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[1][1] > 0.2:
            features["alternative_prediction"] = {
                "value": sorted_scores[1][0],
                "confidence": sorted_scores[1][1],
            }

        # Lower confidence for ethnicity predictions (high uncertainty)
        confidence = best_score * 0.6  # Reduce confidence due to high variability

        return best_ethnicity, confidence, features

    def _infer_geographic_region(self, text: str) -> Tuple[Optional[str, float, Dict]]:
        """
        Infer geographic region from location mentions.

        Returns:
            Tuple of (region, confidence, features)
        """
        features = {
            "matched_locations": [],
            "matched_countries": [],
        }

        scores = {}
        for region, patterns in self.REGIONAL_PATTERNS.items():
            score = 0
            matches = []

            # Check states/provinces
            for state in patterns.get("states", set()):
                if state in text:
                    score += 1
                    matches.append(state)

            # Check cities
            for city in patterns.get("cities", set()):
                if city in text:
                    score += 1.5  # Cities are more specific
                    matches.append(city)

            # Check countries
            for country in patterns.get("countries", set()):
                if country in text:
                    score += 2  # Countries are very specific
                    features["matched_countries"].append(country)

            if score > 0:
                scores[region] = score
                features["matched_locations"].extend(matches)

        if not scores:
            return None, 0.0, features

        # Get best match
        best_region = max(scores, key=scores.get)
        best_score = scores[best_region]

        # Normalize confidence based on match count
        confidence = min(best_score / 3.0, 1.0)

        return best_region, confidence, features

    def _infer_education_level(self, text: str) -> Tuple[Optional[str, float, Dict]]:
        """
        Infer education level from degree mentions.

        Returns:
            Tuple of (education_level, confidence, features)
        """
        features = {
            "matched_keywords": [],
            "matched_degrees": [],
        }

        scores = {}
        for level, patterns in self.EDUCATION_PATTERNS.items():
            score = 0
            matches = []

            # Check keywords
            for keyword in patterns.get("keywords", set()):
                if keyword in text:
                    score += 1
                    matches.append(keyword)

            # Check degree prefixes
            for prefix in patterns.get("degree_prefixes", set()):
                if prefix in text:
                    score += 1.5  # Prefix is more specific
                    matches.append(prefix)

            if score > 0:
                scores[level] = score
                features["matched_keywords"].extend(matches)

        if not scores:
            return None, 0.0, features

        # Get highest level (education levels are ordered in dict)
        best_level = max(scores, key=scores.get)
        best_score = scores[best_level]

        # High confidence if multiple matches
        confidence = min(best_score / 2.0, 1.0)

        return best_level, confidence, features

    def _infer_career_stage(
        self, text: str, analysis: Optional[ResumeAnalysis]
    ) -> Tuple[Optional[str, float, Dict]]:
        """
        Infer career stage from titles and experience.

        Returns:
            Tuple of (career_stage, confidence, features)
        """
        features = {
            "matched_keywords": [],
            "experience_years": 0,
        }

        # Get experience years
        experience_years = 0
        if analysis and analysis.raw_data:
            exp_data = analysis.raw_data.get("experience", {})
            if isinstance(exp_data, dict):
                experience_years = exp_data.get("total_months", 0) / 12
            elif isinstance(exp_data, (int, float)):
                experience_years = exp_data / 12 if exp_data > 12 else 0

        features["experience_years"] = experience_years

        scores = {}
        for stage, patterns in self.CAREER_STAGE_PATTERNS.items():
            score = 0
            matches = []

            # Check keywords
            for keyword in patterns.get("keywords", set()):
                if f" {keyword} " in f" {text} ":
                    score += 1
                    matches.append(keyword)

            # Check experience years
            min_exp = patterns.get("min_experience_years", 0)
            if experience_years >= min_exp:
                score += 1  # Experience supports this stage

            if score > 0:
                scores[stage] = score
                features["matched_keywords"].extend(matches)

        if not scores:
            return None, 0.0, features

        # Get highest stage
        best_stage = max(scores, key=scores.get)
        best_score = scores[best_stage]

        # Higher confidence if both keywords and experience align
        confidence = min(best_score / 2.0, 1.0)

        return best_stage, confidence, features

    def _check_bias_indicators(self, text: str) -> List[str]:
        """
        Check for potential bias indicators in text.

        Returns:
            List of detected bias indicators
        """
        indicators = []

        # Check for explicit demographic mentions
        demographic_keywords = [
            "gender", "sex", "male", "female", "age", "born", "birth date",
            "married", "single", "divorced", "children", "kids", "family status",
            "race", "ethnicity", "national origin", "religion", "religious",
            "disability", "disabled", "handicap", "veteran status",
        ]

        text_lower = text.lower()
        for keyword in demographic_keywords:
            if keyword in text_lower:
                indicators.append(f"demographic_mention_{keyword}")

        # Check for photo mentions
        if any(term in text_lower for term in ["photo", "picture", "image", "portrait"]):
            indicators.append("photo_included")

        # Check for age-related terms
        age_terms = ["young", "energetic", "mature", "overqualified", "recent graduate"]
        for term in age_terms:
            if term in text_lower:
                indicators.append(f"age_related_term_{term}")

        # Check for potentially biased language patterns
        biased_patterns = [
            "native english speaker",
            "english mother tongue",
            "western educated",
            "fitting in with our culture",
            "cultural fit",
        ]

        for pattern in biased_patterns:
            if pattern in text_lower:
                indicators.append(f"biased_language_{pattern.replace(' ', '_')}")

        return list(set(indicators)) if indicators else []


# Global service instance
_demographic_analyzer: Optional[DemographicAnalyzer] = None


def get_demographic_analyzer() -> DemographicAnalyzer:
    """Get or create global demographic analyzer instance."""
    global _demographic_analyzer
    if _demographic_analyzer is None:
        _demographic_analyzer = DemographicAnalyzer()
    return _demographic_analyzer
