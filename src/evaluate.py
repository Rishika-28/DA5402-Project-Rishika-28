from __future__ import annotations

import argparse
import logging
import time

import mlflow
import numpy as np
import pandas as pd

from src.features import FEATURE_COLUMNS, TARGET_COLUMN
from src.train import evaluate_predictions
from src.utils import load_params, read_json, write_json

logger = logging.getLogger(__name__)


def detect_drift(
    baseline: dict,
    current_frame: pd.DataFrame,
    threshold_zscore: float,
) -> dict:
    drifted_features: list[dict] = []
    for feature_name, info in baseline.items():
        if info["dtype"] != "numeric":
            continue
        current_mean = float(current_frame[feature_name].mean())
        z_score = abs(current_mean - info["mean"]) / max(float(info["std"]), 1e-6)
        if z_score >= threshold_zscore:
            drifted_features.append(
                {
                    "feature": feature_name,
                    "baseline_mean": info["mean"],
                    "current_mean": current_mean,
                    "z_score_shift": z_score,
                }
            )
    return {
        "drift_detected": len(drifted_features) > 0,
        "drifted_features": drifted_features,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", default="params.yaml")
    args = parser.parse_args()

    from src.utils import configure_logging

    configure_logging()
    started = time.perf_counter()
    params = load_params(args.params)
    dataset_params = params["dataset"]
    monitor_params = params["monitoring"]
    train_params = params["training"]

    validation_frame = pd.read_csv(dataset_params["validation_processed_path"], low_memory=False)
    baseline = read_json(dataset_params["feature_baseline_path"], {})
    model_uri = PathLike.read_text(train_params["model_uri_output_path"])

    mlflow.set_tracking_uri(train_params["tracking_uri"])
    model = mlflow.pyfunc.load_model(model_uri)
    logger.info("Loaded model uri=%s for evaluation", model_uri)

    predictions = model.predict(validation_frame[FEATURE_COLUMNS])
    metrics = evaluate_predictions(validation_frame[TARGET_COLUMN].values, predictions)
    prediction_frame = validation_frame[["Store", "Date", TARGET_COLUMN]].copy()
    prediction_frame["PredictedSales"] = predictions
    prediction_frame.to_csv(train_params["prediction_output_path"], index=False)

    drift_report = detect_drift(
        baseline=baseline,
        current_frame=validation_frame[FEATURE_COLUMNS],
        threshold_zscore=monitor_params["drift_threshold_zscore"],
    )
    logger.info("Evaluation complete. Drift detected=%s", drift_report["drift_detected"])
    write_json(monitor_params["drift_report_path"], drift_report)
    write_json("reports/evaluation_metrics.json", metrics)
    write_json(
        "reports/api_examples.json",
        {
            "forecast_request": {
                "store": 1,
                "date": "2015-08-01",
                "day_of_week": 6,
                "open": 1,
                "promo": 1,
                "state_holiday": "0",
                "school_holiday": 1,
            },
            "feedback_request": {
                "store": 1,
                "date": "2015-08-01",
                "predicted_sales": 5400.0,
                "actual_sales": 5250.0,
            },
        },
    )
    write_json(
        "reports/pipeline_summary.json",
        {
            "stages": [
                read_json("reports/prepare_summary.json", {}),
                read_json("reports/training_summary.json", {}),
                {
                    "stage": "evaluate_model",
                    "duration_seconds": round(time.perf_counter() - started, 3),
                    "throughput_rows_per_second": round(
                        len(validation_frame) / max(round(time.perf_counter() - started, 3), 0.001),
                        2,
                    ),
                    "metrics": metrics,
                    "drift_detected": drift_report["drift_detected"],
                },
            ],
            "generated_at": pd.Timestamp.utcnow(),
        },
    )
    print(metrics)


class PathLike:
    @staticmethod
    def read_text(path: str) -> str:
        with open(path, "r", encoding="utf-8") as file:
            return file.read().strip()


if __name__ == "__main__":
    main()
