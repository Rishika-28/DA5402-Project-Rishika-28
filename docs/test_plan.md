# Test Plan and Test Cases

## Acceptance Criteria

1. DVC pipeline completes successfully and emits reports.
2. MLflow logs at least one experiment run and one selected best model.
3. `/health` and `/ready` succeed after services start.
4. Frontend can submit a forecast without a UI error.
5. Feedback endpoint stores ground-truth records.
6. Prometheus can scrape both services.

## Test Cases

| ID | Test Case | Type | Expected Result |
|---|---|---|---|
| TC-01 | Run `python -m src.data_pipeline prepare --params params.yaml` | Integration | Processed train and validation files created |
| TC-02 | Run `python -m src.train --params params.yaml` | Integration | MLflow run created and model registry metadata written |
| TC-03 | Run `python -m src.evaluate --params params.yaml` | Integration | Metrics and drift report created |
| TC-04 | Call `GET /health` | API | `200 OK` |
| TC-05 | Call `GET /ready` | API | `200 OK` after model load |
| TC-06 | Call `POST /forecast` with sample payload | E2E | Prediction returned with latency and run ID |
| TC-07 | Call `POST /feedback` with sample payload | E2E | Feedback row appended |
| TC-08 | Run `pytest` | Unit | Tests pass |
| TC-09 | Open frontend in browser | UI | Responsive layout, form submission works |
| TC-10 | Open Grafana dashboard | Monitoring | Panels load Prometheus-backed metrics |

## Test Report Template

| Metric | Value |
|---|---|
| Total Test Cases | 10 |
| Passed | Fill after execution |
| Failed | Fill after execution |
| Blocked | Fill after execution |

