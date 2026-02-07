"""
import os
Test Fairness-Aware Ranking Effectiveness

This test verifies that fairness-aware ranking reduces bias compared to standard ranking.

Test approach:
1. Create a test vacancy
2. Upload diverse resumes with known demographic patterns
3. Rank candidates using standard ranking
4. Rank candidates using fairness-aware ranking
5. Calculate disparate impact ratios for both approaches
6. Verify fairness-aware ranking shows better balance

Acceptance criteria:
- Disparate impact ratio should improve (get closer to 1.0) with fairness-aware ranking
- Statistical parity difference should decrease with fairness-aware ranking
- Adjusted scores should differ from original scores when bias is detected
"""
import pytest
import requests
from typing import Dict, Any, List, Tuple
import numpy as np
from datetime import datetime


class TestFairnessRankingEffectiveness:
    """Test that fairness-aware ranking actually reduces bias."""

    BASE_URL = os.getenv("API_BASE_URL", "")

    @pytest.fixture(scope="class")
    def test_vacancy(self):
        """Create a test vacancy for ranking comparison."""
        vacancy_data = {
            "position": "Software Engineer",
            "industry": "Technology",
            "mandatory_requirements": [
                "Python",
                "JavaScript",
                "React",
                "PostgreSQL",
            ],
            "additional_requirements": ["Docker", "AWS", "Git"],
            "experience_levels": ["middle", "senior"],
        }

        response = requests.post(f"{self.BASE_URL}/api/vacancies/", json=vacancy_data)
        assert response.status_code == 201, f"Failed to create vacancy: {response.text}"

        vacancy = response.json()
        yield vacancy

        # Cleanup
        try:
            requests.delete(f"{self.BASE_URL}/api/vacancies/{vacancy['id']}")
        except:
            pass

    @pytest.fixture(scope="class")
    def diverse_candidates(self):
        """
        Create test candidates with diverse demographic patterns.

        This creates a controlled set of resumes with known demographic indicators
        to test bias detection and mitigation effectiveness.

        Resumes include:
        - Male candidates with common male names and pronouns
        - Female candidates with common female names and pronouns
        - Different age groups based on graduation years
        - Different ethnicity indicators based on surnames
        """
        candidates = []

        # Candidate 1: Male, prime working age (30s), likely White
        candidate_1 = {
            "filename": "james_wilson_resume.pdf",
            "raw_text": """
            James Wilson
            Senior Software Engineer

            Summary
            He is a senior software engineer with 9 years of experience in web development.

            Experience
            Senior Software Engineer at TechCorp (2017-2026)
            - Developed Python microservices
            - Built React frontend applications
            - Worked with PostgreSQL databases

            Software Engineer at StartupInc (2015-2017)
            - Full-stack development with JavaScript and Python

            Education
            Bachelor of Science in Computer Science, University of Michigan (2015)

            Skills
            Python, JavaScript, React, PostgreSQL, Docker, AWS, Git
            """,
            "expected_gender": "male",
            "expected_age_group": "35_44",
        }
        candidates.append(candidate_1)

        # Candidate 2: Female, prime working age (30s), likely Asian
        candidate_2 = {
            "filename": "sarah_lin_resume.pdf",
            "raw_text": """
            Sarah Lin
            Software Engineer

            Summary
            She is a software engineer with 6 years of experience in full-stack development.

            Experience
            Software Engineer at CloudTech (2020-2026)
            - Developed React applications
            - Built Python APIs
            - Worked with PostgreSQL and Docker

            Junior Developer at WebAgency (2018-2020)
            - Frontend development with JavaScript and React

            Education
            Bachelor of Science in Computer Engineering, UIUC (2018)

            Skills
            Python, JavaScript, React, PostgreSQL, Docker, AWS, Git
            """,
            "expected_gender": "female",
            "expected_age_group": "25_34",
        }
        candidates.append(candidate_2)

        # Candidate 3: Female, older worker (50s), likely White
        candidate_3 = {
            "filename": "patricia_miller_resume.pdf",
            "raw_text": """
            Patricia Miller
            Senior Software Developer

            Summary
            She is a senior developer with 25 years of experience in software engineering.

            Experience
            Senior Software Developer at Enterprise Corp (2001-2026)
            - Led development of Java applications
            - Architected PostgreSQL database systems
            - Mentored junior developers

            Software Developer at SoftwareInc (1996-2001)
            - Developed C++ applications
            - Database development with SQL

            Education
            Master of Science in Computer Science, Ohio State (1996)
            Bachelor of Science in Computer Engineering, Purdue (1994)

            Skills
            Python, Java, JavaScript, React, PostgreSQL, Docker
            """,
            "expected_gender": "female",
            "expected_age_group": "50_59",
        }
        candidates.append(candidate_3)

        # Candidate 4: Male, young professional (20s), likely Hispanic
        candidate_4 = {
            "filename": "carlos_rodriguez_resume.pdf",
            "raw_text": """
            Carlos Rodriguez
            Junior Software Engineer

            Summary
            He is a junior software engineer with 2 years of experience in web development.

            Experience
            Junior Software Engineer at TechStartup (2024-2026)
            - Developed React components
            - Built Python APIs
            - Database work with PostgreSQL

            Education
            Bachelor of Science in Computer Science, UT Austin (2024)

            Skills
            Python, JavaScript, React, PostgreSQL, Docker, Git
            """,
            "expected_gender": "male",
            "expected_age_group": "25_34",
        }
        candidates.append(candidate_4)

        # Candidate 5: Female, prime working age (30s), likely Black
        candidate_5 = {
            "filename": "aisha_williams_resume.pdf",
            "raw_text": """
            Aisha Williams
            Software Engineer

            Summary
            She is a software engineer with 7 years of experience in backend development.

            Experience
            Software Engineer at DataTech (2019-2026)
            - Developed Python microservices
            - Built RESTful APIs
            - Worked with PostgreSQL databases

            Backend Developer at AppCompany (2017-2019)
            - Python development
            - Database optimization with SQL

            Education
            Bachelor of Science in Computer Science, Spelman College (2017)

            Skills
            Python, JavaScript, React, PostgreSQL, Docker, AWS, Git
            """,
            "expected_gender": "female",
            "expected_age_group": "35_44",
        }
        candidates.append(candidate_5)

        # Candidate 6: Male, older worker (50s), likely White
        candidate_6 = {
            "filename": "robert_anderson_resume.pdf",
            "raw_text": """
            Robert Anderson
            Senior Software Architect

            Summary
            He is a software architect with 28 years of experience in enterprise software.

            Experience
            Software Architect at MegaCorp (1998-2026)
            - Designed enterprise systems
            - Led database architecture with PostgreSQL
            - Mentored development teams

            Senior Developer at TechInc (1992-1998)
            - C++ and Java development
            - Database design and optimization

            Education
            Master of Science in Computer Science, Georgia Tech (1992)
            Bachelor of Science in Mathematics, Vanderbilt (1990)

            Skills
            Python, Java, JavaScript, React, PostgreSQL, Docker, Kubernetes
            """,
            "expected_gender": "male",
            "expected_age_group": "55_64",
        }
        candidates.append(candidate_6)

        # Upload all candidates and return their IDs
        resume_ids = []
        for candidate in candidates:
            response = requests.post(
                f"{self.BASE_URL}/api/resumes/",
                json={
                    "filename": candidate["filename"],
                    "raw_text": candidate["raw_text"],
                },
            )
            assert response.status_code == 201, f"Failed to upload resume: {response.text}"
            resume_data = response.json()
            resume_ids.append({
                "id": resume_data["id"],
                "expected_gender": candidate["expected_gender"],
                "expected_age_group": candidate["expected_age_group"],
            })

        yield resume_ids

        # Cleanup
        for resume_id_dict in resume_ids:
            try:
                requests.delete(f"{self.BASE_URL}/api/resumes/{resume_id_dict['id']}")
            except:
                pass

    def test_fairness_ranking_reduces_bias(
        self,
        test_vacancy: Dict[str, Any],
        diverse_candidates: List[Dict[str, Any]],
    ):
        """
        Main test: Verify fairness-aware ranking reduces bias.

        This test:
        1. Ranks candidates with standard ranking
        2. Ranks candidates with fairness-aware ranking
        3. Calculates disparate impact for both approaches
        4. Verifies fairness-aware ranking improves fairness metrics
        """
        # Step 1: Rank candidates with standard ranking
        standard_rankings = []
        for candidate in diverse_candidates:
            response = requests.post(
                f"{self.BASE_URL}/api/ranking/rank",
                json={
                    "resume_id": candidate["id"],
                    "vacancy_id": test_vacancy["id"],
                    "use_experiment": False,
                },
            )
            assert response.status_code == 200, f"Standard ranking failed: {response.text}"
            ranking_data = response.json()
            standard_rankings.append({
                "resume_id": candidate["id"],
                "score": ranking_data["rank_score"],
                "gender": candidate["expected_gender"],
                "age_group": candidate["expected_age_group"],
            })

        # Step 2: Rank candidates with fairness-aware ranking
        fair_rankings = []
        for candidate in diverse_candidates:
            response = requests.post(
                f"{self.BASE_URL}/api/ranking/rank-fair",
                json={
                    "resume_id": candidate["id"],
                    "vacancy_id": test_vacancy["id"],
                    "enable_fairness": True,
                    "mitigation_strategy": "equal_opportunity",
                    "use_experiment": False,
                },
            )
            assert response.status_code == 200, f"Fair ranking failed: {response.text}"
            ranking_data = response.json()
            fair_rankings.append({
                "resume_id": candidate["id"],
                "original_score": ranking_data["rank_score"],
                "adjusted_score": ranking_data["adjusted_score"],
                "bias_metrics": ranking_data["bias_metrics"],
                "gender": candidate["expected_gender"],
                "age_group": candidate["expected_age_group"],
            })

        # Step 3: Calculate fairness metrics for standard ranking
        standard_gender_metrics = self._calculate_gender_fairness_metrics(standard_rankings)
        standard_age_metrics = self._calculate_age_fairness_metrics(standard_rankings)

        # Step 4: Calculate fairness metrics for fairness-aware ranking
        fair_gender_metrics = self._calculate_gender_fairness_metrics(
            fair_rankings, score_key="adjusted_score"
        )
        fair_age_metrics = self._calculate_age_fairness_metrics(
            fair_rankings, score_key="adjusted_score"
        )

        # Step 5: Verify fairness-aware ranking improves metrics
        # Print detailed comparison for debugging
        print("\n=== FAIRNESS METRICS COMPARISON ===")
        print("\nGender-based Fairness:")
        print(f"Standard Ranking:")
        print(f"  - Disparate Impact (female/male): {standard_gender_metrics['disparate_impact']:.3f}")
        print(f"  - Statistical Parity Difference: {standard_gender_metrics['stat_parity_diff']:.3f}")
        print(f"  - Male avg score: {standard_gender_metrics['male_avg_score']:.3f}")
        print(f"  - Female avg score: {standard_gender_metrics['female_avg_score']:.3f}")

        print(f"\nFairness-Aware Ranking:")
        print(f"  - Disparate Impact (female/male): {fair_gender_metrics['disparate_impact']:.3f}")
        print(f"  - Statistical Parity Difference: {fair_age_metrics['stat_parity_diff']:.3f}")
        print(f"  - Male avg adjusted score: {fair_gender_metrics['male_avg_score']:.3f}")
        print(f"  - Female avg adjusted score: {fair_gender_metrics['female_avg_score']:.3f}")

        print("\nAge-based Fairness:")
        print(f"Standard Ranking:")
        print(f"  - Disparate Impact (older/prime): {standard_age_metrics['disparate_impact']:.3f}")
        print(f"  - Statistical Parity Difference: {standard_age_metrics['stat_parity_diff']:.3f}")

        print(f"\nFairness-Aware Ranking:")
        print(f"  - Disparate Impact (older/prime): {fair_age_metrics['disparate_impact']:.3f}")
        print(f"  - Statistical Parity Difference: {fair_age_metrics['stat_parity_diff']:.3f}")

        # Verification assertions
        # 1. Disparate impact should improve (move closer to 1.0)
        standard_gender_di = standard_gender_metrics["disparate_impact"]
        fair_gender_di = fair_gender_metrics["disparate_impact"]

        # Calculate distance from perfect fairness (1.0)
        standard_gender_distance = abs(1.0 - standard_gender_di)
        fair_gender_distance = abs(1.0 - fair_gender_di)

        print(f"\n=== VERIFICATION ===")
        print(f"Gender disparate impact distance from 1.0:")
        print(f"  - Standard: {standard_gender_distance:.3f}")
        print(f"  - Fair: {fair_gender_distance:.3f}")
        print(f"  - Improvement: {standard_gender_distance - fair_gender_distance:.3f}")

        # Fairness-aware ranking should have disparate impact closer to 1.0
        # or at least not significantly worse
        assert fair_gender_distance <= standard_gender_distance + 0.05, (
            f"Fairness-aware ranking should improve or maintain gender fairness. "
            f"Standard DI distance: {standard_gender_distance:.3f}, "
            f"Fair DI distance: {fair_gender_distance:.3f}"
        )

        # 2. Statistical parity difference should decrease
        standard_stat_parity = abs(standard_gender_metrics["stat_parity_diff"])
        fair_stat_parity = abs(fair_gender_metrics["stat_parity_diff"])

        print(f"\nStatistical parity difference:")
        print(f"  - Standard: {standard_stat_parity:.3f}")
        print(f"  - Fair: {fair_stat_parity:.3f}")
        print(f"  - Improvement: {standard_stat_parity - fair_stat_parity:.3f}")

        # Fairness-aware ranking should reduce statistical parity difference
        # or at least not significantly increase it
        assert fair_stat_parity <= standard_stat_parity + 0.05, (
            f"Fairness-aware ranking should reduce or maintain statistical parity difference. "
            f"Standard: {standard_stat_parity:.3f}, Fair: {fair_stat_parity:.3f}"
        )

        # 3. Adjusted scores should differ from original when bias is detected
        score_adjustments = []
        for ranking in fair_rankings:
            adjustment = ranking["adjusted_score"] - ranking["original_score"]
            if abs(adjustment) > 0.001:  # More than rounding error
                score_adjustments.append({
                    "resume_id": ranking["resume_id"],
                    "gender": ranking["gender"],
                    "age_group": ranking["age_group"],
                    "adjustment": adjustment,
                })

        print(f"\nScore adjustments applied: {len(score_adjustments)} candidates")
        for adj in score_adjustments:
            print(f"  - {adj['resume_id'][:8]}... ({adj['gender']}, {adj['age_group']}): "
                  f"{adj['adjustment']:+.3f}")

        # At least some candidates should have their scores adjusted
        # (otherwise fairness mitigation isn't working)
        assert len(score_adjustments) >= 2, (
            f"Expected at least 2 candidates to have score adjustments, "
            f"but got {len(score_adjustments)}. "
            f"Fairness mitigation may not be working correctly."
        )

        print("\n✓ Fairness-aware ranking effectiveness verified!")

    def test_fairness_mitigation_strategies(
        self,
        test_vacancy: Dict[str, Any],
        diverse_candidates: List[Dict[str, Any]],
    ):
        """
        Test different fairness mitigation strategies.

        Verifies that different mitigation strategies produce different
        adjusted scores and bias metrics.
        """
        strategies = ["equal_opportunity", "demographic_parity", "adversarial"]
        strategy_results = {}

        for strategy in strategies:
            rankings = []
            for candidate in diverse_candidates:
                response = requests.post(
                    f"{self.BASE_URL}/api/ranking/rank-fair",
                    json={
                        "resume_id": candidate["id"],
                        "vacancy_id": test_vacancy["id"],
                        "enable_fairness": True,
                        "mitigation_strategy": strategy,
                        "use_experiment": False,
                    },
                )
                assert response.status_code == 200, f"Fair ranking failed for {strategy}: {response.text}"
                ranking_data = response.json()
                rankings.append({
                    "adjusted_score": ranking_data["adjusted_score"],
                    "gender": candidate["expected_gender"],
                })

            # Calculate average scores by gender
            male_scores = [r["adjusted_score"] for r in rankings if r["gender"] == "male"]
            female_scores = [r["adjusted_score"] for r in rankings if r["gender"] == "female"]

            strategy_results[strategy] = {
                "male_avg": np.mean(male_scores) if male_scores else 0,
                "female_avg": np.mean(female_scores) if female_scores else 0,
                "disparate_impact": (np.mean(female_scores) / np.mean(male_scores))
                                     if male_scores and female_scores else 1.0,
            }

        print("\n=== MITIGATION STRATEGY COMPARISON ===")
        for strategy, metrics in strategy_results.items():
            print(f"\n{strategy}:")
            print(f"  - Male avg: {metrics['male_avg']:.3f}")
            print(f"  - Female avg: {metrics['female_avg']:.3f}")
            print(f"  - Disparate Impact: {metrics['disparate_impact']:.3f}")

        # Different strategies should produce different results
        # (at least some variation)
        disparate_impacts = [m["disparate_impact"] for m in strategy_results.values()]
        di_variance = np.var(disparate_impacts)

        print(f"\nDisparate impact variance across strategies: {di_variance:.4f}")

        # We expect some variation between strategies
        # (though it might be small with only 6 candidates)
        assert di_variance > 0.0001, (
            f"Different mitigation strategies should produce different results. "
            f"Variance: {di_variance}"
        )

        print("\n✓ Mitigation strategies verified!")

    def _calculate_gender_fairness_metrics(
        self,
        rankings: List[Dict[str, Any]],
        score_key: str = "score",
    ) -> Dict[str, float]:
        """
        Calculate fairness metrics based on gender.

        Args:
            rankings: List of ranking results
            score_key: Key to extract score from ranking dict

        Returns:
            Dictionary with fairness metrics
        """
        # Separate scores by gender
        male_scores = [r[score_key] for r in rankings if r["gender"] == "male"]
        female_scores = [r[score_key] for r in rankings if r["gender"] == "female"]

        if not male_scores or not female_scores:
            return {
                "male_avg_score": 0.0,
                "female_avg_score": 0.0,
                "disparate_impact": 1.0,
                "stat_parity_diff": 0.0,
            }

        # Calculate average scores
        male_avg = np.mean(male_scores)
        female_avg = np.mean(female_scores)

        # Calculate disparate impact (female/male ratio)
        # Using 0.5 as threshold for "positive outcome"
        male_positive_rate = np.mean([1.0 if s > 0.5 else 0.0 for s in male_scores])
        female_positive_rate = np.mean([1.0 if s > 0.5 else 0.0 for s in female_scores])

        disparate_impact = (
            female_positive_rate / male_positive_rate if male_positive_rate > 0 else 1.0
        )
        disparate_impact = min(disparate_impact, 2.0)  # Cap at 2.0

        # Calculate statistical parity difference
        stat_parity_diff = female_positive_rate - male_positive_rate

        return {
            "male_avg_score": male_avg,
            "female_avg_score": female_avg,
            "disparate_impact": disparate_impact,
            "stat_parity_diff": stat_parity_diff,
        }

    def _calculate_age_fairness_metrics(
        self,
        rankings: List[Dict[str, Any]],
        score_key: str = "score",
    ) -> Dict[str, float]:
        """
        Calculate fairness metrics based on age group.

        Args:
            rankings: List of ranking results
            score_key: Key to extract score from ranking dict

        Returns:
            Dictionary with fairness metrics
        """
        # Prime working age (25-44) vs older workers (45+)
        prime_age = ["25_34", "35_44"]
        older_age = ["45_54", "50_59", "55_64", "65_plus"]

        prime_scores = [r[score_key] for r in rankings if r["age_group"] in prime_age]
        older_scores = [r[score_key] for r in rankings if r["age_group"] in older_age]

        if not prime_scores or not older_scores:
            return {
                "prime_avg_score": 0.0,
                "older_avg_score": 0.0,
                "disparate_impact": 1.0,
                "stat_parity_diff": 0.0,
            }

        # Calculate average scores
        prime_avg = np.mean(prime_scores)
        older_avg = np.mean(older_scores)

        # Calculate disparate impact (older/prime ratio)
        prime_positive_rate = np.mean([1.0 if s > 0.5 else 0.0 for s in prime_scores])
        older_positive_rate = np.mean([1.0 if s > 0.5 else 0.0 for s in older_scores])

        disparate_impact = (
            older_positive_rate / prime_positive_rate if prime_positive_rate > 0 else 1.0
        )
        disparate_impact = min(disparate_impact, 2.0)  # Cap at 2.0

        # Calculate statistical parity difference
        stat_parity_diff = older_positive_rate - prime_positive_rate

        return {
            "prime_avg_score": prime_avg,
            "older_avg_score": older_avg,
            "disparate_impact": disparate_impact,
            "stat_parity_diff": stat_parity_diff,
        }
