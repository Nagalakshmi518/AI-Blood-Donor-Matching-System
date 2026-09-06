const API_URL = "https://ai-blood-donor-matching-system.onrender.com";

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
        <p class="error">${data.message}</p>
      `;
      return;
    }

    analyticsContainer.innerHTML = `
      <div class="analytics-grid">
        <div class="analytics-card">
          <h3>Total Requests</h3>
          <h2>${data.total_requests}</h2>
        </div>

        <div class="analytics-card">
          <h3>Completed Requests</h3>
          <h2>${data.completed_requests}</h2>
        </div>

        <div class="analytics-card">
          <h3>Pending Requests</h3>
          <h2>${data.pending_requests}</h2>
        </div>

        <div class="analytics-card">
          <h3>Available Donors</h3>
          <h2>${data.available_donors}</h2>
        </div>

        <div class="analytics-card">
          <h3>Total Donors</h3>
          <h2>${data.total_donors}</h2>
        </div>

        <div class="analytics-card">
          <h3>Total Patients</h3>
          <h2>${data.total_patients}</h2>
        </div>

        <div class="analytics-card">
          <h3>Total Donations</h3>
          <h2>${data.total_donations}</h2>
        </div>

        <div class="analytics-card">
          <h3>Success Rate</h3>
          <h2>${data.success_rate}%</h2>
        </div>
      </div>
    `;
  } catch (error) {
    console.error(error);
    analyticsContainer.innerHTML = `
      <p class="error">Unable to connect to backend.</p>
    `;
  }
}

loadAnalytics();
