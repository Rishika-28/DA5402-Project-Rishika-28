from __future__ import annotations

import os
import logging
from pathlib import Path

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.schemas import FeedbackRequest, ForecastRequest
from app.service_common import get_model_metadata, get_params
from src.utils import read_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter("api_gateway_requests_total", "Total API gateway requests")
REQUEST_LATENCY = Histogram("api_gateway_request_latency_seconds", "API gateway latency")
FEEDBACK_COUNT = Counter("feedback_events_total", "Feedback records received")
FAILURE_COUNT = Counter("api_gateway_failures_total", "Failed API gateway requests")

app = FastAPI(title="Rossmann API Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def model_service_url() -> str:
    params = get_params()
    default_url = params["service"]["local_model_service_url"]
    return os.environ.get("MODEL_SERVICE_URL", default_url)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
        try:
            response = requests.get(f"{model_service_url()}/ready", timeout=5)
            response.raise_for_status()
            return {"ready": True, "model_service": response.json()}
        except requests.RequestException as exc:
            FAILURE_COUNT.inc()
            raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/forecast")
def forecast(payload: ForecastRequest) -> dict:
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        try:
            response = requests.post(
                f"{model_service_url()}/predict",
                json=payload.model_dump(),
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Forwarded forecast request for store=%s date=%s", payload.store, payload.date)
            return response.json()
        except requests.RequestException as exc:
            FAILURE_COUNT.inc()
            logger.exception("Forecast request failed")
            raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/feedback")
def feedback(payload: FeedbackRequest) -> dict:
    params = get_params()
    FEEDBACK_COUNT.inc()
    row = payload.model_dump()
    row["absolute_error"] = abs(row["actual_sales"] - row["predicted_sales"])
    row["absolute_percentage_error"] = (
        row["absolute_error"] / max(row["actual_sales"], 1e-6)
    )

    feedback_path = Path(params["monitoring"]["feedback_path"])
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([row])
    write_header = not feedback_path.exists()
    frame.to_csv(feedback_path, mode="a", index=False, header=write_header)
    logger.info("Feedback recorded for store=%s date=%s", payload.store, payload.date)
    return {"status": "recorded", "rows_appended": 1}


@app.get("/pipeline")
def pipeline() -> dict:
    return {
        "prepare": read_json("reports/prepare_summary.json", {}),
        "training": read_json("reports/training_summary.json", {}),
        "comparison": read_json("reports/model_comparison.json", {}),
        "evaluation": read_json("reports/evaluation_metrics.json", {}),
        "pipeline": read_json("reports/pipeline_summary.json", {}),
        "schema": read_json("reports/schema_report.json", {}),
        "drift": read_json("reports/drift_report.json", {}),
        "model_registry": get_model_metadata(),
    }


@app.get("/monitoring/summary")
def monitoring_summary() -> dict:
    feedback_path = Path(get_params()["monitoring"]["feedback_path"])
    feedback_summary = {
        "feedback_rows": 0,
        "mean_absolute_percentage_error": None,
    }
    if feedback_path.exists():
        frame = pd.read_csv(feedback_path)
        feedback_summary = {
            "feedback_rows": int(len(frame)),
            "mean_absolute_percentage_error": float(
                frame["absolute_percentage_error"].mean()
            )
            if len(frame)
            else None,
        }

    request_log_path = Path(get_params()["monitoring"]["request_log_path"])
    request_count = 0
    if request_log_path.exists():
        request_count = sum(1 for _ in request_log_path.open("r", encoding="utf-8"))

    return {
        "feedback": feedback_summary,
        "requests_logged": request_count,
        "drift": read_json("reports/drift_report.json", {}),
        "model_registry": get_model_metadata(),
    }


@app.get("/user-manual")
def user_manual() -> dict:
    manual_path = Path("docs/user_manual.md")
    return {"markdown": manual_path.read_text(encoding="utf-8")}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
