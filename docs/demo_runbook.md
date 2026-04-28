# Demo Runbook

## Start the Main Stack

```powershell
docker compose up -d --build
```

Open these pages:

- Frontend: `http://localhost:8088`
- API Gateway Docs: `http://localhost:8103/docs`
- Model Service Docs: `http://localhost:8101/docs`
- Prometheus: `http://localhost:9091`
- Grafana: `http://localhost:3001`

## Start the Airflow Stack

Run these commands in order:

```powershell
docker compose -f docker-compose.airflow.yml down
docker compose -f docker-compose.airflow.yml up airflow-init
docker compose -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler
```

If required, create the login user:

```powershell
docker exec -it rossmann-airflow-webserver airflow users create --username admin --firstname Rishi --lastname User --role Admin --email admin@example.com --password admin
```

Open:

- Airflow UI: `http://127.0.0.1:8081`

Login:

- Username: `admin`
- Password: `admin`

## Demo 

1. Open the frontend at `http://localhost:8088`.
2. Show the `Forecast` page and explain that the user only interacts with the API gateway, not the model service directly.
3. Submit a forecast request and explain the returned prediction, latency, run ID, and drift flag.
4. Show the `Feedback Loop` and record ground-truth sales to demonstrate the monitoring feedback path.
5. Open the `Pipeline` tab in the frontend and explain that it surfaces pipeline metadata, model registry details, and evaluation outputs for a non-technical audience.
6. Open the `Monitoring` tab in the frontend and explain that it provides a simplified operational summary for user-facing visibility.
7. Open Grafana at `http://localhost:3001` and show service reachability, request throughput, latency, failure rate, drift events, and feedback counts.
8. Open Prometheus at `http://localhost:9091` and explain that it is scraping the API gateway and model service exporters.
9. Open Airflow at `http://127.0.0.1:8081` and show the DAG `rossmann_sales_forecasting_pipeline`.


## Useful Docker Commands

Start the main stack:

```powershell
docker compose up -d --build
```

Restart Grafana:

```powershell
docker compose restart grafana
```

Restart Prometheus:

```powershell
docker compose restart prometheus
```

Start Airflow:

```powershell
docker compose -f docker-compose.airflow.yml down
docker compose -f docker-compose.airflow.yml up airflow-init
docker compose -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler
```

Stop the main stack:

```powershell
docker compose down
```

Stop Airflow:

```powershell
docker compose -f docker-compose.airflow.yml down
```
