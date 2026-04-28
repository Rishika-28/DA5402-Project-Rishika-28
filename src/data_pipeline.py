from __future__ import annotations

import argparse
import logging
import time

import pandas as pd

from src.features import (
    DATE_COLUMN,
    FEATURE_COLUMNS,
    PreparedData,
    build_feature_frame,
    compute_baseline_statistics,
    compute_schema_report,
    split_train_validation,
)
from src.utils import load_params, write_json

logger = logging.getLogger(__name__)


def read_source_data(train_path: str, store_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df = pd.read_csv(train_path, low_memory=False)
    store_df = pd.read_csv(store_path, low_memory=False)
    return train_df, store_df


def prepare_dataset(params_path: str) -> PreparedData:
    params = load_params(params_path)
    dataset_params = params["dataset"]
    split_params = params["split"]

    train_df, store_df = read_source_data(
        dataset_params["train_path"], dataset_params["store_path"]
    )
    logger.info("Loaded source data: train=%s store=%s", train_df.shape, store_df.shape)
    schema_report = compute_schema_report(train_df, store_df)
    feature_frame = build_feature_frame(train_df, store_df)
    train_frame, validation_frame = split_train_validation(
        feature_frame, split_params["validation_days"]
    )
    baseline = compute_baseline_statistics(train_frame, FEATURE_COLUMNS)
    return PreparedData(
        train_frame=train_frame,
        validation_frame=validation_frame,
        baseline_statistics=baseline,
        schema_report=schema_report,
    )


def persist_prepared_data(prepared_data: PreparedData, params_path: str) -> dict:
    params = load_params(params_path)
    dataset_params = params["dataset"]

    prepared_data.train_frame.to_csv(
        dataset_params["train_processed_path"], index=False
    )
    prepared_data.validation_frame.to_csv(
        dataset_params["validation_processed_path"], index=False
    )
    write_json(dataset_params["feature_baseline_path"], prepared_data.baseline_statistics)
    write_json(dataset_params["schema_report_path"], prepared_data.schema_report)

    return {
        "train_rows": int(prepared_data.train_frame.shape[0]),
        "validation_rows": int(prepared_data.validation_frame.shape[0]),
        "train_date_min": prepared_data.train_frame[DATE_COLUMN].min(),
        "train_date_max": prepared_data.train_frame[DATE_COLUMN].max(),
        "validation_date_min": prepared_data.validation_frame[DATE_COLUMN].min(),
        "validation_date_max": prepared_data.validation_frame[DATE_COLUMN].max(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--params", default="params.yaml")
    args = parser.parse_args()

    if args.command == "prepare":
        from src.utils import configure_logging

        configure_logging()
        started = time.perf_counter()
        prepared_data = prepare_dataset(args.params)
        summary = persist_prepared_data(prepared_data, args.params)
        logger.info("Prepared dataset with train=%s validation=%s", summary["train_rows"], summary["validation_rows"])
        summary["stage"] = "prepare_data"
        summary["duration_seconds"] = round(time.perf_counter() - started, 3)
        summary["throughput_rows_per_second"] = round(
            (summary["train_rows"] + summary["validation_rows"]) / summary["duration_seconds"],
            2,
        )
        write_json("reports/prepare_summary.json", summary)
        print(summary)


if __name__ == "__main__":
    main()
