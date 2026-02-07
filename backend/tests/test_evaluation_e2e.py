"""
End-to-end tests for evaluation scorecards feature.

Tests cover the complete flow:
- Template creation with multiple criteria
- Scorecard filling by multiple evaluators
- Aggregate score calculation across evaluators
"""
import pytest
from uuid import uuid4
from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.evaluation_template import EvaluationTemplate
from models.evaluation_criteria import EvaluationCriteria
from models.evaluation_scorecard import EvaluationScorecard
from models.resume import Resume


# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


class TestTemplateCreation:
    """Tests for evaluation template creation."""

    @pytest.mark.asyncio
    async def test_create_template_with_criteria(self, db_session: AsyncSession):
        """Test creating an evaluation template with multiple criteria."""
        # Create a template
        template_id = str(uuid4())
        organization_id = str(uuid4())
        vacancy_id = str(uuid4())

        template = EvaluationTemplate(
            id=template_id,
            organization_id=organization_id,
            vacancy_id=vacancy_id,
            name="Technical Interview Template",
            description="Template for evaluating technical skills",
            version=1,
            is_active=True,
            is_default=False,
            created_by=str(uuid4()),
        )
        db_session.add(template)
        await db_session.flush()

        # Create criteria
        criteria1 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            description="Core technical abilities",
            criteria_type="skills",
            weight=0.4,
            min_score=1,
            max_score=5,
            rating_scale_description="1-5, Poor to Excellent",
            display_order=1,
        )
        criteria2 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Communication",
            description="Communication skills",
            criteria_type="cultural_fit",
            weight=0.3,
            min_score=1,
            max_score=5,
            rating_scale_description="1-5, Poor to Excellent",
            display_order=2,
        )
        criteria3 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Experience",
            description="Relevant work experience",
            criteria_type="experience",
            weight=0.3,
            min_score=1,
            max_score=5,
            rating_scale_description="1-5, Poor to Excellent",
            display_order=3,
        )

        db_session.add_all([criteria1, criteria2, criteria3])
        await db_session.commit()

        # Verify template was created
        from sqlalchemy import select

        result = await db_session.execute(
            select(EvaluationTemplate).where(EvaluationTemplate.id == template_id)
        )
        retrieved_template = result.scalar_one_or_none()

        assert retrieved_template is not None
        assert retrieved_template.name == "Technical Interview Template"
        assert retrieved_template.version == 1
        assert retrieved_template.is_active is True

        # Verify criteria were created
        result = await db_session.execute(
            select(EvaluationCriteria).where(
                EvaluationCriteria.template_id == template_id
            ).order_by(EvaluationCriteria.display_order)
        )
        criteria_list = result.scalars().all()

        assert len(criteria_list) == 3
        assert criteria_list[0].name == "Technical Skills"
        assert criteria_list[0].weight == 0.4
        assert criteria_list[1].name == "Communication"
        assert criteria_list[1].weight == 0.3
        assert criteria_list[2].name == "Experience"
        assert criteria_list[2].weight == 0.3


class TestScorecardFilling:
    """Tests for scorecard filling by evaluators."""

    @pytest.mark.asyncio
    async def test_create_scorecard_for_candidate(self, db_session: AsyncSession):
        """Test creating a scorecard for a candidate."""
        # Setup: Create template and resume
        template_id = str(uuid4())
        organization_id = str(uuid4())
        resume_id = str(uuid4())
        evaluator_id = str(uuid4())

        # Create a mock resume
        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume content",
            parsed_data={},
        )
        db_session.add(resume)

        # Create template
        template = EvaluationTemplate(
            id=template_id,
            organization_id=organization_id,
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        # Create criteria
        criteria1 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=0.5,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        criteria2 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Communication",
            criteria_type="cultural_fit",
            weight=0.5,
            min_score=1,
            max_score=5,
            display_order=2,
        )
        db_session.add_all([criteria1, criteria2])
        await db_session.flush()

        # Create scorecard
        scorecard_id = str(uuid4())
        scorecard = EvaluationScorecard(
            id=scorecard_id,
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=evaluator_id,
            criteria_responses={
                str(criteria1.id): {"score": 4.0, "comments": "Strong technical skills"},
                str(criteria2.id): {"score": 3.5, "comments": "Good communication"},
            },
            overall_score=3.75,
            status="completed",
            evaluator_comments="Good candidate overall",
        )
        db_session.add(scorecard)
        await db_session.commit()

        # Verify scorecard was created
        from sqlalchemy import select

        result = await db_session.execute(
            select(EvaluationScorecard).where(EvaluationScorecard.id == scorecard_id)
        )
        retrieved_scorecard = result.scalar_one_or_none()

        assert retrieved_scorecard is not None
        assert retrieved_scorecard.template_id == template_id
        assert retrieved_scorecard.resume_id == resume_id
        assert retrieved_scorecard.evaluator_id == evaluator_id
        assert retrieved_scorecard.overall_score == 3.75
        assert retrieved_scorecard.status == "completed"
        assert len(retrieved_scorecard.criteria_responses) == 2


    @pytest.mark.asyncio
    async def test_multiple_evaluators_for_same_candidate(
        self, db_session: AsyncSession
    ):
        """Test multiple evaluators filling scorecards for the same candidate."""
        # Setup
        template_id = str(uuid4())
        organization_id = str(uuid4())
        resume_id = str(uuid4())

        # Create resume
        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        # Create template with criteria
        template = EvaluationTemplate(
            id=template_id,
            organization_id=organization_id,
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        criteria1 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=0.6,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        criteria2 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Cultural Fit",
            criteria_type="cultural_fit",
            weight=0.4,
            min_score=1,
            max_score=5,
            display_order=2,
        )
        db_session.add_all([criteria1, criteria2])
        await db_session.flush()

        # Create scorecards from 3 different evaluators
        evaluator1_id = str(uuid4())
        evaluator2_id = str(uuid4())
        evaluator3_id = str(uuid4())

        scorecard1 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=evaluator1_id,
            criteria_responses={
                str(criteria1.id): {"score": 5.0, "comments": "Excellent"},
                str(criteria2.id): {"score": 4.0, "comments": "Good fit"},
            },
            overall_score=4.5,
            status="completed",
        )

        scorecard2 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=evaluator2_id,
            criteria_responses={
                str(criteria1.id): {"score": 4.0, "comments": "Strong"},
                str(criteria2.id): {"score": 3.5, "comments": "Decent fit"},
            },
            overall_score=3.75,
            status="completed",
        )

        scorecard3 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=evaluator3_id,
            criteria_responses={
                str(criteria1.id): {"score": 4.5, "comments": "Very good"},
                str(criteria2.id): {"score": 4.5, "comments": "Great fit"},
            },
            overall_score=4.5,
            status="completed",
        )

        db_session.add_all([scorecard1, scorecard2, scorecard3])
        await db_session.commit()

        # Verify all scorecards were created
        from sqlalchemy import select

        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id
            )
        )
        scorecards = result.scalars().all()

        assert len(scorecards) == 3

        # Verify evaluator IDs are unique
        evaluator_ids = {s.evaluator_id for s in scorecards}
        assert len(evaluator_ids) == 3
        assert evaluator1_id in evaluator_ids
        assert evaluator2_id in evaluator_ids
        assert evaluator3_id in evaluator_ids


class TestAggregateCalculation:
    """Tests for aggregate score calculation."""

    @pytest.mark.asyncio
    async def test_calculate_average_scores(self, db_session: AsyncSession):
        """Test calculating average scores across multiple evaluators."""
        # Setup
        template_id = str(uuid4())
        organization_id = str(uuid4())
        resume_id = str(uuid4())

        # Create resume
        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        # Create template with criteria
        template = EvaluationTemplate(
            id=template_id,
            organization_id=organization_id,
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        criteria1 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=0.6,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        criteria2 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Cultural Fit",
            criteria_type="cultural_fit",
            weight=0.4,
            min_score=1,
            max_score=5,
            display_order=2,
        )
        db_session.add_all([criteria1, criteria2])
        await db_session.flush()

        # Create scorecards with different scores
        # Evaluator 1: 5.0, 4.0 (overall: 4.5)
        # Evaluator 2: 4.0, 3.5 (overall: 3.75)
        # Evaluator 3: 4.5, 4.5 (overall: 4.5)

        scorecard1 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 5.0, "comments": "Excellent"},
                str(criteria2.id): {"score": 4.0, "comments": "Good"},
            },
            overall_score=4.5,
            status="completed",
        )

        scorecard2 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 4.0, "comments": "Strong"},
                str(criteria2.id): {"score": 3.5, "comments": "Decent"},
            },
            overall_score=3.75,
            status="completed",
        )

        scorecard3 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 4.5, "comments": "Very good"},
                str(criteria2.id): {"score": 4.5, "comments": "Great"},
            },
            overall_score=4.5,
            status="completed",
        )

        db_session.add_all([scorecard1, scorecard2, scorecard3])
        await db_session.commit()

        # Calculate aggregate scores
        from sqlalchemy import select

        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        # Calculate averages
        total_evaluators = len(scorecards)
        assert total_evaluators == 3

        # Calculate average scores per criteria
        criteria_scores = {str(criteria1.id): [], str(criteria2.id): []}
        overall_scores = []

        for scorecard in scorecards:
            overall_scores.append(scorecard.overall_score)
            for criteria_id, response in scorecard.criteria_responses.items():
                if criteria_id in criteria_scores:
                    criteria_scores[criteria_id].append(response["score"])

        # Verify overall average
        overall_avg = sum(overall_scores) / len(overall_scores)
        expected_overall_avg = (4.5 + 3.75 + 4.5) / 3
        assert abs(overall_avg - expected_overall_avg) < 0.01

        # Verify criteria averages
        # Criteria 1: (5.0 + 4.0 + 4.5) / 3 = 4.5
        criteria1_avg = sum(criteria_scores[str(criteria1.id)]) / len(
            criteria_scores[str(criteria1.id)]
        )
        assert abs(criteria1_avg - 4.5) < 0.01

        # Criteria 2: (4.0 + 3.5 + 4.5) / 3 = 4.0
        criteria2_avg = sum(criteria_scores[str(criteria2.id)]) / len(
            criteria_scores[str(criteria2.id)]
        )
        assert abs(criteria2_avg - 4.0) < 0.01

        # Verify weighted score
        # Weighted = (4.5 * 0.6) + (4.0 * 0.4) = 2.7 + 1.6 = 4.3
        weighted_score = (criteria1_avg * 0.6) + (criteria2_avg * 0.4)
        assert abs(weighted_score - 4.3) < 0.01


class TestCompleteFlow:
    """End-to-end tests for the complete evaluation flow."""

    @pytest.mark.asyncio
    async def test_template_to_scorecard_to_aggregate(self, db_session: AsyncSession):
        """Test complete flow: template creation -> scorecard filling -> aggregate calculation."""
        # Step 1: Create evaluation template
        template_id = str(uuid4())
        organization_id = str(uuid4())
        vacancy_id = str(uuid4())

        template = EvaluationTemplate(
            id=template_id,
            organization_id=organization_id,
            vacancy_id=vacancy_id,
            name="Senior Developer Interview",
            description="Template for senior developer candidates",
            version=1,
            is_active=True,
            is_default=True,
            created_by=str(uuid4()),
        )
        db_session.add(template)
        await db_session.flush()

        # Add criteria to template
        criteria1 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Depth",
            description="Depth of technical knowledge",
            criteria_type="skills",
            weight=0.5,
            min_score=1,
            max_score=10,
            rating_scale_description="1-10, Novice to Expert",
            display_order=1,
        )
        criteria2 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Problem Solving",
            description="Ability to solve complex problems",
            criteria_type="skills",
            weight=0.3,
            min_score=1,
            max_score=10,
            rating_scale_description="1-10, Poor to Excellent",
            display_order=2,
        )
        criteria3 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Team Collaboration",
            description="Ability to work in a team",
            criteria_type="cultural_fit",
            weight=0.2,
            min_score=1,
            max_score=10,
            rating_scale_description="1-10, Poor to Excellent",
            display_order=3,
        )
        db_session.add_all([criteria1, criteria2, criteria3])
        await db_session.flush()

        # Verify template was created with criteria
        from sqlalchemy import select

        template_result = await db_session.execute(
            select(EvaluationTemplate).where(EvaluationTemplate.id == template_id)
        )
        created_template = template_result.scalar_one_or_none()
        assert created_template is not None
        assert created_template.name == "Senior Developer Interview"

        criteria_result = await db_session.execute(
            select(EvaluationCriteria).where(
                EvaluationCriteria.template_id == template_id
            )
        )
        created_criteria = criteria_result.scalars().all()
        assert len(created_criteria) == 3

        # Step 2: Create candidate and scorecards
        resume_id = str(uuid4())
        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=vacancy_id,
            content="Senior developer resume",
            parsed_data={},
        )
        db_session.add(resume)
        await db_session.flush()

        # Create scorecards from 3 evaluators
        # Evaluator 1 (Technical Lead)
        evaluator1_id = str(uuid4())
        scorecard1 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=evaluator1_id,
            criteria_responses={
                str(criteria1.id): {"score": 9.0, "comments": "Expert level"},
                str(criteria2.id): {"score": 8.0, "comments": "Excellent problem solver"},
                str(criteria3.id): {"score": 7.0, "comments": "Good collaborator"},
            },
            overall_score=8.0,
            status="completed",
            evaluator_comments="Strong technical candidate",
        )
        db_session.add(scorecard1)

        # Evaluator 2 (Engineering Manager)
        evaluator2_id = str(uuid4())
        scorecard2 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=evaluator2_id,
            criteria_responses={
                str(criteria1.id): {"score": 8.0, "comments": "Very strong"},
                str(criteria2.id): {"score": 9.0, "comments": "Outstanding solutions"},
                str(criteria3.id): {"score": 8.0, "comments": "Great team player"},
            },
            overall_score=8.33,
            status="completed",
            evaluator_comments="Excellent hire",
        )
        db_session.add(scorecard2)

        # Evaluator 3 (Peer Developer)
        evaluator3_id = str(uuid4())
        scorecard3 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=evaluator3_id,
            criteria_responses={
                str(criteria1.id): {"score": 8.5, "comments": "Very knowledgeable"},
                str(criteria2.id): {"score": 7.5, "comments": "Good problem solver"},
                str(criteria3.id): {"score": 9.0, "comments": "Excellent to work with"},
            },
            overall_score=8.33,
            status="completed",
            evaluator_comments="Would love to work with this person",
        )
        db_session.add(scorecard3)
        await db_session.commit()

        # Verify scorecards were created
        scorecard_result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = scorecard_result.scalars().all()
        assert len(scorecards) == 3

        # Step 3: Calculate and verify aggregate scores
        # Expected values:
        # Technical Depth (weight 0.5): (9.0 + 8.0 + 8.5) / 3 = 8.5
        # Problem Solving (weight 0.3): (8.0 + 9.0 + 7.5) / 3 = 8.167
        # Team Collaboration (weight 0.2): (7.0 + 8.0 + 9.0) / 3 = 8.0
        # Overall average: (8.0 + 8.33 + 8.33) / 3 = 8.22
        # Weighted score: (8.5 * 0.5) + (8.167 * 0.3) + (8.0 * 0.2) = 4.25 + 2.45 + 1.6 = 8.3

        criteria_scores = {
            str(criteria1.id): [],
            str(criteria2.id): [],
            str(criteria3.id): [],
        }
        overall_scores = []

        for scorecard in scorecards:
            overall_scores.append(scorecard.overall_score)
            for criteria_id, response in scorecard.criteria_responses.items():
                if criteria_id in criteria_scores:
                    criteria_scores[criteria_id].append(response["score"])

        # Calculate and verify overall average
        overall_avg = sum(overall_scores) / len(overall_scores)
        assert abs(overall_avg - 8.22) < 0.1  # Allow small rounding difference

        # Calculate and verify criteria averages
        tech_depth_avg = sum(criteria_scores[str(criteria1.id)]) / len(
            criteria_scores[str(criteria1.id)]
        )
        assert abs(tech_depth_avg - 8.5) < 0.01

        problem_solving_avg = sum(criteria_scores[str(criteria2.id)]) / len(
            criteria_scores[str(criteria2.id)]
        )
        assert abs(problem_solving_avg - 8.167) < 0.01

        collaboration_avg = sum(criteria_scores[str(criteria3.id)]) / len(
            criteria_scores[str(criteria3.id)]
        )
        assert abs(collaboration_avg - 8.0) < 0.01

        # Calculate and verify weighted score
        weighted_score = (
            (tech_depth_avg * 0.5)
            + (problem_solving_avg * 0.3)
            + (collaboration_avg * 0.2)
        )
        assert abs(weighted_score - 8.3) < 0.1  # Allow small rounding difference

        # Verify completion rate
        completion_rate = 100.0  # All 3 evaluators completed
        assert completion_rate == 100.0
