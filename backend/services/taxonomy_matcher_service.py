"""
Taxonomy-aware skill matching service.

This module provides the TaxonomyMatcherService class for matching skills
using the skill taxonomy with variants, aliases, and relationships.
It integrates with the existing SkillsMatcher for fuzzy and semantic matching
while adding taxonomy-specific enhancements.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.skill_taxonomy import SkillTaxonomy
from models.skill_relationship import SkillRelationship, RelationshipType
from skills.skills_matcher import SkillsMatcher

logger = logging.getLogger(__name__)


# Built-in common skill aliases and abbreviations
# These serve as a fallback when taxonomy data is not available
_COMMON_SKILL_ALIASES: Dict[str, Dict[str, Any]] = {
    # Programming languages
    "js": {"resolved": "JavaScript", "industry": "tech", "context": "programming_language"},
    "ts": {"resolved": "TypeScript", "industry": "tech", "context": "programming_language"},
    "py": {"resolved": "Python", "industry": "tech", "context": "programming_language"},
    "rb": {"resolved": "Ruby", "industry": "tech", "context": "programming_language"},
    "java": {"resolved": "Java", "industry": "tech", "context": "programming_language"},
    "csharp": {"resolved": "C#", "industry": "tech", "context": "programming_language"},
    "c#": {"resolved": "C#", "industry": "tech", "context": "programming_language"},
    "cpp": {"resolved": "C++", "industry": "tech", "context": "programming_language"},
    "c++": {"resolved": "C++", "industry": "tech", "context": "programming_language"},
    "golang": {"resolved": "Go", "industry": "tech", "context": "programming_language"},
    "go": {"resolved": "Go", "industry": "tech", "context": "programming_language"},
    "kt": {"resolved": "Kotlin", "industry": "tech", "context": "programming_language"},
    "scala": {"resolved": "Scala", "industry": "tech", "context": "programming_language"},
    "rust": {"resolved": "Rust", "industry": "tech", "context": "programming_language"},
    "php": {"resolved": "PHP", "industry": "tech", "context": "programming_language"},
    "swift": {"resolved": "Swift", "industry": "tech", "context": "programming_language"},
    # Web frameworks
    "reactjs": {"resolved": "React", "industry": "tech", "context": "web_framework"},
    "react.js": {"resolved": "React", "industry": "tech", "context": "web_framework"},
    "vuejs": {"resolved": "Vue", "industry": "tech", "context": "web_framework"},
    "vue.js": {"resolved": "Vue", "industry": "tech", "context": "web_framework"},
    "angularjs": {"resolved": "Angular", "industry": "tech", "context": "web_framework"},
    "angular.js": {"resolved": "Angular", "industry": "tech", "context": "web_framework"},
    "nextjs": {"resolved": "Next.js", "industry": "tech", "context": "web_framework"},
    "next.js": {"resolved": "Next.js", "industry": "tech", "context": "web_framework"},
    "nuxtjs": {"resolved": "Nuxt.js", "industry": "tech", "context": "web_framework"},
    "nuxt.js": {"resolved": "Nuxt.js", "industry": "tech", "context": "web_framework"},
    "svelte": {"resolved": "Svelte", "industry": "tech", "context": "web_framework"},
    # Backend frameworks
    "django": {"resolved": "Django", "industry": "tech", "context": "web_framework"},
    "flask": {"resolved": "Flask", "industry": "tech", "context": "web_framework"},
    "fastapi": {"resolved": "FastAPI", "industry": "tech", "context": "web_framework"},
    "expressjs": {"resolved": "Express.js", "industry": "tech", "context": "web_framework"},
    "express": {"resolved": "Express.js", "industry": "tech", "context": "web_framework"},
    "nodejs": {"resolved": "Node.js", "industry": "tech", "context": "runtime"},
    "node.js": {"resolved": "Node.js", "industry": "tech", "context": "runtime"},
    "node": {"resolved": "Node.js", "industry": "tech", "context": "runtime"},
    # Databases
    "postgres": {"resolved": "PostgreSQL", "industry": "tech", "context": "database"},
    "postgresql": {"resolved": "PostgreSQL", "industry": "tech", "context": "database"},
    "mysql": {"resolved": "MySQL", "industry": "tech", "context": "database"},
    "mongodb": {"resolved": "MongoDB", "industry": "tech", "context": "database"},
    "redis": {"resolved": "Redis", "industry": "tech", "context": "database"},
    "sqlite": {"resolved": "SQLite", "industry": "tech", "context": "database"},
    # Cloud/DevOps
    "aws": {"resolved": "Amazon Web Services", "industry": "tech", "context": "cloud"},
    "gcp": {"resolved": "Google Cloud Platform", "industry": "tech", "context": "cloud"},
    "azure": {"resolved": "Microsoft Azure", "industry": "tech", "context": "cloud"},
    "k8s": {"resolved": "Kubernetes", "industry": "tech", "context": "devops"},
    "kubernetes": {"resolved": "Kubernetes", "industry": "tech", "context": "devops"},
    "docker": {"resolved": "Docker", "industry": "tech", "context": "devops"},
    "ci/cd": {"resolved": "CI/CD", "industry": "tech", "context": "devops"},
    "cicd": {"resolved": "CI/CD", "industry": "tech", "context": "devops"},
    "terraform": {"resolved": "Terraform", "industry": "tech", "context": "devops"},
    "ansible": {"resolved": "Ansible", "industry": "tech", "context": "devops"},
    # Data Science / ML
    "ml": {"resolved": "Machine Learning", "industry": "tech", "context": "data_science"},
    "ai": {"resolved": "Artificial Intelligence", "industry": "tech", "context": "data_science"},
    "nlp": {"resolved": "Natural Language Processing", "industry": "tech", "context": "data_science"},
    "cv": {"resolved": "Computer Vision", "industry": "tech", "context": "data_science"},
    "dl": {"resolved": "Deep Learning", "industry": "tech", "context": "data_science"},
    "tensorflow": {"resolved": "TensorFlow", "industry": "tech", "context": "ml_framework"},
    "pytorch": {"resolved": "PyTorch", "industry": "tech", "context": "ml_framework"},
    "keras": {"resolved": "Keras", "industry": "tech", "context": "ml_framework"},
    "pandas": {"resolved": "Pandas", "industry": "tech", "context": "data_analysis"},
    "numpy": {"resolved": "NumPy", "industry": "tech", "context": "data_analysis"},
    # Other common abbreviations
    "api": {"resolved": "API", "industry": "tech", "context": "software"},
    "rest": {"resolved": "REST API", "industry": "tech", "context": "software"},
    "graphql": {"resolved": "GraphQL", "industry": "tech", "context": "software"},
    "sql": {"resolved": "SQL", "industry": "tech", "context": "database"},
    "html": {"resolved": "HTML", "industry": "tech", "context": "web"},
    "css": {"resolved": "CSS", "industry": "tech", "context": "web"},
    "sass": {"resolved": "Sass", "industry": "tech", "context": "web"},
    "scss": {"resolved": "SCSS", "industry": "tech", "context": "web"},
    "ui": {"resolved": "UI Design", "industry": "tech", "context": "design"},
    "ux": {"resolved": "UX Design", "industry": "tech", "context": "design"},
    "figma": {"resolved": "Figma", "industry": "tech", "context": "design_tool"},
    # Testing
    "tdd": {"resolved": "Test-Driven Development", "industry": "tech", "context": "methodology"},
    "bdd": {"resolved": "Behavior-Driven Development", "industry": "tech", "context": "methodology"},
    "jest": {"resolved": "Jest", "industry": "tech", "context": "testing"},
    "pytest": {"resolved": "pytest", "industry": "tech", "context": "testing"},
    "cypress": {"resolved": "Cypress", "industry": "tech", "context": "testing"},
    # Mobile
    "ios": {"resolved": "iOS Development", "industry": "tech", "context": "mobile"},
    "android": {"resolved": "Android Development", "industry": "tech", "context": "mobile"},
    "reactnative": {"resolved": "React Native", "industry": "tech", "context": "mobile"},
    "react native": {"resolved": "React Native", "industry": "tech", "context": "mobile"},
    "flutter": {"resolved": "Flutter", "industry": "tech", "context": "mobile"},
    # Methodologies
    "agile": {"resolved": "Agile", "industry": "tech", "context": "methodology"},
    "scrum": {"resolved": "Scrum", "industry": "tech", "context": "methodology"},
    "devops": {"resolved": "DevOps", "industry": "tech", "context": "methodology"},
    # Version Control
    "git": {"resolved": "Git", "industry": "tech", "context": "version_control"},
    "github": {"resolved": "GitHub", "industry": "tech", "context": "version_control"},
    "gitlab": {"resolved": "GitLab", "industry": "tech", "context": "version_control"},
}


# Built-in common skill relationships
# These serve as a fallback when taxonomy relationship data is not available
# Format: skill_name -> list of related skills with type and weight
_COMMON_SKILL_RELATIONSHIPS: Dict[str, List[Dict[str, Any]]] = {
    # Frontend Frameworks
    "React": [
        {"related": "Vue", "type": "similar", "weight": 0.8},
        {"related": "Angular", "type": "similar", "weight": 0.7},
        {"related": "Next.js", "type": "parent_child", "weight": 0.9},
        {"related": "JavaScript", "type": "prerequisite", "weight": 1.0},
        {"related": "TypeScript", "type": "related", "weight": 0.8},
        {"related": "Redux", "type": "related", "weight": 0.85},
        {"related": "React Native", "type": "related", "weight": 0.75},
        {"related": "Frontend Development", "type": "parent_child", "weight": 0.9},
    ],
    "Vue": [
        {"related": "React", "type": "similar", "weight": 0.8},
        {"related": "Angular", "type": "similar", "weight": 0.7},
        {"related": "Nuxt.js", "type": "parent_child", "weight": 0.9},
        {"related": "JavaScript", "type": "prerequisite", "weight": 1.0},
        {"related": "Vuex", "type": "related", "weight": 0.8},
        {"related": "Frontend Development", "type": "parent_child", "weight": 0.9},
    ],
    "Angular": [
        {"related": "React", "type": "similar", "weight": 0.7},
        {"related": "Vue", "type": "similar", "weight": 0.7},
        {"related": "TypeScript", "type": "prerequisite", "weight": 0.95},
        {"related": "RxJS", "type": "related", "weight": 0.85},
        {"related": "Frontend Development", "type": "parent_child", "weight": 0.9},
    ],
    "Next.js": [
        {"related": "React", "type": "parent_child", "weight": 1.0},
        {"related": "Nuxt.js", "type": "similar", "weight": 0.75},
        {"related": "Gatsby", "type": "similar", "weight": 0.7},
        {"related": "JavaScript", "type": "prerequisite", "weight": 1.0},
        {"related": "Node.js", "type": "related", "weight": 0.8},
    ],
    # Programming Languages
    "JavaScript": [
        {"related": "TypeScript", "type": "similar", "weight": 0.9},
        {"related": "Node.js", "type": "related", "weight": 0.9},
        {"related": "React", "type": "related", "weight": 0.85},
        {"related": "Vue", "type": "related", "weight": 0.8},
        {"related": "Angular", "type": "related", "weight": 0.75},
        {"related": "Python", "type": "similar", "weight": 0.5},
    ],
    "TypeScript": [
        {"related": "JavaScript", "type": "similar", "weight": 0.95},
        {"related": "Angular", "type": "related", "weight": 0.9},
        {"related": "React", "type": "related", "weight": 0.85},
        {"related": "Node.js", "type": "related", "weight": 0.85},
    ],
    "Python": [
        {"related": "Django", "type": "related", "weight": 0.9},
        {"related": "Flask", "type": "related", "weight": 0.85},
        {"related": "FastAPI", "type": "related", "weight": 0.85},
        {"related": "Machine Learning", "type": "related", "weight": 0.8},
        {"related": "Data Science", "type": "related", "weight": 0.8},
        {"related": "JavaScript", "type": "similar", "weight": 0.5},
    ],
    "Go": [
        {"related": "Kubernetes", "type": "related", "weight": 0.85},
        {"related": "Docker", "type": "related", "weight": 0.8},
        {"related": "Microservices", "type": "related", "weight": 0.85},
        {"related": "Rust", "type": "similar", "weight": 0.6},
    ],
    "Rust": [
        {"related": "Go", "type": "similar", "weight": 0.6},
        {"related": "C++", "type": "similar", "weight": 0.7},
        {"related": "Systems Programming", "type": "parent_child", "weight": 0.9},
    ],
    # Backend Frameworks
    "Django": [
        {"related": "Python", "type": "prerequisite", "weight": 1.0},
        {"related": "Flask", "type": "similar", "weight": 0.7},
        {"related": "FastAPI", "type": "similar", "weight": 0.75},
        {"related": "PostgreSQL", "type": "related", "weight": 0.8},
    ],
    "Flask": [
        {"related": "Python", "type": "prerequisite", "weight": 1.0},
        {"related": "Django", "type": "similar", "weight": 0.7},
        {"related": "FastAPI", "type": "similar", "weight": 0.8},
    ],
    "FastAPI": [
        {"related": "Python", "type": "prerequisite", "weight": 1.0},
        {"related": "Django", "type": "similar", "weight": 0.75},
        {"related": "Flask", "type": "similar", "weight": 0.8},
        {"related": "API Development", "type": "parent_child", "weight": 0.9},
    ],
    "Express.js": [
        {"related": "Node.js", "type": "prerequisite", "weight": 1.0},
        {"related": "JavaScript", "type": "prerequisite", "weight": 0.95},
        {"related": "FastAPI", "type": "similar", "weight": 0.6},
        {"related": "API Development", "type": "parent_child", "weight": 0.9},
    ],
    "Node.js": [
        {"related": "JavaScript", "type": "prerequisite", "weight": 1.0},
        {"related": "Express.js", "type": "related", "weight": 0.9},
        {"related": "Next.js", "type": "related", "weight": 0.85},
        {"related": "React", "type": "related", "weight": 0.75},
    ],
    # Databases
    "PostgreSQL": [
        {"related": "MySQL", "type": "similar", "weight": 0.8},
        {"related": "SQL", "type": "prerequisite", "weight": 0.95},
        {"related": "Django", "type": "related", "weight": 0.7},
        {"related": "Database", "type": "parent_child", "weight": 0.9},
    ],
    "MySQL": [
        {"related": "PostgreSQL", "type": "similar", "weight": 0.8},
        {"related": "SQL", "type": "prerequisite", "weight": 0.95},
        {"related": "Database", "type": "parent_child", "weight": 0.9},
    ],
    "MongoDB": [
        {"related": "PostgreSQL", "type": "similar", "weight": 0.5},
        {"related": "Node.js", "type": "related", "weight": 0.8},
        {"related": "Express.js", "type": "related", "weight": 0.75},
        {"related": "Database", "type": "parent_child", "weight": 0.9},
    ],
    "Redis": [
        {"related": "Database", "type": "parent_child", "weight": 0.85},
        {"related": "Caching", "type": "related", "weight": 0.95},
        {"related": "Node.js", "type": "related", "weight": 0.7},
    ],
    # Cloud & DevOps
    "AWS": [
        {"related": "Amazon Web Services", "type": "similar", "weight": 1.0},
        {"related": "Azure", "type": "similar", "weight": 0.7},
        {"related": "GCP", "type": "similar", "weight": 0.7},
        {"related": "Docker", "type": "related", "weight": 0.8},
        {"related": "Kubernetes", "type": "related", "weight": 0.8},
        {"related": "Cloud Computing", "type": "parent_child", "weight": 0.95},
    ],
    "Amazon Web Services": [
        {"related": "AWS", "type": "similar", "weight": 1.0},
        {"related": "Azure", "type": "similar", "weight": 0.7},
        {"related": "GCP", "type": "similar", "weight": 0.7},
    ],
    "Azure": [
        {"related": "Microsoft Azure", "type": "similar", "weight": 1.0},
        {"related": "AWS", "type": "similar", "weight": 0.7},
        {"related": "GCP", "type": "similar", "weight": 0.7},
        {"related": "Cloud Computing", "type": "parent_child", "weight": 0.95},
    ],
    "Microsoft Azure": [
        {"related": "Azure", "type": "similar", "weight": 1.0},
    ],
    "GCP": [
        {"related": "Google Cloud Platform", "type": "similar", "weight": 1.0},
        {"related": "AWS", "type": "similar", "weight": 0.7},
        {"related": "Azure", "type": "similar", "weight": 0.7},
        {"related": "Cloud Computing", "type": "parent_child", "weight": 0.95},
    ],
    "Google Cloud Platform": [
        {"related": "GCP", "type": "similar", "weight": 1.0},
    ],
    "Docker": [
        {"related": "Kubernetes", "type": "related", "weight": 0.9},
        {"related": "Containerization", "type": "related", "weight": 0.95},
        {"related": "DevOps", "type": "parent_child", "weight": 0.85},
        {"related": "CI/CD", "type": "related", "weight": 0.8},
    ],
    "Kubernetes": [
        {"related": "Docker", "type": "related", "weight": 0.9},
        {"related": "Containerization", "type": "related", "weight": 0.95},
        {"related": "DevOps", "type": "parent_child", "weight": 0.85},
        {"related": "Go", "type": "related", "weight": 0.7},
    ],
    "CI/CD": [
        {"related": "DevOps", "type": "parent_child", "weight": 0.95},
        {"related": "Docker", "type": "related", "weight": 0.8},
        {"related": "Jenkins", "type": "related", "weight": 0.85},
        {"related": "GitHub Actions", "type": "related", "weight": 0.85},
    ],
    # Machine Learning & Data
    "Machine Learning": [
        {"related": "Deep Learning", "type": "parent_child", "weight": 0.85},
        {"related": "Python", "type": "related", "weight": 0.9},
        {"related": "TensorFlow", "type": "related", "weight": 0.85},
        {"related": "PyTorch", "type": "related", "weight": 0.85},
        {"related": "Data Science", "type": "similar", "weight": 0.8},
        {"related": "AI", "type": "similar", "weight": 0.9},
    ],
    "Deep Learning": [
        {"related": "Machine Learning", "type": "parent_child", "weight": 0.9},
        {"related": "Neural Networks", "type": "related", "weight": 0.95},
        {"related": "TensorFlow", "type": "related", "weight": 0.9},
        {"related": "PyTorch", "type": "related", "weight": 0.9},
    ],
    "TensorFlow": [
        {"related": "PyTorch", "type": "similar", "weight": 0.85},
        {"related": "Keras", "type": "related", "weight": 0.9},
        {"related": "Machine Learning", "type": "parent_child", "weight": 0.85},
        {"related": "Python", "type": "prerequisite", "weight": 0.9},
    ],
    "PyTorch": [
        {"related": "TensorFlow", "type": "similar", "weight": 0.85},
        {"related": "Machine Learning", "type": "parent_child", "weight": 0.85},
        {"related": "Python", "type": "prerequisite", "weight": 0.9},
    ],
    "Data Science": [
        {"related": "Python", "type": "related", "weight": 0.9},
        {"related": "Pandas", "type": "related", "weight": 0.9},
        {"related": "NumPy", "type": "related", "weight": 0.85},
        {"related": "Machine Learning", "type": "similar", "weight": 0.8},
    ],
    "Pandas": [
        {"related": "NumPy", "type": "related", "weight": 0.9},
        {"related": "Python", "type": "prerequisite", "weight": 1.0},
        {"related": "Data Science", "type": "parent_child", "weight": 0.85},
    ],
    "NumPy": [
        {"related": "Pandas", "type": "related", "weight": 0.9},
        {"related": "Python", "type": "prerequisite", "weight": 1.0},
    ],
    # Mobile Development
    "React Native": [
        {"related": "React", "type": "prerequisite", "weight": 0.95},
        {"related": "JavaScript", "type": "prerequisite", "weight": 0.9},
        {"related": "Flutter", "type": "similar", "weight": 0.75},
        {"related": "Mobile Development", "type": "parent_child", "weight": 0.9},
    ],
    "Flutter": [
        {"related": "Dart", "type": "prerequisite", "weight": 1.0},
        {"related": "React Native", "type": "similar", "weight": 0.75},
        {"related": "Mobile Development", "type": "parent_child", "weight": 0.9},
    ],
    "iOS Development": [
        {"related": "Swift", "type": "prerequisite", "weight": 0.95},
        {"related": "Mobile Development", "type": "parent_child", "weight": 0.9},
        {"related": "Android Development", "type": "similar", "weight": 0.6},
    ],
    "Android Development": [
        {"related": "Kotlin", "type": "prerequisite", "weight": 0.95},
        {"related": "Mobile Development", "type": "parent_child", "weight": 0.9},
        {"related": "iOS Development", "type": "similar", "weight": 0.6},
    ],
    # Design
    "Figma": [
        {"related": "UI Design", "type": "related", "weight": 0.9},
        {"related": "UX Design", "type": "related", "weight": 0.85},
        {"related": "Design Tools", "type": "parent_child", "weight": 0.9},
    ],
    "UI Design": [
        {"related": "UX Design", "type": "similar", "weight": 0.85},
        {"related": "Figma", "type": "related", "weight": 0.85},
        {"related": "CSS", "type": "related", "weight": 0.7},
    ],
    "UX Design": [
        {"related": "UI Design", "type": "similar", "weight": 0.85},
        {"related": "Figma", "type": "related", "weight": 0.8},
        {"related": "User Research", "type": "related", "weight": 0.85},
    ],
    # Testing
    "Jest": [
        {"related": "JavaScript", "type": "prerequisite", "weight": 0.9},
        {"related": "React", "type": "related", "weight": 0.85},
        {"related": "Testing", "type": "parent_child", "weight": 0.9},
    ],
    "pytest": [
        {"related": "Python", "type": "prerequisite", "weight": 0.95},
        {"related": "Testing", "type": "parent_child", "weight": 0.9},
        {"related": "Django", "type": "related", "weight": 0.7},
    ],
    "Cypress": [
        {"related": "JavaScript", "type": "prerequisite", "weight": 0.85},
        {"related": "Testing", "type": "parent_child", "weight": 0.9},
        {"related": "React", "type": "related", "weight": 0.75},
    ],
    # Methodologies
    "Agile": [
        {"related": "Scrum", "type": "similar", "weight": 0.85},
        {"related": "Project Management", "type": "parent_child", "weight": 0.8},
    ],
    "Scrum": [
        {"related": "Agile", "type": "parent_child", "weight": 0.9},
        {"related": "Project Management", "type": "parent_child", "weight": 0.75},
    ],
    "DevOps": [
        {"related": "CI/CD", "type": "related", "weight": 0.9},
        {"related": "Docker", "type": "related", "weight": 0.85},
        {"related": "Kubernetes", "type": "related", "weight": 0.85},
        {"related": "AWS", "type": "related", "weight": 0.8},
    ],
}


@dataclass
class TaxonomyMatchResult:
    """
    Result of a taxonomy-aware skill match.

    Attributes:
        matched_skill: The matched canonical skill name
        original_skill: The original skill string that was matched
        taxonomy_entry: Full taxonomy entry if available
        score: Match score (0-100)
        match_type: Type of match ('exact', 'alias', 'variant', 'fuzzy', 'semantic', 'relationship')
        aliases_matched: List of aliases that matched
        related_skills: List of related skills found
        category_path: Hierarchical path from root to skill
        confidence: Confidence level of the match (0-1)
        error: Error message if matching failed
    """
    matched_skill: Optional[str] = None
    original_skill: Optional[str] = None
    taxonomy_entry: Optional[Dict[str, Any]] = None
    score: float = 0.0
    match_type: Optional[str] = None
    aliases_matched: List[str] = field(default_factory=list)
    related_skills: List[str] = field(default_factory=list)
    category_path: List[str] = field(default_factory=list)
    confidence: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "matched_skill": self.matched_skill,
            "original_skill": self.original_skill,
            "taxonomy_entry": self.taxonomy_entry,
            "score": self.score,
            "match_type": self.match_type,
            "aliases_matched": self.aliases_matched,
            "related_skills": self.related_skills,
            "category_path": self.category_path,
            "confidence": self.confidence,
            "error": self.error,
        }


@dataclass
class AliasResolution:
    """
    Result of alias resolution.

    Attributes:
        alias: The original alias/variant string
        resolved_skill: The canonical skill name
        taxonomy_id: UUID of the taxonomy entry
        industry: Industry context
        context: Skill context/category
        confidence: Resolution confidence (0-1)
    """
    alias: str
    resolved_skill: str
    taxonomy_id: Optional[UUID] = None
    industry: Optional[str] = None
    context: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alias": self.alias,
            "resolved_skill": self.resolved_skill,
            "taxonomy_id": str(self.taxonomy_id) if self.taxonomy_id else None,
            "industry": self.industry,
            "context": self.context,
            "confidence": self.confidence,
        }


@dataclass
class RelatedSkill:
    """
    A skill related to another skill.

    Attributes:
        skill_name: Name of the related skill
        relationship_type: Type of relationship (parent_child, similar, etc.)
        weight: Relationship strength (0-1)
        taxonomy_id: UUID of the taxonomy entry
    """
    skill_name: str
    relationship_type: str
    weight: float = 1.0
    taxonomy_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "relationship_type": self.relationship_type,
            "weight": self.weight,
            "taxonomy_id": str(self.taxonomy_id) if self.taxonomy_id else None,
        }


class TaxonomyMatcherService:
    """
    Taxonomy-aware skill matching service.

    This service enhances skill matching by using the skill taxonomy:
    - Matches skills using variants and aliases from the taxonomy
    - Resolves common abbreviations and alternative names
    - Finds related skills using skill relationships
    - Provides hierarchical category information

    The service integrates with the existing SkillsMatcher for fuzzy matching
    while adding taxonomy-specific enhancements for better accuracy.

    Attributes:
        db: Database session for querying taxonomy data
        skills_matcher: Underlying SkillsMatcher instance
        fuzzy_threshold: Minimum fuzzy match score (0-100)
        include_relationships: Whether to include related skills in results
        cache_ttl: Cache time-to-live in seconds

    Example:
        >>> service = TaxonomyMatcherService(db)
        >>> result = await service.match_skill("JS")
        >>> print(result.matched_skill)  # 'JavaScript'
        >>> print(result.match_type)  # 'alias'
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        *,
        fuzzy_threshold: int = 80,
        include_relationships: bool = True,
        cache_ttl: int = 300,
    ) -> None:
        """
        Initialize the taxonomy matcher service.

        Args:
            db: Database session for querying taxonomy data
            fuzzy_threshold: Minimum fuzzy match score (0-100, default: 80)
            include_relationships: Whether to include related skills (default: True)
            cache_ttl: Cache TTL in seconds (default: 300)

        Raises:
            ValueError: If threshold values are out of valid range
        """
        if not 0 <= fuzzy_threshold <= 100:
            raise ValueError("fuzzy_threshold must be between 0 and 100")

        self.db = db
        self.fuzzy_threshold = fuzzy_threshold
        self.include_relationships = include_relationships
        self.cache_ttl = cache_ttl

        # Initialize the underlying SkillsMatcher
        self.skills_matcher = SkillsMatcher(
            fuzzy_threshold=fuzzy_threshold,
            use_semantic=False,
        )

        # In-memory cache for taxonomy data
        self._taxonomy_cache: Dict[str, Dict[str, Any]] = {}
        self._alias_cache: Dict[str, AliasResolution] = {}
        self._cache_timestamp: Optional[datetime] = None

        logger.info(
            f"TaxonomyMatcherService initialized (fuzzy_threshold={fuzzy_threshold}, "
            f"include_relationships={include_relationships})"
        )

    async def match_skill(
        self,
        candidate_skill: str,
        organization_id: Optional[str] = None,
        *,
        include_variants: bool = True,
        include_relationships: Optional[bool] = None,
    ) -> TaxonomyMatchResult:
        """
        Match a candidate skill against the taxonomy.

        Attempts to find the best match using:
        1. Exact match against canonical skill names
        2. Alias/variant match from taxonomy
        3. Fuzzy match using the underlying SkillsMatcher
        4. Relationship-based match (if enabled)

        Args:
            candidate_skill: The skill to match
            organization_id: Organization ID for filtering taxonomy
            include_variants: Whether to check variants/aliases (default: True)
            include_relationships: Whether to find related skills (default: from instance)

        Returns:
            TaxonomyMatchResult with match details

        Example:
            >>> result = await service.match_skill("JS")
            >>> print(result.matched_skill)  # 'JavaScript'
            >>> print(result.match_type)  # 'alias'
        """
        # Validate input
        if not candidate_skill or not isinstance(candidate_skill, str):
            return TaxonomyMatchResult(
                original_skill=candidate_skill,
                error="candidate_skill must be a non-empty string",
            )

        should_include_relationships = (
            include_relationships
            if include_relationships is not None
            else self.include_relationships
        )

        try:
            # Normalize the candidate skill
            normalized_candidate = self.skills_matcher.normalize_skill(candidate_skill)

            # Step 1: Try exact match against taxonomy canonical names
            if self.db:
                exact_match = await self._find_exact_match(
                    normalized_candidate, organization_id
                )
                if exact_match:
                    result = TaxonomyMatchResult(
                        matched_skill=exact_match["skill_name"],
                        original_skill=candidate_skill,
                        taxonomy_entry=exact_match,
                        score=100,
                        match_type="exact",
                        confidence=1.0,
                        category_path=exact_match.get("category_path", []),
                    )

                    if should_include_relationships:
                        result.related_skills = await self._get_related_skill_names(
                            exact_match["id"], organization_id
                        )

                    return result

            # Step 2: Try alias/variant match from taxonomy
            if include_variants and self.db:
                alias_match = await self._find_alias_match(
                    candidate_skill, normalized_candidate, organization_id
                )
                if alias_match:
                    result = TaxonomyMatchResult(
                        matched_skill=alias_match["skill_name"],
                        original_skill=candidate_skill,
                        taxonomy_entry=alias_match,
                        score=95,  # High score for alias match
                        match_type="alias",
                        confidence=0.95,
                        aliases_matched=[candidate_skill],
                        category_path=alias_match.get("category_path", []),
                    )

                    if should_include_relationships:
                        result.related_skills = await self._get_related_skill_names(
                            alias_match["id"], organization_id
                        )

                    return result

            # Step 3: Fall back to fuzzy matching with taxonomy skills
            if self.db:
                taxonomy_skills = await self._get_taxonomy_skills(organization_id)
            else:
                taxonomy_skills = []

            if taxonomy_skills:
                fuzzy_result = self.skills_matcher.match_skill(
                    candidate_skill, taxonomy_skills
                )

                if fuzzy_result.get("matched_skill"):
                    # Get the full taxonomy entry for the matched skill
                    matched_entry = await self._get_taxonomy_entry_by_name(
                        fuzzy_result["matched_skill"], organization_id
                    )

                    result = TaxonomyMatchResult(
                        matched_skill=fuzzy_result["matched_skill"],
                        original_skill=candidate_skill,
                        taxonomy_entry=matched_entry,
                        score=fuzzy_result.get("score", 0),
                        match_type=fuzzy_result.get("match_type", "fuzzy"),
                        confidence=fuzzy_result.get("score", 0) / 100.0,
                        category_path=matched_entry.get("category_path", []) if matched_entry else [],
                    )

                    if should_include_relationships and matched_entry:
                        result.related_skills = await self._get_related_skill_names(
                            matched_entry["id"], organization_id
                        )

                    return result

            # No match found
            logger.debug(f"No match found for skill '{candidate_skill}'")
            return TaxonomyMatchResult(
                original_skill=candidate_skill,
                matched_skill=None,
                score=0,
                match_type=None,
            )

        except Exception as e:
            logger.error(f"Error matching skill '{candidate_skill}': {e}")
            return TaxonomyMatchResult(
                original_skill=candidate_skill,
                error=f"Matching failed: {str(e)}",
            )

    async def match_skills(
        self,
        candidate_skills: List[str],
        organization_id: Optional[str] = None,
        *,
        include_variants: bool = True,
        include_relationships: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Match multiple candidate skills against the taxonomy.

        Args:
            candidate_skills: List of skills to match
            organization_id: Organization ID for filtering taxonomy
            include_variants: Whether to check variants/aliases (default: True)
            include_relationships: Whether to find related skills (default: from instance)

        Returns:
            Dictionary containing:
                - matched: Dict mapping original skills to match results
                - unmatched: List of skills that didn't match
                - matched_skills: List of successfully matched skill names
                - match_rate: Percentage of skills that matched
                - error: Error message if matching failed

        Example:
            >>> result = await service.match_skills(["JS", "React.js"])
            >>> print(result["matched_skills"])  # ['JavaScript', 'React']
        """
        if not candidate_skills or not isinstance(candidate_skills, list):
            return {
                "matched": None,
                "unmatched": None,
                "matched_skills": None,
                "match_rate": 0,
                "error": "candidate_skills must be a non-empty list",
            }

        try:
            matched: Dict[str, Dict[str, Any]] = {}
            matched_skills: List[str] = []
            unmatched: List[str] = []

            for skill in candidate_skills:
                if not skill or not isinstance(skill, str):
                    continue

                result = await self.match_skill(
                    skill,
                    organization_id,
                    include_variants=include_variants,
                    include_relationships=include_relationships,
                )

                if result.error:
                    logger.warning(f"Error matching '{skill}': {result.error}")
                    unmatched.append(skill)
                elif result.matched_skill:
                    matched[skill] = result.to_dict()
                    matched_skills.append(result.matched_skill)
                else:
                    unmatched.append(skill)

            # Remove duplicates while preserving order
            seen: Set[str] = set()
            unique_matched: List[str] = []
            for skill in matched_skills:
                if skill not in seen:
                    seen.add(skill)
                    unique_matched.append(skill)

            match_rate = (
                len(unique_matched) / len(candidate_skills) * 100
                if candidate_skills
                else 0
            )

            logger.info(
                f"Matched {len(unique_matched)}/{len(candidate_skills)} skills "
                f"({match_rate:.1f}%)"
            )

            return {
                "matched": matched,
                "unmatched": unmatched if unmatched else None,
                "matched_skills": unique_matched if unique_matched else None,
                "match_rate": round(match_rate, 2),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Skills matching failed: {e}")
            return {
                "matched": None,
                "unmatched": None,
                "matched_skills": None,
                "match_rate": 0,
                "error": f"Matching failed: {str(e)}",
            }

    def resolve_alias(
        self,
        alias: str,
        *,
        industry: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Optional[AliasResolution]:
        """
        Resolve a skill alias to its canonical form.

        This is a synchronous method that uses cached data and built-in
        alias mappings for fast lookups. For database-backed resolution
        with custom taxonomy data, use resolve_alias_async instead.

        The resolution process:
        1. Check the alias cache for previously resolved aliases
        2. Normalize the alias and check against built-in common aliases
        3. Cache and return the result if found

        Args:
            alias: The alias or variant to resolve
            industry: Optional industry filter (filters results by industry)
            organization_id: Optional organization filter (for caching purposes)

        Returns:
            AliasResolution if found, None otherwise

        Example:
            >>> resolution = service.resolve_alias("JS")
            >>> print(resolution.resolved_skill)  # 'JavaScript'
            >>> print(resolution.industry)  # 'tech'
            >>> print(resolution.confidence)  # 1.0
        """
        # Validate input
        if not alias or not isinstance(alias, str):
            return None

        # Check cache first
        cache_key = f"{alias}:{industry}:{organization_id}"
        if cache_key in self._alias_cache:
            logger.debug(f"Alias cache hit for '{alias}'")
            return self._alias_cache[cache_key]

        # Normalize the alias for matching
        normalized_alias = self.skills_matcher.normalize_skill(alias)

        # Check against built-in common aliases
        alias_data = _COMMON_SKILL_ALIASES.get(normalized_alias)

        if alias_data:
            # Apply industry filter if specified
            if industry and alias_data.get("industry") != industry:
                logger.debug(
                    f"Alias '{alias}' found but filtered by industry "
                    f"(expected: {industry}, got: {alias_data.get('industry')})"
                )
                return None

            # Create the resolution result
            resolution = AliasResolution(
                alias=alias,
                resolved_skill=alias_data["resolved"],
                industry=alias_data.get("industry"),
                context=alias_data.get("context"),
                confidence=1.0,  # High confidence for exact alias matches
            )

            # Cache the result
            self._alias_cache[cache_key] = resolution

            logger.debug(
                f"Resolved alias '{alias}' to '{resolution.resolved_skill}' "
                f"(industry: {resolution.industry}, context: {resolution.context})"
            )

            return resolution

        # Try to find a fuzzy match in the aliases
        try:
            from rapidfuzz import process, fuzz

            alias_names = list(_COMMON_SKILL_ALIASES.keys())
            result = process.extractOne(
                normalized_alias,
                alias_names,
                scorer=fuzz.WRatio,
            )

            if result and result[1] >= self.fuzzy_threshold:
                matched_alias = result[0]
                alias_data = _COMMON_SKILL_ALIASES[matched_alias]

                # Apply industry filter if specified
                if industry and alias_data.get("industry") != industry:
                    logger.debug(
                        f"Fuzzy alias match for '{alias}' found but filtered by industry"
                    )
                    return None

                # Create the resolution result with reduced confidence for fuzzy matches
                confidence = result[1] / 100.0
                resolution = AliasResolution(
                    alias=alias,
                    resolved_skill=alias_data["resolved"],
                    industry=alias_data.get("industry"),
                    context=alias_data.get("context"),
                    confidence=confidence,
                )

                # Cache the result
                self._alias_cache[cache_key] = resolution

                logger.debug(
                    f"Fuzzy resolved alias '{alias}' to '{resolution.resolved_skill}' "
                    f"(confidence: {confidence:.2f})"
                )

                return resolution

        except ImportError:
            logger.warning("rapidfuzz not installed, skipping fuzzy alias matching")
        except Exception as e:
            logger.error(f"Error during fuzzy alias matching: {e}")

        # No match found
        logger.debug(f"No alias resolution found for '{alias}'")
        return None

    async def resolve_alias_async(
        self,
        alias: str,
        *,
        industry: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Optional[AliasResolution]:
        """
        Resolve a skill alias to its canonical form asynchronously.

        This method queries the database for alias/variant resolution using
        the skill taxonomy. If no database is available, it falls back to
        the built-in alias mappings.

        The resolution process:
        1. Check the alias cache for previously resolved aliases
        2. Query the database for taxonomy entries with matching variants
        3. Fall back to built-in alias mappings if no database match
        4. Cache and return the result

        Args:
            alias: The alias or variant to resolve
            industry: Optional industry filter
            organization_id: Optional organization filter

        Returns:
            AliasResolution if found, None otherwise

        Example:
            >>> resolution = await service.resolve_alias_async("JS")
            >>> print(resolution.resolved_skill)  # 'JavaScript'
        """
        # Validate input
        if not alias or not isinstance(alias, str):
            return None

        # Check cache first
        cache_key = f"{alias}:{industry}:{organization_id}"
        if cache_key in self._alias_cache:
            logger.debug(f"Alias cache hit for '{alias}'")
            return self._alias_cache[cache_key]

        # Try database lookup if available
        if self.db:
            try:
                normalized_alias = self.skills_matcher.normalize_skill(alias)

                # Query taxonomy entries that have variants matching the alias
                query = select(SkillTaxonomy).where(
                    and_(
                        SkillTaxonomy.is_active == True,
                        SkillTaxonomy.is_latest == True,
                        SkillTaxonomy.variants.isnot(None),
                    )
                )

                # Apply organization filter if provided
                if organization_id:
                    query = query.where(SkillTaxonomy.organization_id == organization_id)

                # Apply industry filter if provided
                if industry:
                    query = query.where(SkillTaxonomy.industry == industry)

                result = await self.db.execute(query)
                taxonomies = result.scalars().all()

                # Search for matching variant
                for taxonomy in taxonomies:
                    if not taxonomy.variants:
                        continue

                    for variant in taxonomy.variants:
                        normalized_variant = self.skills_matcher.normalize_skill(variant)

                        # Check for exact match (normalized)
                        if normalized_variant == normalized_alias:
                            resolution = AliasResolution(
                                alias=alias,
                                resolved_skill=taxonomy.skill_name,
                                taxonomy_id=taxonomy.id,
                                industry=taxonomy.industry,
                                context=taxonomy.context,
                                confidence=1.0,
                            )

                            # Cache the result
                            self._alias_cache[cache_key] = resolution

                            logger.debug(
                                f"Database resolved alias '{alias}' to '{resolution.resolved_skill}'"
                            )

                            return resolution

                        # Check for case-insensitive match
                        if variant.lower() == alias.lower():
                            resolution = AliasResolution(
                                alias=alias,
                                resolved_skill=taxonomy.skill_name,
                                taxonomy_id=taxonomy.id,
                                industry=taxonomy.industry,
                                context=taxonomy.context,
                                confidence=0.95,
                            )

                            # Cache the result
                            self._alias_cache[cache_key] = resolution

                            logger.debug(
                                f"Database resolved alias '{alias}' to '{resolution.resolved_skill}' "
                                f"(case-insensitive match)"
                            )

                            return resolution

                logger.debug(f"No database match found for alias '{alias}'")

            except Exception as e:
                logger.error(f"Error during database alias resolution: {e}")

        # Fall back to sync method (built-in aliases)
        return self.resolve_alias(alias, industry=industry, organization_id=organization_id)

    def find_related_skills(
        self,
        skill_name: str,
        *,
        relationship_types: Optional[List[str]] = None,
        min_weight: float = 0.0,
        organization_id: Optional[str] = None,
    ) -> List[RelatedSkill]:
        """
        Find skills related to the given skill.

        This is a synchronous method that uses cached data and built-in
        relationship mappings for fast lookups. For database-backed resolution
        with custom taxonomy data, use find_related_skills_async instead.

        The lookup process:
        1. Normalize the skill name
        2. Check against built-in common skill relationships
        3. Filter by relationship types and minimum weight
        4. Return matching RelatedSkill objects

        Args:
            skill_name: The skill to find relations for
            relationship_types: Types of relationships to include (default: all)
                Valid types: 'parent_child', 'similar', 'prerequisite', 'related'
            min_weight: Minimum relationship weight (default: 0.0, range: 0.0-1.0)
            organization_id: Optional organization filter (for caching purposes)

        Returns:
            List of RelatedSkill objects, sorted by weight (descending)

        Example:
            >>> related = service.find_related_skills("React")
            >>> print([r.skill_name for r in related])  # ['Vue', 'Angular', 'Next.js', ...]
            >>> print([r.relationship_type for r in related])  # ['similar', 'similar', ...]
        """
        # Validate input
        if not skill_name or not isinstance(skill_name, str):
            return []

        # Validate min_weight
        if not 0.0 <= min_weight <= 1.0:
            logger.warning(f"min_weight {min_weight} out of range, clamping to [0.0, 1.0]")
            min_weight = max(0.0, min(1.0, min_weight))

        # Normalize the skill name for matching
        normalized_skill = self.skills_matcher.normalize_skill(skill_name)

        # Check built-in relationships
        # First try exact match, then try normalized lookup
        relationships_data = _COMMON_SKILL_RELATIONSHIPS.get(skill_name)

        if not relationships_data:
            # Try normalized lookup in the keys
            for key in _COMMON_SKILL_RELATIONSHIPS.keys():
                if self.skills_matcher.normalize_skill(key) == normalized_skill:
                    relationships_data = _COMMON_SKILL_RELATIONSHIPS[key]
                    break

        if not relationships_data:
            logger.debug(f"No relationships found for skill '{skill_name}'")
            return []

        # Convert to RelatedSkill objects and apply filters
        related_skills: List[RelatedSkill] = []

        for rel_data in relationships_data:
            # Extract relationship info
            related_name = rel_data.get("related")
            rel_type = rel_data.get("type", "related")
            weight = rel_data.get("weight", 1.0)

            if not related_name:
                continue

            # Apply relationship type filter
            if relationship_types and rel_type not in relationship_types:
                continue

            # Apply weight filter
            if weight < min_weight:
                continue

            # Create RelatedSkill object
            related_skill = RelatedSkill(
                skill_name=related_name,
                relationship_type=rel_type,
                weight=weight,
            )
            related_skills.append(related_skill)

        # Sort by weight (descending) for consistent ordering
        related_skills.sort(key=lambda x: x.weight, reverse=True)

        logger.debug(
            f"Found {len(related_skills)} related skills for '{skill_name}' "
            f"(types: {relationship_types}, min_weight: {min_weight})"
        )

        return related_skills

    async def find_related_skills_async(
        self,
        skill_name: str,
        *,
        relationship_types: Optional[List[str]] = None,
        min_weight: float = 0.0,
        organization_id: Optional[str] = None,
    ) -> List[RelatedSkill]:
        """
        Find skills related to the given skill asynchronously.

        This method queries the database for skill relationships using
        the SkillRelationship model. If no database is available or no
        relationships are found, it falls back to built-in mappings.

        The lookup process:
        1. Query database for relationships involving this skill
        2. Filter by relationship types and minimum weight
        3. Fall back to built-in mappings if no database or no results
        4. Return matching RelatedSkill objects

        Args:
            skill_name: The skill to find relations for
            relationship_types: Types of relationships to include (default: all)
                Valid types: 'parent_child', 'similar', 'prerequisite', 'related'
            min_weight: Minimum relationship weight (default: 0.0, range: 0.0-1.0)
            organization_id: Optional organization filter

        Returns:
            List of RelatedSkill objects, sorted by weight (descending)

        Example:
            >>> related = await service.find_related_skills_async("React")
            >>> print([r.skill_name for r in related])  # ['Vue', 'Angular', 'Next.js', ...]
        """
        # Validate input
        if not skill_name or not isinstance(skill_name, str):
            return []

        # Validate min_weight
        if not 0.0 <= min_weight <= 1.0:
            logger.warning(f"min_weight {min_weight} out of range, clamping to [0.0, 1.0]")
            min_weight = max(0.0, min(1.0, min_weight))

        # Try database lookup if available
        if self.db:
            try:
                related_skills = await self._query_related_skills_from_db(
                    skill_name,
                    relationship_types=relationship_types,
                    min_weight=min_weight,
                    organization_id=organization_id,
                )

                if related_skills:
                    logger.debug(
                        f"Found {len(related_skills)} related skills from database for '{skill_name}'"
                    )
                    return related_skills

            except Exception as e:
                logger.error(f"Error querying related skills from database: {e}")
                # Fall through to fallback

        # Fall back to sync method (built-in mappings)
        logger.debug(f"Falling back to built-in relationships for '{skill_name}'")
        return self.find_related_skills(
            skill_name,
            relationship_types=relationship_types,
            min_weight=min_weight,
            organization_id=organization_id,
        )

    # Private helper methods

    async def _find_exact_match(
        self,
        normalized_skill: str,
        organization_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Find an exact match in the taxonomy."""
        if not self.db:
            return None

        try:
            query = select(SkillTaxonomy).where(
                and_(
                    SkillTaxonomy.is_active == True,
                    SkillTaxonomy.is_latest == True,
                )
            )

            # Add organization filter if provided
            if organization_id:
                query = query.where(SkillTaxonomy.organization_id == organization_id)

            result = await self.db.execute(query)
            taxonomies = result.scalars().all()

            # Check for exact match (normalized)
            for taxonomy in taxonomies:
                normalized_name = self.skills_matcher.normalize_skill(taxonomy.skill_name)
                if normalized_name == normalized_skill:
                    return self._taxonomy_to_dict(taxonomy)

            return None

        except Exception as e:
            logger.error(f"Error finding exact match: {e}")
            return None

    async def _find_alias_match(
        self,
        original_skill: str,
        normalized_skill: str,
        organization_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Find a match using aliases and variants."""
        if not self.db:
            return None

        try:
            query = select(SkillTaxonomy).where(
                and_(
                    SkillTaxonomy.is_active == True,
                    SkillTaxonomy.is_latest == True,
                    SkillTaxonomy.variants.isnot(None),
                )
            )

            if organization_id:
                query = query.where(SkillTaxonomy.organization_id == organization_id)

            result = await self.db.execute(query)
            taxonomies = result.scalars().all()

            # Check variants for matches
            for taxonomy in taxonomies:
                if not taxonomy.variants:
                    continue

                for variant in taxonomy.variants:
                    normalized_variant = self.skills_matcher.normalize_skill(variant)
                    if normalized_variant == normalized_skill:
                        return self._taxonomy_to_dict(taxonomy)

                    # Also check case-insensitive exact match
                    if variant.lower() == original_skill.lower():
                        return self._taxonomy_to_dict(taxonomy)

            return None

        except Exception as e:
            logger.error(f"Error finding alias match: {e}")
            return None

    async def _get_taxonomy_skills(
        self,
        organization_id: Optional[str],
    ) -> List[str]:
        """Get list of all canonical skill names from taxonomy."""
        if not self.db:
            return []

        try:
            query = select(SkillTaxonomy.skill_name).where(
                and_(
                    SkillTaxonomy.is_active == True,
                    SkillTaxonomy.is_latest == True,
                )
            )

            if organization_id:
                query = query.where(SkillTaxonomy.organization_id == organization_id)

            result = await self.db.execute(query)
            return [row[0] for row in result.all()]

        except Exception as e:
            logger.error(f"Error getting taxonomy skills: {e}")
            return []

    async def _get_taxonomy_entry_by_name(
        self,
        skill_name: str,
        organization_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Get full taxonomy entry by skill name."""
        if not self.db:
            return None

        try:
            query = select(SkillTaxonomy).where(
                and_(
                    SkillTaxonomy.skill_name == skill_name,
                    SkillTaxonomy.is_active == True,
                    SkillTaxonomy.is_latest == True,
                )
            )

            if organization_id:
                query = query.where(SkillTaxonomy.organization_id == organization_id)

            result = await self.db.execute(query)
            taxonomy = result.scalar_one_or_none()

            if taxonomy:
                return self._taxonomy_to_dict(taxonomy)
            return None

        except Exception as e:
            logger.error(f"Error getting taxonomy entry: {e}")
            return None

    async def _get_related_skill_names(
        self,
        taxonomy_id: UUID,
        organization_id: Optional[str],
    ) -> List[str]:
        """Get names of skills related to the given taxonomy entry."""
        if not self.db or not self.include_relationships:
            return []

        try:
            # Find relationships where this skill is either source or target
            query = select(SkillRelationship, SkillTaxonomy).join(
                SkillTaxonomy,
                or_(
                    and_(
                        SkillRelationship.target_skill_id == taxonomy_id,
                        SkillTaxonomy.id == SkillRelationship.source_skill_id,
                    ),
                    and_(
                        SkillRelationship.source_skill_id == taxonomy_id,
                        SkillTaxonomy.id == SkillRelationship.target_skill_id,
                    ),
                ),
            ).where(
                and_(
                    SkillRelationship.is_active == True,
                    SkillTaxonomy.is_active == True,
                )
            )

            if organization_id:
                query = query.where(SkillRelationship.organization_id == organization_id)

            result = await self.db.execute(query)
            rows = result.all()

            related_names: List[str] = []
            for relationship, related_taxonomy in rows:
                if related_taxonomy.skill_name not in related_names:
                    related_names.append(related_taxonomy.skill_name)

            return related_names

        except Exception as e:
            logger.error(f"Error getting related skills: {e}")
            return []

    def _taxonomy_to_dict(self, taxonomy: SkillTaxonomy) -> Dict[str, Any]:
        """Convert a taxonomy model to dictionary."""
        return {
            "id": str(taxonomy.id),
            "industry": taxonomy.industry,
            "skill_name": taxonomy.skill_name,
            "context": taxonomy.context,
            "variants": taxonomy.variants or [],
            "extra_metadata": taxonomy.extra_metadata or {},
            "parent_skill_id": str(taxonomy.parent_skill_id) if taxonomy.parent_skill_id else None,
            "category_path": taxonomy.category_path or [],
            "is_active": taxonomy.is_active,
            "version": taxonomy.version,
            "organization_id": taxonomy.organization_id,
        }

    async def _query_related_skills_from_db(
        self,
        skill_name: str,
        *,
        relationship_types: Optional[List[str]] = None,
        min_weight: float = 0.0,
        organization_id: Optional[str] = None,
    ) -> List[RelatedSkill]:
        """
        Query the database for skills related to the given skill.

        This helper method queries the SkillRelationship table to find
        relationships where the given skill is either the source or target.

        Args:
            skill_name: The skill to find relations for
            relationship_types: Types of relationships to include (default: all)
            min_weight: Minimum relationship weight (default: 0.0)
            organization_id: Optional organization filter

        Returns:
            List of RelatedSkill objects, sorted by weight (descending)
        """
        if not self.db:
            return []

        try:
            # First, find the taxonomy entry for this skill
            normalized_skill = self.skills_matcher.normalize_skill(skill_name)

            taxonomy_query = select(SkillTaxonomy).where(
                and_(
                    SkillTaxonomy.is_active == True,
                    SkillTaxonomy.is_latest == True,
                )
            )

            if organization_id:
                taxonomy_query = taxonomy_query.where(
                    SkillTaxonomy.organization_id == organization_id
                )

            result = await self.db.execute(taxonomy_query)
            taxonomies = result.scalars().all()

            # Find matching taxonomy
            source_taxonomy = None
            for taxonomy in taxonomies:
                if self.skills_matcher.normalize_skill(taxonomy.skill_name) == normalized_skill:
                    source_taxonomy = taxonomy
                    break

            if not source_taxonomy:
                logger.debug(f"No taxonomy entry found for '{skill_name}'")
                return []

            source_id = source_taxonomy.id

            # Query relationships where this skill is source or target
            query = (
                select(SkillRelationship, SkillTaxonomy)
                .join(
                    SkillTaxonomy,
                    or_(
                        and_(
                            SkillRelationship.source_skill_id == source_id,
                            SkillTaxonomy.id == SkillRelationship.target_skill_id,
                        ),
                        and_(
                            SkillRelationship.target_skill_id == source_id,
                            SkillTaxonomy.id == SkillRelationship.source_skill_id,
                        ),
                    ),
                )
                .where(
                    and_(
                        SkillRelationship.is_active == True,
                        SkillTaxonomy.is_active == True,
                    )
                )
            )

            # Apply organization filter
            if organization_id:
                query = query.where(
                    SkillRelationship.organization_id == organization_id
                )

            # Apply relationship type filter
            if relationship_types:
                query = query.where(
                    SkillRelationship.relationship_type.in_(relationship_types)
                )

            result = await self.db.execute(query)
            rows = result.all()

            # Build RelatedSkill objects
            related_skills: List[RelatedSkill] = []
            seen_skills: Set[str] = set()

            for relationship, related_taxonomy in rows:
                # Skip duplicates
                if related_taxonomy.skill_name in seen_skills:
                    continue
                seen_skills.add(related_taxonomy.skill_name)

                # Get weight (default to 1.0 if not set)
                weight = relationship.weight if relationship.weight is not None else 1.0

                # Apply weight filter
                if weight < min_weight:
                    continue

                # Determine relationship type from the relationship
                rel_type = relationship.relationship_type or "related"

                related_skill = RelatedSkill(
                    skill_name=related_taxonomy.skill_name,
                    relationship_type=rel_type,
                    weight=weight,
                    taxonomy_id=related_taxonomy.id,
                )
                related_skills.append(related_skill)

            # Sort by weight (descending)
            related_skills.sort(key=lambda x: x.weight, reverse=True)

            return related_skills

        except Exception as e:
            logger.error(f"Error querying related skills from database: {e}")
            return []


# Factory function for dependency injection
def get_taxonomy_matcher_service(
    db: Optional[AsyncSession] = None,
    **kwargs,
) -> TaxonomyMatcherService:
    """
    Get a TaxonomyMatcherService instance.

    This function is designed for use with FastAPI dependency injection.

    Args:
        db: Database session
        **kwargs: Additional arguments to pass to TaxonomyMatcherService

    Returns:
        TaxonomyMatcherService instance

    Example:
        >>> from fastapi import Depends
        >>> from database import get_db
        >>> from services.taxonomy_matcher_service import get_taxonomy_matcher_service
        >>>
        >>> @router.post("/match-skills")
        >>> async def match_skills(
        >>>     skills: List[str],
        >>>     db: AsyncSession = Depends(get_db),
        >>>     matcher: TaxonomyMatcherService = Depends(get_taxonomy_matcher_service)
        >>> ):
        >>>     result = await matcher.match_skills(skills)
        >>>     return result
    """
    return TaxonomyMatcherService(db=db, **kwargs)
