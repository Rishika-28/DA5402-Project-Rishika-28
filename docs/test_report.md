# Test Report

## Executed On

- Date: 2026-04-27
- Environment: local Windows machine, Python 3.11.9

## Commands Executed

```powershell
python -m pytest tests/test_features.py tests/test_api.py
python -m src.data_pipeline prepare --params params.yaml
python -m src.train --params params.yaml
python -m src.evaluate --params params.yaml
dvc repro
```

## Results

| Metric | Value |
|---|---|
| Total Test Cases | 10 |
| Passed | 10 |
| Failed | 0 |
| Blocked | 0 |

## Acceptance Criteria Outcome

- DVC pipeline completed successfully: `Passed`
- MLflow experiment and run tracking produced a best run ID: `Passed`
- API `/health` and `/ready` worked locally: `Passed`
- Forecast endpoint returned a valid prediction: `Passed`
- Feedback endpoint recorded ground truth: `Passed`
- Monitoring exporters exposed metrics endpoints: `Passed`

## Observed Validation Metrics

- RMSE: `1215.8768`
- MAE: `745.8641`
- MAPE: `0.1130`
- R2: `0.8935`
- RMSPE: `0.1876`

## Notes

- Validation used the last 42 days to simulate the six-week forecasting horizon.
- A request-level drift flag can trigger for unusual input combinations; that is expected behavior and useful during the monitoring demo.
