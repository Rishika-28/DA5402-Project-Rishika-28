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

- `src/`: training, feature engineering, evaluation, and metadata export
- `app/`: FastAPI gateway and model service
- `frontend/`: responsive static frontend
- `monitoring/`: Prometheus and Grafana configuration
- `dags/`: Airflow orchestration DAG
- `docs/`: architecture, HLD, LLD, tests, and user manual
- `tests/`: unit and API tests

## Quick Start

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Initialize DVC in this subdirectory once:

   ```powershell
   dvc init --subdir
   ```

3. Run the pipeline:

   ```powershell
   dvc repro
   ```

4. Start the local services:

   ```powershell
   uvicorn app.model_service:app --host 0.0.0.0 --port 8001
   uvicorn app.gateway:app --host 0.0.0.0 --port 8000
   python -m http.server 8080 --directory frontend
   ```

5. Open the frontend:

   - `http://localhost:8080`

## Docker Demo

```powershell
docker compose up --build
```

Services:

- Frontend: `http://localhost:8088`
- API gateway: `http://localhost:8103/docs`
- Model service: `http://localhost:8101/docs`
- Prometheus: `http://localhost:9091`
- Grafana: `http://localhost:3001`

## Demo Flow

Use `docs/demo_runbook.md` for the exact commands and narration.
