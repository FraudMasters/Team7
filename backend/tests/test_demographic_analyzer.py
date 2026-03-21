"""
Tests for demographic analyzer.

This module tests the demographic inference analyzer including:
- Gender inference from names and pronouns
- Age group estimation from graduation dates
- Ethnicity inference from name patterns
- Geographic region detection
- Education level and career stage inference
- Bias indicator detection
"""
import pytest
from datetime import datetime
from uuid import uuid4

from analyzers.demographic_analyzer import DemographicAnalyzer, get_demographic_analyzer
from models.resume import Resume
from models.resume_analysis import ResumeAnalysis
from models.demographic_inference import DemographicInference


class TestDemographicAnalyzer:
    """Tests for DemographicAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test analyzer initializes with correct defaults."""
        analyzer = DemographicAnalyzer()

        assert analyzer.inference_method == "nlp_heuristic_v1"
        assert analyzer.inference_version == "1.0.0"
        assert analyzer.MIN_CONFIDENCE_THRESHOLD == 0.6

    def test_get_demographic_analyzer(self):
        """Test singleton instance retrieval."""
        analyzer1 = get_demographic_analyzer()
        analyzer2 = get_demographic_analyzer()

        assert analyzer1 is analyzer2  # Same instance


class TestGenderInference:
    """Tests for gender inference."""

    def test_infer_gender_from_male_name(self):
        """Test gender inference from male name."""
        analyzer = DemographicAnalyzer()
        text = "experienced software engineer"
        name = "John Smith"

        gender, confidence, features = analyzer._infer_gender(text, name)

        assert gender == "male"
        assert confidence > 0.0
        assert features["name_used"] is True
        assert features["first_name_match"] == "male"

    def test_infer_gender_from_female_name(self):
        """Test gender inference from female name."""
        analyzer = DemographicAnalyzer()
        text = "senior developer with excellent skills"
        name = "Jennifer Davis"

        gender, confidence, features = analyzer._infer_gender(text, name)

        assert gender == "female"
        assert confidence > 0.0
        assert features["name_used"] is True
        assert features["first_name_match"] == "female"

    def test_infer_gender_from_pronouns(self):
        """Test gender inference from pronouns in text."""
        analyzer = DemographicAnalyzer()
        text = "she has extensive experience in python and she is proficient in django"
        name = None

        gender, confidence, features = analyzer._infer_gender(text, name)

        assert gender == "female"
        assert features["pronoun_count"] > 0

    def test_infer_gender_no_indicators(self):
        """Test gender inference with no indicators."""
        analyzer = DemographicAnalyzer()
        text = "experienced software engineer"
        name = None

        gender, confidence, features = analyzer._infer_gender(text, name)

        assert gender is None
        assert confidence == 0.0

    def test_infer_gender_non_binary_pronouns(self):
        """Test detection of non-binary gender indicators."""
        analyzer = DemographicAnalyzer()
        text = "they are an excellent developer and they have great skills"
        name = None

        gender, confidence, features = analyzer._infer_gender(text, name)

        # Should detect non-binary pronouns
        assert features["pronoun_count"] > 0


class TestAgeGroupInference:
    """Tests for age group inference."""

    def test_infer_age_from_graduation_year(self):
        """Test age inference from graduation year."""
        analyzer = DemographicAnalyzer()
        current_year = datetime.now().year
        grad_year = current_year - 10  # Graduated 10 years ago
        text = f"bachelor of science in computer science {grad_year}"

        age_group, confidence, features = analyzer._infer_age_group(text, None)

        assert age_group is not None
        assert len(features["graduation_years"]) > 0
        assert confidence > 0.0

    def test_infer_age_from_experience(self):
        """Test age inference from experience data."""
        analyzer = DemographicAnalyzer()
        text = "software engineer with python experience"

        # Create mock analysis with experience data
        analysis = ResumeAnalysis(
            resume_id=uuid4(),
            raw_data={"experience": {"total_months": 120}}  # 10 years
        )

        age_group, confidence, features = analyzer._infer_age_group(text, analysis)

        assert features["experience_years"] == 10.0

    def test_infer_age_no_data(self):
        """Test age inference with no data."""
        analyzer = DemographicAnalyzer()
        text = "software engineer"

        age_group, confidence, features = analyzer._infer_age_group(text, None)

        assert age_group is None or age_group == "35_44"  # Default fallback
        assert confidence < 1.0


class TestEthnicityInference:
    """Tests for ethnicity inference."""

    def test_infer_ethnicity_asian_surname(self):
        """Test ethnicity inference from Asian surname."""
        analyzer = DemographicAnalyzer()
        name = "Michael Zhang"
        text = ""

        ethnicity, confidence, features = analyzer._infer_ethnicity(name, text)

        assert ethnicity == "asian"
        assert confidence > 0.0
        assert features["surname"] == "zhang"
        assert "asian" in str(features["pattern_matches"])

    def test_infer_ethnicity_hispanic_surname(self):
        """Test ethnicity inference from Hispanic surname."""
        analyzer = DemographicAnalyzer()
        name = "Carlos Garcia"
        text = ""

        ethnicity, confidence, features = analyzer._infer_ethnicity(name, text)

        assert ethnicity == "hispanic"
        assert confidence > 0.0
        assert features["surname"] == "garcia"

    def test_infer_ethnicity_no_name(self):
        """Test ethnicity inference with no name."""
        analyzer = DemographicAnalyzer()
        name = None
        text = "software engineer"

        ethnicity, confidence, features = analyzer._infer_ethnicity(name, text)

        assert ethnicity is None
        assert confidence == 0.0

    def test_infer_ethnicity_single_name(self):
        """Test ethnicity inference with single name."""
        analyzer = DemographicAnalyzer()
        name = "John"
        text = ""

        ethnicity, confidence, features = analyzer._infer_ethnicity(name, text)

        assert ethnicity is None  # Need surname


class TestGeographicRegionInference:
    """Tests for geographic region inference."""

    def test_infer_region_usa_west(self):
        """Test region inference for USA West."""
        analyzer = DemographicAnalyzer()
        text = "located in san francisco california with experience"

        region, confidence, features = analyzer._infer_geographic_region(text)

        assert region == "usa_west"
        assert confidence > 0.0
        assert len(features["matched_locations"]) > 0

    def test_infer_region_usa_northeast(self):
        """Test region inference for USA Northeast."""
        analyzer = DemographicAnalyzer()
        text = "based in new york with extensive experience"

        region, confidence, features = analyzer._infer_geographic_region(text)

        assert region == "usa_northeast"
        assert confidence > 0.0

    def test_infer_region_international(self):
        """Test region inference for international locations."""
        analyzer = DemographicAnalyzer()
        text = "located in london united kingdom"

        region, confidence, features = analyzer._infer_geographic_region(text)

        assert region == "international"
        assert len(features["matched_countries"]) > 0

    def test_infer_region_no_location(self):
        """Test region inference with no location data."""
        analyzer = DemographicAnalyzer()
        text = "software engineer with skills"

        region, confidence, features = analyzer._infer_geographic_region(text)

        assert region is None
        assert confidence == 0.0


class TestEducationLevelInference:
    """Tests for education level inference."""

    def test_infer_education_doctoral(self):
        """Test doctoral degree detection."""
        analyzer = DemographicAnalyzer()
        text = "ph.d in computer science from stanford university"

        education, confidence, features = analyzer._infer_education_level(text)

        assert education == "doctoral"
        assert confidence > 0.0
        assert len(features["matched_keywords"]) > 0

    def test_infer_education_masters(self):
        """Test master's degree detection."""
        analyzer = DemographicAnalyzer()
        text = "master of science in software engineering"

        education, confidence, features = analyzer._infer_education_level(text)

        assert education == "masters"
        assert confidence > 0.0

    def test_infer_education_bachelors(self):
        """Test bachelor's degree detection."""
        analyzer = DemographicAnalyzer()
        text = "bachelor of science in computer science b.s degree"

        education, confidence, features = analyzer._infer_education_level(text)

        assert education == "bachelors"
        assert confidence > 0.0

    def test_infer_education_no_degree(self):
        """Test education inference with no degree mentions."""
        analyzer = DemographicAnalyzer()
        text = "software engineer with experience"

        education, confidence, features = analyzer._infer_education_level(text)

        assert education is None
        assert confidence == 0.0


class TestCareerStageInference:
    """Tests for career stage inference."""

    def test_infer_career_stage_executive(self):
        """Test executive career stage detection."""
        analyzer = DemographicAnalyzer()
        text = "cto and vp of engineering with chief experience"

        # Mock analysis with executive experience
        analysis = ResumeAnalysis(
            resume_id=uuid4(),
            raw_data={"experience": {"total_months": 180}}  # 15 years
        )

        stage, confidence, features = analyzer._infer_career_stage(text, analysis)

        assert stage == "executive"
        assert confidence > 0.0
        assert features["experience_years"] == 15.0

    def test_infer_career_stage_senior(self):
        """Test senior career stage detection."""
        analyzer = DemographicAnalyzer()
        text = "senior software engineer and lead developer"

        analysis = ResumeAnalysis(
            resume_id=uuid4(),
            raw_data={"experience": {"total_months": 120}}  # 10 years
        )

        stage, confidence, features = analyzer._infer_career_stage(text, analysis)

        assert stage == "senior"
        assert confidence > 0.0

    def test_infer_career_stage_entry(self):
        """Test entry-level career stage detection."""
        analyzer = DemographicAnalyzer()
        text = "junior developer seeking entry level position"

        analysis = ResumeAnalysis(
            resume_id=uuid4(),
            raw_data={"experience": {"total_months": 12}}  # 1 year
        )

        stage, confidence, features = analyzer._infer_career_stage(text, analysis)

        assert stage == "entry"

    def test_infer_career_stage_no_indicators(self):
        """Test career stage inference with no indicators."""
        analyzer = DemographicAnalyzer()
        text = "software engineer"

        stage, confidence, features = analyzer._infer_career_stage(text, None)

        assert stage is None
        assert confidence == 0.0


class TestBiasIndicators:
    """Tests for bias indicator detection."""

    def test_detect_demographic_mentions(self):
        """Test detection of demographic keyword mentions."""
        analyzer = DemographicAnalyzer()
        text = "male candidate age 25 with experience"

        indicators = analyzer._check_bias_indicators(text)

        assert len(indicators) > 0
        assert any("demographic_mention" in ind for ind in indicators)

    def test_detect_photo_mentions(self):
        """Test detection of photo-related bias indicators."""
        analyzer = DemographicAnalyzer()
        text = "resume with photo attached showing professional image"

        indicators = analyzer._check_bias_indicators(text)

        assert "photo_included" in indicators

    def test_detect_age_related_terms(self):
        """Test detection of age-related bias terms."""
        analyzer = DemographicAnalyzer()
        text = "young and energetic recent graduate"

        indicators = analyzer._check_bias_indicators(text)

        assert len(indicators) > 0
        assert any("age_related_term" in ind for ind in indicators)

    def test_detect_biased_language(self):
        """Test detection of biased language patterns."""
        analyzer = DemographicAnalyzer()
        text = "native english speaker fitting in with our culture"

        indicators = analyzer._check_bias_indicators(text)

        assert len(indicators) > 0
        assert any("biased_language" in ind for ind in indicators)

    def test_no_bias_indicators(self):
        """Test detection with clean text."""
        analyzer = DemographicAnalyzer()
        text = "experienced software engineer with python and django skills"

        indicators = analyzer._check_bias_indicators(text)

        assert len(indicators) == 0


class TestNameExtraction:
    """Tests for name extraction from resume."""

    def test_extract_name_from_analysis(self):
        """Test name extraction from resume analysis."""
        analyzer = DemographicAnalyzer()

        resume = Resume(
            id=uuid4(),
            filename="test.pdf",
            file_path="/test.pdf",
            raw_text="Some resume content"
        )

        analysis = ResumeAnalysis(
            resume_id=resume.id,
            raw_text="John Smith\nSoftware Engineer\nExperience..."
        )

        name = analyzer._extract_name(resume, analysis)

        assert name == "John Smith"

    def test_extract_name_from_resume_raw_text(self):
        """Test name extraction from resume raw text."""
        analyzer = DemographicAnalyzer()

        resume = Resume(
            id=uuid4(),
            filename="test.pdf",
            file_path="/test.pdf",
            raw_text="Jane Doe\nSenior Developer"
        )

        name = analyzer._extract_name(resume, None)

        assert name == "Jane Doe"

    def test_extract_name_filters_cv_keywords(self):
        """Test that CV/Resume keywords are filtered from name."""
        analyzer = DemographicAnalyzer()

        resume = Resume(
            id=uuid4(),
            filename="test.pdf",
            file_path="/test.pdf",
            raw_text="RESUME John Smith"
        )

        name = analyzer._extract_name(resume, None)

        assert "resume" not in name.lower()
        assert "john smith" in name.lower()


class TestAnalyzeResumeIntegration:
    """Integration tests for full resume analysis."""

    @pytest.mark.asyncio
    async def test_analyze_resume_complete_flow(self, test_db):
        """Test complete resume analysis flow."""
        analyzer = DemographicAnalyzer()

        # Create resume
        resume = Resume(
            id=uuid4(),
            filename="john_smith_resume.pdf",
            file_path="/test/john_smith_resume.pdf",
            raw_text="John Smith\nSoftware Engineer\nBachelor of Science 2015\nExperience in Python"
        )
        test_db.add(resume)

        # Create analysis
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            raw_text=resume.raw_text,
            skills=["Python", "Django"],
            raw_data={"experience": {"total_months": 72}},  # 6 years
        )
        test_db.add(analysis)
        await test_db.commit()
        await test_db.refresh(resume)

        # Analyze resume
        result = await analyzer.analyze_resume(test_db, resume.id)

        # Verify result structure
        assert "inference_id" in result
        assert "resume_id" in result
        assert result["resume_id"] == str(resume.id)
        assert "gender" in result
        assert "age_group" in result
        assert "ethnicity" in result
        assert "geographic_region" in result
        assert "education_level" in result
        assert "career_stage" in result
        assert "raw_features" in result
        assert "processing_time_seconds" in result

        # Verify database record created
        from sqlalchemy import select
        query = select(DemographicInference).where(
            DemographicInference.resume_id == resume.id
        )
        db_result = await test_db.execute(query)
        inference = db_result.scalar_one_or_none()

        assert inference is not None
        assert inference.inference_method == "nlp_heuristic_v1"
        assert inference.inference_version == "1.0.0"
        assert inference.processing_time_seconds > 0

    @pytest.mark.asyncio
    async def test_analyze_resume_updates_existing(self, test_db):
        """Test that analyzing resume updates existing inference."""
        analyzer = DemographicAnalyzer()

        # Create resume
        resume = Resume(
            id=uuid4(),
            filename="test.pdf",
            file_path="/test/test.pdf",
            raw_text="Jane Williams\nSenior Engineer"
        )
        test_db.add(resume)
        await test_db.commit()

        # Create existing inference
        existing = DemographicInference(
            resume_id=resume.id,
            inferred_gender="male",
            gender_confidence=0.5,
            inference_method="old_method",
        )
        test_db.add(existing)
        await test_db.commit()
        existing_id = existing.id

        # Analyze resume (should update)
        result = await analyzer.analyze_resume(test_db, resume.id)

        # Verify updated
        from sqlalchemy import select
        query = select(DemographicInference).where(
            DemographicInference.resume_id == resume.id
        )
        db_result = await test_db.execute(query)
        updated = db_result.scalar_one_or_none()

        assert updated.id == existing_id  # Same record
        assert updated.inference_method == "nlp_heuristic_v1"  # Updated

    @pytest.mark.asyncio
    async def test_analyze_resume_not_found(self, test_db):
        """Test analyzing non-existent resume raises error."""
        analyzer = DemographicAnalyzer()
        fake_id = uuid4()

        with pytest.raises(ValueError, match="Resume not found"):
            await analyzer.analyze_resume(test_db, fake_id)

    @pytest.mark.asyncio
    async def test_analyze_resume_low_confidence(self, test_db):
        """Test that low confidence sets requires_review flag."""
        analyzer = DemographicAnalyzer()

        # Create resume with minimal information (low confidence)
        resume = Resume(
            id=uuid4(),
            filename="minimal.pdf",
            file_path="/test/minimal.pdf",
            raw_text="Software engineer with skills"  # No name, dates, etc.
        )
        test_db.add(resume)
        await test_db.commit()

        # Analyze resume
        result = await analyzer.analyze_resume(test_db, resume.id)

        # Should flag for review due to low confidence
        assert result["requires_review"] is True
        assert result["confidence_threshold_met"] is False
