from __future__ import annotations

import argparse
import logging
import shutil
import time
from dataclasses import dataclass

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import Ridge

from src.features import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, NUMERICAL_COLUMNS, TARGET_COLUMN
from src.utils import load_params, write_json, write_text

logger = logging.getLogger(__name__)


def rmspe(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 0
    if not np.any(mask):
        return 0.0
    pct_errors = ((y_true[mask] - y_pred[mask]) / y_true[mask]) ** 2
    return float(np.sqrt(np.mean(pct_errors)))


def build_preprocessor() -> ColumnTransformer:
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    numerical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler(with_mean=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("categorical", categorical_transformer, CATEGORICAL_COLUMNS),
            ("numerical", numerical_transformer, NUMERICAL_COLUMNS),
        ]
    )


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "mape": float(mean_absolute_percentage_error(y_true + 1e-6, y_pred + 1e-6)),
        "r2": float(r2_score(y_true, y_pred)),
        "rmspe": float(rmspe(y_true, y_pred)),
    }


def build_candidates(random_state: int) -> dict[str, Pipeline]:
    preprocessor = build_preprocessor()
    return {
        "ridge": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", Ridge(alpha=1.0, random_state=random_state)),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=80,
                        max_depth=18,
                        min_samples_leaf=2,
                        n_jobs=-1,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
        "extra_trees": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    ExtraTreesRegressor(
                        n_estimators=120,
                        max_depth=20,
                        min_samples_leaf=2,
                        n_jobs=-1,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
    }


@dataclass
class TrainingResult:
    best_model_name: str
    best_metrics: dict[str, float]
    run_id: str
    model_uri: str
    best_pipeline: Pipeline
    comparison: list[dict]


def train_models(params_path: str) -> TrainingResult:
    params = load_params(params_path)
    train_params = params["training"]
    dataset_params = params["dataset"]

    train_frame = pd.read_csv(dataset_params["train_processed_path"], low_memory=False)
    validation_frame = pd.read_csv(
        dataset_params["validation_processed_path"], low_memory=False
    )

    sample_rows = min(train_params["sample_rows"], len(train_frame))
    sampled_train = train_frame.sample(sample_rows, random_state=train_params["random_state"])

    x_train = sampled_train[FEATURE_COLUMNS]
    y_train = sampled_train[TARGET_COLUMN].values
    x_validation = validation_frame[FEATURE_COLUMNS]
    y_validation = validation_frame[TARGET_COLUMN].values

    mlflow.set_tracking_uri(train_params["tracking_uri"])
    mlflow.set_experiment(train_params["experiment_name"])

    comparison: list[dict] = []
    best_model_name = ""
    best_metrics: dict[str, float] | None = None
    best_run_id = ""
    best_model_uri = ""
    best_pipeline: Pipeline | None = None

    for model_name, pipeline in build_candidates(train_params["random_state"]).items():
        started = time.perf_counter()
        logger.info("Training candidate model: %s", model_name)
        with mlflow.start_run(run_name=model_name) as run:
            mlflow.log_params(
                {
                    "model_name": model_name,
                    "sample_rows": sample_rows,
                    "validation_rows": int(len(validation_frame)),
                    "feature_count": len(FEATURE_COLUMNS),
                    "target": TARGET_COLUMN,
                }
            )

            pipeline.fit(x_train, y_train)
            predictions = pipeline.predict(x_validation)
            metrics = evaluate_predictions(y_validation, predictions)
            mlflow.log_metrics(metrics)
            mlflow.log_metric(
                "training_duration_seconds", round(time.perf_counter() - started, 3)
            )
            model_info = mlflow.sklearn.log_model(
                sk_model=pipeline,
                artifact_path="model",
                registered_model_name=None,
            )

            record = {
                "model_name": model_name,
                "run_id": run.info.run_id,
                "metrics": metrics,
            }
            comparison.append(record)
            logger.info("Completed model=%s run_id=%s rmspe=%.4f", model_name, run.info.run_id, metrics["rmspe"])

            if best_metrics is None or metrics["rmspe"] < best_metrics["rmspe"]:
                best_metrics = metrics
                best_model_name = model_name
                best_run_id = run.info.run_id
                best_model_uri = "models/serving_model"
                best_pipeline = pipeline

    assert best_metrics is not None
    assert best_pipeline is not None

    shutil.rmtree(best_model_uri, ignore_errors=True)
    mlflow.sklearn.save_model(
        sk_model=best_pipeline,
        path=best_model_uri,
    )

    return TrainingResult(
        best_model_name=best_model_name,
        best_metrics=best_metrics,
        run_id=best_run_id,
        model_uri=best_model_uri,
        best_pipeline=best_pipeline,
        comparison=comparison,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", default="params.yaml")
    args = parser.parse_args()

    from src.utils import configure_logging

    configure_logging()
    started = time.perf_counter()
    params = load_params(args.params)
    result = train_models(args.params)
    summary = {
        "best_model_name": result.best_model_name,
        "best_run_id": result.run_id,
        "best_model_uri": result.model_uri,
        "best_metrics": result.best_metrics,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "training_rows_used": min(
            params["training"]["sample_rows"],
            int(pd.read_csv(params["dataset"]["train_processed_path"], usecols=["Store"]).shape[0]),
        ),
    }
    write_json("reports/training_summary.json", summary)
    write_json("reports/model_comparison.json", {"candidates": result.comparison})
    write_text("models/latest_model_uri.txt", result.model_uri)
    write_json(
        "models/model_registry.json",
        {
            "model_name": result.best_model_name,
            "run_id": result.run_id,
            "model_uri": result.model_uri,
            "metrics": result.best_metrics,
        },
    )
    print(summary)


if __name__ == "__main__":
    main()
