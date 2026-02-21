"""
Model versioning system with A/B testing allocation logic.

This module provides intelligent model version management for machine learning models,
including A/B testing capabilities, performance tracking, and automatic model selection.
The system supports:
- Active model version management
- A/B testing with configurable traffic allocation
- Performance-based model promotion with statistical significance testing
- Fallback handling for model failures
"""
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

from models.ml_model_version import MLModelVersion
from models.model_performance_history import ModelPerformanceHistory

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """
    Model versioning manager with A/B testing allocation logic.

    This class provides methods to manage ML model versions, allocate traffic
    between models for A/B testing, and track performance metrics for automatic
    model promotion.

    Attributes:
        default_fallback_version: Default version to use when no active model is found

    Example:
        >>> manager = ModelVersionManager()
        >>> model_info = manager.get_active_model('skill_matching')
        >>> print(model_info['version'])
        'v1.0.0'
        >>> allocated_model = manager.allocate_model_for_user('skill_matching', 'user123')
        >>> print(allocated_model['version'])
        'v2.0.0'  # User allocated to experimental model
    """

    # Default fallback version when no active model is found
    DEFAULT_FALLBACK_VERSION = "v1.0.0"

    # Default canary traffic allocation (10%)
    DEFAULT_CANARY_TRAFFIC_PERCENTAGE = 10

    # Maximum canary traffic before requiring promotion
    MAX_CANARY_TRAFFIC_PERCENTAGE = 50

    def __init__(self, default_fallback_version: Optional[str] = None) -> None:
        """
        Initialize the model version manager.

        Args:
            default_fallback_version: Default version to use as fallback
                                     (defaults to DEFAULT_FALLBACK_VERSION)
        """
        self.default_fallback_version = (
            default_fallback_version or self.DEFAULT_FALLBACK_VERSION
        )

    def get_active_model(
        self, model_name: str, db_session: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the currently active model version for a given model name.

        Queries the database for the active (non-experimental) model version
        marked as active. This is the production model that receives the
        majority of traffic.

        Args:
            model_name: Name of the model (e.g., 'skill_matching', 'resume_parser')
            db_session: Optional database session for querying

        Returns:
            Dictionary with model information (id, version, file_path, etc.)
            or None if no active model found

        Example:
            >>> manager = ModelVersionManager()
            >>> model = manager.get_active_model('skill_matching')
            >>> print(model['version'])
            'v1.2.0'
        """
        if db_session is None:
            logger.debug(
                f"No database session provided for get_active_model({model_name}), returning None"
            )
            return None

        try:
            # Query for active, non-experimental model
            active_model = (
                db_session.query(MLModelVersion)
                .filter(
                    MLModelVersion.model_name == model_name,
                    MLModelVersion.is_active == True,
                    MLModelVersion.is_experiment == False,
                )
                .first()
            )

            if active_model:
                model_info = {
                    "id": str(active_model.id),
                    "model_name": active_model.model_name,
                    "version": active_model.version,
                    "file_path": active_model.file_path,
                    "performance_score": float(active_model.performance_score)
                    if active_model.performance_score
                    else None,
                    "model_metadata": active_model.model_metadata or {},
                    "accuracy_metrics": active_model.accuracy_metrics or {},
                    "is_active": active_model.is_active,
                    "is_experiment": active_model.is_experiment,
                }
                logger.info(
                    f"Found active model {model_name}:{active_model.version} "
                    f"(score: {model_info['performance_score']})"
                )
                return model_info
            else:
                logger.warning(f"No active model found for {model_name}")
                return None

        except Exception as e:
            logger.error(
                f"Error getting active model for {model_name}: {e}", exc_info=True
            )
            return None

    def get_experiment_models(
        self, model_name: str, db_session: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all experimental model versions for A/B testing.

        Returns all models marked as experiments for the given model name,
        along with their traffic allocation configuration.

        Args:
            model_name: Name of the model
            db_session: Optional database session for querying

        Returns:
            List of dictionaries with experimental model information

        Example:
            >>> manager = ModelVersionManager()
            >>> experiments = manager.get_experiment_models('skill_matching')
            >>> for exp in experiments:
            ...     print(f"{exp['version']}: {exp['traffic_percentage']}%")
        """
        if db_session is None:
            logger.debug(
                f"No database session provided for get_experiment_models({model_name}), returning []"
            )
            return []

        try:
            # Query for experimental models
            experiment_models = (
                db_session.query(MLModelVersion)
                .filter(
                    MLModelVersion.model_name == model_name,
                    MLModelVersion.is_experiment == True,
                )
                .all()
            )

            experiments = []
            for model in experiment_models:
                # Extract traffic percentage from experiment_config
                traffic_percentage = 0
                if model.experiment_config:
                    traffic_percentage = model.experiment_config.get(
                        "traffic_percentage", 0
                    )

                exp_info = {
                    "id": str(model.id),
                    "model_name": model.model_name,
                    "version": model.version,
                    "file_path": model.file_path,
                    "performance_score": float(model.performance_score)
                    if model.performance_score
                    else None,
                    "traffic_percentage": traffic_percentage,
                    "model_metadata": model.model_metadata or {},
                    "accuracy_metrics": model.accuracy_metrics or {},
                }
                experiments.append(exp_info)

            logger.info(
                f"Found {len(experiments)} experimental models for {model_name}"
            )
            return experiments

        except Exception as e:
            logger.error(
                f"Error getting experiment models for {model_name}: {e}", exc_info=True
            )
            return []

    def allocate_model_for_user(
        self,
        model_name: str,
        user_id: str,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Allocate a model version for a specific user using A/B testing logic.

        This method implements consistent A/B testing allocation by hashing
        the user_id to deterministically assign users to model versions.
        This ensures the same user always gets the same model version.

        Allocation strategy:
        1. Get all active and experimental models
        2. Calculate total traffic allocation (control + experiments)
        3. Hash user_id to get a value 0-100
        4. Assign user to model based on traffic buckets

        Args:
            model_name: Name of the model
            user_id: Unique user identifier for consistent allocation
            db_session: Optional database session for querying

        Returns:
            Dictionary with allocated model information

        Example:
            >>> manager = ModelVersionManager()
            >>> model = manager.allocate_model_for_user('skill_matching', 'user123')
            >>> print(model['version'])
            'v2.0.0-experiment'
        """
        # Get active (control) model
        active_model = self.get_active_model(model_name, db_session)
        if not active_model:
            logger.warning(f"No active model for {model_name}, using fallback")
            return {
                "model_name": model_name,
                "version": self.default_fallback_version,
                "file_path": None,
                "is_fallback": True,
                "allocation_type": "fallback",
            }

        # Get experimental models
        experiments = self.get_experiment_models(model_name, db_session)

        # If no experiments, return active model
        if not experiments:
            logger.debug(f"No experiments for {model_name}, using active model")
            return {
                **active_model,
                "is_fallback": False,
                "allocation_type": "control",
            }

        # Calculate allocation buckets
        # Control model gets remaining traffic after experiments
        total_experiment_traffic = sum(
            exp.get("traffic_percentage", 0) for exp in experiments
        )
        control_traffic = 100 - total_experiment_traffic

        # Hash user_id for consistent allocation
        # Use SHA256 for uniform distribution
        hash_value = int(hashlib.sha256(user_id.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        # Allocate based on traffic buckets
        cumulative_traffic = 0

        # Check experimental models first
        for exp in experiments:
            traffic = exp.get("traffic_percentage", 0)
            cumulative_traffic += traffic
            if bucket < cumulative_traffic:
                logger.info(
                    f"Allocated user {user_id} to experiment {exp['version']} "
                    f"(bucket: {bucket}, traffic: {traffic}%)"
                )
                return {
                    **exp,
                    "is_fallback": False,
                    "allocation_type": "experiment",
                }

        # Default to control model
        logger.info(
            f"Allocated user {user_id} to control {active_model['version']} "
            f"(bucket: {bucket}, control traffic: {control_traffic}%)"
        )
        return {
            **active_model,
            "is_fallback": False,
            "allocation_type": "control",
        }

    def get_all_model_versions(
        self, model_name: str, db_session: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all model versions (both active and experimental) for a model.

        Args:
            model_name: Name of the model
            db_session: Optional database session for querying

        Returns:
            List of all model versions with their metadata

        Example:
            >>> manager = ModelVersionManager()
            >>> versions = manager.get_all_model_versions('skill_matching')
            >>> for v in versions:
            ...     print(f"{v['version']} - active: {v['is_active']}")
        """
        if db_session is None:
            logger.debug(
                f"No database session provided for get_all_model_versions({model_name}), returning []"
            )
            return []

        try:
            # Query all model versions
            all_models = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.model_name == model_name)
                .order_by(MLModelVersion.created_at.desc())
                .all()
            )

            versions = []
            for model in all_models:
                version_info = {
                    "id": str(model.id),
                    "model_name": model.model_name,
                    "version": model.version,
                    "file_path": model.file_path,
                    "performance_score": float(model.performance_score)
                    if model.performance_score
                    else None,
                    "is_active": model.is_active,
                    "is_experiment": model.is_experiment,
                    "experiment_config": model.experiment_config or {},
                    "model_metadata": model.model_metadata or {},
                    "accuracy_metrics": model.accuracy_metrics or {},
                    "created_at": model.created_at.isoformat()
                    if model.created_at
                    else None,
                    "updated_at": model.updated_at.isoformat()
                    if model.updated_at
                    else None,
                }
                versions.append(version_info)

            logger.info(f"Found {len(versions)} total versions for {model_name}")
            return versions

        except Exception as e:
            logger.error(
                f"Error getting all model versions for {model_name}: {e}", exc_info=True
            )
            return []

    def calculate_model_metrics(
        self, model_name: str, db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Calculate aggregate metrics for all versions of a model.

        Computes summary statistics including performance scores,
        accuracy metrics, and A/B testing traffic distribution.

        Args:
            model_name: Name of the model
            db_session: Optional database session for querying

        Returns:
            Dictionary with aggregate metrics

        Example:
            >>> manager = ModelVersionManager()
            >>> metrics = manager.calculate_model_metrics('skill_matching')
            >>> print(metrics['total_versions'])
            3
        """
        versions = self.get_all_model_versions(model_name, db_session)

        if not versions:
            return {
                "model_name": model_name,
                "total_versions": 0,
                "active_version": None,
                "experiment_count": 0,
                "avg_performance_score": 0.0,
                "best_performance_score": 0.0,
                "traffic_distribution": {},
            }

        # Separate active and experimental models
        active_model = next(
            (v for v in versions if v["is_active"] and not v["is_experiment"]), None
        )
        experiments = [v for v in versions if v["is_experiment"]]

        # Calculate performance metrics
        scores = [
            v["performance_score"]
            for v in versions
            if v["performance_score"] is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        best_score = max(scores) if scores else 0.0

        # Build traffic distribution
        traffic_dist = {}
        if active_model:
            traffic_dist["control"] = 100 - sum(
                e.get("experiment_config", {}).get("traffic_percentage", 0)
                for e in experiments
            )
        for exp in experiments:
            traffic_pct = exp.get("experiment_config", {}).get("traffic_percentage", 0)
            if traffic_pct > 0:
                traffic_dist[exp["version"]] = traffic_pct

        return {
            "model_name": model_name,
            "total_versions": len(versions),
            "active_version": active_model["version"] if active_model else None,
            "experiment_count": len(experiments),
            "avg_performance_score": round(avg_score, 2),
            "best_performance_score": round(best_score, 2),
            "traffic_distribution": traffic_dist,
        }

    def recommend_promotion(
        self,
        model_name: str,
        min_performance_improvement: float = 5.0,
        min_sample_size: int = 100,
        significance_level: float = 0.05,
        min_confidence: float = 0.80,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Recommend whether an experimental model should be promoted to active.

        Compares experimental model performance against the active model using
        statistical significance testing and recommends promotion if:
        1. Performance improvement exceeds threshold
        2. Sample size is sufficient for statistical power
        3. Statistical tests show significant improvement
        4. Confidence level meets minimum threshold

        The method uses ABTestAnalyzer for statistical testing, including:
        - Chi-square tests for success/failure rate comparisons
        - T-tests for continuous metric comparisons
        - Effect size calculations (Cohen's d, Cramer's V)
        - Confidence intervals for metric differences

        Args:
            model_name: Name of the model
            min_performance_improvement: Minimum performance gain (%) to recommend promotion
            min_sample_size: Minimum sample size for statistical significance
            significance_level: Significance level (alpha) for hypothesis tests (default: 0.05)
            min_confidence: Minimum confidence level required for promotion (default: 0.80)
            db_session: Optional database session for querying

        Returns:
            Dictionary with promotion recommendation including statistical analysis,
            or None if no models available for comparison

        Example:
            >>> manager = ModelVersionManager()
            >>> rec = manager.recommend_promotion('skill_matching')
            >>> if rec['should_promote']:
            ...     print(f"Promote {rec['experiment_version']} to active")
            ...     print(f"Statistical significance: p={rec['p_value']:.4f}")
        """
        active_model = self.get_active_model(model_name, db_session)
        experiments = self.get_experiment_models(model_name, db_session)

        if not active_model or not experiments:
            logger.debug(
                f"Cannot recommend promotion for {model_name}: "
                f"active={bool(active_model)}, experiments={len(experiments)}"
            )
            return None

        # Import ABTestAnalyzer for statistical testing
        try:
            from analyzers.ab_test_analyzer import ABTestAnalyzer

            ab_analyzer = ABTestAnalyzer(
                default_significance_level=significance_level,
                min_sample_size=min_sample_size,
            )
        except ImportError:
            logger.warning(
                "ABTestAnalyzer not available, falling back to basic comparison"
            )
            ab_analyzer = None

        best_candidate = None
        best_improvement = 0.0
        best_statistical_result = None

        for exp in experiments:
            # Check if experiment has sufficient sample size
            sample_size = exp.get("accuracy_metrics", {}).get("sample_size", 0)
            if sample_size < min_sample_size:
                logger.debug(
                    f"Experiment {exp['version']} has insufficient sample size: {sample_size}"
                )
                continue

            # Compare performance scores
            active_score = active_model.get("performance_score", 0) or 0
            exp_score = exp.get("performance_score", 0) or 0

            if exp_score > active_score:
                improvement = ((exp_score - active_score) / active_score * 100) if active_score > 0 else 0

                # Perform statistical analysis if ABTestAnalyzer is available
                statistical_result = None
                if ab_analyzer:
                    statistical_result = self._analyze_statistical_significance(
                        active_model=active_model,
                        experiment_model=exp,
                        ab_analyzer=ab_analyzer,
                        significance_level=significance_level,
                        db_session=db_session,
                    )

                # Consider both raw improvement and statistical significance
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_candidate = exp
                    best_statistical_result = statistical_result

        # Determine if promotion should be recommended
        should_promote = False
        promotion_reason = ""
        confidence = 0.0
        p_value = 1.0
        effect_size = 0.0
        statistical_tests = {}
        confidence_interval = None

        if best_candidate and best_improvement >= min_performance_improvement:
            if best_statistical_result:
                # Extract statistical analysis results
                confidence = best_statistical_result.get("confidence", 0.0)
                p_value = best_statistical_result.get("p_value", 1.0)
                effect_size = best_statistical_result.get("effect_size", 0.0)
                statistical_tests = best_statistical_result.get("statistical_tests", {})
                confidence_interval = best_statistical_result.get("confidence_interval")

                # Check if statistical criteria are met
                is_significant = best_statistical_result.get("is_significant", False)

                if is_significant and confidence >= min_confidence:
                    should_promote = True
                    promotion_reason = (
                        f"Statistically significant improvement of {best_improvement:.2f}% "
                        f"with {confidence:.0%} confidence (p={p_value:.4f})"
                    )
                elif is_significant:
                    should_promote = True  # Significant but lower confidence
                    promotion_reason = (
                        f"Statistically significant improvement of {best_improvement:.2f}% "
                        f"but confidence ({confidence:.0%}) below threshold ({min_confidence:.0%}). "
                        f"Consider gathering more data."
                    )
                elif best_improvement >= min_performance_improvement * 1.5:
                    # Strong improvement without significance - might be underpowered
                    should_promote = False
                    promotion_reason = (
                        f"Large improvement ({best_improvement:.2f}%) but not statistically "
                        f"significant (p={p_value:.4f}). May need more samples."
                    )
                else:
                    should_promote = False
                    promotion_reason = (
                        f"Improvement of {best_improvement:.2f}% but not statistically "
                        f"significant (p={p_value:.4f}). Continue testing."
                    )
            else:
                # Fallback to basic comparison without statistical testing
                if best_improvement >= min_performance_improvement * 2:
                    should_promote = True
                    confidence = 0.5  # Conservative estimate
                    promotion_reason = (
                        f"Improvement of {best_improvement:.2f}% without statistical "
                        f"testing (ABTestAnalyzer unavailable). Recommend manual review."
                    )
                else:
                    should_promote = False
                    promotion_reason = "Insufficient data for statistical analysis"

        # Build result dictionary
        result = {
            "should_promote": should_promote,
            "model_name": model_name,
            "current_active": active_model["version"] if active_model else None,
            "experiment_version": best_candidate["version"] if best_candidate else None,
            "performance_improvement_pct": round(best_improvement, 2),
            "active_score": active_model.get("performance_score", 0) if active_model else 0,
            "experiment_score": best_candidate.get("performance_score", 0) if best_candidate else 0,
            "reason": promotion_reason,
            # Statistical confidence data
            "statistical_confidence": {
                "confidence": round(confidence, 4),
                "p_value": round(p_value, 6),
                "effect_size": round(effect_size, 4),
                "is_significant": p_value < significance_level,
                "significance_level": significance_level,
                "min_confidence": min_confidence,
                "confidence_interval": list(confidence_interval) if confidence_interval else None,
                "sample_sizes": {
                    "control": active_model.get("accuracy_metrics", {}).get("sample_size", 0) if active_model else 0,
                    "treatment": best_candidate.get("accuracy_metrics", {}).get("sample_size", 0) if best_candidate else 0,
                },
            },
            # Detailed statistical test results
            "statistical_tests": statistical_tests,
            # Recommendation metadata
            "recommendation_metadata": {
                "min_performance_improvement": min_performance_improvement,
                "min_sample_size": min_sample_size,
                "experiments_evaluated": len(experiments),
                "experiments_meeting_threshold": len([
                    e for e in experiments
                    if e.get("accuracy_metrics", {}).get("sample_size", 0) >= min_sample_size
                ]),
            },
        }

        if should_promote:
            logger.info(
                f"Recommending promotion of {best_candidate['version']} "
                f"for {model_name}: {promotion_reason}"
            )
        else:
            logger.info(
                f"No promotion recommended for {model_name}: {promotion_reason}"
            )

        return result

    def _analyze_statistical_significance(
        self,
        active_model: Dict[str, Any],
        experiment_model: Dict[str, Any],
        ab_analyzer: Any,
        significance_level: float,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Perform statistical significance analysis between active and experiment models.

        This internal method uses ABTestAnalyzer to compare models using various
        statistical tests and returns a comprehensive analysis result.

        Args:
            active_model: Dictionary with active model information and metrics
            experiment_model: Dictionary with experiment model information and metrics
            ab_analyzer: ABTestAnalyzer instance for statistical testing
            significance_level: Significance level (alpha) for tests
            db_session: Optional database session for fetching historical data

        Returns:
            Dictionary with statistical analysis results including:
            - confidence: Overall confidence level (0-1)
            - p_value: Most significant p-value from tests
            - effect_size: Effect size measure
            - is_significant: Whether result is statistically significant
            - statistical_tests: Detailed results from individual tests
            - confidence_interval: Confidence interval for the difference
        """
        result = {
            "confidence": 0.0,
            "p_value": 1.0,
            "effect_size": 0.0,
            "is_significant": False,
            "statistical_tests": {},
            "confidence_interval": None,
        }

        try:
            # Extract metrics for both models
            control_metrics = active_model.get("accuracy_metrics", {})
            treatment_metrics = experiment_model.get("accuracy_metrics", {})

            # Get sample sizes
            control_sample = control_metrics.get("sample_size", 0)
            treatment_sample = treatment_metrics.get("sample_size", 0)

            # Try to get data from database if available
            if db_session and active_model.get("id") and experiment_model.get("id"):
                db_comparison = ab_analyzer.analyze_from_database(
                    control_model_id=active_model["id"],
                    treatment_model_id=experiment_model["id"],
                    db_session=db_session,
                    dataset_type="production",
                    significance_level=significance_level,
                )
                if db_comparison:
                    result["confidence"] = db_comparison.confidence
                    result["p_value"] = min(
                        (t.p_value for t in db_comparison.statistical_tests.values()),
                        default=1.0,
                    )
                    result["effect_size"] = max(
                        (t.effect_size or 0 for t in db_comparison.statistical_tests.values()),
                        default=0.0,
                    )
                    result["is_significant"] = db_comparison.confidence >= 0.8
                    result["statistical_tests"] = {
                        k: v.to_dict() if hasattr(v, "to_dict") else v
                        for k, v in db_comparison.statistical_tests.items()
                    }
                    return result

            # Fall back to summary statistics comparison
            if control_sample >= ab_analyzer.min_sample_size and treatment_sample >= ab_analyzer.min_sample_size:
                comparison = ab_analyzer.compare_models(
                    control_model_id=active_model.get("id", "unknown"),
                    treatment_model_id=experiment_model.get("id", "unknown"),
                    control_metrics=control_metrics,
                    treatment_metrics=treatment_metrics,
                    significance_level=significance_level,
                    db_session=None,
                )

                result["confidence"] = comparison.confidence
                result["p_value"] = min(
                    (t.p_value for t in comparison.statistical_tests.values()),
                    default=1.0,
                )
                result["effect_size"] = max(
                    (t.effect_size or 0 for t in comparison.statistical_tests.values()),
                    default=0.0,
                )
                result["is_significant"] = comparison.confidence >= 0.8
                result["statistical_tests"] = {
                    k: v.to_dict() if hasattr(v, "to_dict") else v
                    for k, v in comparison.statistical_tests.items()
                }

                # Extract confidence interval if available
                for test_result in comparison.statistical_tests.values():
                    if test_result.confidence_interval:
                        result["confidence_interval"] = test_result.confidence_interval
                        break

            return result

        except Exception as e:
            logger.error(
                f"Error performing statistical analysis: {e}", exc_info=True
            )
            return result

    def record_performance_metrics(
        self,
        model_version_id: str,
        metrics: Dict[str, Any],
        dataset_type: str = "production",
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Record performance metrics for a model version in the performance history.

        Creates a new ModelPerformanceHistory record with the provided metrics
        and updates the model version's current performance score and accuracy metrics.

        Args:
            model_version_id: UUID of the model version to record metrics for
            metrics: Dictionary containing performance metrics:
                - accuracy: Overall accuracy (0-1)
                - precision: Precision score (0-1)
                - recall: Recall score (0-1)
                - f1_score: F1 score (0-1)
                - auc_score: AUC-ROC score (0-1, optional)
                - sample_size: Number of samples evaluated
                - confusion_matrix: Confusion matrix data (optional)
                - custom_metrics: Additional model-specific metrics (optional)
                - evaluation_metadata: Evaluation details (optional)
            dataset_type: Type of dataset (training, validation, test, production)
            db_session: Optional database session for querying and writing

        Returns:
            Dictionary with recorded performance history information or None on failure

        Example:
            >>> manager = ModelVersionManager()
            >>> metrics = {
            ...     "accuracy": 0.85,
            ...     "precision": 0.82,
            ...     "recall": 0.88,
            ...     "f1_score": 0.85,
            ...     "sample_size": 1000
            ... }
            >>> result = manager.record_performance_metrics(
            ...     model_version_id='uuid-here',
            ...     metrics=metrics,
            ...     dataset_type='production'
            ... )
            >>> print(result['f1_score'])
            0.85
        """
        if db_session is None:
            logger.debug(
                f"No database session provided for record_performance_metrics({model_version_id}), returning None"
            )
            return None

        try:
            # Get the model version
            model_version = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == model_version_id)
                .first()
            )

            if not model_version:
                logger.error(f"Model version {model_version_id} not found")
                return None

            # Get previous performance to calculate delta
            previous_history = (
                db_session.query(ModelPerformanceHistory)
                .filter(
                    ModelPerformanceHistory.model_version_id == model_version_id,
                    ModelPerformanceHistory.dataset_type == dataset_type,
                )
                .order_by(ModelPerformanceHistory.created_at.desc())
                .first()
            )

            previous_score = (
                float(previous_history.f1_score)
                if previous_history and previous_history.f1_score
                else None
            )

            # Calculate performance delta
            current_f1 = metrics.get("f1_score", 0)
            performance_delta = None
            if previous_score is not None:
                performance_delta = current_f1 - previous_score

            # Create performance history record
            performance_record = ModelPerformanceHistory(
                model_version_id=model_version_id,
                dataset_type=dataset_type,
                accuracy=metrics.get("accuracy"),
                precision=metrics.get("precision"),
                recall=metrics.get("recall"),
                f1_score=metrics.get("f1_score"),
                auc_score=metrics.get("auc_score"),
                sample_size=metrics.get("sample_size"),
                confusion_matrix=metrics.get("confusion_matrix"),
                custom_metrics=metrics.get("custom_metrics"),
                performance_delta=performance_delta,
                evaluation_metadata=metrics.get("evaluation_metadata"),
            )

            db_session.add(performance_record)
            db_session.flush()  # Flush to get the ID without committing

            # Update model version's current performance metrics
            # Use F1 score as the primary performance score
            model_version.performance_score = current_f1 * 100  # Convert to 0-100 scale

            # Update accuracy metrics
            accuracy_metrics = {
                "accuracy": metrics.get("accuracy"),
                "precision": metrics.get("precision"),
                "recall": metrics.get("recall"),
                "f1_score": metrics.get("f1_score"),
                "auc_score": metrics.get("auc_score"),
                "sample_size": metrics.get("sample_size"),
                "last_updated": performance_record.created_at.isoformat()
                if performance_record.created_at
                else None,
            }
            model_version.accuracy_metrics = accuracy_metrics

            db_session.commit()

            logger.info(
                f"Recorded performance metrics for model {model_version.model_name}:"
                f"{model_version.version} (F1: {current_f1:.4f}, "
                f"delta: {performance_delta:.4f if performance_delta else 'N/A'})"
            )

            return {
                "id": str(performance_record.id),
                "model_version_id": str(performance_record.model_version_id),
                "dataset_type": performance_record.dataset_type,
                "accuracy": float(performance_record.accuracy)
                if performance_record.accuracy
                else None,
                "precision": float(performance_record.precision)
                if performance_record.precision
                else None,
                "recall": float(performance_record.recall)
                if performance_record.recall
                else None,
                "f1_score": float(performance_record.f1_score)
                if performance_record.f1_score
                else None,
                "auc_score": float(performance_record.auc_score)
                if performance_record.auc_score
                else None,
                "sample_size": performance_record.sample_size,
                "performance_delta": float(performance_record.performance_delta)
                if performance_record.performance_delta
                else None,
                "created_at": performance_record.created_at.isoformat()
                if performance_record.created_at
                else None,
            }

        except Exception as e:
            logger.error(
                f"Error recording performance metrics for model version {model_version_id}: {e}",
                exc_info=True,
            )
            if db_session:
                db_session.rollback()
            return None

    def get_performance_history(
        self,
        model_version_id: str,
        dataset_type: Optional[str] = None,
        limit: int = 100,
        db_session: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get performance history for a model version.

        Retrieves historical performance records for a model version,
        optionally filtered by dataset type.

        Args:
            model_version_id: UUID of the model version
            dataset_type: Optional dataset type filter (training, validation, test, production)
            limit: Maximum number of records to return
            db_session: Optional database session for querying

        Returns:
            List of dictionaries with performance history data

        Example:
            >>> manager = ModelVersionManager()
            >>> history = manager.get_performance_history(
            ...     model_version_id='uuid-here',
            ...     dataset_type='production',
            ...     limit=10
            ... )
            >>> for record in history:
            ...     print(f"{record['created_at']}: F1={record['f1_score']}")
        """
        if db_session is None:
            logger.debug(
                f"No database session provided for get_performance_history({model_version_id}), returning []"
            )
            return []

        try:
            query = db_session.query(ModelPerformanceHistory).filter(
                ModelPerformanceHistory.model_version_id == model_version_id
            )

            if dataset_type:
                query = query.filter(
                    ModelPerformanceHistory.dataset_type == dataset_type
                )

            history_records = (
                query.order_by(ModelPerformanceHistory.created_at.desc())
                .limit(limit)
                .all()
            )

            history = []
            for record in history_records:
                history_info = {
                    "id": str(record.id),
                    "model_version_id": str(record.model_version_id),
                    "dataset_type": record.dataset_type,
                    "accuracy": float(record.accuracy) if record.accuracy else None,
                    "precision": float(record.precision) if record.precision else None,
                    "recall": float(record.recall) if record.recall else None,
                    "f1_score": float(record.f1_score) if record.f1_score else None,
                    "auc_score": float(record.auc_score) if record.auc_score else None,
                    "sample_size": record.sample_size,
                    "performance_delta": float(record.performance_delta)
                    if record.performance_delta
                    else None,
                    "confusion_matrix": record.confusion_matrix or {},
                    "custom_metrics": record.custom_metrics or {},
                    "evaluation_metadata": record.evaluation_metadata or {},
                    "created_at": record.created_at.isoformat()
                    if record.created_at
                    else None,
                }
                history.append(history_info)

            logger.info(
                f"Retrieved {len(history)} performance history records for model version {model_version_id}"
            )
            return history

        except Exception as e:
            logger.error(
                f"Error getting performance history for model version {model_version_id}: {e}",
                exc_info=True,
            )
            return []

    def create_canary_deployment(
        self,
        model_name: str,
        canary_version_id: str,
        initial_traffic_percentage: Optional[float] = None,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a canary deployment for a model version with initial traffic allocation.

        Canary deployments allow gradual rollout of new model versions by routing
        a small percentage of traffic to the new version while monitoring performance.
        This method sets up a model version as a canary with the specified traffic
        allocation (default 10%).

        Args:
            model_name: Name of the model (e.g., 'skill_matching')
            canary_version_id: UUID of the model version to use as canary
            initial_traffic_percentage: Initial traffic percentage for canary (default: 10%)
            db_session: Optional database session for querying and writing

        Returns:
            Dictionary with canary deployment information or None on failure

        Example:
            >>> manager = ModelVersionManager()
            >>> canary = manager.create_canary_deployment(
            ...     model_name='skill_matching',
            ...     canary_version_id='uuid-here',
            ...     initial_traffic_percentage=10
            ... )
            >>> print(canary['traffic_percentage'])
            10
        """
        traffic_pct = initial_traffic_percentage or self.DEFAULT_CANARY_TRAFFIC_PERCENTAGE

        # Validate traffic percentage
        if traffic_pct <= 0 or traffic_pct > self.MAX_CANARY_TRAFFIC_PERCENTAGE:
            logger.error(
                f"Invalid canary traffic percentage: {traffic_pct}. "
                f"Must be between 1 and {self.MAX_CANARY_TRAFFIC_PERCENTAGE}"
            )
            return None

        if db_session is None:
            logger.debug(
                f"No database session provided for create_canary_deployment({model_name}), returning None"
            )
            return None

        try:
            # Get the canary model version
            canary_model = (
                db_session.query(MLModelVersion)
                .filter(
                    MLModelVersion.id == canary_version_id,
                    MLModelVersion.model_name == model_name,
                )
                .first()
            )

            if not canary_model:
                logger.error(
                    f"Canary model version {canary_version_id} not found for {model_name}"
                )
                return None

            # Check for existing active canary
            existing_canary = self.get_canary_model(model_name, db_session)
            if existing_canary:
                logger.warning(
                    f"Existing canary deployment found for {model_name}: "
                    f"{existing_canary['version']}. Rollback first to create new canary."
                )
                return None

            # Get active model to ensure it exists
            active_model = self.get_active_model(model_name, db_session)
            if not active_model:
                logger.error(f"No active model found for {model_name}, cannot create canary")
                return None

            # Update canary model configuration
            canary_model.is_experiment = True
            canary_model.is_active = True  # Canary is active but as experiment

            # Set experiment config with canary settings
            experiment_config = canary_model.experiment_config or {}
            experiment_config.update({
                "traffic_percentage": traffic_pct,
                "is_canary": True,
                "canary_created_at": canary_model.updated_at.isoformat()
                if canary_model.updated_at
                else None,
                "canary_status": "active",
                "canary_stage": "initial",
                "initial_traffic_percentage": traffic_pct,
            })
            canary_model.experiment_config = experiment_config

            db_session.commit()

            logger.info(
                f"Created canary deployment for {model_name}:{canary_model.version} "
                f"with {traffic_pct}% traffic allocation"
            )

            return {
                "id": str(canary_model.id),
                "model_name": canary_model.model_name,
                "version": canary_model.version,
                "file_path": canary_model.file_path,
                "traffic_percentage": traffic_pct,
                "is_canary": True,
                "canary_status": "active",
                "canary_stage": "initial",
                "experiment_config": experiment_config,
                "performance_score": float(canary_model.performance_score)
                if canary_model.performance_score
                else None,
            }

        except Exception as e:
            logger.error(
                f"Error creating canary deployment for {model_name}: {e}", exc_info=True
            )
            if db_session:
                db_session.rollback()
            return None

    def get_canary_model(
        self, model_name: str, db_session: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current canary model for a given model name.

        Returns the active canary deployment if one exists. A canary is identified
        by having is_experiment=True and is_canary=True in experiment_config.

        Args:
            model_name: Name of the model
            db_session: Optional database session for querying

        Returns:
            Dictionary with canary model information or None if no canary exists

        Example:
            >>> manager = ModelVersionManager()
            >>> canary = manager.get_canary_model('skill_matching')
            >>> if canary:
            ...     print(f"Canary version: {canary['version']}, traffic: {canary['traffic_percentage']}%")
        """
        if db_session is None:
            logger.debug(
                f"No database session provided for get_canary_model({model_name}), returning None"
            )
            return None

        try:
            # Query for canary models (experimental with is_canary flag)
            canary_models = (
                db_session.query(MLModelVersion)
                .filter(
                    MLModelVersion.model_name == model_name,
                    MLModelVersion.is_experiment == True,
                )
                .all()
            )

            # Filter for canary deployments
            for model in canary_models:
                if model.experiment_config and model.experiment_config.get("is_canary"):
                    traffic_pct = model.experiment_config.get("traffic_percentage", 0)
                    return {
                        "id": str(model.id),
                        "model_name": model.model_name,
                        "version": model.version,
                        "file_path": model.file_path,
                        "traffic_percentage": traffic_pct,
                        "is_canary": True,
                        "canary_status": model.experiment_config.get("canary_status", "active"),
                        "canary_stage": model.experiment_config.get("canary_stage", "initial"),
                        "experiment_config": model.experiment_config,
                        "performance_score": float(model.performance_score)
                        if model.performance_score
                        else None,
                        "accuracy_metrics": model.accuracy_metrics or {},
                        "model_metadata": model.model_metadata or {},
                    }

            logger.debug(f"No canary deployment found for {model_name}")
            return None

        except Exception as e:
            logger.error(
                f"Error getting canary model for {model_name}: {e}", exc_info=True
            )
            return None

    def increase_canary_traffic(
        self,
        model_name: str,
        increment_percentage: float = 10.0,
        max_traffic_percentage: Optional[float] = None,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Increase traffic to the canary deployment incrementally.

        This method implements gradual traffic shifting by increasing the canary's
        traffic allocation in small increments. Traffic is capped at max_traffic_percentage
        (default 50%) to prevent full rollout without explicit promotion.

        Args:
            model_name: Name of the model
            increment_percentage: Amount to increase traffic by (default: 10%)
            max_traffic_percentage: Maximum traffic percentage allowed (default: 50%)
            db_session: Optional database session for querying and writing

        Returns:
            Dictionary with updated canary information or None on failure

        Example:
            >>> manager = ModelVersionManager()
            >>> result = manager.increase_canary_traffic('skill_matching', increment_percentage=10)
            >>> print(result['traffic_percentage'])
            20  # Increased from 10% to 20%
        """
        max_traffic = max_traffic_percentage or self.MAX_CANARY_TRAFFIC_PERCENTAGE

        if db_session is None:
            logger.debug(
                f"No database session provided for increase_canary_traffic({model_name}), returning None"
            )
            return None

        try:
            # Get current canary model
            canary = self.get_canary_model(model_name, db_session)
            if not canary:
                logger.warning(f"No canary deployment found for {model_name}")
                return None

            # Get the model version record
            canary_model = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == canary["id"])
                .first()
            )

            if not canary_model:
                logger.error(f"Canary model {canary['id']} not found in database")
                return None

            current_traffic = canary.get("traffic_percentage", 0)
            new_traffic = min(current_traffic + increment_percentage, max_traffic)

            if new_traffic == current_traffic:
                logger.info(
                    f"Canary traffic for {model_name} already at maximum allowed: {current_traffic}%"
                )
                return canary

            # Update experiment config
            experiment_config = canary_model.experiment_config or {}
            experiment_config["traffic_percentage"] = new_traffic
            experiment_config["canary_stage"] = self._get_canary_stage(new_traffic)
            experiment_config["previous_traffic_percentage"] = current_traffic
            experiment_config["last_traffic_update"] = canary_model.updated_at.isoformat()
            canary_model.experiment_config = experiment_config

            db_session.commit()

            logger.info(
                f"Increased canary traffic for {model_name}:{canary_model.version} "
                f"from {current_traffic}% to {new_traffic}%"
            )

            return {
                "id": str(canary_model.id),
                "model_name": canary_model.model_name,
                "version": canary_model.version,
                "previous_traffic_percentage": current_traffic,
                "traffic_percentage": new_traffic,
                "is_canary": True,
                "canary_status": experiment_config.get("canary_status", "active"),
                "canary_stage": experiment_config.get("canary_stage"),
                "experiment_config": experiment_config,
            }

        except Exception as e:
            logger.error(
                f"Error increasing canary traffic for {model_name}: {e}", exc_info=True
            )
            if db_session:
                db_session.rollback()
            return None

    def promote_canary_to_production(
        self,
        model_name: str,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Promote the canary deployment to full production.

        This method promotes the canary model to become the new active production model.
        The previous active model is deactivated, and the canary is converted to a
        regular active model with 100% traffic.

        Args:
            model_name: Name of the model
            db_session: Optional database session for querying and writing

        Returns:
            Dictionary with promotion result or None on failure

        Example:
            >>> manager = ModelVersionManager()
            >>> result = manager.promote_canary_to_production('skill_matching')
            >>> print(result['new_active_version'])
            'v2.0.0'
        """
        if db_session is None:
            logger.debug(
                f"No database session provided for promote_canary_to_production({model_name}), returning None"
            )
            return None

        try:
            # Get current canary and active models
            canary = self.get_canary_model(model_name, db_session)
            active = self.get_active_model(model_name, db_session)

            if not canary:
                logger.error(f"No canary deployment found for {model_name}")
                return None

            # Get database records
            canary_model = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == canary["id"])
                .first()
            )

            if not canary_model:
                logger.error(f"Canary model {canary['id']} not found in database")
                return None

            # Deactivate current active model if exists
            if active:
                old_active_model = (
                    db_session.query(MLModelVersion)
                    .filter(MLModelVersion.id == active["id"])
                    .first()
                )
                if old_active_model:
                    old_active_model.is_active = False
                    logger.info(
                        f"Deactivated previous active model {model_name}:{old_active_model.version}"
                    )

            # Promote canary to active production
            previous_version = canary_model.version
            canary_model.is_experiment = False
            canary_model.is_active = True

            # Update experiment config to reflect promotion
            experiment_config = canary_model.experiment_config or {}
            experiment_config["is_canary"] = False
            experiment_config["canary_status"] = "promoted"
            experiment_config["promoted_at"] = canary_model.updated_at.isoformat()
            experiment_config["traffic_percentage"] = 100
            experiment_config["previous_active_version"] = active.get("version") if active else None
            canary_model.experiment_config = experiment_config

            db_session.commit()

            logger.info(
                f"Promoted canary {model_name}:{previous_version} to production"
            )

            return {
                "model_name": model_name,
                "new_active_version": previous_version,
                "previous_active_version": active.get("version") if active else None,
                "promotion_status": "success",
                "traffic_percentage": 100,
                "canary_id": str(canary_model.id),
            }

        except Exception as e:
            logger.error(
                f"Error promoting canary to production for {model_name}: {e}", exc_info=True
            )
            if db_session:
                db_session.rollback()
            return None

    def rollback_canary(
        self,
        model_name: str,
        reason: Optional[str] = None,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Rollback a canary deployment, routing all traffic back to the stable version.

        This method deactivates the canary deployment and restores the previous
        active model to handle 100% of traffic. The canary is marked as rolled back
        for audit purposes.

        Args:
            model_name: Name of the model
            reason: Optional reason for the rollback (for audit trail)
            db_session: Optional database session for querying and writing

        Returns:
            Dictionary with rollback result or None on failure

        Example:
            >>> manager = ModelVersionManager()
            >>> result = manager.rollback_canary('skill_matching', reason='Performance degradation')
            >>> print(result['active_version'])
            'v1.0.0'  # Reverted to stable version
        """
        if db_session is None:
            logger.debug(
                f"No database session provided for rollback_canary({model_name}), returning None"
            )
            return None

        try:
            # Get current canary and active models
            canary = self.get_canary_model(model_name, db_session)
            active = self.get_active_model(model_name, db_session)

            if not canary:
                logger.warning(f"No canary deployment found for {model_name} to rollback")
                return None

            # Get the canary model record
            canary_model = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == canary["id"])
                .first()
            )

            if not canary_model:
                logger.error(f"Canary model {canary['id']} not found in database")
                return None

            rolled_back_version = canary_model.version
            previous_traffic = canary.get("traffic_percentage", 0)

            # Deactivate canary
            canary_model.is_active = False
            canary_model.is_experiment = False

            # Update experiment config to reflect rollback
            experiment_config = canary_model.experiment_config or {}
            experiment_config["is_canary"] = False
            experiment_config["canary_status"] = "rolled_back"
            experiment_config["rolled_back_at"] = canary_model.updated_at.isoformat()
            experiment_config["rollback_reason"] = reason
            experiment_config["previous_traffic_percentage"] = previous_traffic
            canary_model.experiment_config = experiment_config

            # Ensure active model is properly set
            if active:
                active_model = (
                    db_session.query(MLModelVersion)
                    .filter(MLModelVersion.id == active["id"])
                    .first()
                )
                if active_model:
                    active_model.is_active = True
                    active_model.is_experiment = False

            db_session.commit()

            logger.info(
                f"Rolled back canary {model_name}:{rolled_back_version}, "
                f"restored {active.get('version') if active else 'unknown'} as active"
            )

            return {
                "model_name": model_name,
                "rolled_back_version": rolled_back_version,
                "active_version": active.get("version") if active else None,
                "rollback_status": "success",
                "reason": reason,
                "previous_canary_traffic": previous_traffic,
            }

        except Exception as e:
            logger.error(
                f"Error rolling back canary for {model_name}: {e}", exc_info=True
            )
            if db_session:
                db_session.rollback()
            return None

    def get_canary_status(
        self, model_name: str, db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Get the current status of canary deployment for a model.

        Returns comprehensive information about the canary deployment including
        traffic allocation, performance metrics, and deployment stage.

        Args:
            model_name: Name of the model
            db_session: Optional database session for querying

        Returns:
            Dictionary with canary status information

        Example:
            >>> manager = ModelVersionManager()
            >>> status = manager.get_canary_status('skill_matching')
            >>> print(status['canary_active'])
            True
            >>> print(status['traffic_percentage'])
            10
        """
        canary = self.get_canary_model(model_name, db_session)
        active = self.get_active_model(model_name, db_session)

        if not canary:
            return {
                "model_name": model_name,
                "canary_active": False,
                "canary_version": None,
                "active_version": active.get("version") if active else None,
                "traffic_percentage": 0,
                "canary_stage": None,
                "message": "No active canary deployment",
            }

        return {
            "model_name": model_name,
            "canary_active": True,
            "canary_id": canary.get("id"),
            "canary_version": canary.get("version"),
            "active_version": active.get("version") if active else None,
            "traffic_percentage": canary.get("traffic_percentage", 0),
            "canary_stage": canary.get("canary_stage"),
            "canary_status": canary.get("canary_status"),
            "performance_score": canary.get("performance_score"),
            "initial_traffic_percentage": canary.get("experiment_config", {}).get(
                "initial_traffic_percentage"
            ),
            "experiment_config": canary.get("experiment_config"),
        }

    def _get_canary_stage(self, traffic_percentage: float) -> str:
        """
        Determine the canary stage based on traffic percentage.

        Args:
            traffic_percentage: Current traffic percentage allocated to canary

        Returns:
            String describing the canary stage
        """
        if traffic_percentage <= 10:
            return "initial"
        elif traffic_percentage <= 25:
            return "early"
        elif traffic_percentage <= 40:
            return "mid"
        elif traffic_percentage < 50:
            return "advanced"
        else:
            return "pre_promotion"

    def promote_challenger_to_champion(
        self,
        model_name: str,
        challenger_version_id: str,
        min_performance_improvement: float = 5.0,
        min_sample_size: int = 100,
        significance_level: float = 0.05,
        min_confidence: float = 0.80,
        force: bool = False,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Promote a challenger (experimental) model to champion (active) with A/B test validation.

        This method implements the champion/challenger pattern for model promotion,
        using statistical significance testing to determine if the challenger should
        replace the current champion model.

        The promotion process:
        1. Validates that the challenger exists and is an experimental model
        2. Gets the current champion (active) model
        3. Performs A/B test statistical analysis comparing champion vs challenger
        4. Promotes challenger if it meets criteria (or force=True)
        5. Demotes champion to inactive status

        Args:
            model_name: Name of the model (e.g., 'skill_matching')
            challenger_version_id: UUID of the challenger model version to promote
            min_performance_improvement: Minimum performance gain (%) required for promotion
            min_sample_size: Minimum sample size for statistical significance
            significance_level: Significance level (alpha) for hypothesis tests
            min_confidence: Minimum confidence level required for auto-promotion
            force: If True, skip statistical validation and force promotion
            db_session: Database session for querying and writing

        Returns:
            Dictionary with promotion result including:
            - success: Whether promotion was successful
            - model_name: The model name
            - challenger_version: The promoted challenger version
            - previous_champion_version: The previous champion version
            - statistical_analysis: A/B test analysis results (if not forced)
            - promotion_reason: Reason for promotion decision
            - promoted_at: Timestamp of promotion

        Raises:
            ValueError: If challenger not found or not an experimental model

        Example:
            >>> manager = ModelVersionManager()
            >>> result = manager.promote_challenger_to_champion(
            ...     model_name='skill_matching',
            ...     challenger_version_id='uuid-here',
            ...     min_confidence=0.85
            ... )
            >>> if result['success']:
            ...     print(f"Promoted {result['challenger_version']} to champion")
            ...     print(f"Statistical confidence: {result['statistical_analysis']['confidence']:.2%}")
        """
        if db_session is None:
            return {
                "success": False,
                "model_name": model_name,
                "error": "No database session provided",
                "challenger_version": None,
                "previous_champion_version": None,
            }

        try:
            # Get the challenger model
            challenger_model = (
                db_session.query(MLModelVersion)
                .filter(
                    MLModelVersion.id == challenger_version_id,
                    MLModelVersion.model_name == model_name,
                )
                .first()
            )

            if not challenger_model:
                logger.error(
                    f"Challenger model {challenger_version_id} not found for {model_name}"
                )
                return {
                    "success": False,
                    "model_name": model_name,
                    "error": f"Challenger model version {challenger_version_id} not found",
                    "challenger_version": None,
                    "previous_champion_version": None,
                }

            # Get the current champion model
            champion_model = (
                db_session.query(MLModelVersion)
                .filter(
                    MLModelVersion.model_name == model_name,
                    MLModelVersion.is_active == True,
                    MLModelVersion.is_experiment == False,
                )
                .first()
            )

            previous_champion_version = champion_model.version if champion_model else None
            challenger_version = challenger_model.version

            # Prepare statistical analysis result
            statistical_analysis = None
            should_promote = False
            promotion_reason = ""

            if force:
                # Force promotion without statistical validation
                should_promote = True
                promotion_reason = "Forced promotion - statistical validation bypassed"
                logger.warning(
                    f"Force promoting challenger {model_name}:{challenger_version} "
                    "without statistical validation"
                )
            else:
                # Perform A/B test statistical analysis
                recommendation = self.recommend_promotion(
                    model_name=model_name,
                    min_performance_improvement=min_performance_improvement,
                    min_sample_size=min_sample_size,
                    significance_level=significance_level,
                    min_confidence=min_confidence,
                    db_session=db_session,
                )

                if recommendation is None:
                    return {
                        "success": False,
                        "model_name": model_name,
                        "error": "No models available for comparison",
                        "challenger_version": challenger_version,
                        "previous_champion_version": previous_champion_version,
                    }

                # Check if the recommended challenger matches the requested one
                recommended_version = recommendation.get("experiment_version")
                if recommended_version != challenger_version:
                    # Check if our specific challenger is a candidate
                    experiments = self.get_experiment_models(model_name, db_session)
                    challenger_exists = any(
                        str(e["id"]) == str(challenger_version_id)
                        for e in experiments
                    )

                    if not challenger_exists:
                        return {
                            "success": False,
                            "model_name": model_name,
                            "error": f"Challenger {challenger_version} is not an experimental model",
                            "challenger_version": challenger_version,
                            "previous_champion_version": previous_champion_version,
                        }

                    # Calculate stats for this specific challenger
                    challenger_data = next(
                        (e for e in experiments if str(e["id"]) == str(challenger_version_id)),
                        None
                    )

                    if challenger_data and champion_model:
                        # Build metrics for comparison
                        champion_metrics = champion_model.accuracy_metrics or {}
                        challenger_metrics = challenger_data.get("accuracy_metrics", {})

                        champion_score = champion_model.performance_score or 0
                        challenger_score = challenger_data.get("performance_score", 0) or 0

                        improvement = 0
                        if champion_score > 0:
                            improvement = (challenger_score - champion_score) / champion_score * 100

                        statistical_analysis = {
                            "champion_score": float(champion_score),
                            "challenger_score": float(challenger_score),
                            "improvement_pct": round(improvement, 2),
                            "sample_sizes": {
                                "champion": champion_metrics.get("sample_size", 0),
                                "challenger": challenger_metrics.get("sample_size", 0),
                            },
                            "meets_threshold": improvement >= min_performance_improvement,
                            "confidence": 0.0,
                            "is_significant": False,
                        }

                        if improvement >= min_performance_improvement:
                            should_promote = True
                            promotion_reason = (
                                f"Challenger shows {improvement:.2f}% improvement over champion. "
                                f"Meets minimum threshold of {min_performance_improvement}%."
                            )
                        else:
                            promotion_reason = (
                                f"Challenger improvement ({improvement:.2f}%) below "
                                f"minimum threshold ({min_performance_improvement}%)."
                            )
                else:
                    # The requested challenger is the recommended one
                    should_promote = recommendation.get("should_promote", False)
                    promotion_reason = recommendation.get("reason", "No reason provided")

                    statistical_confidence = recommendation.get("statistical_confidence", {})
                    statistical_analysis = {
                        "champion_score": recommendation.get("active_score", 0),
                        "challenger_score": recommendation.get("experiment_score", 0),
                        "improvement_pct": recommendation.get("performance_improvement_pct", 0),
                        "sample_sizes": statistical_confidence.get("sample_sizes", {}),
                        "meets_threshold": should_promote,
                        "confidence": statistical_confidence.get("confidence", 0),
                        "p_value": statistical_confidence.get("p_value", 1),
                        "effect_size": statistical_confidence.get("effect_size", 0),
                        "is_significant": statistical_confidence.get("is_significant", False),
                        "significance_level": statistical_confidence.get("significance_level", 0.05),
                        "confidence_interval": statistical_confidence.get("confidence_interval"),
                        "statistical_tests": recommendation.get("statistical_tests", {}),
                    }

            # Perform promotion if criteria met
            if should_promote:
                # Demote current champion if exists
                if champion_model:
                    champion_model.is_active = False
                    champion_model.is_experiment = False
                    logger.info(
                        f"Demoted champion {model_name}:{previous_champion_version}"
                    )

                # Promote challenger to champion
                challenger_model.is_active = True
                challenger_model.is_experiment = False

                # Update experiment config to reflect promotion
                experiment_config = challenger_model.experiment_config or {}
                experiment_config["promotion_type"] = "champion_challenger"
                experiment_config["promoted_at"] = challenger_model.updated_at.isoformat()
                experiment_config["previous_champion_version"] = previous_champion_version
                experiment_config["promotion_reason"] = promotion_reason
                experiment_config["was_forced"] = force
                challenger_model.experiment_config = experiment_config

                db_session.commit()

                logger.info(
                    f"Promoted challenger {model_name}:{challenger_version} to champion. "
                    f"Reason: {promotion_reason}"
                )

                return {
                    "success": True,
                    "model_name": model_name,
                    "challenger_version": challenger_version,
                    "challenger_id": str(challenger_model.id),
                    "previous_champion_version": previous_champion_version,
                    "statistical_analysis": statistical_analysis,
                    "promotion_reason": promotion_reason,
                    "forced": force,
                    "promoted_at": challenger_model.updated_at.isoformat(),
                }
            else:
                # Promotion criteria not met
                logger.info(
                    f"Challenger {model_name}:{challenger_version} promotion rejected. "
                    f"Reason: {promotion_reason}"
                )

                return {
                    "success": False,
                    "model_name": model_name,
                    "challenger_version": challenger_version,
                    "challenger_id": str(challenger_model.id),
                    "previous_champion_version": previous_champion_version,
                    "statistical_analysis": statistical_analysis,
                    "promotion_reason": promotion_reason,
                    "forced": False,
                    "promoted_at": None,
                }

        except Exception as e:
            logger.error(
                f"Error promoting challenger to champion for {model_name}: {e}",
                exc_info=True
            )
            if db_session:
                db_session.rollback()
            return {
                "success": False,
                "model_name": model_name,
                "error": str(e),
                "challenger_version": None,
                "previous_champion_version": None,
            }

    def get_champion_challenger_status(
        self,
        model_name: str,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Get the current champion/challenger status for a model.

        Returns information about the current champion (active) model and any
        challenger (experimental) models, including performance comparison.

        Args:
            model_name: Name of the model
            db_session: Database session for querying

        Returns:
            Dictionary with champion and challenger status

        Example:
            >>> manager = ModelVersionManager()
            >>> status = manager.get_champion_challenger_status('skill_matching')
            >>> print(f"Champion: {status['champion']['version']}")
            >>> print(f"Challengers: {len(status['challengers'])}")
        """
        if db_session is None:
            return {
                "model_name": model_name,
                "champion": None,
                "challengers": [],
                "has_challenger": False,
            }

        try:
            # Get champion (active, non-experimental)
            champion = self.get_active_model(model_name, db_session)

            # Get challengers (experimental models)
            challengers = self.get_experiment_models(model_name, db_session)

            # Calculate comparison metrics if both exist
            comparison = None
            if champion and challengers:
                champion_score = champion.get("performance_score", 0) or 0
                best_challenger = max(
                    challengers,
                    key=lambda c: c.get("performance_score", 0) or 0
                )
                challenger_score = best_challenger.get("performance_score", 0) or 0

                if champion_score > 0:
                    improvement_pct = (challenger_score - champion_score) / champion_score * 100
                else:
                    improvement_pct = 0 if challenger_score == 0 else 100

                comparison = {
                    "best_challenger_version": best_challenger.get("version"),
                    "best_challenger_score": challenger_score,
                    "champion_score": champion_score,
                    "improvement_pct": round(improvement_pct, 2),
                }

            return {
                "model_name": model_name,
                "champion": champion,
                "challengers": challengers,
                "has_challenger": len(challengers) > 0,
                "challenger_count": len(challengers),
                "comparison": comparison,
            }

        except Exception as e:
            logger.error(
                f"Error getting champion/challenger status for {model_name}: {e}",
                exc_info=True
            )
            return {
                "model_name": model_name,
                "champion": None,
                "challengers": [],
                "has_challenger": False,
                "error": str(e),
            }
