"""Model registry wrapper — logs runs to MLflow.

Usage:
    from argus.models.registry import log_run, load_latest

    log_run(
        run_name="farrington_ca_v1",
        params={"z_threshold": 1.96, "warmup": 15},
        metrics={"sensitivity": 0.6, "specificity": 0.9},
    )

MLflow server defaults to a local file store under `mlruns/` unless the
MLFLOW_TRACKING_URI environment variable is set.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any

_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "./mlruns")


@contextmanager
def _mlflow_session():
    """Yield an active MLflow run, or a null context if MLflow is missing."""
    try:
        import mlflow
    except ImportError:
        yield None
        return
    mlflow.set_tracking_uri(_TRACKING_URI)
    mlflow.set_experiment("argus")
    with mlflow.start_run():
        yield mlflow


def log_run(
    run_name: str,
    params: dict[str, Any],
    metrics: dict[str, float],
) -> None:
    """Log a model run to MLflow. No-op if MLflow is not installed."""
    with _mlflow_session() as mlflow:
        if mlflow is None:
            return
        mlflow.set_tag("run_name", run_name)
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)


def list_runs() -> list[dict[str, Any]]:
    """Return all runs as a list of dicts. Empty if MLflow not installed."""
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except ImportError:
        return []
    mlflow.set_tracking_uri(_TRACKING_URI)
    client = MlflowClient()
    experiment = client.get_experiment_by_name("argus")
    if experiment is None:
        return []
    runs = client.search_runs(experiment_ids=[experiment.experiment_id])
    return [
        {
            "run_id": r.info.run_id,
            "name": r.data.tags.get("run_name", r.info.run_id),
            "params": r.data.params,
            "metrics": r.data.metrics,
        }
        for r in runs
    ]