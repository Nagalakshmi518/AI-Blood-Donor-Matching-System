const RENDER_FALLBACK_URL = "https://ai-blood-donor-matching-system.onrender.com";

function resolveApiUrl() {
  if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
  ) {
    if (window.location.port === "5000") {
      return window.location.origin;
    }
    return "http://127.0.0.1:5000";
  }
  if (window.location.origin.includes("onrender.com")) {
    return window.location.origin;
  }
  return RENDER_FALLBACK_URL;
}

const API_URL = resolveApiUrl();
const token = localStorage.getItem("token");

if (!token) {
  window.location.href = "login.html";
}

const analyticsContainer = document.getElementById("analyticsContainer");

async function loadAnalytics() {
  try {
    const response = await fetch(`${API_URL}/api/analytics/`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      analyticsContainer.innerHTML = `
        <p class="error">${data.message || "Failed to load telemetry"}</p>
      `;
      return;
    }

    analyticsContainer.innerHTML = `
      <div class="analytics-grid">
        <div class="analytics-card">
          <h3>Total Requests</h3>
          <h2>${data.total_requests || 0}</h2>
        </div>

        <div class="analytics-card">
          <h3>Completed Requests</h3>
          <h2 style="color: #10B981;">${data.completed_requests || 0}</h2>
        </div>

        <div class="analytics-card">
          <h3>Pending Requests</h3>
          <h2 style="color: #F59E0B;">${data.pending_requests || 0}</h2>
        </div>

        <div class="analytics-card">
          <h3>Available Donors</h3>
          <h2 style="color: #38BDF8;">${data.available_donors || 0}</h2>
        </div>

        <div class="analytics-card">
          <h3>Total Donors</h3>
          <h2>${data.total_donors || 0}</h2>
        </div>

        <div class="analytics-card">
          <h3>Total Patients</h3>
          <h2>${data.total_patients || 0}</h2>
        </div>

        <div class="analytics-card">
          <h3>Total Donations</h3>
          <h2 style="color: #10B981;">${data.total_donations || 0}</h2>
        </div>

        <div class="analytics-card">
          <h3>Success Rate</h3>
          <h2 style="color: var(--bn-ai-cyan);">${data.success_rate != null ? data.success_rate : 0}%</h2>
        </div>
      </div>
    `;
  } catch (error) {
    console.error(error);
    analyticsContainer.innerHTML = `
      <p class="error">Unable to connect to backend telemetry service.</p>
    `;
  }
}

const mlResearchSection = document.getElementById("mlResearchSection");

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function parseJsonSafe(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function parseFiniteInput(elementId, label) {
  const el = document.getElementById(elementId);
  const raw = el ? el.value.trim() : "";
  if (raw === "") {
    throw new Error(`${label} is required.`);
  }
  const num = Number(raw);
  if (!Number.isFinite(num)) {
    throw new Error(`${label} must be a valid finite number.`);
  }
  return num;
}

function validateSandboxInputs() {
  const recency = parseFiniteInput("mlRecency", "Recency (months)");
  const frequency = parseFiniteInput("mlFrequency", "Frequency (times)");
  const monetary = parseFiniteInput("mlMonetary", "Monetary (c.c. blood)");
  const timeMonths = parseFiniteInput("mlTime", "Time (months)");

  if (recency < 0) {
    throw new Error("Recency (months) must be >= 0.");
  }
  if (frequency < 1) {
    throw new Error("Frequency (times) must be >= 1.");
  }
  if (monetary <= 0) {
    throw new Error("Monetary (c.c. blood) must be > 0.");
  }
  if (timeMonths < 0) {
    throw new Error("Time (months) must be >= 0.");
  }
  if (timeMonths < recency) {
    throw new Error("Time (months since first donation) cannot be less than Recency (months since last donation).");
  }

  return {
    recency_months: recency,
    frequency_times: frequency,
    monetary_cc: monetary,
    time_months: timeMonths,
  };
}

async function loadMlResearch() {
  if (!mlResearchSection) return;
  try {
    const response = await fetch(`${API_URL}/api/ml-research/status`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (response.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "login.html";
      return;
    }

    const data = await parseJsonSafe(response);

    if (!response.ok || !data.available) {
      mlResearchSection.innerHTML = `
        <div class="ml-research-header">
          <h2><i class="fa-solid fa-flask" style="color: var(--bn-ai-cyan);"></i> Research ML Module (UCI Blood Transfusion)</h2>
          <span class="ml-badge">Experimental / Non-Operational</span>
        </div>
        <p style="color: var(--bn-text-secondary); margin: 0;">${escapeHtml(data.message || "Research ML model artifacts are not yet available.")}</p>
      `;
      return;
    }

    const selectedKey = data.selected_model ? data.selected_model.key : "";
    const rowsHtml = (data.all_models || [])
      .map((model) => {
        const tm = model.test_metrics || {};
        const cv = model.cv_metrics || {};
        const isSelected = model.key === selectedKey;
        return `
          <tr class="${isSelected ? "ml-selected-row" : ""}">
            <td><strong>${escapeHtml(model.name)}</strong>${isSelected ? ' <span class="ml-badge">Selected</span>' : ""}</td>
            <td>${escapeHtml(cv.f1 ? cv.f1.mean : "N/A")}</td>
            <td>${escapeHtml(cv.roc_auc ? cv.roc_auc.mean : "N/A")}</td>
            <td>${escapeHtml(tm.accuracy ?? "N/A")}</td>
            <td>${escapeHtml(tm.precision ?? "N/A")}</td>
            <td>${escapeHtml(tm.recall ?? "N/A")}</td>
            <td>${escapeHtml(tm.f1_score ?? "N/A")}</td>
            <td>${escapeHtml(tm.roc_auc ?? "N/A")}</td>
          </tr>
        `;
      })
      .join("");

    const schemaGapReason = data.schema_gap?.reason
      ? `<div class="ml-schema-gap"><strong>Operational Isolation:</strong> ${escapeHtml(data.schema_gap.reason)}</div>`
      : "";

    mlResearchSection.innerHTML = `
      <div class="ml-research-header">
        <h2><i class="fa-solid fa-flask" style="color: var(--bn-ai-cyan);"></i> Research ML Evaluation — UCI Blood Transfusion Dataset</h2>
        <span class="ml-badge">Academic Research Only (Non-Operational)</span>
      </div>
      <div class="ml-disclaimer">
        <strong>Scope Notice:</strong> ${escapeHtml(data.disclaimer)}
      </div>
      ${schemaGapReason}
      <div class="ml-table-wrap">
        <table class="ml-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>CV F1 (5-Fold)</th>
              <th>CV ROC-AUC</th>
              <th>Test Accuracy</th>
              <th>Test Precision</th>
              <th>Test Recall</th>
              <th>Test F1</th>
              <th>Test ROC-AUC</th>
            </tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>
      <h3 style="margin-top: 0; margin-bottom: 12px; color: #FFFFFF;">Historical Donation Tendency Sandbox (UCI RFMT Inputs)</h3>
      <form id="mlPredictForm" novalidate>
        <div class="ml-form-grid">
          <div class="ml-field">
            <label for="mlRecency">Recency (months)</label>
            <input type="number" id="mlRecency" min="0" step="1" value="2" required>
          </div>
          <div class="ml-field">
            <label for="mlFrequency">Frequency (times)</label>
            <input type="number" id="mlFrequency" min="1" step="1" value="6" required>
          </div>
          <div class="ml-field">
            <label for="mlMonetary">Monetary (c.c. blood)</label>
            <input type="number" id="mlMonetary" min="1" step="50" value="1500" required>
          </div>
          <div class="ml-field">
            <label for="mlTime">Time (months since first)</label>
            <input type="number" id="mlTime" min="0" step="1" value="16" required>
          </div>
        </div>
        <button type="submit" id="mlPredictBtn" class="ml-predict-btn">
          <i class="fa-solid fa-brain"></i> Predict Historical Donation Tendency
        </button>
      </form>
      <div id="mlPredictResult" class="ml-result-box" style="display: none;"></div>
    `;

    const form = document.getElementById("mlPredictForm");
    const submitBtn = document.getElementById("mlPredictBtn");
    const resultBox = document.getElementById("mlPredictResult");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      resultBox.style.display = "block";

      let payload;
      try {
        payload = validateSandboxInputs();
      } catch (validationError) {
        resultBox.innerHTML = `<span style="color: #F87171;">${escapeHtml(validationError.message)}</span>`;
        return;
      }

      submitBtn.disabled = true;
      resultBox.textContent = "Running historical donation prediction...";
      try {
        const predResponse = await fetch(`${API_URL}/api/ml-research/predict`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });
        if (predResponse.status === 401) {
          localStorage.removeItem("token");
          window.location.href = "login.html";
          return;
        }
        const predData = await parseJsonSafe(predResponse);
        if (!predResponse.ok) {
          resultBox.innerHTML = `<span style="color: #F87171;">${escapeHtml(predData.message || "Invalid input or model unavailable.")}</span>`;
          return;
        }
        const probPercent =
          predData.probability_score != null
            ? `${(Number(predData.probability_score) * 100).toFixed(2)}%`
            : "N/A";
        resultBox.innerHTML = `
          <div><strong>Prediction:</strong> ${escapeHtml(predData.predicted_label)}</div>
          <div><strong>Historical Donation Probability:</strong> ${escapeHtml(probPercent)}</div>
          <div><strong>Model:</strong> ${escapeHtml(predData.model_info?.model_name || "N/A")}</div>
          <div style="margin-top: 6px; color: #FCD34D; font-size: 12.5px;">${escapeHtml(predData.disclaimer)}</div>
        `;
      } catch (err) {
        resultBox.innerHTML = `<span style="color: #F87171;">Unable to reach research ML prediction endpoint.</span>`;
      } finally {
        submitBtn.disabled = false;
      }
    });
  } catch (error) {
    mlResearchSection.innerHTML = `
      <div class="ml-research-header">
        <h2><i class="fa-solid fa-flask" style="color: var(--bn-ai-cyan);"></i> Research ML Module</h2>
        <span class="ml-badge">Offline</span>
      </div>
      <p style="color: var(--bn-text-muted); margin: 0;">Research ML telemetry unavailable.</p>
    `;
  }
}

loadAnalytics();
loadMlResearch();
