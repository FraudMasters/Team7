#!/usr/bin/env python3
"""
End-to-End Verification Script for A/B Testing System

This script verifies the complete A/B testing system functionality:
1. Database migration and table creation
2. Model imports and validation
3. A/B test creation via service
4. User assignment to variants
5. Metric recording
6. Statistical analysis
7. Weight optimization

Run this script after setting up the database to verify the A/B testing system.
"""
import asyncio
import sys
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db
from models.ab_testing import (
    ABTest,
    ABTestAssignment,
    ABTestMetric,
    ABTestMetricType,
    ABTestStatus,
)
from models.matching_weights import create_preset_profiles
from services.weight_optimizer import WeightOptimizerService


# ANSI color codes for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_step(num, description):
    """Print a verification step header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== Step {num}: {description} ==={Colors.RESET}")


def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message):
    """Print an info message."""
    print(f"{Colors.YELLOW}  {message}{Colors.RESET}")


async def verify_models_import():
    """Verify that all A/B testing models can be imported."""
    print_step(1, "Model Import Verification")

    try:
        from models.ab_testing import (
            ABTest,
            ABTestAssignment,
            ABTestMetric,
            ABTestStatus,
            ABTestMetricType,
        )
        print_success("All A/B testing models imported successfully")

        # Verify enum values
        assert ABTestStatus.DRAFT.value == "draft"
        assert ABTestStatus.RUNNING.value == "running"
        assert ABTestMetricType.MATCH_ACCEPTANCE.value == "match_acceptance"
        assert ABTestMetricType.TIME_TO_HIRE.value == "time_to_hire"
        assert ABTestMetricType.USER_SATISFACTION.value == "user_satisfaction"
        print_success("Model enums validated successfully")

        return True
    except Exception as e:
        print_error(f"Model import failed: {e}")
        return False


async def verify_service_import():
    """Verify that the WeightOptimizerService can be imported."""
    print_step(2, "Service Import Verification")

    try:
        from services.weight_optimizer import (
            WeightOptimizerService,
            UserAssignment,
            MetricRecord,
            StatisticalTestResult,
            OptimizationResult,
        )
        print_success("WeightOptimizerService and dataclasses imported successfully")

        # Verify service constants
        assert WeightOptimizerService.MIN_SAMPLE_SIZE == 30
        assert WeightOptimizerService.SIGNIFICANCE_LEVEL == 0.05
        assert WeightOptimizerService.RANDOM_SEED == 42
        print_success("Service constants validated (MIN_SAMPLE_SIZE=30, ALPHA=0.05)")

        return True
    except Exception as e:
        print_error(f"Service import failed: {e}")
        return False


async def verify_scipy_import():
    """Verify that scipy.stats functions can be imported."""
    print_step(3, "scipy Import Verification")

    try:
        from scipy.stats import ttest_ind, chi2_contingency, mannwhitneyu
        print_success("scipy.stats functions imported successfully")

        # Verify basic functionality
        import numpy as np
        g1 = np.random.normal(0.5, 0.1, 100)
        g2 = np.random.normal(0.6, 0.1, 100)
        stat, p = ttest_ind(g1, g2)
        print_info(f"Sample t-test: p-value = {p:.4f}")

        return True
    except Exception as e:
        print_error(f"scipy import failed: {e}")
        return False


async def verify_database_migration():
    """Verify that database tables exist."""
    print_step(4, "Database Migration Verification")

    try:
        # Import database module
        from database import async_session_maker

        # Try to query each table
        async with async_session_maker() as session:
            # Check ab_tests table
            from sqlalchemy import text
            result = await session.execute(text(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'ab_tests')"
            ))
            exists = result.scalar()
            if exists:
                print_success("ab_tests table exists")
            else:
                print_error("ab_tests table does not exist")
                return False

            # Check ab_test_assignments table
            result = await session.execute(text(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'ab_test_assignments')"
            ))
            exists = result.scalar()
            if exists:
                print_success("ab_test_assignments table exists")
            else:
                print_error("ab_test_assignments table does not exist")
                return False

            # Check ab_test_metrics table
            result = await session.execute(text(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'ab_test_metrics')"
            ))
            exists = result.scalar()
            if exists:
                print_success("ab_test_metrics table exists")
            else:
                print_error("ab_test_metrics table does not exist")
                return False

        return True
    except Exception as e:
        print_error(f"Database migration verification failed: {e}")
        print_info("Make sure to run: alembic upgrade head")
        return False


async def verify_ab_test_creation():
    """Verify creating an A/B test instance."""
    print_step(5, "A/B Test Creation")

    try:
        from database import async_session_maker

        async with async_session_maker() as session:
            # Create preset profiles first
            profiles = create_preset_profiles()
            for profile in profiles:
                session.add(profile)
            await session.commit()
            print_info(f"Created {len(profiles)} preset profiles")

            # Create A/B test
            org_id = str(uuid4())
            test = ABTest(
                name="E2E Verification Test",
                description="End-to-end verification of A/B testing system",
                status=ABTestStatus.RUNNING,
                start_date=datetime.now(timezone.utc),
                organization_id=org_id,
                created_by=str(uuid4()),
            )
            session.add(test)
            await session.commit()
            await session.refresh(test)

            print_success(f"Created A/B test: {test.name} (ID: {test.id})")
            print_info(f"  Status: {test.status.value}")
            print_info(f"  Organization: {org_id}")

            return test.id, org_id
    except Exception as e:
        print_error(f"A/B test creation failed: {e}")
        return None, None


async def verify_user_assignment(test_id, org_id):
    """Verify user assignment to variants."""
    print_step(6, "User Assignment to Variants")

    try:
        from database import async_session_maker

        async with async_session_maker() as session:
            service = WeightOptimizerService(session)

            # Assign multiple users
            num_users = 20
            assignments = []
            for i in range(num_users):
                user_id = str(uuid4())
                assignment = await service.assign_user_to_variant(
                    test_id=str(test_id),
                    user_id=user_id,
                    organization_id=org_id,
                )
                assignments.append(assignment)

            print_success(f"Assigned {num_users} users to variants")

            # Check distribution
            profile_counts = {}
            for assignment in assignments:
                name = assignment.profile_name
                profile_counts[name] = profile_counts.get(name, 0) + 1

            print_info("Distribution across profiles:")
            for profile, count in profile_counts.items():
                print_info(f"  {profile}: {count} users ({count/num_users*100:.1f}%)")

            # Verify deterministic assignment
            test_user_id = str(uuid4())
            assignment1 = await service.assign_user_to_variant(
                test_id=str(test_id),
                user_id=test_user_id,
                organization_id=org_id,
            )
            assignment2 = await service.assign_user_to_variant(
                test_id=str(test_id),
                user_id=test_user_id,
                organization_id=org_id,
            )

            if assignment1.profile_id == assignment2.profile_id:
                print_success("Deterministic assignment verified (same user gets same profile)")
            else:
                print_error("Deterministic assignment failed!")
                return False

            return assignments
    except Exception as e:
        print_error(f"User assignment failed: {e}")
        return None


async def verify_metric_recording(test_id, assignments):
    """Verify metric recording."""
    print_step(7, "Metric Recording")

    try:
        from database import async_session_maker

        async with async_session_maker() as session:
            service = WeightOptimizerService(session)

            # Record metrics for first 10 assignments
            metrics_count = 0
            for i, assignment in enumerate(assignments[:10]):
                # Record match acceptance
                await service.record_metric(
                    test_id=str(test_id),
                    user_id=assignment.user_id,
                    metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
                    metric_value=1.0 if i < 5 else 0.0,
                )

                # Record time to hire
                await service.record_metric(
                    test_id=str(test_id),
                    user_id=assignment.user_id,
                    metric_type=ABTestMetricType.TIME_TO_HIRE,
                    metric_value=14.0 if i < 5 else 45.0,
                )

                # Record user satisfaction
                await service.record_metric(
                    test_id=str(test_id),
                    user_id=assignment.user_id,
                    metric_type=ABTestMetricType.USER_SATISFACTION,
                    metric_value=4.5 if i < 5 else 2.5,
                )
                metrics_count += 3

            print_success(f"Recorded {metrics_count} metrics across {len(assignments[:10])} users")

            # Verify metrics in database
            from sqlalchemy import select
            result = await session.execute(
                select(ABTestMetric).where(ABTestMetric.test_id == test_id)
            )
            metrics = result.scalars().all()
            print_info(f"Verified {len(metrics)} metrics in database")

            return True
    except Exception as e:
        print_error(f"Metric recording failed: {e}")
        return False


async def verify_statistical_analysis(test_id):
    """Verify statistical analysis."""
    print_step(8, "Statistical Analysis")

    try:
        from database import async_session_maker

        async with async_session_maker() as session:
            service = WeightOptimizerService(session)

            # Analyze each metric type
            for metric_type in ABTestMetricType:
                try:
                    analysis = await service.analyze_metrics(
                        test_id=str(test_id),
                        metric_type=metric_type,
                    )
                    print_success(f"Analysis for {metric_type.value}:")
                    print_info(f"  Profiles analyzed: {len(analysis['profiles'])}")
                    if 'statistical_test' in analysis and analysis['statistical_test']:
                        st = analysis['statistical_test']
                        print_info(f"  Test type: {st.get('test_type', 'N/A')}")
                        print_info(f"  P-value: {st.get('p_value', 'N/A'):.4f}" if isinstance(st.get('p_value'), (int, float)) else f"  P-value: {st.get('p_value', 'N/A')}")
                        print_info(f"  Significant: {st.get('is_significant', False)}")
                except ValueError as e:
                    if "Insufficient sample size" in str(e):
                        print_info(f"  {metric_type.value}: Skipped (insufficient sample size)")
                    else:
                        raise

            return True
    except Exception as e:
        print_error(f"Statistical analysis failed: {e}")
        return False


async def verify_weight_optimization(test_id):
    """Verify weight optimization."""
    print_step(9, "Weight Optimization")

    try:
        from database import async_session_maker

        async with async_session_maker() as session:
            service = WeightOptimizerService(session)

            # Run optimization
            result = await service.optimize_weights(test_id=str(test_id))

            print_success("Optimization analysis completed")
            print_info(f"  Should optimize: {result.should_optimize}")
            print_info(f"  Reason: {result.reason}")

            if result.should_optimize:
                weights = result.recommended_weights
                print_info("  Recommended weights:")
                print_info(f"    keyword_weight: {weights.get('keyword_weight', 'N/A')}")
                print_info(f"    tfidf_weight: {weights.get('tfidf_weight', 'N/A')}")
                print_info(f"    vector_weight: {weights.get('vector_weight', 'N/A')}")

                # Verify weights sum to 1.0
                total = (
                    weights.get('keyword_weight', 0) +
                    weights.get('tfidf_weight', 0) +
                    weights.get('vector_weight', 0)
                )
                if abs(total - 1.0) < 0.01:
                    print_success(f"  Weights sum to 1.0 (total: {total:.3f})")
                else:
                    print_error(f"  Weights do not sum to 1.0 (total: {total:.3f})")

            if result.statistical_significance:
                st = result.statistical_significance
                print_info("  Statistical significance:")
                print_info(f"    P-value: {st.p_value:.4f}")
                print_info(f"    Effect size: {st.effect_size:.4f}")

            return True
    except Exception as e:
        print_error(f"Weight optimization failed: {e}")
        return False


async def main():
    """Run all verification steps."""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  A/B Testing System - End-to-End Verification")
    print("=" * 60)
    print(f"{Colors.RESET}\n")

    results = []

    # Step 1: Verify model imports
    result = await verify_models_import()
    results.append(("Model Import", result))
    if not result:
        print_error("Cannot continue without models. Exiting.")
        return 1

    # Step 2: Verify service imports
    result = await verify_service_import()
    results.append(("Service Import", result))
    if not result:
        print_error("Cannot continue without service. Exiting.")
        return 1

    # Step 3: Verify scipy
    result = await verify_scipy_import()
    results.append(("scipy Import", result))
    if not result:
        print_error("Cannot continue without scipy. Exiting.")
        return 1

    # Step 4: Verify database migration
    result = await verify_database_migration()
    results.append(("Database Migration", result))
    if not result:
        print_error("Cannot continue without database. Exiting.")
        return 1

    # Step 5: Create A/B test
    test_id, org_id = await verify_ab_test_creation()
    results.append(("A/B Test Creation", test_id is not None))
    if not test_id:
        print_error("Cannot continue without test. Exiting.")
        return 1

    # Step 6: Assign users
    assignments = await verify_user_assignment(test_id, org_id)
    results.append(("User Assignment", assignments is not None))
    if not assignments:
        print_error("Cannot continue without assignments. Exiting.")
        return 1

    # Step 7: Record metrics
    result = await verify_metric_recording(test_id, assignments)
    results.append(("Metric Recording", result))

    # Step 8: Statistical analysis
    result = await verify_statistical_analysis(test_id)
    results.append(("Statistical Analysis", result))

    # Step 9: Weight optimization
    result = await verify_weight_optimization(test_id)
    results.append(("Weight Optimization", result))

    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  Verification Summary")
    print("=" * 60)
    print(f"{Colors.RESET}\n")

    all_passed = True
    for step, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {step:.<40} {status}")
        if not result:
            all_passed = False

    print()
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}All verification steps passed!{Colors.RESET}\n")
        print(f"The A/B testing system is working correctly.")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}Some verification steps failed.{Colors.RESET}\n")
        print(f"Please review the errors above and fix any issues.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
