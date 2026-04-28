from __future__ import annotations

import os
import time
import logging

import mlflow
import pandas as pd
from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.schemas import ForecastRequest, ForecastResponse
from app.service_common import get_model_metadata, get_params
from src.features import FEATURE_COLUMNS
from src.utils import append_jsonl, read_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


REQUEST_COUNT = Counter("model_service_requests_total", "Total model service requests")
REQUEST_LATENCY = Histogram(
    "model_service_request_latency_seconds", "Model service request latency"
)
DRIFT_EVENTS = Counter("model_service_drift_events_total", "Detected drift events")
FAILURE_COUNT = Counter("model_service_failures_total", "Failed model service requests")

app = FastAPI(title="Rossmann Model Service", version="1.0.0")


def build_inference_frame(payload: ForecastRequest) -> pd.DataFrame:
    store_frame = pd.read_csv("data/store.csv", low_memory=False)
    matched_store = store_frame[store_frame["Store"] == payload.store]
    if matched_store.empty:
        raise HTTPException(status_code=404, detail=f"Store {payload.store} not found")

    store_row = matched_store.iloc[0].to_dict()
    request_row = {
        "Store": payload.store,
        "DayOfWeek": payload.day_of_week,
        "Date": payload.date,
        "Open": payload.open,
        "Promo": payload.promo,
        "StateHoliday": payload.state_holiday,
        "SchoolHoliday": payload.school_holiday,
        "Sales": 0,
        "Customers": 0,
    }
    raw = pd.DataFrame([{**request_row, **store_row}])
    from src.features import build_feature_frame

    engineered = build_feature_frame(
        raw[
            [
                "Store",
                "DayOfWeek",
                "Date",
                "Sales",
                "Customers",
                "Open",
                "Promo",
                "StateHoliday",
                "SchoolHoliday",
            ]
        ],
        raw[
            [
                "Store",
                "StoreType",
                "Assortment",
                "CompetitionDistance",
                "CompetitionOpenSinceMonth",
                "CompetitionOpenSinceYear",
                "Promo2",
                "Promo2SinceWeek",
                "Promo2SinceYear",
                "PromoInterval",
            ]
        ],
    )
    return engineered[FEATURE_COLUMNS]


def detect_request_drift(inference_frame: pd.DataFrame) -> bool:
    params = get_params()
    baseline = read_json(params["dataset"]["feature_baseline_path"], {})
    threshold = params["monitoring"]["drift_threshold_zscore"]

    for feature_name, info in baseline.items():
        if info.get("dtype") != "numeric":
            continue
        current_mean = float(inference_frame[feature_name].mean())
        z_score = abs(current_mean - info["mean"]) / max(float(info["std"]), 1e-6)
        if z_score >= threshold:
            return True
    return False


@app.on_event("startup")
def startup() -> None:
    params = get_params()
    model_uri_path = params["training"]["model_uri_output_path"]
    with open(model_uri_path, "r", encoding="utf-8") as file:
        model_uri = file.read().strip()
    tracking_uri = params["training"]["tracking_uri"]
    mlflow.set_tracking_uri(tracking_uri)
    app.state.model = mlflow.pyfunc.load_model(model_uri)
    app.state.ready = True
    logger.info("Model service ready with model_uri=%s", model_uri)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    return {"ready": bool(getattr(app.state, "ready", False))}


@app.post("/predict", response_model=ForecastResponse)
def predict(payload: ForecastRequest) -> ForecastResponse:
    REQUEST_COUNT.inc()
    started = time.perf_counter()
    try:
        inference_frame = build_inference_frame(payload)
        prediction = float(app.state.model.predict(inference_frame)[0])
        drift_detected = detect_request_drift(inference_frame)
        if drift_detected:
            DRIFT_EVENTS.inc()
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        append_jsonl(
            get_params()["monitoring"]["request_log_path"],
            {
                "store": payload.store,
                "date": payload.date,
                "predicted_sales": prediction,
                "drift_detected": drift_detected,
                "latency_ms": latency_ms,
            },
        )
        REQUEST_LATENCY.observe(latency_ms / 1000)
        metadata = get_model_metadata()
        logger.info(
            "Prediction served store=%s date=%s latency_ms=%.3f drift=%s",
            payload.store,
            payload.date,
            latency_ms,
            drift_detected,
        )
        return ForecastResponse(
            predicted_sales=prediction,
            model_name=metadata.get("model_name", "unknown"),
            model_run_id=metadata.get("run_id", "unknown"),
            drift_detected=drift_detected,
            inference_latency_ms=latency_ms,
        )
    except HTTPException:
        FAILURE_COUNT.inc()
        logger.exception("Prediction failed for store=%s", payload.store)
        raise
    except Exception as exc:
        FAILURE_COUNT.inc()
        logger.exception("Unexpected model service failure")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
