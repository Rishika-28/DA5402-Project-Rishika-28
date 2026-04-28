# Low-Level Design Document

## Components

### Frontend

- Technology: static HTML, CSS, JS
- Port: `8080`
- Responsibility: forecast input, result display, pipeline console, monitoring summary, user manual

### API Gateway

- Technology: FastAPI
- Port: `8000`
- Responsibility: validation, proxying, feedback logging, metadata exposure

### Model Service

- Technology: FastAPI + MLflow pyfunc
- Port: `8001`
- Responsibility: load model artifact, perform inference, detect request-level drift

## Endpoint Specification

### `GET /health`

- Purpose: liveness check
- Response:

```json
{"status": "ok"}
```

### `GET /ready`

- Purpose: readiness check
- Response:

```json
{"ready": true}
```

### `POST /forecast`

- Request:

```json
{
  "store": 1,
  "date": "2015-08-01",
  "day_of_week": 6,
  "open": 1,
  "promo": 1,
  "state_holiday": "0",
  "school_holiday": 1
}
```

- Response:

```json
{
  "predicted_sales": 5400.12,
  "model_name": "extra_trees",
  "model_run_id": "abc123",
  "drift_detected": false,
  "inference_latency_ms": 73.4
}
```

### `POST /feedback`

- Request:

```json
{
  "store": 1,
  "date": "2015-08-01",
  "predicted_sales": 5400.12,
  "actual_sales": 5250.0
}
```

- Response:

```json
{"status": "recorded", "rows_appended": 1}
```

### `GET /pipeline`

- Purpose: pipeline visualization and evaluation metadata for the frontend/demo

### `GET /monitoring/summary`

- Purpose: summarize feedback volume, live MAPE, and drift flags

## Model Inputs

- `Store`
- `DayOfWeek`
- `Open`
- `Promo`
- `SchoolHoliday`
- `StateHoliday`
- `StoreType`
- `Assortment`
- `CompetitionDistance`
- `CompetitionOpenSinceMonth`
- `CompetitionOpenSinceYear`
- `Promo2`
- `Promo2SinceWeek`
- `Promo2SinceYear`
- `Year`
- `Month`
- `Day`
- `WeekOfYear`
- `IsWeekend`
- `IsMonthStart`
- `IsMonthEnd`
- `CompetitionOpenMonths`
- `Promo2Active`

