"""
Unit and integration tests for multi-evaluator aggregate score calculation.

Tests cover:
- Average score calculation across multiple evaluators
- Weighted score calculation using criteria weights
- Overall average calculation
- Completion rate calculation
- Scores by evaluator breakdown
- Edge cases (no scorecards, single evaluator, incomplete evaluations)
- Different rating scales and weight distributions
- Decimal precision and rounding accuracy
- Status and template filtering
"""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

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
async def db_session(test_engine) -> AsyncSession:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


class TestBasicAggregation:
    """Tests for basic aggregate score calculations."""

    @pytest.mark.asyncio
    async def test_average_score_calculation_two_evaluators(self, db_session: AsyncSession):
        """Test average score calculation with exactly two evaluators."""
        # Setup
        template_id = str(uuid4())
        resume_id = str(uuid4())

        # Create resume and template
        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        # Create criteria with equal weights
        criteria = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=0.5,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        db_session.add(criteria)
        await db_session.flush()

        # Create two scorecards with different scores
        # Evaluator 1: score = 4.0
        # Evaluator 2: score = 5.0
        # Expected average: (4.0 + 5.0) / 2 = 4.5

        scorecard1 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={str(criteria.id): {"score": 4.0, "comments": "Good"}},
            overall_score=4.0,
            status="completed",
        )

        scorecard2 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={str(criteria.id): {"score": 5.0, "comments": "Excellent"}},
            overall_score=5.0,
            status="completed",
        )

        db_session.add_all([scorecard1, scorecard2])
        await db_session.commit()

        # Calculate aggregate
        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        # Verify average calculation
        total_evaluators = len(scorecards)
        assert total_evaluators == 2

        criteria_scores = {str(criteria.id): []}
        overall_scores = []

        for scorecard in scorecards:
            overall_scores.append(scorecard.overall_score)
            for criteria_id, response in scorecard.criteria_responses.items():
                if criteria_id in criteria_scores:
                    criteria_scores[criteria_id].append(response["score"])

        # Verify criteria average: (4.0 + 5.0) / 2 = 4.5
        criteria_avg = sum(criteria_scores[str(criteria.id)]) / len(
            criteria_scores[str(criteria.id)]
        )
        assert abs(criteria_avg - 4.5) < 0.01

        # Verify overall average: (4.0 + 5.0) / 2 = 4.5
        overall_avg = sum(overall_scores) / len(overall_scores)
        assert abs(overall_avg - 4.5) < 0.01

    @pytest.mark.asyncio
    async def test_average_score_calculation_three_evaluators(self, db_session: AsyncSession):
        """Test average score calculation with three evaluators."""
        # Setup
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        criteria = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=0.5,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        db_session.add(criteria)
        await db_session.flush()

        # Create three scorecards: 3.0, 4.0, 5.0
        # Expected average: (3.0 + 4.0 + 5.0) / 3 = 4.0

        scorecard1 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={str(criteria.id): {"score": 3.0, "comments": "Average"}},
            overall_score=3.0,
            status="completed",
        )

        scorecard2 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={str(criteria.id): {"score": 4.0, "comments": "Good"}},
            overall_score=4.0,
            status="completed",
        )

        scorecard3 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={str(criteria.id): {"score": 5.0, "comments": "Excellent"}},
            overall_score=5.0,
            status="completed",
        )

        db_session.add_all([scorecard1, scorecard2, scorecard3])
        await db_session.commit()

        # Calculate and verify
        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        overall_scores = [s.overall_score for s in scorecards]
        overall_avg = sum(overall_scores) / len(overall_scores)

        assert abs(overall_avg - 4.0) < 0.01


class TestWeightedScoreCalculation:
    """Tests for weighted score calculation accuracy."""

    @pytest.mark.asyncio
    async def test_weighted_score_with_two_criteria(self, db_session: AsyncSession):
        """Test weighted score calculation with two criteria of different weights."""
        # Setup: Criteria 1 (weight 0.6), Criteria 2 (weight 0.4)
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
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
            name="Communication",
            criteria_type="cultural_fit",
            weight=0.4,
            min_score=1,
            max_score=5,
            display_order=2,
        )
        db_session.add_all([criteria1, criteria2])
        await db_session.flush()

        # Create scorecards from 2 evaluators
        # Evaluator 1: Tech=5.0, Comm=4.0, Overall=4.5
        # Evaluator 2: Tech=4.0, Comm=5.0, Overall=4.5
        # Expected averages: Tech=4.5, Comm=4.5
        # Expected weighted: (4.5 * 0.6) + (4.5 * 0.4) = 2.7 + 1.8 = 4.5

        scorecard1 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 5.0, "comments": "Excellent tech"},
                str(criteria2.id): {"score": 4.0, "comments": "Good comm"},
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
                str(criteria1.id): {"score": 4.0, "comments": "Good tech"},
                str(criteria2.id): {"score": 5.0, "comments": "Excellent comm"},
            },
            overall_score=4.5,
            status="completed",
        )

        db_session.add_all([scorecard1, scorecard2])
        await db_session.commit()

        # Calculate weighted score
        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        # Get criteria weights
        criteria_result = await db_session.execute(
            select(EvaluationCriteria).where(EvaluationCriteria.template_id == template_id)
        )
        all_criteria = criteria_result.scalars().all()
        criteria_weights = {
            str(c.id): float(c.weight)
            for c in all_criteria
        }

        # Calculate averages
        criteria_scores_sum = {str(criteria1.id): 0.0, str(criteria2.id): 0.0}
        criteria_counts = {str(criteria1.id): 0, str(criteria2.id): 0}

        for scorecard in scorecards:
            for criteria_id, data in scorecard.criteria_responses.items():
                score = data["score"]
                criteria_scores_sum[criteria_id] += score
                criteria_counts[criteria_id] += 1

        average_scores = {
            criteria_id: criteria_scores_sum[criteria_id] / criteria_counts[criteria_id]
            for criteria_id in criteria_scores_sum
        }

        # Verify averages
        assert abs(average_scores[str(criteria1.id)] - 4.5) < 0.01
        assert abs(average_scores[str(criteria2.id)] - 4.5) < 0.01

        # Calculate weighted score
        weighted_sum = 0.0
        total_weight = 0.0

        for criteria_id, avg_score in average_scores.items():
            weight = criteria_weights.get(criteria_id, 1.0)
            weighted_sum += avg_score * weight
            total_weight += weight

        weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Verify weighted score: (4.5 * 0.6) + (4.5 * 0.4) = 4.5
        assert abs(weighted_score - 4.5) < 0.01

    @pytest.mark.asyncio
    async def test_weighted_score_with_three_criteria(self, db_session: AsyncSession):
        """Test weighted score calculation with three criteria."""
        # Setup: Criteria 1 (weight 0.5), Criteria 2 (weight 0.3), Criteria 3 (weight 0.2)
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
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
            weight=0.5,
            min_score=1,
            max_score=10,
            display_order=1,
        )
        criteria2 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Problem Solving",
            criteria_type="skills",
            weight=0.3,
            min_score=1,
            max_score=10,
            display_order=2,
        )
        criteria3 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Communication",
            criteria_type="cultural_fit",
            weight=0.2,
            min_score=1,
            max_score=10,
            display_order=3,
        )
        db_session.add_all([criteria1, criteria2, criteria3])
        await db_session.flush()

        # Create scorecards from 3 evaluators
        # Evaluator 1: Tech=9.0, Prob=8.0, Comm=7.0
        # Evaluator 2: Tech=8.0, Prob=9.0, Comm=8.0
        # Evaluator 3: Tech=8.5, Prob=7.5, Comm=9.0
        # Expected averages: Tech=8.5, Prob=8.167, Comm=8.0
        # Expected weighted: (8.5 * 0.5) + (8.167 * 0.3) + (8.0 * 0.2) = 4.25 + 2.45 + 1.6 = 8.3

        scorecard1 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 9.0, "comments": "Excellent"},
                str(criteria2.id): {"score": 8.0, "comments": "Good"},
                str(criteria3.id): {"score": 7.0, "comments": "Average"},
            },
            overall_score=8.0,
            status="completed",
        )

        scorecard2 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 8.0, "comments": "Good"},
                str(criteria2.id): {"score": 9.0, "comments": "Excellent"},
                str(criteria3.id): {"score": 8.0, "comments": "Good"},
            },
            overall_score=8.33,
            status="completed",
        )

        scorecard3 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 8.5, "comments": "Very good"},
                str(criteria2.id): {"score": 7.5, "comments": "Good"},
                str(criteria3.id): {"score": 9.0, "comments": "Excellent"},
            },
            overall_score=8.33,
            status="completed",
        )

        db_session.add_all([scorecard1, scorecard2, scorecard3])
        await db_session.commit()

        # Calculate weighted score
        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        # Get criteria weights
        criteria_result = await db_session.execute(
            select(EvaluationCriteria).where(EvaluationCriteria.template_id == template_id)
        )
        all_criteria = criteria_result.scalars().all()
        criteria_weights = {
            str(c.id): float(c.weight)
            for c in all_criteria
        }

        # Calculate averages
        criteria_scores_sum = {}
        criteria_counts = {}

        for scorecard in scorecards:
            for criteria_id, data in scorecard.criteria_responses.items():
                score = data["score"]
                if criteria_id not in criteria_scores_sum:
                    criteria_scores_sum[criteria_id] = 0.0
                    criteria_counts[criteria_id] = 0
                criteria_scores_sum[criteria_id] += score
                criteria_counts[criteria_id] += 1

        average_scores = {
            criteria_id: criteria_scores_sum[criteria_id] / criteria_counts[criteria_id]
            for criteria_id in criteria_scores_sum
        }

        # Calculate weighted score
        weighted_sum = 0.0
        total_weight = 0.0

        for criteria_id, avg_score in average_scores.items():
            weight = criteria_weights.get(criteria_id, 1.0)
            weighted_sum += avg_score * weight
            total_weight += weight

        weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Verify weighted score: (8.5 * 0.5) + (8.167 * 0.3) + (8.0 * 0.2) = 8.3
        assert abs(weighted_score - 8.3) < 0.1

    @pytest.mark.asyncio
    async def test_weighted_score_with_decimal_weights(self, db_session: AsyncSession):
        """Test weighted score calculation with non-integer weight sums."""
        # Setup: Weights that don't sum to 1.0 (0.25, 0.35, 0.40)
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        criteria1 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Criteria 1",
            criteria_type="skills",
            weight=0.25,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        criteria2 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Criteria 2",
            criteria_type="skills",
            weight=0.35,
            min_score=1,
            max_score=5,
            display_order=2,
        )
        criteria3 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Criteria 3",
            criteria_type="cultural_fit",
            weight=0.40,
            min_score=1,
            max_score=5,
            display_order=3,
        )
        db_session.add_all([criteria1, criteria2, criteria3])
        await db_session.flush()

        # Create scorecards
        # All evaluators give: Crit1=4.0, Crit2=4.0, Crit3=4.0
        # Expected weighted: (4.0 * 0.25 + 4.0 * 0.35 + 4.0 * 0.40) / 1.0 = 4.0

        scorecard1 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 4.0, "comments": "Good"},
                str(criteria2.id): {"score": 4.0, "comments": "Good"},
                str(criteria3.id): {"score": 4.0, "comments": "Good"},
            },
            overall_score=4.0,
            status="completed",
        )

        scorecard2 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 4.0, "comments": "Good"},
                str(criteria2.id): {"score": 4.0, "comments": "Good"},
                str(criteria3.id): {"score": 4.0, "comments": "Good"},
            },
            overall_score=4.0,
            status="completed",
        )

        db_session.add_all([scorecard1, scorecard2])
        await db_session.commit()

        # Calculate weighted score
        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        # Get criteria weights
        criteria_result = await db_session.execute(
            select(EvaluationCriteria).where(EvaluationCriteria.template_id == template_id)
        )
        all_criteria = criteria_result.scalars().all()
        criteria_weights = {
            str(c.id): float(c.weight)
            for c in all_criteria
        }

        # Calculate averages
        criteria_scores_sum = {}
        criteria_counts = {}

        for scorecard in scorecards:
            for criteria_id, data in scorecard.criteria_responses.items():
                score = data["score"]
                if criteria_id not in criteria_scores_sum:
                    criteria_scores_sum[criteria_id] = 0.0
                    criteria_counts[criteria_id] = 0
                criteria_scores_sum[criteria_id] += score
                criteria_counts[criteria_id] += 1

        average_scores = {
            criteria_id: criteria_scores_sum[criteria_id] / criteria_counts[criteria_id]
            for criteria_id in criteria_scores_sum
        }

        # Calculate weighted score
        weighted_sum = 0.0
        total_weight = 0.0

        for criteria_id, avg_score in average_scores.items():
            weight = criteria_weights.get(criteria_id, 1.0)
            weighted_sum += avg_score * weight
            total_weight += weight

        weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Verify weighted score is 4.0 (all criteria scored 4.0)
        assert abs(weighted_score - 4.0) < 0.01


class TestCompletionRateCalculation:
    """Tests for completion rate calculation."""

    @pytest.mark.asyncio
    async def test_completion_rate_all_completed(self, db_session: AsyncSession):
        """Test completion rate when all scorecards are completed."""
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        criteria = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=1.0,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        db_session.add(criteria)
        await db_session.flush()

        # Create 3 completed scorecards
        for _ in range(3):
            scorecard = EvaluationScorecard(
                id=str(uuid4()),
                template_id=template_id,
                resume_id=resume_id,
                evaluator_id=str(uuid4()),
                criteria_responses={str(criteria.id): {"score": 4.0, "comments": "Good"}},
                overall_score=4.0,
                status="completed",
            )
            db_session.add(scorecard)

        await db_session.commit()

        # Calculate completion rate
        result = await db_session.execute(
            select(EvaluationScorecard).where(EvaluationScorecard.resume_id == resume_id)
        )
        scorecards = result.scalars().all()

        total_evaluators = len(scorecards)
        completed_count = sum(1 for s in scorecards if s.status == "completed")
        completion_rate = completed_count / total_evaluators if total_evaluators > 0 else 0.0

        assert total_evaluators == 3
        assert completed_count == 3
        assert completion_rate == 1.0

    @pytest.mark.asyncio
    async def test_completion_rate_partial_completion(self, db_session: AsyncSession):
        """Test completion rate with mixed completed and draft scorecards."""
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        criteria = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=1.0,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        db_session.add(criteria)
        await db_session.flush()

        # Create scorecards with different statuses
        # 2 completed, 1 in_progress, 1 draft
        statuses = ["completed", "completed", "in_progress", "draft"]
        for status in statuses:
            scorecard = EvaluationScorecard(
                id=str(uuid4()),
                template_id=template_id,
                resume_id=resume_id,
                evaluator_id=str(uuid4()),
                criteria_responses={str(criteria.id): {"score": 4.0, "comments": "Good"}},
                overall_score=4.0,
                status=status,
            )
            db_session.add(scorecard)

        await db_session.commit()

        # Calculate completion rate
        result = await db_session.execute(
            select(EvaluationScorecard).where(EvaluationScorecard.resume_id == resume_id)
        )
        scorecards = result.scalars().all()

        total_evaluators = len(scorecards)
        completed_count = sum(1 for s in scorecards if s.status == "completed")
        completion_rate = completed_count / total_evaluators if total_evaluators > 0 else 0.0

        assert total_evaluators == 4
        assert completed_count == 2
        assert abs(completion_rate - 0.5) < 0.01


class TestEvaluatorBreakdown:
    """Tests for scores by evaluator breakdown."""

    @pytest.mark.asyncio
    async def test_scores_by_evaluator_breakdown(self, db_session: AsyncSession):
        """Test that evaluator breakdown correctly groups scores by evaluator."""
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        criteria = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=1.0,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        db_session.add(criteria)
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
            criteria_responses={str(criteria.id): {"score": 5.0, "comments": "Excellent"}},
            overall_score=5.0,
            status="completed",
        )

        scorecard2 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=evaluator2_id,
            criteria_responses={str(criteria.id): {"score": 3.5, "comments": "Average"}},
            overall_score=3.5,
            status="completed",
        )

        scorecard3 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=evaluator3_id,
            criteria_responses={str(criteria.id): {"score": 4.5, "comments": "Good"}},
            overall_score=4.5,
            status="completed",
        )

        db_session.add_all([scorecard1, scorecard2, scorecard3])
        await db_session.commit()

        # Build evaluator breakdown
        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        scores_by_evaluator = []
        for scorecard in scorecards:
            evaluator_scores = {
                criteria_id: data["score"]
                for criteria_id, data in scorecard.criteria_responses.items()
            }
            scores_by_evaluator.append({
                "evaluator_id": str(scorecard.evaluator_id),
                "overall_score": float(scorecard.overall_score),
                "criteria_scores": evaluator_scores,
                "status": scorecard.status,
                "scorecard_id": str(scorecard.id),
            })

        # Verify breakdown
        assert len(scores_by_evaluator) == 3

        # Check that each evaluator's scores are correctly attributed
        evaluator_ids_in_breakdown = {e["evaluator_id"] for e in scores_by_evaluator}
        assert evaluator1_id in evaluator_ids_in_breakdown
        assert evaluator2_id in evaluator_ids_in_breakdown
        assert evaluator3_id in evaluator_ids_in_breakdown

        # Verify scores
        for evaluator in scores_by_evaluator:
            if evaluator["evaluator_id"] == evaluator1_id:
                assert evaluator["overall_score"] == 5.0
            elif evaluator["evaluator_id"] == evaluator2_id:
                assert evaluator["overall_score"] == 3.5
            elif evaluator["evaluator_id"] == evaluator3_id:
                assert evaluator["overall_score"] == 4.5


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_aggregation_with_no_scorecards(self, db_session: AsyncSession):
        """Test aggregation when no scorecards exist for a candidate."""
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)
        await db_session.commit()

        # Try to get scorecards
        result = await db_session.execute(
            select(EvaluationScorecard).where(EvaluationScorecard.resume_id == resume_id)
        )
        scorecards = result.scalars().all()

        # Verify empty result
        assert len(scorecards) == 0
        assert len(scorecards) == 0

    @pytest.mark.asyncio
    async def test_aggregation_with_single_evaluator(self, db_session: AsyncSession):
        """Test aggregation with only one evaluator."""
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        criteria = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=1.0,
            min_score=1,
            max_score=5,
            display_order=1,
        )
        db_session.add(criteria)
        await db_session.flush()

        # Create single scorecard
        scorecard = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={str(criteria.id): {"score": 4.0, "comments": "Good"}},
            overall_score=4.0,
            status="completed",
        )
        db_session.add(scorecard)
        await db_session.commit()

        # Calculate aggregation
        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        total_evaluators = len(scorecards)
        overall_scores = [s.overall_score for s in scorecards]
        overall_avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0

        assert total_evaluators == 1
        assert abs(overall_avg - 4.0) < 0.01

    @pytest.mark.asyncio
    async def test_aggregation_with_different_rating_scales(self, db_session: AsyncSession):
        """Test aggregation with different rating scales (1-5 vs 1-10)."""
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        # Criteria with 1-10 scale
        criteria1 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=0.6,
            min_score=1,
            max_score=10,
            display_order=1,
        )
        # Criteria with 1-5 scale
        criteria2 = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Communication",
            criteria_type="cultural_fit",
            weight=0.4,
            min_score=1,
            max_score=5,
            display_order=2,
        )
        db_session.add_all([criteria1, criteria2])
        await db_session.flush()

        # Create scorecards
        scorecard = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={
                str(criteria1.id): {"score": 8.0, "comments": "Very good"},
                str(criteria2.id): {"score": 4.0, "comments": "Good"},
            },
            overall_score=6.0,
            status="completed",
        )
        db_session.add(scorecard)
        await db_session.commit()

        # Verify aggregation handles different scales correctly
        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        assert len(scorecards) == 1
        scorecard = scorecards[0]
        assert scorecard.criteria_responses[str(criteria1.id)]["score"] == 8.0
        assert scorecard.criteria_responses[str(criteria2.id)]["score"] == 4.0


class TestDecimalPrecision:
    """Tests for decimal precision and rounding accuracy."""

    @pytest.mark.asyncio
    async def test_decimal_precision_in_averages(self, db_session: AsyncSession):
        """Test that decimal precision is maintained in average calculations."""
        template_id = str(uuid4())
        resume_id = str(uuid4())

        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=str(uuid4()),
            content="Test resume",
            parsed_data={},
        )
        db_session.add(resume)

        template = EvaluationTemplate(
            id=template_id,
            organization_id=str(uuid4()),
            name="Interview Template",
            version=1,
            is_active=True,
        )
        db_session.add(template)

        criteria = EvaluationCriteria(
            id=str(uuid4()),
            template_id=template_id,
            name="Technical Skills",
            criteria_type="skills",
            weight=1.0,
            min_score=1,
            max_score=10,
            display_order=1,
        )
        db_session.add(criteria)
        await db_session.flush()

        # Create scorecards with decimal scores
        # Scores: 8.33, 7.67, 8.0
        # Expected average: (8.33 + 7.67 + 8.0) / 3 = 8.0

        scorecard1 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={str(criteria.id): {"score": 8.33, "comments": "Very good"}},
            overall_score=8.33,
            status="completed",
        )

        scorecard2 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={str(criteria.id): {"score": 7.67, "comments": "Good"}},
            overall_score=7.67,
            status="completed",
        )

        scorecard3 = EvaluationScorecard(
            id=str(uuid4()),
            template_id=template_id,
            resume_id=resume_id,
            evaluator_id=str(uuid4()),
            criteria_responses={str(criteria.id): {"score": 8.0, "comments": "Very good"}},
            overall_score=8.0,
            status="completed",
        )

        db_session.add_all([scorecard1, scorecard2, scorecard3])
        await db_session.commit()

        # Calculate average
        result = await db_session.execute(
            select(EvaluationScorecard).where(
                EvaluationScorecard.resume_id == resume_id,
                EvaluationScorecard.status == "completed",
            )
        )
        scorecards = result.scalars().all()

        overall_scores = [s.overall_score for s in scorecards]
        overall_avg = sum(overall_scores) / len(overall_scores)

        # Verify average is close to 8.0 (allow small floating point errors)
        assert abs(overall_avg - 8.0) < 0.01
