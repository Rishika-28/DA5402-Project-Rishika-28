# Sales Forecasting System with MLOps

End-to-end Rossmann sales forecasting system with:

- reproducible data and model pipeline using DVC
- experiment tracking and model registry metadata using MLflow
- separate frontend, API gateway, and model service
- Prometheus and Grafana monitoring
- Airflow DAG for pipeline orchestration
- project documents required for the final evaluation

## Problem

Forecast daily store sales for Rossmann stores using historical sales, calendar effects, promotions, and store metadata.

## Success Metrics

- Primary ML metric: `RMSPE`
- Secondary ML metrics: `RMSE`, `MAPE`, `MAE`, `R2`
- Business metric: online inference p95 latency under `200 ms` for single-row requests on local deployment
- Reliability metric: `/health` and `/ready` endpoints return success when services are healthy

## Repository Layout

- `app/`: FastAPI API gateway and model service
- `dags/`: Airflow DAG for offline pipeline orchestration
- `data/`: training data, store metadata, processed outputs, and feedback logs
- `docs/`: architecture, HLD, LLD, test plan, test report, demo runbook, and user manual
- `frontend/`: static HTML/CSS/JS user interface
- `models/`: serving model, selected model URI, and registry metadata
- `monitoring/`: Prometheus config, alert rules, Grafana dashboards, and provisioning
- `reports/`: evaluation metrics, drift reports, and pipeline summaries
- `src/`: data preparation, feature engineering, training, and evaluation logic
- `tests/`: unit and API tests
- `docker-compose.yml`: main application stack
- `docker-compose.airflow.yml`: Airflow UI stack for offline pipeline visualization

## Prerequisites

Install these before running the project:

- `Python 3.11+`
- `Docker Desktop`
- `Git`
- `DVC`

## Environment Setup

Create a Python virtual environment for local development, inspection, and optional non-Docker workflows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Initialize DVC in this repository once if needed:

```powershell
dvc init --subdir
```

## Repository Outputs and Important Files

- `models/model_registry.json`: selected model name, run ID, model URI, and metrics
- `models/latest_model_uri.txt`: active serving model URI
- `reports/evaluation_metrics.json`: validation metrics
- `reports/drift_report.json`: drift summary
- `reports/pipeline_summary.json`: end-to-end pipeline summary
- `reports/request_log.jsonl`: online inference log
- `data/feedback/live_feedback.csv`: feedback loop records

## Local Pipeline Commands

These commands are useful for development, validation, and debugging:

```powershell
dvc repro
```

```powershell
pytest
```

## Submission Flow

This submission is designed to be demonstrated entirely with Docker.

### 1. Start the Main Application Stack

```powershell
docker compose up -d --build
```

This starts:

- `rossmann-frontend`
- `rossmann-api-gateway`
- `rossmann-model-service`
- `rossmann-prometheus`
- `rossmann-grafana`

### 2. Open the Main Application Pages

- Frontend UI: `http://localhost:8088`
- API Gateway Swagger UI: `http://localhost:8103/docs`
- Model Service Swagger UI: `http://localhost:8101/docs`
- Prometheus: `http://localhost:9091`
- Grafana: `http://localhost:3001`

### 3. Start the Airflow UI Stack

Run these commands in order:

```powershell
docker compose -f docker-compose.airflow.yml down
docker compose -f docker-compose.airflow.yml up airflow-init
docker compose -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler
```

If the Airflow user does not exist yet, create it:

```powershell
docker exec -it rossmann-airflow-webserver airflow users create --username admin --firstname Rishi --lastname User --role Admin --email admin@example.com --password admin
```

Open:

- Airflow UI: `http://127.0.0.1:8081`

Login:

- Username: `admin`
- Password: `admin`

## All Pages to Open

- Frontend UI: `http://localhost:8088`
- API Gateway Swagger UI: `http://localhost:8103/docs`
- Model Service Swagger UI: `http://localhost:8101/docs`
- Prometheus: `http://localhost:9091`
- Grafana: `http://localhost:3001`
- Airflow UI: `http://127.0.0.1:8081`

## What Each UI Is For

- `Frontend UI`: non-technical user workflow for forecasting, feedback submission, pipeline summary, and monitoring summary.
- `Grafana`: live operational monitoring for request throughput, service reachability, latency, failure rate, drift alerts, and feedback events.
- `Prometheus`: raw metrics and scrape target visibility.
- `Airflow`: offline ML pipeline orchestration view for `prepare_data`, `train_model`, and `evaluate_model`.
- `Swagger UIs`: technical verification of API contracts and responses.

## Shutdown Commands

Stop the main application stack:

```powershell
docker compose down
```

Stop the Airflow stack:

```powershell
docker compose -f docker-compose.airflow.yml down
```

## Note
- The dataset should be downloaded from https://www.kaggle.com/competitions/rossmann-store-sales/data
