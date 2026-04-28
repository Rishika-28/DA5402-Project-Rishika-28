from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


TARGET_COLUMN = "Sales"
DATE_COLUMN = "Date"


FEATURE_COLUMNS = [
    "Store",
    "DayOfWeek",
    "Open",
    "Promo",
    "SchoolHoliday",
    "StateHoliday",
    "StoreType",
    "Assortment",
    "CompetitionDistance",
    "CompetitionOpenSinceMonth",
    "CompetitionOpenSinceYear",
    "Promo2",
    "Promo2SinceWeek",
    "Promo2SinceYear",
    "Year",
    "Month",
    "Day",
    "WeekOfYear",
    "IsWeekend",
    "IsMonthStart",
    "IsMonthEnd",
    "CompetitionOpenMonths",
    "Promo2Active",
]

CATEGORICAL_COLUMNS = [
    "StateHoliday",
    "StoreType",
    "Assortment",
]

NUMERICAL_COLUMNS = [
    column for column in FEATURE_COLUMNS if column not in CATEGORICAL_COLUMNS
]


@dataclass
class PreparedData:
    train_frame: pd.DataFrame
    validation_frame: pd.DataFrame
    baseline_statistics: dict
    schema_report: dict


def build_feature_frame(train_df: pd.DataFrame, store_df: pd.DataFrame) -> pd.DataFrame:
    df = train_df.copy()
    stores = store_df.copy()

    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], format="%Y-%m-%d")
    stores["CompetitionDistance"] = stores["CompetitionDistance"].fillna(
        stores["CompetitionDistance"].median()
    )

    merged = df.merge(stores, on="Store", how="left", validate="many_to_one")

    merged["Open"] = merged["Open"].fillna(1).astype(int)
    merged["Promo"] = merged["Promo"].fillna(0).astype(int)
    merged["SchoolHoliday"] = merged["SchoolHoliday"].fillna(0).astype(int)
    merged["StateHoliday"] = merged["StateHoliday"].fillna("0").astype(str)
    merged["StoreType"] = merged["StoreType"].fillna("unknown").astype(str)
    merged["Assortment"] = merged["Assortment"].fillna("unknown").astype(str)
    merged["Promo2"] = merged["Promo2"].fillna(0).astype(int)

    for column in [
        "CompetitionOpenSinceMonth",
        "CompetitionOpenSinceYear",
        "Promo2SinceWeek",
        "Promo2SinceYear",
    ]:
        merged[column] = merged[column].fillna(0).astype(int)

    merged["Year"] = merged[DATE_COLUMN].dt.year
    merged["Month"] = merged[DATE_COLUMN].dt.month
    merged["Day"] = merged[DATE_COLUMN].dt.day
    merged["WeekOfYear"] = merged[DATE_COLUMN].dt.isocalendar().week.astype(int)
    merged["IsWeekend"] = merged["DayOfWeek"].isin([6, 7]).astype(int)
    merged["IsMonthStart"] = merged[DATE_COLUMN].dt.is_month_start.astype(int)
    merged["IsMonthEnd"] = merged[DATE_COLUMN].dt.is_month_end.astype(int)

    month_diff = (
        (merged["Year"] - merged["CompetitionOpenSinceYear"]) * 12
        + (merged["Month"] - merged["CompetitionOpenSinceMonth"])
    )
    merged["CompetitionOpenMonths"] = np.where(
        (merged["CompetitionOpenSinceYear"] > 0) & (month_diff > 0),
        month_diff,
        0,
    )

    merged["Promo2Active"] = np.where(
        (merged["Promo2"] == 1)
        & (
            (merged["Year"] > merged["Promo2SinceYear"])
            | (
                (merged["Year"] == merged["Promo2SinceYear"])
                & (merged["WeekOfYear"] >= merged["Promo2SinceWeek"])
            )
        ),
        1,
        0,
    )

    merged["LogSales"] = np.log1p(merged[TARGET_COLUMN].clip(lower=0))
    return merged


def split_train_validation(
    feature_frame: pd.DataFrame, validation_days: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    max_date = feature_frame[DATE_COLUMN].max()
    cutoff_date = max_date - pd.Timedelta(days=validation_days)
    train_frame = feature_frame[feature_frame[DATE_COLUMN] <= cutoff_date].copy()
    validation_frame = feature_frame[feature_frame[DATE_COLUMN] > cutoff_date].copy()
    return train_frame, validation_frame


def compute_baseline_statistics(frame: pd.DataFrame, feature_columns: Iterable[str]) -> dict:
    baseline: dict[str, dict] = {}
    for column in feature_columns:
        series = frame[column]
        if pd.api.types.is_numeric_dtype(series):
            baseline[column] = {
                "dtype": "numeric",
                "mean": float(series.mean()),
                "std": float(series.std(ddof=0) or 1.0),
                "min": float(series.min()),
                "max": float(series.max()),
            }
        else:
            distribution = (
                series.astype(str).value_counts(normalize=True).sort_index().to_dict()
            )
            baseline[column] = {
                "dtype": "categorical",
                "distribution": distribution,
            }
    return baseline


def compute_schema_report(train_df: pd.DataFrame, store_df: pd.DataFrame) -> dict:
    return {
        "train_rows": int(train_df.shape[0]),
        "train_columns": list(train_df.columns),
        "store_rows": int(store_df.shape[0]),
        "store_columns": list(store_df.columns),
        "missing_values": {
            "train": train_df.isna().sum().to_dict(),
            "store": store_df.isna().sum().to_dict(),
        },
    }

