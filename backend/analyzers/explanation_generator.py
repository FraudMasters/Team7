"""
Enhanced Explanation Generator Module

This module provides LLM-based explanation generation for AI-powered candidate ranking.
It creates human-readable explanations that help recruiters understand why candidates
are ranked certain ways.

Key features:
- Natural language explanations for ranking decisions
- Feature contribution breakdown with percentage attribution
- Confidence interval calculation and communication
- Side-by-side comparison explanations
- Resume section highlighting suggestions
- What-if scenario explanations

The module uses OpenAI, Anthropic, or Google APIs to generate comprehensive
explanations for AI decisions.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from config import get_settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ZAI = "zai"


class ExplanationType(str, Enum):
    """Types of explanations that can be generated."""
    RANKING = "ranking"
    FEATURE_BREAKDOWN = "feature_breakdown"
    COMPARISON = "comparison"
    WHAT_IF = "what_if"
    CONFIDENCE = "confidence"


@dataclass
class FeatureExplanation:
    """
    Explanation for a single feature's contribution to ranking.

    Attributes:
        name: Feature name
        value: Feature value
        contribution: Contribution score to overall ranking
        contribution_percent: Contribution as percentage of total
        description: Human-readable description of what this feature means
        impact_level: Impact level (high, medium, low)
        resume_section: Related resume section (if applicable)
    """
    name: str
    value: float
    contribution: float
    contribution_percent: float
    description: str
    impact_level: str = "medium"
    resume_section: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "contribution": self.contribution,
            "contribution_percent": self.contribution_percent,
            "description": self.description,
            "impact_level": self.impact_level,
            "resume_section": self.resume_section,
        }


@dataclass
class ConfidenceInterval:
    """
    Confidence interval for ranking prediction.

    Attributes:
        lower: Lower bound of confidence interval
        upper: Upper bound of confidence interval
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        margin_of_error: Margin of error
        explanation: Human-readable explanation of uncertainty
    """
    lower: float
    upper: float
    confidence_level: float
    margin_of_error: float
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "lower": self.lower,
            "upper": self.upper,
            "confidence_level": self.confidence_level,
            "margin_of_error": self.margin_of_error,
            "explanation": self.explanation,
        }


@dataclass
class RankingExplanation:
    """
    Comprehensive explanation for a candidate ranking.

    Attributes:
        candidate_name: Candidate's name (if available)
        rank_score: Overall ranking score
        rank_position: Position in ranked list
        narrative: Natural language explanation (1-3 sentences)
        feature_explanations: List of feature contribution explanations
        confidence_interval: Confidence interval for the prediction
        strengths: List of candidate strengths identified
        weaknesses: List of areas for improvement
        recommendation: Hiring recommendation
        highlight_sections: Resume sections to highlight
        provider: LLM provider used
        model: Model name used
        generated_at: Timestamp of generation
    """
    candidate_name: Optional[str]
    rank_score: float
    rank_position: Optional[int]
    narrative: str
    feature_explanations: List[FeatureExplanation]
    confidence_interval: Optional[ConfidenceInterval]
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str
    highlight_sections: Dict[str, str]
    provider: str = ""
    model: str = ""
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "candidate_name": self.candidate_name,
            "rank_score": self.rank_score,
            "rank_position": self.rank_position,
            "narrative": self.narrative,
            "feature_explanations": [f.to_dict() for f in self.feature_explanations],
            "confidence_interval": self.confidence_interval.to_dict() if self.confidence_interval else None,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendation": self.recommendation,
            "highlight_sections": self.highlight_sections,
            "provider": self.provider,
            "model": self.model,
            "generated_at": self.generated_at,
        }


@dataclass
class ComparisonExplanation:
    """
    Explanation for why one candidate ranks higher than another.

    Attributes:
        candidate_a_name: First candidate's name
        candidate_b_name: Second candidate's name
        candidate_a_score: First candidate's score
        candidate_b_score: Second candidate's score
        narrative: Natural language explanation of the comparison
        key_differences: List of key differences between candidates
        winning_factors: Factors that favor candidate A
        losing_factors: Factors that favor candidate B
        recommendation: Which candidate to prioritize
        provider: LLM provider used
        model: Model name used
        generated_at: Timestamp of generation
    """
    candidate_a_name: str
    candidate_b_name: str
    candidate_a_score: float
    candidate_b_score: float
    narrative: str
    key_differences: List[str]
    winning_factors: List[str]
    losing_factors: List[str]
    recommendation: str
    provider: str = ""
    model: str = ""
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "candidate_a_name": self.candidate_a_name,
            "candidate_b_name": self.candidate_b_name,
            "candidate_a_score": self.candidate_a_score,
            "candidate_b_score": self.candidate_b_score,
            "narrative": self.narrative,
            "key_differences": self.key_differences,
            "winning_factors": self.winning_factors,
            "losing_factors": self.losing_factors,
            "recommendation": self.recommendation,
            "provider": self.provider,
            "model": self.model,
            "generated_at": self.generated_at,
        }


class ExplanationGenerator:
    """
    Enhanced Explanation Generator using LLM for comprehensive explanations.

    This generator creates human-readable explanations for AI ranking decisions,
    helping recruiters understand and trust the AI recommendations.

    Example:
        >>> generator = ExplanationGenerator()
        >>> result = await generator.generate_ranking_explanation(
        ...     candidate_name="John Doe",
        ...     rank_score=0.85,
        ...     feature_contributions={"skills_match": 0.30, ...},
        ...     ranking_factors={"skills_match": {"score": 0.9, ...}, ...},
        ...     job_title="Senior Python Developer",
        ...     recommendation="excellent"
        ... )
        >>> print(result.narrative)
        "John Doe is an excellent match for this position, primarily due to strong
        technical skills alignment and relevant experience."
    """

    # Feature name mappings for human-readable explanations
    FEATURE_DESCRIPTIONS = {
        "overall_match_score": "Overall compatibility between the candidate's profile and job requirements",
        "keyword_score": "Direct keyword matches between resume and job description",
        "tfidf_score": "Relevance based on term frequency-inverse document frequency analysis",
        "vector_score": "Semantic similarity using embeddings-based matching",
        "skills_match_ratio": "Percentage of required skills the candidate possesses",
        "experience_months": "Total professional experience in months",
        "experience_relevance": "How closely the candidate's experience aligns with job requirements",
        "education_level": "Educational attainment relative to job requirements",
        "recent_experience": "Relevant experience gained in recent years",
        "skill_rarity_score": "Possession of rare, specialized skills that are highly valued",
        "title_similarity": "Similarity between candidate's current/previous titles and target position",
        "freshness_score": "Recency of resume updates and activity",
        "completeness_score": "How complete and detailed the resume is",
    }

    # Resume section mappings
    FEATURE_TO_SECTION = {
        "overall_match_score": "summary",
        "keyword_score": "skills",
        "tfidf_score": "summary",
        "vector_score": "summary",
        "skills_match_ratio": "skills",
        "experience_months": "experience",
        "experience_relevance": "experience",
        "education_level": "education",
        "recent_experience": "experience",
        "skill_rarity_score": "skills",
        "title_similarity": "experience",
        "freshness_score": "header",
        "completeness_score": "overall",
    }

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the Explanation Generator.

        Args:
            provider: LLM provider to use (default from config)
            model: Model name to use (default from config)
        """
        settings = get_settings()

        self.provider = provider or LLMProvider(settings.llm_provider)
        self.model = model or settings.llm_model

        # LLM parameters
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

        # API keys
        self.zai_api_key = settings.zai_api_key
        self.zai_base_url = settings.zai_base_url
        self.openai_api_key = settings.openai_api_key
        self.anthropic_api_key = settings.anthropic_api_key
        self.google_api_key = settings.google_api_key

        logger.info(
            f"ExplanationGenerator initialized: provider={self.provider}, "
            f"model={self.model}"
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for explanation generation."""
        return """You are an expert AI explainer specializing in making AI hiring decisions transparent and understandable. Your task is to generate clear, concise explanations that help recruiters understand why candidates are ranked certain ways.

Your explanations should:
1. Be concise (1-3 sentences for main narrative)
2. Be accessible to non-technical users (no ML jargon)
3. Focus on the most impactful factors
4. Be honest about uncertainty
5. Avoid bias and discrimination

Generate explanations in the following JSON format:
```json
{
    "narrative": "Brief 1-3 sentence explanation of why the candidate received this ranking",
    "strengths": [
        "Specific strength 1",
        "Specific strength 2"
    ],
    "weaknesses": [
        "Specific area for improvement 1",
        "Specific area for improvement 2"
    ],
    "highlight_suggestions": {
        "skills": "Explanation of what to highlight in the skills section",
        "experience": "Explanation of what to highlight in the experience section"
    }
}
```

Important guidelines:
- Narrative should directly answer "Why this ranking?"
- Prioritize factors that have the biggest impact
- For strengths/weaknesses, focus on the top 3-5 most important items
- Be specific about what aspects of the resume are relevant
- Maintain a professional, objective tone
- Avoid assumptions about gender, age, race, or other protected characteristics
"""

    def _create_ranking_prompt(
        self,
        candidate_name: Optional[str],
        rank_score: float,
        feature_contributions: Dict[str, float],
        ranking_factors: Dict[str, Any],
        job_title: str,
        job_description: str,
        recommendation: str,
    ) -> str:
        """Create the ranking explanation prompt for the LLM."""
        # Sort features by contribution
        sorted_features = sorted(
            feature_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        feature_details = []
        for feature_name, contribution in sorted_features[:5]:  # Top 5 features
            description = self.FEATURE_DESCRIPTIONS.get(
                feature_name,
                feature_name.replace("_", " ").title()
            )
            impact = "positive" if contribution > 0 else "negative"
            feature_details.append(
                f"- {description}: {contribution:.3f} ({impact} impact)"
            )

        # Extract detailed candidate context
        skills_details = ranking_factors.get('skills_match', {})
        experience_details = ranking_factors.get('experience_analysis', {})
        education_details = ranking_factors.get('education_analysis', {})

        # Build skills list
        skills_context = []
        if isinstance(skills_details, dict):
            matched_skills = skills_details.get('matched_skills', [])
            if matched_skills:
                skills_context.append(f"Matched Skills: {', '.join(matched_skills[:10])}")
            missing_skills = skills_details.get('missing_skills', [])
            if missing_skills:
                skills_context.append(f"Missing Skills: {', '.join(missing_skills[:5])}")
            skills_score = skills_details.get('score', 'N/A')
            if skills_score != 'N/A':
                skills_context.append(f"Skills Match Score: {skills_score:.2f}")

        # Build experience context
        experience_context = []
        if isinstance(experience_details, dict):
            total_months = experience_details.get('total_months', 0)
            if total_months:
                years = total_months // 12
                months = total_months % 12
                if years > 0 and months > 0:
                    duration_str = f"{years} years, {months} months"
                elif years > 0:
                    duration_str = f"{years} years"
                else:
                    duration_str = f"{months} months"
                experience_context.append(f"Total Experience: {duration_str}")

            relevant_months = experience_details.get('relevant_months', 0)
            if relevant_months:
                years = relevant_months // 12
                months = relevant_months % 12
                if years > 0 and months > 0:
                    duration_str = f"{years} years, {months} months"
                elif years > 0:
                    duration_str = f"{years} years"
                else:
                    duration_str = f"{months} months"
                experience_context.append(f"Relevant Experience: {duration_str}")

            experience_score = experience_details.get('score', ranking_factors.get('experience_score', 'N/A'))
            if experience_score != 'N/A':
                experience_context.append(f"Experience Score: {experience_score:.2f}")

        # Build education context
        education_context = []
        if isinstance(education_details, dict):
            degree = education_details.get('degree', '')
            field_of_study = education_details.get('field_of_study', '')
            institution = education_details.get('institution', '')

            if degree:
                education_context.append(f"Degree: {degree}")
            if field_of_study:
                education_context.append(f"Field of Study: {field_of_study}")
            if institution:
                education_context.append(f"Institution: {institution}")

            education_score = education_details.get('score', ranking_factors.get('education_score', 'N/A'))
            if education_score != 'N/A':
                education_context.append(f"Education Score: {education_score:.2f}")

        prompt_parts = [
            f"Generate an explanation for the following candidate ranking:\n\n",
            f"=== CANDIDATE ===\n",
            f"Name: {candidate_name or 'Unknown'}\n",
            f"Overall Score: {rank_score:.2f}\n",
            f"Recommendation: {recommendation}\n\n",
            f"=== JOB POSTING ===\n",
            f"Title: {job_title}\n",
            f"Description: {job_description[:500]}...\n\n",
            f"=== TOP FACTORS INFLUENCING RANKING ===\n",
        ]
        prompt_parts.extend([f"{fd}\n" for fd in feature_details])

        # Add detailed candidate context section
        prompt_parts.append(f"\n=== CANDIDATE DETAILS ===\n")
        if skills_context:
            prompt_parts.extend([f"  {item}\n" for item in skills_context])
            prompt_parts.append("\n")
        if experience_context:
            prompt_parts.extend([f"  {item}\n" for item in experience_context])
            prompt_parts.append("\n")
        if education_context:
            prompt_parts.extend([f"  {item}\n" for item in education_context])
            prompt_parts.append("\n")

        prompt_parts.append("Please generate a clear explanation following the JSON format.\n")
        prompt_parts.append("Use the specific candidate details (skills, experience duration, education) to provide personalized, concrete explanations.")

        return "".join(prompt_parts)

    def _format_candidate_context(
        self,
        candidate_name: str,
        score: float,
        factors: Dict[str, Any],
    ) -> str:
        """Format candidate details for prompts."""
        lines = [
            f"Name: {candidate_name}\n",
            f"Score: {score:.2f}\n",
        ]

        # Skills context
        skills_details = factors.get('skills_match', {})
        if isinstance(skills_details, dict):
            matched_skills = skills_details.get('matched_skills', [])
            if matched_skills:
                lines.append(f"Matched Skills: {', '.join(matched_skills[:10])}\n")
            skills_score = skills_details.get('score', factors.get('experience_score', 'N/A'))
            if skills_score != 'N/A':
                lines.append(f"Skills Match Score: {skills_score:.2f}\n")

        # Experience context
        experience_details = factors.get('experience_analysis', {})
        if isinstance(experience_details, dict):
            total_months = experience_details.get('total_months', 0)
            if total_months:
                years = total_months // 12
                months = total_months % 12
                if years > 0 and months > 0:
                    duration_str = f"{years} years, {months} months"
                elif years > 0:
                    duration_str = f"{years} years"
                else:
                    duration_str = f"{months} months"
                lines.append(f"Total Experience: {duration_str}\n")

            experience_score = experience_details.get('score', factors.get('experience_score', 'N/A'))
            if experience_score != 'N/A':
                lines.append(f"Experience Score: {experience_score:.2f}\n")

        # Education context
        education_details = factors.get('education_analysis', {})
        if isinstance(education_details, dict):
            degree = education_details.get('degree', '')
            field_of_study = education_details.get('field_of_study', '')
            if degree:
                lines.append(f"Degree: {degree}\n")
            if field_of_study:
                lines.append(f"Field of Study: {field_of_study}\n")

            education_score = education_details.get('score', factors.get('education_score', 'N/A'))
            if education_score != 'N/A':
                lines.append(f"Education Score: {education_score:.2f}\n")

        return "".join(lines)

    def _create_comparison_prompt(
        self,
        candidate_a_name: str,
        candidate_b_name: str,
        candidate_a_score: float,
        candidate_b_score: float,
        candidate_a_factors: Dict[str, Any],
        candidate_b_factors: Dict[str, Any],
        job_title: str,
    ) -> str:
        """Create the comparison explanation prompt for the LLM."""
        prompt_parts = [
            f"Generate an explanation for why one candidate ranks higher than another:\n\n",
            f"=== JOB POSITION ===\n",
            f"Title: {job_title}\n\n",
            f"=== CANDIDATE A (Higher Score) ===\n",
            self._format_candidate_context(candidate_a_name, candidate_a_score, candidate_a_factors),
            f"\n=== CANDIDATE B (Lower Score) ===\n",
            self._format_candidate_context(candidate_b_name, candidate_b_score, candidate_b_factors),
            f"\nReturn your analysis in JSON format:\n",
            f'{{"narrative": "...", "key_differences": [...], "winning_factors": [...], "losing_factors": [...], "recommendation": "..."}}\n',
            f"Use the specific candidate details (skills, experience duration, education) to provide personalized, concrete comparisons.",
        ]
        return "".join(prompt_parts)

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API for explanation generation."""
        try:
            from openai import AsyncOpenAI

            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")

            client = AsyncOpenAI(api_key=self.openai_api_key)

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    async def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API for explanation generation."""
        try:
            from anthropic import AsyncAnthropic

            if not self.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")

            client = AsyncAnthropic(api_key=self.anthropic_api_key)

            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self._get_system_prompt(),
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            result_text = response.content[0].text
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result_text = json_match.group(0)

            return json.loads(result_text)

        except ImportError:
            logger.error("Anthropic package not installed. Install with: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    async def _call_google(self, prompt: str) -> Dict[str, Any]:
        """Call Google Gemini API for explanation generation."""
        try:
            import google.generativeai as genai

            if not self.google_api_key:
                raise ValueError("Google API key not configured")

            genai.configure(api_key=self.google_api_key)
            genai_model = genai.GenerativeModel(
                self.model,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    response_mime_type="application/json",
                ),
                system_instruction=self._get_system_prompt(),
            )

            response = await genai_model.generate_content_async(prompt)
            result_text = response.text

            return json.loads(result_text)

        except ImportError:
            logger.error("Google Generative AI package not installed. Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"Google API call failed: {e}")
            raise

    async def _call_zai(self, prompt: str) -> Dict[str, Any]:
        """Call Z.ai API for explanation generation (OpenAI-compatible)."""
        try:
            from openai import AsyncOpenAI

            if not self.zai_api_key:
                raise ValueError("Z.ai API key not configured")

            client = AsyncOpenAI(
                api_key=self.zai_api_key,
                base_url=self.zai_base_url,
            )

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content
            logger.info(f"Z.ai API call successful, response length: {len(content)}")

            # Try to extract JSON from response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()

            return json.loads(content)

        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Z.ai JSON response: {e}")
            logger.error(f"Response content: {content[:500]}...")
            raise ValueError(f"Invalid JSON response from Z.ai API: {e}")
        except Exception as e:
            logger.error(f"Z.ai API call failed: {e}")
            raise

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call the appropriate LLM provider."""
        if self.provider == LLMProvider.ZAI:
            return await self._call_zai(prompt)
        elif self.provider == LLMProvider.OPENAI:
            return await self._call_openai(prompt)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(prompt)
        elif self.provider == LLMProvider.GOOGLE:
            return await self._call_google(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _calculate_confidence_interval(
        self,
        rank_score: float,
        prediction_confidence: Optional[float],
        num_features: int,
    ) -> ConfidenceInterval:
        """
        Calculate confidence interval for ranking prediction.

        Args:
            rank_score: The ranking score
            prediction_confidence: Model's prediction confidence (if available)
            num_features: Number of features used in prediction

        Returns:
            ConfidenceInterval with bounds and explanation
        """
        # Use prediction confidence if available, otherwise use heuristic
        if prediction_confidence is not None:
            margin = 0.1 * (1 - prediction_confidence)
        else:
            # Heuristic: more features = more confident
            margin = 0.15 * (1 - min(num_features / 15, 1))

        lower = max(0, rank_score - margin)
        upper = min(1, rank_score + margin)
        confidence_level = 0.95

        # Generate explanation
        if margin < 0.05:
            explanation = "High confidence: The model is very certain about this ranking based on clear signals."
        elif margin < 0.1:
            explanation = "Moderate confidence: The ranking is reliable but has some uncertainty."
        else:
            explanation = "Lower confidence: The ranking has significant uncertainty. Consider reviewing manually."

        return ConfidenceInterval(
            lower=lower,
            upper=upper,
            confidence_level=confidence_level,
            margin_of_error=margin,
            explanation=explanation,
        )

    def _create_feature_explanations(
        self,
        feature_contributions: Dict[str, float],
        ranking_factors: Dict[str, Any],
    ) -> List[FeatureExplanation]:
        """
        Create detailed explanations for each feature's contribution.

        Args:
            feature_contributions: Dictionary of feature contributions
            ranking_factors: Dictionary of ranking factor details

        Returns:
            List of FeatureExplanation objects
        """
        explanations = []

        # Calculate total absolute contribution for percentage
        total_abs_contribution = sum(abs(v) for v in feature_contributions.values())

        for feature_name, contribution in feature_contributions.items():
            if total_abs_contribution > 0:
                contribution_percent = (abs(contribution) / total_abs_contribution) * 100
            else:
                contribution_percent = 0.0

            # Get feature value from ranking factors if available
            feature_value = 0.0
            if feature_name in ranking_factors:
                factor_data = ranking_factors[feature_name]
                if isinstance(factor_data, dict):
                    feature_value = factor_data.get("score", 0.0)
                else:
                    feature_value = float(factor_data)

            # Determine impact level
            abs_contribution = abs(contribution)
            if abs_contribution > 0.15:
                impact_level = "high"
            elif abs_contribution > 0.05:
                impact_level = "medium"
            else:
                impact_level = "low"

            # Get description
            description = self.FEATURE_DESCRIPTIONS.get(
                feature_name,
                feature_name.replace("_", " ").title()
            )

            # Get resume section
            resume_section = self.FEATURE_TO_SECTION.get(feature_name)

            explanations.append(FeatureExplanation(
                name=feature_name,
                value=feature_value,
                contribution=contribution,
                contribution_percent=round(contribution_percent, 1),
                description=description,
                impact_level=impact_level,
                resume_section=resume_section,
            ))

        # Sort by contribution (descending)
        explanations.sort(key=lambda x: abs(x.contribution), reverse=True)

        return explanations

    async def generate_ranking_explanation(
        self,
        candidate_name: Optional[str],
        rank_score: float,
        rank_position: Optional[int],
        feature_contributions: Dict[str, float],
        ranking_factors: Dict[str, Any],
        job_title: str,
        job_description: str = "",
        recommendation: str = "good",
        prediction_confidence: Optional[float] = None,
        use_llm: bool = True,
    ) -> RankingExplanation:
        """
        Generate comprehensive explanation for a candidate ranking.

        Args:
            candidate_name: Candidate's name (if available)
            rank_score: Overall ranking score
            rank_position: Position in ranked list
            feature_contributions: Dictionary of feature contributions
            ranking_factors: Dictionary of ranking factor details
            job_title: Job posting title
            job_description: Job posting description
            recommendation: Hiring recommendation
            prediction_confidence: Model's prediction confidence
            use_llm: Whether to use LLM for narrative generation

        Returns:
            RankingExplanation with comprehensive explanation
        """
        logger.info(
            f"Generating ranking explanation for {candidate_name or 'candidate'}, "
            f"score={rank_score:.2f}, recommendation={recommendation}"
        )

        # Create feature explanations
        feature_explanations = self._create_feature_explanations(
            feature_contributions,
            ranking_factors
        )

        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            rank_score,
            prediction_confidence,
            len(feature_contributions),
        )

        # Generate LLM-based narrative if enabled
        narrative = ""
        strengths = []
        weaknesses = []
        highlight_sections = {}

        if use_llm:
            try:
                prompt = self._create_ranking_prompt(
                    candidate_name=candidate_name,
                    rank_score=rank_score,
                    feature_contributions=feature_contributions,
                    ranking_factors=ranking_factors,
                    job_title=job_title,
                    job_description=job_description,
                    recommendation=recommendation,
                )

                llm_result = await self._call_llm(prompt)

                narrative = llm_result.get("narrative", "")
                strengths = llm_result.get("strengths", [])
                weaknesses = llm_result.get("weaknesses", [])
                highlight_sections = llm_result.get("highlight_suggestions", {})

            except Exception as e:
                logger.warning(f"LLM explanation generation failed: {e}")
                # Fallback to basic explanation
                narrative = self._generate_basic_narrative(
                    candidate_name,
                    rank_score,
                    recommendation,
                    feature_explanations[:3]
                )
        else:
            # Generate basic narrative without LLM
            narrative = self._generate_basic_narrative(
                candidate_name,
                rank_score,
                recommendation,
                feature_explanations[:3]
            )

        # Generate timestamp
        generated_at = datetime.utcnow().isoformat()

        result = RankingExplanation(
            candidate_name=candidate_name,
            rank_score=rank_score,
            rank_position=rank_position,
            narrative=narrative,
            feature_explanations=feature_explanations,
            confidence_interval=confidence_interval,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation,
            highlight_sections=highlight_sections,
            provider=self.provider.value,
            model=self.model,
            generated_at=generated_at,
        )

        logger.info(f"Ranking explanation generated successfully")
        return result

    def _generate_basic_narrative(
        self,
        candidate_name: Optional[str],
        rank_score: float,
        recommendation: str,
        top_features: List[FeatureExplanation],
    ) -> str:
        """Generate basic narrative without LLM."""
        name = candidate_name or "This candidate"

        if recommendation == "excellent":
            base = f"{name} is an excellent match for this position"
        elif recommendation == "good":
            base = f"{name} is a good match for this position"
        elif recommendation == "maybe":
            base = f"{name} shows potential for this position"
        else:
            base = f"{name} may not be the best fit for this position"

        if top_features:
            top_feature_desc = top_features[0].description.lower()
            return f"{base}, primarily due to strong {top_feature_desc}."

        return f"{base} with a score of {rank_score:.2f}."

    async def generate_comparison_explanation(
        self,
        candidate_a_name: str,
        candidate_b_name: str,
        candidate_a_score: float,
        candidate_b_score: float,
        candidate_a_factors: Dict[str, Any],
        candidate_b_factors: Dict[str, Any],
        job_title: str,
        use_llm: bool = True,
    ) -> ComparisonExplanation:
        """
        Generate explanation for why one candidate ranks higher than another.

        Args:
            candidate_a_name: First candidate's name (higher score)
            candidate_b_name: Second candidate's name (lower score)
            candidate_a_score: First candidate's score
            candidate_b_score: Second candidate's score
            candidate_a_factors: First candidate's ranking factors
            candidate_b_factors: Second candidate's ranking factors
            job_title: Job posting title
            use_llm: Whether to use LLM for explanation

        Returns:
            ComparisonExplanation with detailed comparison
        """
        logger.info(
            f"Generating comparison explanation: {candidate_a_name} "
            f"({candidate_a_score:.2f}) vs {candidate_b_name} ({candidate_b_score:.2f})"
        )

        narrative = ""
        key_differences = []
        winning_factors = []
        losing_factors = []
        recommendation = candidate_a_name

        if use_llm:
            try:
                prompt = self._create_comparison_prompt(
                    candidate_a_name=candidate_a_name,
                    candidate_b_name=candidate_b_name,
                    candidate_a_score=candidate_a_score,
                    candidate_b_score=candidate_b_score,
                    candidate_a_factors=candidate_a_factors,
                    candidate_b_factors=candidate_b_factors,
                    job_title=job_title,
                )

                llm_result = await self._call_llm(prompt)

                narrative = llm_result.get("narrative", "")
                key_differences = llm_result.get("key_differences", [])
                winning_factors = llm_result.get("winning_factors", [])
                losing_factors = llm_result.get("losing_factors", [])
                if llm_result.get("recommendation"):
                    recommendation = llm_result["recommendation"]

            except Exception as e:
                logger.warning(f"LLM comparison generation failed: {e}")
                # Fallback to basic comparison
                score_diff = candidate_a_score - candidate_b_score
                narrative = (
                    f"{candidate_a_name} ranks {score_diff:.2f} points higher than "
                    f"{candidate_b_name} primarily due to better skills alignment "
                    f"and experience relevance."
                )
        else:
            score_diff = candidate_a_score - candidate_b_score
            narrative = (
                f"{candidate_a_name} ranks {score_diff:.2f} points higher than "
                f"{candidate_b_name} primarily due to better skills alignment "
                f"and experience relevance."
            )

        generated_at = datetime.utcnow().isoformat()

        result = ComparisonExplanation(
            candidate_a_name=candidate_a_name,
            candidate_b_name=candidate_b_name,
            candidate_a_score=candidate_a_score,
            candidate_b_score=candidate_b_score,
            narrative=narrative,
            key_differences=key_differences,
            winning_factors=winning_factors,
            losing_factors=losing_factors,
            recommendation=recommendation,
            provider=self.provider.value,
            model=self.model,
            generated_at=generated_at,
        )

        logger.info(f"Comparison explanation generated successfully")
        return result

    def generate_explanation_sync(
        self,
        candidate_name: Optional[str],
        rank_score: float,
        rank_position: Optional[int],
        feature_contributions: Dict[str, float],
        ranking_factors: Dict[str, Any],
        job_title: str,
        job_description: str = "",
        recommendation: str = "good",
        prediction_confidence: Optional[float] = None,
        use_llm: bool = True,
    ) -> RankingExplanation:
        """
        Synchronous wrapper for explanation generation.

        Use this when calling from non-async contexts.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.generate_ranking_explanation(
                candidate_name=candidate_name,
                rank_score=rank_score,
                rank_position=rank_position,
                feature_contributions=feature_contributions,
                ranking_factors=ranking_factors,
                job_title=job_title,
                job_description=job_description,
                recommendation=recommendation,
                prediction_confidence=prediction_confidence,
                use_llm=use_llm,
            )
        )


# Singleton instance
_default_generator: Optional[ExplanationGenerator] = None


def get_explanation_generator() -> Optional[ExplanationGenerator]:
    """
    Get or create the default explanation generator instance.

    Returns None if LLM API is not configured.
    """
    global _default_generator
    settings = get_settings()

    # Check if any LLM API key is configured
    has_api_key = bool(
        settings.zai_api_key or
        settings.openai_api_key or
        settings.anthropic_api_key or
        settings.google_api_key
    )

    if not has_api_key:
        logger.warning("No LLM API key configured, explanation generator unavailable")
        return None

    if _default_generator is None:
        _default_generator = ExplanationGenerator()

    return _default_generator


async def generate_ranking_explanation(
    candidate_name: Optional[str],
    rank_score: float,
    rank_position: Optional[int],
    feature_contributions: Dict[str, float],
    ranking_factors: Dict[str, Any],
    job_title: str,
    job_description: str = "",
    recommendation: str = "good",
    prediction_confidence: Optional[float] = None,
    use_llm: bool = True,
) -> Optional[RankingExplanation]:
    """
    Convenience function to generate ranking explanation.

    Returns None if LLM is not configured.

    Args:
        candidate_name: Candidate's name
        rank_score: Overall ranking score
        rank_position: Position in ranked list
        feature_contributions: Dictionary of feature contributions
        ranking_factors: Dictionary of ranking factor details
        job_title: Job posting title
        job_description: Job posting description
        recommendation: Hiring recommendation
        prediction_confidence: Model's prediction confidence
        use_llm: Whether to use LLM for narrative generation

    Returns:
        RankingExplanation with comprehensive explanation, or None if unavailable
    """
    generator = get_explanation_generator()
    if generator:
        return await generator.generate_ranking_explanation(
            candidate_name=candidate_name,
            rank_score=rank_score,
            rank_position=rank_position,
            feature_contributions=feature_contributions,
            ranking_factors=ranking_factors,
            job_title=job_title,
            job_description=job_description,
            recommendation=recommendation,
            prediction_confidence=prediction_confidence,
            use_llm=use_llm,
        )

    return None
