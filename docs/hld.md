# High-Level Design Document

## Goal

Build a dependable forecasting product for store managers that predicts daily sales while satisfying MLOps requirements for reproducibility, monitoring, documentation, and deployment.

## Design Choices

1. `Loose coupling`: the frontend talks only to the API gateway; it never imports model code directly.
2. `Separate services`: API gateway and model service are deployed as independent containers and communicate through REST.
3. `Reproducibility`: DVC stages define the pipeline, MLflow stores run metadata, and the selected model run ID is written to `models/model_registry.json`.
4. `Time-aware validation`: the last 42 days form the validation window to match the six-week business forecast horizon.
5. `Operational resilience`: `/health`, `/ready`, metrics exporters, and feedback capture are included for runtime observability.
6. `Local-first deployment`: the project runs on a laptop without cloud dependencies.

## Functional Architecture

- Data ingestion merges `train.csv` with `store.csv`
- Feature engineering derives calendar, competition, and promotion features
- Model training compares multiple candidates and selects the lowest validation RMSPE
- Model service loads the best MLflow artifact
- API gateway exposes user-facing endpoints and pipeline metadata
- Frontend displays forecasts, monitoring summaries, and pipeline information

## Non-Functional Requirements

- Inference latency target: under 200 ms for a single forecast request
- Transparent monitoring and traceability
- Clear docs for evaluators and non-technical users
- Docker Compose packaging for parity across environments

