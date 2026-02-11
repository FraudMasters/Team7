"""
MLflow experiment tracking service for logging ML experiments.

This module provides a comprehensive MLflow integration layer for tracking
machine learning experiments, including:
- Experiment and run management
- Parameter and metric logging
- Model artifact registration
- Integration with model versioning system
- Support for both local and remote MLflow tracking servers
"""
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# MLflow import with graceful fallback
try:
    import mlflow
    from mlflow.entities import Experiment, Run
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    mlflow = None
    MlflowClient = None
    Experiment = None
    Run = None
    logger.warning(
        "MLflow is not installed. Experiment tracking will be disabled. "
        "Install mlflow package to enable experiment tracking."
    )


class MLflowExperimentTracker:
    """
    MLflow experiment tracking service for logging ML experiments.

    This class provides methods to manage MLflow experiments, log parameters,
    metrics, and model artifacts. It integrates with the model versioning
    system for seamless experiment tracking during model training.

    Attributes:
        tracking_uri: URI of the MLflow tracking server
        registry_uri: URI of the MLflow model registry
        default_experiment_name: Default name for experiments

    Example:
        >>> tracker = MLflowExperimentTracker(tracking_uri="http://localhost:5000")
        >>> with tracker.start_run("skill_matching_training") as run:
        ...     tracker.log_params({"learning_rate": 0.01, "epochs": 100})
        ...     tracker.log_metrics({"accuracy": 0.95, "f1_score": 0.93})
        ...     tracker.log_model(model, "model")
    """

    # Default experiment naming convention
    DEFAULT_EXPERIMENT_PREFIX = "agenthr"

    # Default artifact location
    DEFAULT_ARTIFACT_ROOT = "./mlruns"

    # Model registration stages
    MODEL_STAGES = ["None", "Staging", "Production", "Archived"]

    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        registry_uri: Optional[str] = None,
        default_experiment_name: Optional[str] = None,
        artifact_root: Optional[str] = None,
    ) -> None:
        """
        Initialize the MLflow experiment tracker.

        Args:
            tracking_uri: URI of the MLflow tracking server
                         (e.g., "http://localhost:5000", "sqlite:///mlflow.db")
                         If None, uses MLFLOW_TRACKING_URI env var or defaults to local
            registry_uri: URI of the MLflow model registry
                         If None, uses MLFLOW_REGISTRY_URI env var or defaults to tracking_uri
            default_experiment_name: Default experiment name prefix
            artifact_root: Root directory for storing artifacts (for local tracking)
        """
        self._mlflow_available = MLFLOW_AVAILABLE
        self._client = None
        self._active_run = None

        # Configure tracking URI
        self.tracking_uri = tracking_uri or os.environ.get(
            "MLFLOW_TRACKING_URI", None
        )
        self.registry_uri = registry_uri or os.environ.get(
            "MLFLOW_REGISTRY_URI", self.tracking_uri
        )
        self.artifact_root = artifact_root or os.environ.get(
            "MLFLOW_ARTIFACT_ROOT", self.DEFAULT_ARTIFACT_ROOT
        )

        # Set default experiment name
        self.default_experiment_name = default_experiment_name or self.DEFAULT_EXPERIMENT_PREFIX

        # Initialize MLflow if available
        if self._mlflow_available:
            self._initialize_mlflow()

    def _initialize_mlflow(self) -> None:
        """
        Initialize MLflow tracking client with configured settings.
        """
        try:
            if self.tracking_uri:
                mlflow.set_tracking_uri(self.tracking_uri)
                logger.info(f"MLflow tracking URI set to: {self.tracking_uri}")

            self._client = MlflowClient(tracking_uri=self.tracking_uri)
            logger.info("MLflow client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MLflow client: {e}", exc_info=True)
            self._mlflow_available = False

    @property
    def is_available(self) -> bool:
        """Check if MLflow is available and properly configured."""
        return self._mlflow_available and self._client is not None

    def get_or_create_experiment(
        self,
        experiment_name: str,
        artifact_location: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Get an existing experiment or create a new one if it doesn't exist.

        Args:
            experiment_name: Name of the experiment
            artifact_location: Optional custom artifact location
            tags: Optional tags to attach to the experiment

        Returns:
            Experiment ID string or None if MLflow is unavailable

        Example:
            >>> tracker = MLflowExperimentTracker()
            >>> exp_id = tracker.get_or_create_experiment("skill_matching_v2")
            >>> print(exp_id)
            '1'
        """
        if not self.is_available:
            logger.debug("MLflow not available, skipping experiment creation")
            return None

        try:
            # Normalize experiment name
            full_name = f"{self.default_experiment_name}_{experiment_name}" if not experiment_name.startswith(self.default_experiment_name) else experiment_name

            # Check if experiment exists
            experiment = self._client.get_experiment_by_name(full_name)

            if experiment:
                logger.info(f"Found existing experiment: {full_name} (ID: {experiment.experiment_id})")
                return experiment.experiment_id

            # Create new experiment
            exp_id = self._client.create_experiment(
                name=full_name,
                artifact_location=artifact_location,
                tags=tags or {},
            )
            logger.info(f"Created new experiment: {full_name} (ID: {exp_id})")
            return exp_id

        except Exception as e:
            logger.error(f"Error getting/creating experiment {experiment_name}: {e}", exc_info=True)
            return None

    @contextmanager
    def start_run(
        self,
        experiment_name: str,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        nested: bool = False,
    ):
        """
        Context manager for starting and managing an MLflow run.

        This method provides a convenient way to start a run, log data,
        and automatically end the run when the context exits.

        Args:
            experiment_name: Name of the experiment
            run_name: Optional name for this specific run
            tags: Optional tags to attach to the run
            description: Optional description of the run
            nested: Whether this is a nested run

        Yields:
            The MLflow run object or None if MLflow unavailable

        Example:
            >>> tracker = MLflowExperimentTracker()
            >>> with tracker.start_run("model_training", run_name="run_001") as run:
            ...     tracker.log_params({"lr": 0.01})
            ...     tracker.log_metrics({"accuracy": 0.95})
        """
        if not self.is_available:
            logger.debug("MLflow not available, yielding None context")
            yield None
            return

        run = None
        try:
            # Get or create experiment
            experiment_id = self.get_or_create_experiment(experiment_name)

            # Set experiment for this run
            if experiment_id:
                mlflow.set_experiment(experiment_id=experiment_id)

            # Start the run
            run = mlflow.start_run(
                run_name=run_name,
                tags=tags,
                description=description,
                nested=nested,
            )
            self._active_run = run

            # Log system information
            self._log_system_info()

            logger.info(f"Started MLflow run: {run.info.run_id} in experiment {experiment_name}")
            yield run

        except Exception as e:
            logger.error(f"Error in MLflow run context: {e}", exc_info=True)
            yield None

        finally:
            if run and mlflow.active_run():
                mlflow.end_run()
                self._active_run = None
                logger.info(f"Ended MLflow run: {run.info.run_id}")

    def log_params(self, params: Dict[str, Any]) -> bool:
        """
        Log multiple parameters for the current run.

        Args:
            params: Dictionary of parameter names and values

        Returns:
            True if logging succeeded, False otherwise

        Example:
            >>> tracker.log_params({
            ...     "learning_rate": 0.01,
            ...     "batch_size": 32,
            ...     "epochs": 100
            ... })
        """
        if not self.is_available or not mlflow.active_run():
            logger.debug("MLflow not available or no active run, skipping param logging")
            return False

        try:
            # Convert all values to strings for MLflow
            str_params = {k: str(v) for k, v in params.items()}
            mlflow.log_params(str_params)
            logger.debug(f"Logged {len(params)} parameters to MLflow")
            return True

        except Exception as e:
            logger.error(f"Error logging parameters to MLflow: {e}", exc_info=True)
            return False

    def log_param(self, key: str, value: Any) -> bool:
        """
        Log a single parameter for the current run.

        Args:
            key: Parameter name
            value: Parameter value

        Returns:
            True if logging succeeded, False otherwise
        """
        return self.log_params({key: value})

    def log_metrics(
        self,
        metrics: Dict[str, float],
        step: Optional[int] = None,
        timestamp: Optional[int] = None,
    ) -> bool:
        """
        Log multiple metrics for the current run.

        Args:
            metrics: Dictionary of metric names and values
            step: Optional training step number
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            True if logging succeeded, False otherwise

        Example:
            >>> tracker.log_metrics({
            ...     "accuracy": 0.95,
            ...     "precision": 0.93,
            ...     "recall": 0.97,
            ...     "f1_score": 0.95
            ... }, step=100)
        """
        if not self.is_available or not mlflow.active_run():
            logger.debug("MLflow not available or no active run, skipping metric logging")
            return False

        try:
            mlflow.log_metrics(metrics, step=step, timestamp=timestamp)
            logger.debug(f"Logged {len(metrics)} metrics to MLflow" + (f" at step {step}" if step else ""))
            return True

        except Exception as e:
            logger.error(f"Error logging metrics to MLflow: {e}", exc_info=True)
            return False

    def log_metric(
        self,
        key: str,
        value: float,
        step: Optional[int] = None,
    ) -> bool:
        """
        Log a single metric for the current run.

        Args:
            key: Metric name
            value: Metric value
            step: Optional training step number

        Returns:
            True if logging succeeded, False otherwise
        """
        return self.log_metrics({key: value}, step=step)

    def log_artifact(
        self,
        local_path: str,
        artifact_path: Optional[str] = None,
    ) -> bool:
        """
        Log a local file as an artifact.

        Args:
            local_path: Path to the local file
            artifact_path: Optional directory path within the artifact directory

        Returns:
            True if logging succeeded, False otherwise

        Example:
            >>> tracker.log_artifact("./confusion_matrix.png", "plots")
        """
        if not self.is_available or not mlflow.active_run():
            logger.debug("MLflow not available or no active run, skipping artifact logging")
            return False

        try:
            mlflow.log_artifact(local_path, artifact_path=artifact_path)
            logger.info(f"Logged artifact: {local_path}" + (f" to {artifact_path}" if artifact_path else ""))
            return True

        except Exception as e:
            logger.error(f"Error logging artifact to MLflow: {e}", exc_info=True)
            return False

    def log_artifacts(
        self,
        local_dir: str,
        artifact_path: Optional[str] = None,
    ) -> bool:
        """
        Log all files in a directory as artifacts.

        Args:
            local_dir: Path to the local directory
            artifact_path: Optional directory path within the artifact directory

        Returns:
            True if logging succeeded, False otherwise
        """
        if not self.is_available or not mlflow.active_run():
            logger.debug("MLflow not available or no active run, skipping artifacts logging")
            return False

        try:
            mlflow.log_artifacts(local_dir, artifact_path=artifact_path)
            logger.info(f"Logged artifacts from: {local_dir}" + (f" to {artifact_path}" if artifact_path else ""))
            return True

        except Exception as e:
            logger.error(f"Error logging artifacts to MLflow: {e}", exc_info=True)
            return False

    def log_model(
        self,
        model: Any,
        artifact_path: str,
        model_type: str = "sklearn",
        registered_model_name: Optional[str] = None,
        signature: Optional[Any] = None,
        input_example: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Log a model as an artifact with optional registration.

        Args:
            model: The model object to log
            artifact_path: Path within the artifact directory
            model_type: Type of model (sklearn, tensorflow, pytorch, etc.)
            registered_model_name: Optional name to register in model registry
            signature: Optional model signature for input/output schema
            input_example: Optional example input for model documentation
            metadata: Optional additional metadata

        Returns:
            Model URI if successful, None otherwise

        Example:
            >>> model_uri = tracker.log_model(
            ...     trained_model,
            ...     "model",
            ...     model_type="sklearn",
            ...     registered_model_name="skill_matching_model"
            ... )
        """
        if not self.is_available or not mlflow.active_run():
            logger.debug("MLflow not available or no active run, skipping model logging")
            return None

        try:
            # Get the appropriate logging function based on model type
            log_model_func = self._get_log_model_function(model_type)

            if log_model_func is None:
                logger.warning(f"Unknown model type: {model_type}, using generic artifact logging")
                # Fall back to pickling the model
                import pickle
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
                    pickle.dump(model, f)
                    temp_path = f.name

                self.log_artifact(temp_path, artifact_path)
                os.unlink(temp_path)
                return f"runs:/{mlflow.active_run().info.run_id}/{artifact_path}"

            # Log model with MLflow flavor
            model_info = log_model_func(
                model,
                artifact_path,
                registered_model_name=registered_model_name,
                signature=signature,
                input_example=input_example,
                metadata=metadata,
            )

            model_uri = f"runs:/{mlflow.active_run().info.run_id}/{artifact_path}"
            logger.info(
                f"Logged {model_type} model to MLflow at {artifact_path}" +
                (f", registered as '{registered_model_name}'" if registered_model_name else "")
            )

            return model_uri

        except Exception as e:
            logger.error(f"Error logging model to MLflow: {e}", exc_info=True)
            return None

    def _get_log_model_function(self, model_type: str):
        """Get the appropriate MLflow log_model function for the model type."""
        if not self._mlflow_available:
            return None

        model_type_lower = model_type.lower()

        # Map model types to MLflow logging functions
        log_model_map = {
            "sklearn": mlflow.sklearn.log_model,
            "scikit-learn": mlflow.sklearn.log_model,
            "tensorflow": mlflow.tensorflow.log_model,
            "tf": mlflow.tensorflow.log_model,
            "pytorch": mlflow.pytorch.log_model,
            "torch": mlflow.pytorch.log_model,
            "keras": mlflow.keras.log_model,
            "xgboost": mlflow.xgboost.log_model,
            "xgb": mlflow.xgboost.log_model,
            "lightgbm": mlflow.lightgbm.log_model,
            "lgbm": mlflow.lightgbm.log_model,
            "catboost": None,  # May need custom handling
            "onnx": None,  # May need custom handling
            "custom": None,
        }

        return log_model_map.get(model_type_lower)

    def log_figure(
        self,
        figure: Any,
        artifact_file: str,
    ) -> bool:
        """
        Log a matplotlib or plotly figure as an artifact.

        Args:
            figure: The figure object to log
            artifact_file: Filename for the artifact

        Returns:
            True if logging succeeded, False otherwise
        """
        if not self.is_available or not mlflow.active_run():
            logger.debug("MLflow not available or no active run, skipping figure logging")
            return False

        try:
            mlflow.log_figure(figure, artifact_file)
            logger.info(f"Logged figure: {artifact_file}")
            return True

        except Exception as e:
            logger.error(f"Error logging figure to MLflow: {e}", exc_info=True)
            return False

    def log_dict(
        self,
        dictionary: Dict[str, Any],
        artifact_file: str,
    ) -> bool:
        """
        Log a dictionary as a JSON artifact.

        Args:
            dictionary: The dictionary to log
            artifact_file: Filename for the artifact

        Returns:
            True if logging succeeded, False otherwise
        """
        if not self.is_available or not mlflow.active_run():
            logger.debug("MLflow not available or no active run, skipping dict logging")
            return False

        try:
            mlflow.log_dict(dictionary, artifact_file)
            logger.info(f"Logged dictionary: {artifact_file}")
            return True

        except Exception as e:
            logger.error(f"Error logging dict to MLflow: {e}", exc_info=True)
            return False

    def set_tags(self, tags: Dict[str, str]) -> bool:
        """
        Set multiple tags for the current run.

        Args:
            tags: Dictionary of tag names and values

        Returns:
            True if tagging succeeded, False otherwise
        """
        if not self.is_available or not mlflow.active_run():
            logger.debug("MLflow not available or no active run, skipping tag setting")
            return False

        try:
            mlflow.set_tags(tags)
            logger.debug(f"Set {len(tags)} tags in MLflow")
            return True

        except Exception as e:
            logger.error(f"Error setting tags in MLflow: {e}", exc_info=True)
            return False

    def set_tag(self, key: str, value: str) -> bool:
        """
        Set a single tag for the current run.

        Args:
            key: Tag name
            value: Tag value

        Returns:
            True if tagging succeeded, False otherwise
        """
        return self.set_tags({key: value})

    def _log_system_info(self) -> None:
        """Log system and environment information as tags."""
        if not self.is_available or not mlflow.active_run():
            return

        try:
            import platform
            import sys

            system_tags = {
                "system.os": platform.system(),
                "system.python_version": platform.python_version(),
                "system.platform": platform.platform(),
                "mlflow.tracking_uri": str(self.tracking_uri or "local"),
            }

            # Add any relevant environment variables (non-sensitive)
            for env_var in ["MLFLOW_EXPERIMENT_NAME"]:
                if env_var in os.environ:
                    system_tags[f"env.{env_var.lower()}"] = os.environ[env_var]

            self.set_tags(system_tags)

        except Exception as e:
            logger.debug(f"Could not log system info: {e}")

    def get_experiment_runs(
        self,
        experiment_name: str,
        max_results: int = 100,
        order_by: Optional[List[str]] = None,
        filter_string: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all runs for an experiment.

        Args:
            experiment_name: Name of the experiment
            max_results: Maximum number of runs to return
            order_by: Optional list of columns to order by
            filter_string: Optional filter string for runs

        Returns:
            List of run dictionaries with run info and metrics

        Example:
            >>> runs = tracker.get_experiment_runs("skill_matching")
            >>> for run in runs:
            ...     print(f"{run['run_id']}: accuracy={run['metrics'].get('accuracy')}")
        """
        if not self.is_available:
            logger.debug("MLflow not available, returning empty runs list")
            return []

        try:
            # Get experiment
            full_name = f"{self.default_experiment_name}_{experiment_name}" if not experiment_name.startswith(self.default_experiment_name) else experiment_name
            experiment = self._client.get_experiment_by_name(full_name)

            if not experiment:
                logger.debug(f"Experiment {experiment_name} not found")
                return []

            # Search runs
            runs = self._client.search_runs(
                experiment_ids=[experiment.experiment_id],
                max_results=max_results,
                order_by=order_by or ["start_time DESC"],
                filter_string=filter_string,
            )

            # Convert to dictionaries
            run_list = []
            for run in runs:
                run_info = {
                    "run_id": run.info.run_id,
                    "run_name": run.info.run_name,
                    "experiment_id": run.info.experiment_id,
                    "status": run.info.status,
                    "start_time": datetime.fromtimestamp(run.info.start_time / 1000).isoformat() if run.info.start_time else None,
                    "end_time": datetime.fromtimestamp(run.info.end_time / 1000).isoformat() if run.info.end_time else None,
                    "artifact_uri": run.info.artifact_uri,
                    "lifecycle_stage": run.info.lifecycle_stage,
                    "params": dict(run.data.params),
                    "metrics": {k: float(v) for k, v in run.data.metrics.items()},
                    "tags": dict(run.data.tags),
                }
                run_list.append(run_info)

            logger.info(f"Retrieved {len(run_list)} runs for experiment {experiment_name}")
            return run_list

        except Exception as e:
            logger.error(f"Error getting experiment runs: {e}", exc_info=True)
            return []

    def get_best_run(
        self,
        experiment_name: str,
        metric_key: str,
        maximize: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the best run for an experiment based on a metric.

        Args:
            experiment_name: Name of the experiment
            metric_key: Name of the metric to optimize
            maximize: Whether to maximize (True) or minimize (False) the metric

        Returns:
            Best run dictionary or None if no runs found

        Example:
            >>> best_run = tracker.get_best_run("model_training", "accuracy", maximize=True)
            >>> print(f"Best accuracy: {best_run['metrics']['accuracy']}")
        """
        order = [f"metrics.{metric_key} DESC"] if maximize else [f"metrics.{metric_key} ASC"]

        runs = self.get_experiment_runs(
            experiment_name,
            max_results=1,
            order_by=order,
        )

        if runs:
            logger.info(f"Found best run for {experiment_name} by {metric_key}")
            return runs[0]

        return None

    def register_model(
        self,
        model_uri: str,
        model_name: str,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        await_registration_for: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """
        Register a model in the MLflow Model Registry.

        Args:
            model_uri: URI of the model to register (e.g., "runs:/<run_id>/model")
            model_name: Name to register the model under
            tags: Optional tags for the registered model
            description: Optional description of the model
            await_registration_for: Seconds to wait for registration to complete

        Returns:
            Dictionary with model version info or None on failure

        Example:
            >>> result = tracker.register_model(
            ...     "runs:/abc123/model",
            ...     "skill_matching_model",
            ...     tags={"stage": "production"},
            ...     description="Best performing model"
            ... )
        """
        if not self.is_available:
            logger.debug("MLflow not available, skipping model registration")
            return None

        try:
            # Register the model
            model_version = self._client.create_model_version(
                name=model_name,
                source=model_uri,
                tags=tags,
                description=description,
                await_creation_for=await_registration_for,
            )

            result = {
                "name": model_version.name,
                "version": model_version.version,
                "source": model_version.source,
                "status": model_version.status,
                "creation_timestamp": datetime.fromtimestamp(
                    model_version.creation_timestamp / 1000
                ).isoformat() if model_version.creation_timestamp else None,
                "description": model_version.description,
                "tags": dict(model_version.tags) if model_version.tags else {},
            }

            logger.info(f"Registered model {model_name} version {model_version.version}")
            return result

        except Exception as e:
            logger.error(f"Error registering model: {e}", exc_info=True)
            return None

    def transition_model_stage(
        self,
        model_name: str,
        version: str,
        stage: str,
        archive_existing: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Transition a registered model to a different stage.

        Args:
            model_name: Name of the registered model
            version: Version number of the model
            stage: Target stage (None, Staging, Production, Archived)
            archive_existing: Whether to archive existing production models

        Returns:
            Dictionary with model version info or None on failure

        Example:
            >>> result = tracker.transition_model_stage(
            ...     "skill_matching_model",
            ...     "1",
            ...     "Production"
            ... )
        """
        if not self.is_available:
            logger.debug("MLflow not available, skipping model stage transition")
            return None

        if stage not in self.MODEL_STAGES:
            logger.error(f"Invalid stage: {stage}. Must be one of {self.MODEL_STAGES}")
            return None

        try:
            model_version = self._client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
                archive_existing_versions=archive_existing,
            )

            result = {
                "name": model_version.name,
                "version": model_version.version,
                "current_stage": model_version.current_stage,
                "source": model_version.source,
                "status": model_version.status,
            }

            logger.info(f"Transitioned {model_name} v{version} to {stage}")
            return result

        except Exception as e:
            logger.error(f"Error transitioning model stage: {e}", exc_info=True)
            return None

    def get_registered_model_versions(
        self,
        model_name: str,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all versions of a registered model.

        Args:
            model_name: Name of the registered model
            max_results: Maximum number of versions to return

        Returns:
            List of model version dictionaries

        Example:
            >>> versions = tracker.get_registered_model_versions("skill_matching_model")
            >>> for v in versions:
            ...     print(f"v{v['version']}: {v['current_stage']}")
        """
        if not self.is_available:
            logger.debug("MLflow not available, returning empty versions list")
            return []

        try:
            versions = self._client.search_model_versions(
                filter_string=f"name='{model_name}'",
                max_results=max_results,
            )

            version_list = []
            for mv in versions:
                version_info = {
                    "name": mv.name,
                    "version": mv.version,
                    "current_stage": mv.current_stage,
                    "source": mv.source,
                    "status": mv.status,
                    "creation_timestamp": datetime.fromtimestamp(
                        mv.creation_timestamp / 1000
                    ).isoformat() if mv.creation_timestamp else None,
                    "last_updated_timestamp": datetime.fromtimestamp(
                        mv.last_updated_timestamp / 1000
                    ).isoformat() if mv.last_updated_timestamp else None,
                    "description": mv.description,
                    "tags": dict(mv.tags) if mv.tags else {},
                    "run_id": mv.run_id,
                    "run_link": mv.run_link,
                }
                version_list.append(version_info)

            logger.info(f"Retrieved {len(version_list)} versions for model {model_name}")
            return version_list

        except Exception as e:
            logger.error(f"Error getting registered model versions: {e}", exc_info=True)
            return []

    def get_production_model(
        self,
        model_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current production version of a registered model.

        Args:
            model_name: Name of the registered model

        Returns:
            Production model version dictionary or None if no production model

        Example:
            >>> prod_model = tracker.get_production_model("skill_matching_model")
            >>> if prod_model:
            ...     print(f"Production version: {prod_model['version']}")
        """
        versions = self.get_registered_model_versions(model_name)

        for version in versions:
            if version.get("current_stage") == "Production":
                logger.info(f"Found production model {model_name} v{version['version']}")
                return version

        logger.debug(f"No production model found for {model_name}")
        return None

    def log_training_run(
        self,
        experiment_name: str,
        model_name: str,
        model_version: str,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        training_metadata: Optional[Dict[str, Any]] = None,
        model_path: Optional[str] = None,
        register_model: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Convenience method to log a complete training run.

        This method combines common operations for logging a training run
        including parameters, metrics, and optional model registration.

        Args:
            experiment_name: Name of the experiment
            model_name: Name of the model being trained
            model_version: Version identifier for the model
            params: Training parameters
            metrics: Evaluation metrics
            training_metadata: Optional additional metadata
            model_path: Optional path to the trained model
            register_model: Whether to register the model in the registry

        Returns:
            Dictionary with run info and model URI, or None on failure

        Example:
            >>> result = tracker.log_training_run(
            ...     experiment_name="skill_matching_v2",
            ...     model_name="skill_matching",
            ...     model_version="v2.0.0",
            ...     params={"learning_rate": 0.01, "epochs": 100},
            ...     metrics={"accuracy": 0.95, "f1_score": 0.93},
            ...     model_path="./models/skill_matching_v2.pkl",
            ...     register_model=True
            ... )
        """
        if not self.is_available:
            logger.debug("MLflow not available, skipping training run logging")
            return None

        result = {
            "experiment_name": experiment_name,
            "model_name": model_name,
            "model_version": model_version,
            "run_id": None,
            "model_uri": None,
            "registered": False,
        }

        try:
            with self.start_run(
                experiment_name,
                run_name=f"{model_name}_{model_version}",
                tags={
                    "model_name": model_name,
                    "model_version": model_version,
                },
            ) as run:
                if not run:
                    return result

                result["run_id"] = run.info.run_id

                # Log parameters
                self.log_params(params)
                self.log_param("model_version", model_version)

                # Log metrics
                self.log_metrics(metrics)

                # Log training metadata
                if training_metadata:
                    self.log_dict(training_metadata, "training_metadata.json")
                    self.set_tags({
                        "training.trigger": training_metadata.get("trigger", "manual"),
                        "training.dataset": training_metadata.get("dataset", "unknown"),
                    })

                # Log model if path provided
                model_uri = None
                if model_path:
                    model_uri = self.log_model(
                        model_path,
                        "model",
                        registered_model_name=model_name if register_model else None,
                    )
                    result["model_uri"] = model_uri
                    result["registered"] = register_model and model_uri is not None

                logger.info(
                    f"Logged training run for {model_name}:{model_version} "
                    f"(run_id: {result['run_id']}, registered: {result['registered']})"
                )

                return result

        except Exception as e:
            logger.error(f"Error logging training run: {e}", exc_info=True)
            return result

    def compare_runs(
        self,
        run_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Compare multiple runs across their parameters and metrics.

        Args:
            run_ids: List of run IDs to compare

        Returns:
            Dictionary with comparison data

        Example:
            >>> comparison = tracker.compare_runs(["run1", "run2"])
            >>> print(comparison["metrics"]["accuracy"])
            {"run1": 0.95, "run2": 0.93}
        """
        if not self.is_available:
            logger.debug("MLflow not available, returning empty comparison")
            return {"runs": [], "params": {}, "metrics": {}}

        try:
            runs_data = []
            all_params = set()
            all_metrics = set()

            for run_id in run_ids:
                run = self._client.get_run(run_id)

                run_info = {
                    "run_id": run.info.run_id,
                    "run_name": run.info.run_name,
                    "status": run.info.status,
                    "start_time": datetime.fromtimestamp(
                        run.info.start_time / 1000
                    ).isoformat() if run.info.start_time else None,
                    "params": dict(run.data.params),
                    "metrics": {k: float(v) for k, v in run.data.metrics.items()},
                }

                all_params.update(run.data.params.keys())
                all_metrics.update(run.data.metrics.keys())
                runs_data.append(run_info)

            # Create comparison matrices
            params_comparison = {}
            for param in sorted(all_params):
                params_comparison[param] = {
                    run["run_id"]: run["params"].get(param)
                    for run in runs_data
                }

            metrics_comparison = {}
            for metric in sorted(all_metrics):
                metrics_comparison[metric] = {
                    run["run_id"]: run["metrics"].get(metric)
                    for run in runs_data
                }

            return {
                "runs": runs_data,
                "params": params_comparison,
                "metrics": metrics_comparison,
            }

        except Exception as e:
            logger.error(f"Error comparing runs: {e}", exc_info=True)
            return {"runs": [], "params": {}, "metrics": {}}

    def delete_run(
        self,
        run_id: str,
    ) -> bool:
        """
        Delete (trash) a run.

        Args:
            run_id: ID of the run to delete

        Returns:
            True if deletion succeeded, False otherwise
        """
        if not self.is_available:
            logger.debug("MLflow not available, skipping run deletion")
            return False

        try:
            self._client.delete_run(run_id)
            logger.info(f"Deleted run: {run_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting run: {e}", exc_info=True)
            return False

    def restore_run(
        self,
        run_id: str,
    ) -> bool:
        """
        Restore a deleted run.

        Args:
            run_id: ID of the run to restore

        Returns:
            True if restoration succeeded, False otherwise
        """
        if not self.is_available:
            logger.debug("MLflow not available, skipping run restoration")
            return False

        try:
            self._client.restore_run(run_id)
            logger.info(f"Restored run: {run_id}")
            return True

        except Exception as e:
            logger.error(f"Error restoring run: {e}", exc_info=True)
            return False


# Singleton instance for convenience
_tracker_instance: Optional[MLflowExperimentTracker] = None


def get_mlflow_tracker(
    tracking_uri: Optional[str] = None,
    **kwargs,
) -> MLflowExperimentTracker:
    """
    Get or create the global MLflowExperimentTracker instance.

    Args:
        tracking_uri: Optional tracking URI (only used on first call)
        **kwargs: Additional arguments for MLflowExperimentTracker

    Returns:
        Global MLflowExperimentTracker instance

    Example:
        >>> tracker = get_mlflow_tracker()
        >>> with tracker.start_run("experiment") as run:
        ...     tracker.log_metric("accuracy", 0.95)
    """
    global _tracker_instance

    if _tracker_instance is None:
        _tracker_instance = MLflowExperimentTracker(
            tracking_uri=tracking_uri,
            **kwargs,
        )

    return _tracker_instance
