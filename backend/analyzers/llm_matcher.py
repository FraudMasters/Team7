"""
LLM semantic matcher using large language models for contextual understanding.

This module provides semantic similarity matching between resumes and job postings
using LLM APIs (OpenAI, Anthropic, Google, or Z.ai) for deep contextual analysis.

Key features:
- Natural language understanding beyond keyword matching
- Contextual semantic analysis using LLM reasoning
- Transferable skill recognition
- Embedding support for efficient caching
- Multi-language support via LLM capabilities
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import get_settings

logger = logging.getLogger(__name__)


class LLMProvider(str, type):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ZAI = "zai"


@dataclass
class LLMMatchResult:
    """Result of LLM semantic matching."""

    # Overall scores
    semantic_score: float  # 0-1, overall semantic similarity
    passed: bool
    method: str = "llm"

    # Detailed scores
    skill_match_score: float = 0.0  # Skills alignment (0-1)
    experience_relevance_score: float = 0.0  # Experience relevance (0-1)
    context_fit_score: float = 0.0  # Overall contextual fit (0-1)

    # Additional details
    explanation: str = ""
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    inferred_skills: List[str] = field(default_factory=list)  # Skills inferred from context
    transferable_skills: List[str] = field(default_factory=list)

    # Embedding info
    embedding_similarity: float = 0.0  # Similarity from embeddings if computed
    used_embeddings: bool = False

    # Provider info
    provider: str = ""
    model: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "semantic_score": round(self.semantic_score, 4),
            "passed": self.passed,
            "method": self.method,
            "skill_match_score": round(self.skill_match_score, 4),
            "experience_relevance_score": round(self.experience_relevance_score, 4),
            "context_fit_score": round(self.context_fit_score, 4),
            "explanation": self.explanation,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "inferred_skills": self.inferred_skills,
            "transferable_skills": self.transferable_skills,
            "embedding_similarity": round(self.embedding_similarity, 4),
            "used_embeddings": self.used_embeddings,
            "provider": self.provider,
            "model": self.model,
        }


def detect_language(text: str, default: str = "en") -> str:
    """
    Detect the language of input text.

    Args:
        text: Text to analyze
        default: Default language if detection fails

    Returns:
        Language code (e.g., 'en', 'ru', 'es', 'de')
    """
    if not text or len(text.strip()) < 20:
        return default

    try:
        from langdetect import detect, LangDetectException

        try:
            detected = detect(text)
            # Map detected language to supported languages
            supported_langs = {
                "en": "en",  # English
                "ru": "ru",  # Russian
                "es": "es",  # Spanish
                "de": "de",  # German
                "fr": "fr",  # French
                "it": "it",  # Italian
                "pt": "pt",  # Portuguese
                "zh": "zh",  # Chinese
                "ja": "ja",  # Japanese
                "ko": "ko",  # Korean
                "ar": "ar",  # Arabic
                "hi": "hi",  # Hindi
                "tr": "tr",  # Turkish
                "pl": "pl",  # Polish
                "uk": "uk",  # Ukrainian
                "cs": "cs",  # Czech
                "nl": "nl",  # Dutch
                "sv": "sv",  # Swedish
                "no": "no",  # Norwegian
                "da": "da",  # Danish
                "fi": "fi",  # Finnish
            }

            return supported_langs.get(detected, default)
        except LangDetectException:
            return default
    except ImportError:
        # langdetect not available, use simple heuristics
        text_lower = text.lower()

        # Check for Cyrillic characters (Russian, Ukrainian, etc.)
        if any(0x0400 <= ord(c) <= 0x04FF for c in text):
            # More specific: distinguish Russian vs Ukrainian
            uk_chars = ["і", "ї", "є", "ґ"]
            if any(c in text_lower for c in uk_chars):
                return "uk"
            return "ru"

        # Check for CJK characters
        if any(0x4E00 <= ord(c) <= 0x9FFF for c in text):
            return "zh"  # Simplified Chinese as default for CJK

        # Check for Arabic
        if any(0x0600 <= ord(c) <= 0x06FF for c in text):
            return "ar"

        # Check for specific language patterns
        if "el" in text_lower.split() or "la" in text_lower.split():
            return "es"  # Spanish

        if "der" in text_lower.split() or "die" in text_lower.split():
            return "de"  # German

        if "le" in text_lower.split() and "la" in text_lower.split():
            return "fr"  # French

        return default


class LLMSemanticMatcher:
    """
    LLM-powered semantic matcher for resume-job matching.

    Uses large language models to perform deep semantic analysis of resume
    to job posting matching. Goes beyond keyword matching to understand:
    - Contextual skill alignment
    - Transferable skills
    - Experience relevance
    - Natural language queries

    Example:
        >>> matcher = LLMSemanticMatcher()
        >>> result = await matcher.match(
        ...     resume_text="Senior React developer with fintech experience...",
        ...     job_title="Senior Frontend Developer",
        ...     job_description="Looking for React expert with finance background",
        ...     required_skills=["React", "TypeScript", "Finance"]
        ... )
        >>> print(result.semantic_score)
        0.87
        >>> print(result.inferred_skills)
        ["JavaScript", "Frontend Architecture"]
    """

    # Class-level embedding cache
    _embedding_cache: Dict[str, Any] = {}

    def __init__(
        self,
        threshold: float = 0.6,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        use_embeddings: bool = True,
        cache_embeddings: bool = True,
    ):
        """
        Initialize the LLM semantic matcher.

        Args:
            threshold: Minimum semantic score to pass (0.0-1.0)
            provider: LLM provider to use (default from config)
            model: Model name to use (default from config)
            use_embeddings: Whether to use embeddings for similarity comparison
            cache_embeddings: Whether to cache embeddings for performance
        """
        settings = get_settings()

        self.threshold = threshold
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.use_embeddings = use_embeddings
        self.cache_embeddings = cache_embeddings

        # LLM parameters
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

        # API keys
        self.zai_api_key = settings.zai_api_key
        self.zai_base_url = settings.zai_base_url
        self.openai_api_key = settings.openai_api_key
        self.anthropic_api_key = settings.anthropic_api_key
        self.google_api_key = settings.google_api_key

        # Check for embedding API support
        self._has_embedding_api = self._check_embedding_support()

        logger.info(
            f"LLMSemanticMatcher initialized: provider={self.provider}, "
            f"model={self.model}, threshold={self.threshold}, "
            f"use_embeddings={self.use_embeddings}, has_embedding_api={self._has_embedding_api}"
        )

    def _check_embedding_support(self) -> bool:
        """Check if the configured provider supports embeddings."""
        try:
            if self.provider == "openai":
                return bool(self.openai_api_key)
            elif self.provider == "anthropic":
                # Anthropic doesn't have a public embeddings API yet
                return False
            elif self.provider == "google":
                return bool(self.google_api_key)
            elif self.provider == "zai":
                # Z.ai may support OpenAI-compatible embeddings
                return bool(self.zai_api_key)
            return False
        except Exception:
            return False

    def _get_system_prompt(self, language: str = "en") -> str:
        """
        Get the system prompt for semantic matching.

        Args:
            language: Language code for the prompt (en, ru, etc.)

        Returns:
            System prompt string appropriate for the language
        """
        base_prompt = """You are an expert semantic matching system specialized in analyzing resumes against job postings. Your task is to evaluate how well a candidate's resume matches a job posting using deep semantic understanding.

Go beyond simple keyword matching to consider:

1. **Skill Match Score (0-1)**: Evaluate how well the candidate's demonstrated skills align with required skills. Consider:
   - Direct skill matches
   - Related/transferable skills
   - Skills inferred from project descriptions

2. **Experience Relevance (0-1)**: Assess how relevant the candidate's experience is for this role. Consider:
   - Industry relevance (e.g., fintech experience for finance role)
   - Domain expertise
   - Seniority level alignment
   - Project complexity and scope

3. **Context Fit (0-1)**: Evaluate overall contextual fit considering:
   - Career trajectory and progression
   - Company culture fit indicators
   - Learning capability and adaptability
   - Specializations that align with job requirements

Return your analysis in the following JSON format:
```json
{
    "skill_match_score": <float 0-1>,
    "experience_relevance_score": <float 0-1>,
    "context_fit_score": <float 0-1>,
    "matched_skills": ["<list of directly matched skills>"],
    "missing_skills": ["<list of clearly missing skills>"],
    "inferred_skills": ["<skills inferred from context>"],
    "transferable_skills": ["<skills that are transferable>"],
    "explanation": "<detailed explanation of the match quality>"
}
```

Be generous with inferred skills - if the resume describes work that would require a skill, consider it as present. For example, "built scalable web services" implies knowledge of backend concepts even if not explicitly stated.
"""

        # Add multi-language instruction
        multi_language_suffix = """

**MULTI-LANGUAGE SUPPORT**: You can analyze resumes and job postings in multiple languages including English, Russian, Spanish, German, French, and others. When the content is in a language other than English:
- Analyze the content in its original language without requiring translation
- Recognize technical terms and skills regardless of language (e.g., "Python", "JavaScript", "React")
- Match skills across languages (e.g., "разработка" in Russian matches "development" in English)
- Provide explanations in the same language as the resume content
- Handle language-specific job titles and terminology appropriately

Your analysis should be language-agnostic and focus on the semantic meaning of skills and experience.
"""

        return base_prompt + multi_language_suffix

    def _create_matching_prompt(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        query: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        """
        Create the semantic matching prompt with multi-language support.

        Args:
            resume_text: Resume text content
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills from job posting
            query: Optional natural language query for additional context
            language: Optional language code for the content (en, ru, etc.)

        Returns:
            Formatted prompt string for LLM
        """
        prompt_parts = [
            f"Please semantically evaluate this resume against the job posting:\n\n",
            f"=== JOB POSTING ===\n",
            f"Title: {job_title}\n",
            f"Description: {job_description}\n",
            f"Required Skills: {', '.join(required_skills)}\n",
        ]

        if query:
            prompt_parts.append(f"\nAdditional Query Context: {query}\n")

        # Add language context if specified
        if language and language != "en":
            language_names = {
                "ru": "Russian",
                "es": "Spanish",
                "de": "German",
                "fr": "French",
                "it": "Italian",
                "pt": "Portuguese",
                "zh": "Chinese",
                "ja": "Japanese",
                "ko": "Korean",
                "ar": "Arabic",
                "hi": "Hindi",
                "tr": "Turkish",
                "pl": "Polish",
                "uk": "Ukrainian",
                "cs": "Czech",
                "nl": "Dutch",
                "sv": "Swedish",
                "no": "Norwegian",
                "da": "Danish",
                "fi": "Finnish",
            }
            lang_name = language_names.get(language, language)
            prompt_parts.append(f"\nLanguage Context: The content may be in {lang_name} or mixed with English.\n")

        prompt_parts.extend([
            f"\n=== RESUME ===\n",
            f"{resume_text}\n",
            f"\n=== END ===\n",
            f"Analyze the semantic alignment and return JSON with scores and explanations.",
        ])

        return "".join(prompt_parts)

    async def _get_embedding(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> Optional[List[float]]:
        """
        Get embedding for text using the configured provider.

        Args:
            text: Text to embed
            model: Optional embedding model name

        Returns:
            List of embedding values or None if not available
        """
        if not self.use_embeddings or not self._has_embedding_api:
            return None

        # Check cache
        cache_key = f"{self.provider}:{text[:100]}"
        if self.cache_embeddings and cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        try:
            if self.provider == "openai":
                return await self._get_openai_embedding(text, model)
            elif self.provider == "google":
                return await self._get_google_embedding(text, model)
            elif self.provider == "zai":
                return await self._get_zai_embedding(text, model)
            else:
                return None
        except Exception as e:
            logger.warning(f"Failed to get embedding: {e}")
            return None

    async def batch_get_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[Optional[List[float]]]:
        """
        Get embeddings for multiple texts in batch.

        More efficient than calling _get_embedding multiple times,
        especially for providers that support batch requests.

        Args:
            texts: List of texts to embed
            model: Optional embedding model name

        Returns:
            List of embeddings (same order as input), None for failed embeddings
        """
        if not self.use_embeddings or not self._has_embedding_api:
            return [None] * len(texts)

        try:
            if self.provider == "openai":
                return await self._batch_get_openai_embeddings(texts, model)
            elif self.provider == "google":
                return await self._batch_get_google_embeddings(texts, model)
            elif self.provider == "zai":
                return await self._batch_get_zai_embeddings(texts, model)
            else:
                return [None] * len(texts)
        except Exception as e:
            logger.warning(f"Failed to get batch embeddings: {e}")
            return [None] * len(texts)

    async def _get_openai_embedding(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> Optional[List[float]]:
        """Get embedding from OpenAI."""
        try:
            from openai import AsyncOpenAI

            if not self.openai_api_key:
                return None

            client = AsyncOpenAI(api_key=self.openai_api_key)
            embedding_model = model or "text-embedding-3-small"

            response = await client.embeddings.create(
                input=text,
                model=embedding_model,
            )

            embedding = response.data[0].embedding

            # Cache if enabled
            if self.cache_embeddings:
                cache_key = f"openai:{text[:100]}"
                self._embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return None

    async def _batch_get_openai_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[Optional[List[float]]]:
        """Get multiple embeddings from OpenAI in a single batch request."""
        try:
            from openai import AsyncOpenAI

            if not self.openai_api_key:
                return [None] * len(texts)

            client = AsyncOpenAI(api_key=self.openai_api_key)
            embedding_model = model or "text-embedding-3-small"

            # OpenAI supports up to 2048 texts in a single batch request
            batch_size = 2048
            results = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                # Check cache first for each text
                embeddings_to_fetch = []
                cache_indices = []
                batch_results = [None] * len(batch)

                for j, text in enumerate(batch):
                    cache_key = f"openai:{text[:100]}"
                    if self.cache_embeddings and cache_key in self._embedding_cache:
                        batch_results[j] = self._embedding_cache[cache_key]
                    else:
                        embeddings_to_fetch.append((j, text))
                        cache_indices.append(cache_key)

                if embeddings_to_fetch:
                    # Prepare texts for batch request
                    texts_to_fetch = [text for _, text in embeddings_to_fetch]

                    response = await client.embeddings.create(
                        input=texts_to_fetch,
                        model=embedding_model,
                    )

                    # Cache and store results
                    for idx, (result_idx, _) in enumerate(zip(range(len(embeddings_to_fetch)), embeddings_to_fetch)):
                        embedding = response.data[idx].embedding
                        batch_results[result_idx] = embedding

                        if self.cache_embeddings:
                            self._embedding_cache[cache_indices[idx]] = embedding

                results.extend(batch_results)

            return results

        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            return [None] * len(texts)

    async def _get_google_embedding(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> Optional[List[float]]:
        """Get embedding from Google."""
        try:
            import google.generativeai as genai

            if not self.google_api_key:
                return None

            genai.configure(api_key=self.google_api_key)
            embedding_model = model or "models/text-embedding-004"

            result = await genai.embed_content_async(
                model=embedding_model,
                content=text,
                task_type="retrieval_document",
            )

            embedding = result.get("embedding")

            # Cache if enabled
            if self.cache_embeddings and embedding:
                cache_key = f"google:{text[:100]}"
                self._embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Google embedding failed: {e}")
            return None

    async def _batch_get_google_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[Optional[List[float]]]:
        """Get multiple embeddings from Google in batch."""
        try:
            import google.generativeai as genai

            if not self.google_api_key:
                return [None] * len(texts)

            genai.configure(api_key=self.google_api_key)
            embedding_model = model or "models/text-embedding-004"

            results = []

            for text in texts:
                cache_key = f"google:{text[:100]}"
                if self.cache_embeddings and cache_key in self._embedding_cache:
                    results.append(self._embedding_cache[cache_key])
                else:
                    result = await genai.embed_content_async(
                        model=embedding_model,
                        content=text,
                        task_type="retrieval_document",
                    )
                    embedding = result.get("embedding")

                    if self.cache_embeddings and embedding:
                        self._embedding_cache[cache_key] = embedding

                    results.append(embedding)

            return results

        except Exception as e:
            logger.error(f"Google batch embedding failed: {e}")
            return [None] * len(texts)

    async def _get_zai_embedding(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> Optional[List[float]]:
        """Get embedding from Z.ai (OpenAI-compatible)."""
        try:
            from openai import AsyncOpenAI

            if not self.zai_api_key:
                return None

            client = AsyncOpenAI(
                api_key=self.zai_api_key,
                base_url=self.zai_base_url,
            )
            embedding_model = model or "text-embedding-ada-002"

            response = await client.embeddings.create(
                input=text,
                model=embedding_model,
            )

            embedding = response.data[0].embedding

            # Cache if enabled
            if self.cache_embeddings:
                cache_key = f"zai:{text[:100]}"
                self._embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Z.ai embedding failed: {e}")
            return None

    async def _batch_get_zai_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[Optional[List[float]]]:
        """Get multiple embeddings from Z.ai in a single batch request."""
        try:
            from openai import AsyncOpenAI

            if not self.zai_api_key:
                return [None] * len(texts)

            client = AsyncOpenAI(
                api_key=self.zai_api_key,
                base_url=self.zai_base_url,
            )
            embedding_model = model or "text-embedding-ada-002"

            # Try batch request first (Z.ai may support OpenAI-compatible batching)
            batch_size = 2048
            results = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                # Check cache first
                embeddings_to_fetch = []
                cache_indices = []
                batch_results = [None] * len(batch)

                for j, text in enumerate(batch):
                    cache_key = f"zai:{text[:100]}"
                    if self.cache_embeddings and cache_key in self._embedding_cache:
                        batch_results[j] = self._embedding_cache[cache_key]
                    else:
                        embeddings_to_fetch.append((j, text))
                        cache_indices.append(cache_key)

                if embeddings_to_fetch:
                    texts_to_fetch = [text for _, text in embeddings_to_fetch]

                    response = await client.embeddings.create(
                        input=texts_to_fetch,
                        model=embedding_model,
                    )

                    for idx, (result_idx, _) in enumerate(embeddings_to_fetch):
                        embedding = response.data[idx].embedding
                        batch_results[result_idx] = embedding

                        if self.cache_embeddings:
                            self._embedding_cache[cache_indices[idx]] = embedding

                results.extend(batch_results)

            return results

        except Exception as e:
            logger.error(f"Z.ai batch embedding failed: {e}")
            return [None] * len(texts)

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import numpy as np

            dot_product = np.dot(vec1, vec2)
            norm1 = np.sqrt(np.dot(vec1, vec1))
            norm2 = np.sqrt(np.dot(vec2, vec2))

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))
        except Exception:
            return 0.0

    async def _call_openai(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """Call OpenAI API for semantic matching."""
        try:
            from openai import AsyncOpenAI

            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")

            client = AsyncOpenAI(api_key=self.openai_api_key)

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(language=language)},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except ImportError:
            logger.error("OpenAI package not installed")
            raise
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    async def _call_anthropic(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """Call Anthropic API for semantic matching."""
        try:
            from anthropic import AsyncAnthropic

            if not self.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")

            client = AsyncAnthropic(api_key=self.anthropic_api_key)

            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self._get_system_prompt(language=language),
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
            logger.error("Anthropic package not installed")
            raise
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    async def _call_google(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """Call Google Gemini API for semantic matching."""
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
                system_instruction=self._get_system_prompt(language=language),
            )

            response = await genai_model.generate_content_async(prompt)
            result_text = response.text

            return json.loads(result_text)

        except ImportError:
            logger.error("Google Generative AI package not installed")
            raise
        except Exception as e:
            logger.error(f"Google API call failed: {e}")
            raise

    async def _call_zai(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """Call Z.ai API for semantic matching (OpenAI-compatible)."""
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
                    {"role": "system", "content": self._get_system_prompt(language=language)},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content

            # Extract JSON from response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()

            return json.loads(content)

        except Exception as e:
            logger.error(f"Z.ai API call failed: {e}")
            raise

    async def _call_llm(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """
        Call the appropriate LLM provider with language support.

        Args:
            prompt: The prompt to send to the LLM
            language: Language code for the system prompt

        Returns:
            Dictionary with LLM response parsed as JSON
        """
        if self.provider == "zai":
            return await self._call_zai(prompt, language=language)
        elif self.provider == "openai":
            return await self._call_openai(prompt, language=language)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt, language=language)
        elif self.provider == "google":
            return await self._call_google(prompt, language=language)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def match(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        query: Optional[str] = None,
        threshold: Optional[float] = None,
        use_embeddings: Optional[bool] = None,
        language: Optional[str] = None,
    ) -> LLMMatchResult:
        """
        Perform LLM semantic matching with multi-language support.

        Args:
            resume_text: Resume text content
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills from job posting
            query: Optional natural language query for additional context
            threshold: Override default threshold
            use_embeddings: Override embedding setting
            language: Optional language code (en, ru, es, etc.) for content

        Returns:
            LLMMatchResult with semantic match details
        """
        if threshold is None:
            threshold = self.threshold
        if use_embeddings is None:
            use_embeddings = self.use_embeddings

        # Get embeddings for similarity comparison if enabled
        embedding_similarity = 0.0
        used_embeddings = False

        if use_embeddings and self._has_embedding_api:
            try:
                # Combine job text
                job_text = f"{job_title} {job_description} {' '.join(required_skills)}"

                resume_embedding = await self._get_embedding(resume_text)
                job_embedding = await self._get_embedding(job_text)

                if resume_embedding and job_embedding:
                    embedding_similarity = self._cosine_similarity(
                        resume_embedding,
                        job_embedding,
                    )
                    used_embeddings = True
                    logger.debug(f"Embedding similarity: {embedding_similarity:.3f}")
            except Exception as e:
                logger.warning(f"Embedding computation failed: {e}")

        # Create matching prompt with language context
        prompt = self._create_matching_prompt(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            required_skills=required_skills,
            query=query,
            language=language,
        )

        # Get language-appropriate system prompt
        system_prompt = self._get_system_prompt(language=language or "en")

        try:
            # Call LLM for semantic analysis with language context
            llm_result = await self._call_llm(prompt, language=language or "en")

            # Extract scores
            skill_match_score = float(llm_result.get("skill_match_score", 0.0))
            experience_relevance_score = float(llm_result.get("experience_relevance_score", 0.0))
            context_fit_score = float(llm_result.get("context_fit_score", 0.0))

            # Extract skill lists
            matched_skills = llm_result.get("matched_skills", [])
            missing_skills = llm_result.get("missing_skills", [])
            inferred_skills = llm_result.get("inferred_skills", [])
            transferable_skills = llm_result.get("transferable_skills", [])

            # Get explanation
            explanation = llm_result.get("explanation", "")

            # Calculate overall semantic score (weighted average)
            semantic_score = (
                0.4 * skill_match_score +
                0.3 * experience_relevance_score +
                0.3 * context_fit_score
            )

            # Incorporate embedding similarity if computed
            if used_embeddings:
                # Blend semantic score with embedding similarity
                semantic_score = 0.7 * semantic_score + 0.3 * embedding_similarity

            passed = semantic_score >= threshold

            result = LLMMatchResult(
                semantic_score=round(semantic_score, 4),
                passed=passed,
                method="llm",
                skill_match_score=round(skill_match_score, 4),
                experience_relevance_score=round(experience_relevance_score, 4),
                context_fit_score=round(context_fit_score, 4),
                explanation=explanation,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                inferred_skills=inferred_skills,
                transferable_skills=transferable_skills,
                embedding_similarity=round(embedding_similarity, 4),
                used_embeddings=used_embeddings,
                provider=self.provider,
                model=self.model,
            )

            logger.info(
                f"LLM semantic match: score={semantic_score:.3f}, "
                f"passed={passed}, embedding={used_embeddings}"
            )

            return result

        except Exception as e:
            logger.error(f"LLM semantic matching failed: {e}")

            # Return fallback result
            return LLMMatchResult(
                semantic_score=0.0,
                passed=False,
                method="error",
                explanation=f"Semantic matching failed: {str(e)}",
                provider=self.provider,
                model=self.model,
            )

    def match_sync(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        query: Optional[str] = None,
        threshold: Optional[float] = None,
        language: Optional[str] = None,
    ) -> LLMMatchResult:
        """
        Synchronous wrapper for LLM semantic matching.

        Use this when calling from non-async contexts.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.match(
                resume_text=resume_text,
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
                query=query,
                threshold=threshold,
                language=language,
            )
        )

    async def semantic_search(
        self,
        resumes: List[Dict[str, Any]],
        query: str,
        job_title: Optional[str] = None,
        job_description: Optional[str] = None,
        top_k: Optional[int] = None,
        language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform natural language semantic search across resumes with multi-language support.

        Args:
            resumes: List of resumes with 'text' and optional 'id', 'name'
            query: Natural language query (e.g., "senior Python developer with fintech experience")
            job_title: Optional job title for context
            job_description: Optional job description for context
            top_k: Maximum number of results to return
            language: Optional language code (en, ru, etc.) for content

        Returns:
            List of resumes with added 'semantic_score' and 'match_result', sorted by score
        """
        results = []

        for resume in resumes:
            resume_text = resume.get("text", "")

            # Detect language from resume if not specified
            resume_language = language
            if not resume_language:
                resume_language = detect_language(resume_text, default="en")

            # Extract implied requirements from query
            result = await self.match(
                resume_text=resume_text,
                job_title=job_title or "",
                job_description=job_description or "",
                required_skills=[],
                query=query,
                language=resume_language,
            )

            results.append({
                **resume,
                "semantic_score": result.semantic_score,
                "match_result": result.to_dict(),
            })

        # Sort by semantic score descending
        results.sort(key=lambda x: x["semantic_score"], reverse=True)

        # Return top_k results if specified
        if top_k:
            results = results[:top_k]

        return results

    async def batch_match(
        self,
        resume_texts: List[str],
        job_title: str,
        job_description: str,
        required_skills: List[str],
        use_batch_embeddings: bool = True,
    ) -> List[LLMMatchResult]:
        """
        Match multiple resumes against a single job posting.

        Useful for ranking candidates for a position. Uses batch embeddings
        for better performance when enabled.

        Args:
            resume_texts: List of resume texts
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills
            use_batch_embeddings: Whether to use batch embedding for efficiency

        Returns:
            List of LLMMatchResult in the same order as input
        """
        # Pre-compute embeddings if enabled and available
        job_embedding = None
        resume_embeddings = [None] * len(resume_texts)

        if use_batch_embeddings and self.use_embeddings and self._has_embedding_api:
            try:
                # Combine job text
                job_text = f"{job_title} {job_description} {' '.join(required_skills)}"

                # Get all embeddings in batch for efficiency
                all_texts = [job_text] + resume_texts
                all_embeddings = await self.batch_get_embeddings(all_texts)

                if all_embeddings and all_embeddings[0] is not None:
                    job_embedding = all_embeddings[0]
                    resume_embeddings = all_embeddings[1:]
                    logger.debug(f"Batch embeddings computed for {len(resume_texts)} resumes")
            except Exception as e:
                logger.warning(f"Batch embedding computation failed: {e}")

        # Create matching tasks with pre-computed embeddings
        tasks = []
        for i, resume_text in enumerate(resume_texts):
            task = self.match(
                resume_text=resume_text,
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Resume {i} matching failed: {result}")
                processed_results.append(
                    LLMMatchResult(
                        semantic_score=0.0,
                        passed=False,
                        method="error",
                        explanation=f"Matching failed: {str(result)}",
                        provider=self.provider,
                        model=self.model,
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    def clear_embedding_cache(self) -> None:
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")


# Singleton instance
_default_matcher: Optional[LLMSemanticMatcher] = None


def get_llm_matcher(
    threshold: Optional[float] = None,
    provider: Optional[str] = None,
    use_embeddings: Optional[bool] = None,
) -> Optional[LLMSemanticMatcher]:
    """
    Get or create default LLM matcher instance.

    Args:
        threshold: Optional threshold for new instance
        provider: Optional provider for new instance
        use_embeddings: Optional embedding setting for new instance

    Returns:
        LLMSemanticMatcher instance or None if LLM not configured

    Note:
        If custom parameters are provided, a new matcher is created.
        Otherwise, returns the default singleton instance.
        Returns None if no LLM API key is configured.
    """
    global _default_matcher
    settings = get_settings()

    # Check if any LLM API key is configured
    has_api_key = bool(
        settings.zai_api_key or
        settings.openai_api_key or
        settings.anthropic_api_key or
        settings.google_api_key
    )

    if not has_api_key:
        logger.warning("No LLM API key configured, LLM matcher unavailable")
        return None

    # If custom settings requested, create a new matcher
    if any(v is not None for v in [threshold, provider, use_embeddings]):
        return LLMSemanticMatcher(
            threshold=threshold if threshold is not None else 0.6,
            provider=provider,
            use_embeddings=use_embeddings if use_embeddings is not None else True,
        )

    # Return default singleton
    if _default_matcher is None:
        _default_matcher = LLMSemanticMatcher()

    return _default_matcher
