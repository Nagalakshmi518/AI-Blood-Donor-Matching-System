const API_URL = "https://ai-blood-donor-matching-system.onrender.com";
function getStoredRole() {
  return String(localStorage.getItem("role") || "")
    .trim()
    .toUpperCase();
}

function getDashboardForRole(role) {
  const normalizedRole = String(role || "")
    .trim()
    .toUpperCase();

  if (normalizedRole === "DONOR") {
    return "donor-dashboard.html";
  }

  if (normalizedRole === "ADMIN") {
    return "admin-dashboard.html";
  }

  return "patient-dashboard.html";
}

function ensureExpectedRole(expectedRole) {
  const token = localStorage.getItem("token");
  const role = getStoredRole();

  if (!token) {
    window.location.href = "login.html";
    return false;
  }

  if (expectedRole && role && role !== expectedRole) {
    window.location.href = getDashboardForRole(role);
    return false;
  }

  return true;
}

function safeLogout() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("user");
  localStorage.removeItem("patient_id");
  localStorage.removeItem("donor_id");
  window.location.href = "login.html";
}

const token = localStorage.getItem("token");

if (!ensureExpectedRole("PATIENT")) {
  throw new Error("Unauthorized patient dashboard access.");
}

function getStatusDisplay(status) {
  if (!status) return "Pending";
  if (status === "Accepted")
    return "Accepted - Donation Pending / Awaiting Completion";
  if (status === "Matched") return "Matched";
  if (status === "Completed") return "Completed";
  if (status === "Cancelled") return "Cancelled";
  if (status === "Rejected") return "Rejected";
  return status;
}

function getStatusColor(status) {
  const value = status || "Pending";
  if (value === "Completed") return "blue";
  if (value === "Accepted") return "green";
  if (value === "Rejected") return "red";
  if (value === "Pending") return "orange";
  if (value === "Matched") return "purple";
  return "gray";
}

async function loadPatientDashboard() {
  if (!token) {
    window.location.href = "login.html";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/api/patients/dashboard`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      return;
    }

    if (data.patient) {
      localStorage.setItem("patient_id", data.patient.patient_id);
    }

    const patientName = document.getElementById("patientName");
    const stats = data.statistics || {};

    if (patientName && data.patient) {
      patientName.textContent = `Welcome ${data.patient.full_name || "Patient"}`;
    }

    document.getElementById("totalRequests").textContent =
      stats.total_requests ?? 0;
    document.getElementById("pendingRequests").textContent = stats.pending ?? 0;
    document.getElementById("matchedRequests").textContent = stats.matched ?? 0;
    document.getElementById("acceptedRequests").textContent =
      stats.accepted ?? 0;
    document.getElementById("completedRequests").textContent =
      stats.completed ?? 0;
    document.getElementById("rejectedRequests").textContent =
      stats.rejected ?? 0;
    document.getElementById("cancelledRequests").textContent =
      stats.cancelled ?? 0;

    const recentActivity = document.getElementById("recentActivity");
    recentActivity.innerHTML = "";

    if (!data.recent_activities || data.recent_activities.length === 0) {
      recentActivity.innerHTML = "<p>No recent activity.</p>";
    } else {
      data.recent_activities.forEach((activity) => {
        recentActivity.innerHTML += `
          <div class="activity-card">
            <h3>Request #${activity.request_id}</h3>
            <p>${activity.activity}</p>
            <p>🩸 ${activity.blood_group}</p>
            <p>🏥 ${activity.hospital}</p>
            <p>
              Status:
              <b style="color:${getStatusColor(activity.status)};">${getStatusDisplay(activity.status)}</b>
            </p>
            <p>🕒 ${activity.request_time}</p>
          </div>
        `;
      });
    }
  } catch (error) {
    console.error(error);
  }
}

const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", function () {
    safeLogout();
  });
}

loadPatientDashboard();
