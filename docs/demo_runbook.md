# Demo Runbook

## One-Time Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
dvc init --subdir
```

## Pipeline Commands

```powershell
dvc repro
mlflow ui --backend-store-uri .\mlruns --port 5000
```

## Local App Commands

Open three terminals:

```powershell
uvicorn app.model_service:app --host 0.0.0.0 --port 8001
```

```powershell
uvicorn app.gateway:app --host 0.0.0.0 --port 8000
```

```powershell
python -m http.server 8080 --directory frontend
```

## Docker Demo

```powershell
docker compose up --build
```

## Demo Narration

1. Show `dvc dag` to visualize the reproducible pipeline.
2. Show `mlflow ui` and open the best run ID from `models/model_registry.json`.
3. Open the frontend and generate a forecast.
4. Record feedback to show the ground-truth loop.
5. Open `http://localhost:8103/pipeline` to show pipeline metadata.
6. Open Prometheus and Grafana to show runtime monitoring.
7. Open `docs/architecture.md`, `docs/hld.md`, and `docs/lld.md` during design questions.

## Useful Commands for Viva

```powershell
dvc dag
type .\models\model_registry.json
type .\reports\evaluation_metrics.json
type .\reports\drift_report.json
pytest
curl http://127.0.0.1:8103/health
curl http://127.0.0.1:8103/ready
```
