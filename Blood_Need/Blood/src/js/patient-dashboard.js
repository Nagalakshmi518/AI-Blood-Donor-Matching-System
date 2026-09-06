const API_URL = "https://ai-blood-donor-matching-system.onrender.com";
const token = localStorage.getItem("token");

if (!token) {
  window.location.href = "login.html";
}

const patientName = document.getElementById("patientName");
const totalRequests = document.getElementById("totalRequests");
const pendingRequests = document.getElementById("pendingRequests");
const completedRequests = document.getElementById("completedRequests");
const acceptedRequests = document.getElementById("acceptedRequests");
const rejectedRequests = document.getElementById("rejectedRequests");
const matchedRequests = document.getElementById("matchedRequests");
const cancelledRequests = document.getElementById("cancelledRequests");
const recentActivity = document.getElementById("recentActivity");
const requestContainer = document.getElementById("requestContainer");
const logoutBtn = document.getElementById("logoutBtn");

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

async function loadDashboard() {
  try {
    const response = await fetch(`${API_URL}/api/patients/dashboard`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 401) {
      // Token is invalid/expired - redirect to login but do NOT clear localStorage
      // The token will be replaced when user logs in again
      window.location.href = "login.html";
      return;
    }

    const data = await response.json();

    if (!response.ok) {
      alert(data.message || "Unable to load dashboard.");
      return;
    }

    if (patientName && data.patient) {
      patientName.innerHTML = `Welcome ${data.patient.full_name || ""}`;
    }

    if (totalRequests) totalRequests.innerHTML = data.statistics.total_requests;
    if (pendingRequests) pendingRequests.innerHTML = data.statistics.pending;
    if (completedRequests)
      completedRequests.innerHTML = data.statistics.completed;
    if (acceptedRequests) acceptedRequests.innerHTML = data.statistics.accepted;
    if (rejectedRequests) rejectedRequests.innerHTML = data.statistics.rejected;
    if (matchedRequests) matchedRequests.innerHTML = data.statistics.matched;
    if (cancelledRequests)
      cancelledRequests.innerHTML = data.statistics.cancelled;

    recentActivity.innerHTML = "";
    if (!data.recent_activities || data.recent_activities.length === 0) {
      recentActivity.innerHTML = "<p>No recent activity.</p>";
    } else {
      data.recent_activities.forEach((activity) => {
        recentActivity.innerHTML += `
          <div class="activity-card">
            <h4>🩸 Request #${activity.request_id}</h4>
            <p><strong>${activity.activity}</strong></p>
            <p>Blood Group: ${activity.blood_group}</p>
            <p>Hospital: ${activity.hospital}</p>
            <p>
              Status:
              <strong style="color:${getStatusColor(activity.status)};">
                ${getStatusDisplay(activity.status)}
              </strong>
            </p>
            <small>${activity.request_time}</small>
            <hr>
          </div>
        `;
      });
    }
  } catch (error) {
    console.log(error);
    if (recentActivity)
      recentActivity.innerHTML = "<p>Unable to connect to backend.</p>";
  }
}

async function loadRequests() {
  try {
    const response = await fetch(`${API_URL}/api/patients/requests`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 401) {
      // Token is invalid/expired - redirect to login but do NOT clear localStorage
      // The token will be replaced when user logs in again
      window.location.href = "login.html";
      return;
    }

    const requests = await response.json();

    if (!response.ok) {
      if (requestContainer)
        requestContainer.innerHTML = `<p>${requests.message || "Unable to load requests."}</p>`;
      return;
    }

    if (!requests || requests.length === 0) {
      if (requestContainer)
        requestContainer.innerHTML = "<p>No blood requests found.</p>";
      return;
    }

    requestContainer.innerHTML = "";

    requests.forEach((request) => {
      const donorItems = Array.isArray(request.matched_donors)
        ? request.matched_donors
        : [];
      let donorHTML = "";

      if (donorItems.length === 0) {
        donorHTML = `
          <p>
            ${request.status === "Pending" ? "No matched donors yet. Request is still active and waiting for donor or inventory fulfillment." : "No donor response information available."}
          </p>
        `;
      } else {
        donorItems.forEach((donor) => {
          const donorName = donor.full_name || "Donor";
          const donorPhone = donor.phone || "N/A";
          const donorEmail = donor.email || "N/A";

          donorHTML += `
            <div class="donor-card" style="border:2px solid ${donor.donor_response === "Accepted" ? "green" : "#ddd"}; background:${donor.donor_response === "Accepted" ? "#e8ffe8" : "#fff"};">
              <h4>${donorName}${donor.donor_response === "Accepted" ? " ✅ Accepted Donor" : ""}</h4>
              <p>📞 ${donorPhone}</p>
              <p>📧 ${donorEmail}</p>
              <p>Blood: ${donor.blood_group || "N/A"}</p>
              <p>Distance: ${donor.distance_km != null ? `${donor.distance_km} km` : "N/A"}</p>
              <p>Ranking: ${donor.ranking_score != null ? donor.ranking_score : "N/A"}</p>
              <p>Reliability: ${donor.reliability_score != null ? donor.reliability_score : "N/A"}</p>
              <p>
                Response:
                <strong style="color:${getStatusColor(donor.donor_response)};">
                  ${donor.donor_response || "Pending"}
                </strong>
              </p>
            </div>
          `;
        });
      }

      const requestStatusDisplay = getStatusDisplay(request.status);
      const requestStatusColor = getStatusColor(request.status);

      requestContainer.innerHTML += `
        <div class="request-card">
          <h3>Blood Request #${request.request_id}</h3>
          <p>Blood Group: ${request.blood_group}</p>
          <p>Hospital: ${request.hospital_name}</p>
          <p>Emergency: ${request.emergency_level}</p>
          <p>
            Status:
            <strong style="color:${requestStatusColor};">${requestStatusDisplay}</strong>
          </p>
          <p>Units Needed: ${request.units_needed}</p>
          <p>Hospital Inventory Fallback: ${request.status === "Completed" && donorItems.length === 0 ? "Used" : donorItems.length === 0 ? "Awaiting donor or inventory" : "Not required"}</p>
          <div class="matched-donors">
            ${donorHTML}
          </div>
        </div>
      `;
    });
  } catch (error) {
    console.log(error);
    if (requestContainer)
      requestContainer.innerHTML = "<p>Unable to connect to backend.</p>";
  }
}

function safeLogout() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("user");
  localStorage.removeItem("patient_id");
  localStorage.removeItem("donor_id");
  window.location.href = "login.html";
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", function () {
    safeLogout();
  });
}

loadDashboard();
loadRequests();

setInterval(() => {
  loadDashboard();
  loadRequests();
}, 5000);
