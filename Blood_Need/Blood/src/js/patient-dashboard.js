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
      cache: "no-store",
    });

    if (response.status === 401) {
      window.location.href = "login.html";
      return;
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Unable to load dashboard.");
    }

    if (patientName && data.patient) {
      patientName.textContent = `Welcome ${data.patient.full_name || ""}`;
    }

    const stats = data.statistics || {};

    if (totalRequests) totalRequests.textContent = stats.total_requests || 0;

    if (pendingRequests) pendingRequests.textContent = stats.pending || 0;

    if (completedRequests) completedRequests.textContent = stats.completed || 0;

    if (acceptedRequests) acceptedRequests.textContent = stats.accepted || 0;

    if (rejectedRequests) rejectedRequests.textContent = stats.rejected || 0;

    if (matchedRequests) matchedRequests.textContent = stats.matched || 0;

    if (cancelledRequests) cancelledRequests.textContent = stats.cancelled || 0;

    if (!recentActivity) return;

    const activities = data.recent_activities || [];

    if (activities.length === 0) {
      recentActivity.innerHTML = "<p>No recent activity.</p>";
      return;
    }

    // Build HTML first
    const activityHTML = activities
      .map(
        (activity) => `
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
    `,
      )
      .join("");

    // ONE DOM update
    recentActivity.innerHTML = activityHTML;
  } catch (error) {
    console.error("Dashboard Error:", error);

    if (recentActivity) {
      recentActivity.innerHTML = `<p>Unable to load dashboard: ${error.message}</p>`;
    }
  }
}
async function loadRequests() {
  try {
    const response = await fetch(`${API_URL}/api/patients/requests`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    if (response.status === 401) {
      window.location.href = "login.html";
      return;
    }

    const requests = await response.json();

    if (!response.ok) {
      throw new Error(requests.message || "Unable to load requests.");
    }

    if (!requestContainer) return;

    if (!Array.isArray(requests) || requests.length === 0) {
      requestContainer.innerHTML = "<p>No blood requests found.</p>";
      return;
    }

    // Build EVERYTHING in memory first
    const requestsHTML = requests
      .map((request) => {
        const donorItems = Array.isArray(request.matched_donors)
          ? request.matched_donors
          : [];

        let donorHTML;

        if (donorItems.length === 0) {
          donorHTML = `
          <p>
            ${
              request.status === "Pending"
                ? "No matched donors yet. Request is still active and waiting for donor or inventory fulfillment."
                : "No donor response information available."
            }
          </p>
        `;
        } else {
          donorHTML = donorItems
            .map((donor) => {
              const donorName = donor.full_name || "Donor";

              const donorPhone = donor.phone || "N/A";

              const donorEmail = donor.email || "N/A";

              const accepted = donor.donor_response === "Accepted";

              return `
            <div class="donor-card"
              style="
                border:2px solid ${accepted ? "green" : "#ddd"};
                background:${accepted ? "#e8ffe8" : "#fff"};
              ">

              <h4>
                ${donorName}
                ${accepted ? " ✅ Accepted Donor" : ""}
              </h4>

              <p>📞 ${donorPhone}</p>
              <p>📧 ${donorEmail}</p>

              <p>
                Blood: ${donor.blood_group || "N/A"}
              </p>

              <p>
                Distance:
                ${donor.distance_km != null ? `${donor.distance_km} km` : "N/A"}
              </p>

              <p>
                Ranking:
                ${donor.ranking_score != null ? donor.ranking_score : "N/A"}
              </p>

              <p>
                Reliability:
                ${
                  donor.reliability_score != null
                    ? donor.reliability_score
                    : "N/A"
                }
              </p>

              <p>
                Response:
                <strong
                  style="color:${getStatusColor(donor.donor_response)};"
                >
                  ${donor.donor_response || "Pending"}
                </strong>
              </p>

            </div>
          `;
            })
            .join("");
        }

        const requestStatusDisplay = getStatusDisplay(request.status);

        const requestStatusColor = getStatusColor(request.status);

        const inventoryFallback =
          request.status === "Completed" && donorItems.length === 0
            ? "Used"
            : donorItems.length === 0
              ? "Awaiting donor or inventory"
              : "Not required";

        return `
        <div class="request-card">

          <h3>
            Blood Request #${request.request_id}
          </h3>

          <p>
            Blood Group: ${request.blood_group}
          </p>

          <p>
            Hospital: ${request.hospital_name}
          </p>

          <p>
            Emergency: ${request.emergency_level}
          </p>

          <p>
            Status:
            <strong style="color:${requestStatusColor};">
              ${requestStatusDisplay}
            </strong>
          </p>

          <p>
            Units Needed: ${request.units_needed}
          </p>

          <p>
            Hospital Inventory Fallback:
            ${inventoryFallback}
          </p>

          <div class="matched-donors">
            ${donorHTML}
          </div>

        </div>
      `;
      })
      .join("");

    // ONE DOM update instead of innerHTML += repeatedly
    requestContainer.innerHTML = requestsHTML;
  } catch (error) {
    console.error("My Requests Error:", error);

    if (requestContainer) {
      requestContainer.innerHTML = `<p>Unable to load requests: ${error.message}</p>`;
    }
  }
}
// ==========================================
// INITIAL LOAD
// ==========================================

async function initializeDashboard() {
  await Promise.all([
    loadDashboard(),
    loadRequests()
  ]);
}

initializeDashboard();


// ==========================================
// AUTO REFRESH DASHBOARD STATS
// ==========================================

// Refresh only dashboard statistics every 30 seconds.
// Full request data is not repeatedly fetched to reduce
// unnecessary database and server load.