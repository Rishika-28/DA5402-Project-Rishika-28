const apiBase = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://127.0.0.1:8103"
  : `${window.location.protocol}//${window.location.hostname}:8103`;

const views = ["forecast", "pipeline", "monitoring", "manual"];

document.querySelectorAll(".nav-btn").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach((btn) => btn.classList.remove("active"));
    document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(`view-${button.dataset.view}`).classList.add("active");
  });
});

function asCard(title, value, subtitle = "") {
  return `<div class="panel stat-card"><span>${title}</span><strong>${value}</strong><small>${subtitle}</small></div>`;
}

async function loadDashboard() {
  const pipelineResponse = await fetch(`${apiBase}/pipeline`);
  const pipeline = await pipelineResponse.json();
  const monitoringResponse = await fetch(`${apiBase}/monitoring/summary`);
  const monitoring = await monitoringResponse.json();
  const manualResponse = await fetch(`${apiBase}/user-manual`);
  const manual = await manualResponse.json();

  document.getElementById("stat-model").textContent = pipeline.model_registry.model_name || "unknown";
  document.getElementById("stat-rmspe").textContent = pipeline.evaluation.rmspe?.toFixed(4) || "-";

  const pipelineCards = document.getElementById("pipeline-cards");
  pipelineCards.innerHTML = [
    asCard("Training rows", pipeline.prepare.train_rows ?? "-", "Post feature engineering"),
    asCard("Validation rows", pipeline.prepare.validation_rows ?? "-", "Last 42 days"),
    asCard("Best model", pipeline.training.best_model_name ?? "-", "Selected by RMSPE"),
    asCard("RMSE", pipeline.evaluation.rmse?.toFixed(2) ?? "-", "Validation score"),
    asCard("MAPE", pipeline.evaluation.mape?.toFixed(4) ?? "-", "Validation score"),
    asCard("Drift detected", pipeline.drift.drift_detected ? "Yes" : "No", "Validation-vs-train baseline"),
  ].join("");

  document.getElementById("pipeline-json").textContent = JSON.stringify(pipeline, null, 2);

  const monitoringCards = document.getElementById("monitoring-cards");
  monitoringCards.innerHTML = [
    asCard("Feedback rows", monitoring.feedback.feedback_rows ?? 0, "Ground truth captured"),
    asCard("Request log entries", monitoring.requests_logged ?? 0, "Inference audit trail"),
    asCard(
      "Live MAPE",
      monitoring.feedback.mean_absolute_percentage_error !== null
        ? monitoring.feedback.mean_absolute_percentage_error.toFixed(4)
        : "-",
      "From recorded feedback"
    ),
    asCard("Registry run ID", monitoring.model_registry.run_id ?? "-", "Reproducibility anchor"),
    asCard("Drift status", monitoring.drift.drift_detected ? "Alert" : "Normal", "Threshold-based detection"),
    asCard("Prometheus", "Enabled", "Scrapes API and model service"),
  ].join("");

  document.getElementById("manual-content").textContent = manual.markdown;
}

document.getElementById("forecast-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  const payload = Object.fromEntries(formData.entries());
  payload.store = Number(payload.store);
  payload.day_of_week = Number(payload.day_of_week);
  payload.open = Number(payload.open);
  payload.promo = Number(payload.promo);
  payload.school_holiday = Number(payload.school_holiday);

  const response = await fetch(`${apiBase}/forecast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  const target = document.getElementById("forecast-result");
  if (!response.ok) {
    target.innerHTML = `<p class="error">${data.detail || "Forecast failed"}</p>`;
    return;
  }
  document.querySelector('input[name="predicted_sales"]').value = data.predicted_sales.toFixed(2);
  target.innerHTML = `
    <div class="prediction-value">${data.predicted_sales.toFixed(2)}</div>
    <div class="prediction-meta">
      <span>Model: ${data.model_name}</span>
      <span>Run ID: ${data.model_run_id}</span>
      <span>Latency: ${data.inference_latency_ms} ms</span>
      <span>Drift: ${data.drift_detected ? "Detected" : "Normal"}</span>
    </div>
  `;
});

document.getElementById("feedback-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  const payload = Object.fromEntries(formData.entries());
  payload.store = Number(payload.store);
  payload.predicted_sales = Number(payload.predicted_sales);
  payload.actual_sales = Number(payload.actual_sales);

  const response = await fetch(`${apiBase}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  const target = document.getElementById("feedback-result");
  target.textContent = response.ok ? "Ground truth recorded successfully." : data.detail || "Unable to record feedback.";
  loadDashboard();
});

loadDashboard().catch((error) => {
  console.error(error);
  document.getElementById("forecast-result").innerHTML =
    `<p class="error">Could not load dashboard. Start the API and model service first.</p>`;
});
