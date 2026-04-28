# User Manual

## Who this is for

This application is for a store planner or manager who wants a simple sales forecast without needing to understand machine learning.

## How to use the system

1. Open the web application in your browser.
2. Stay on the `Forecast` screen.
3. Enter the store number.
4. Pick the forecast date.
5. Confirm whether the store is open and whether a promotion is running.
6. Select the holiday settings if relevant.
7. Click `Generate Forecast`.
8. Read the predicted sales value shown on the right.

## Recording actual sales later

1. After real sales are known, use the `Feedback Loop` section.
2. Enter the same store and date.
3. Enter the predicted sales and the actual sales.
4. Click `Record Ground Truth`.

## Other screens

- `Pipeline`: shows the ML workflow status, evaluation metrics, and model run information.
- `Monitoring`: shows feedback counts, drift status, and operations summary.
- `User Manual`: shows these instructions inside the application.

## Notes

- If the system says drift was detected, the input pattern may differ from the training baseline.
- If the app does not load, ask the operator to confirm that the API gateway and model service are running.

