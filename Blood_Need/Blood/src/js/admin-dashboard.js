const API_BASE = "https://ai-blood-donor-matching-system.onrender.com";
const API_URL = `${API_BASE}/api/admin`;
const HOSPITAL_API_URL = `${API_BASE}/api/hospitals`;

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

  if (normalizedRole === "PATIENT") {
    return "patient-dashboard.html";
  }

  return "admin-dashboard.html";
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

if (!ensureExpectedRole("ADMIN")) {
  throw new Error("Unauthorized admin dashboard access.");
}

// ================================
// LOGOUT
// ================================

document.getElementById("logoutBtn").addEventListener("click", () => {
  safeLogout();
});
// ================================
// COMMON FETCH
// ================================

async function api(url) {
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (response.status === 401) {
    console.warn("Admin API session expired or invalid.");
    window.location.href = "login.html";
    return null;
  }

  if (!response.ok) {
    alert(data.message || "Request failed.");
    throw new Error(data.message || "Request failed.");
  }

  return data;
}

// ================================
// DASHBOARD SUMMARY
// ================================

async function loadSummary() {
  const data = await api(`${API_URL}/dashboard`);

  document.getElementById("summaryCards").innerHTML = `

<div class="card">
<h3>Total Users</h3>
<h1>${data.total_users}</h1>
</div>

<div class="card">
<h3>Donors</h3>
<h1>${data.total_donors}</h1>
</div>

<div class="card">
<h3>Patients</h3>
<h1>${data.total_patients}</h1>
</div>

<div class="card">
<h3>Blood Requests</h3>
<h1>${data.total_requests}</h1>
</div>

<div class="card">
<h3>Donations</h3>
<h1>${data.total_donations}</h1>
</div>

<div class="card">
<h3>Pending Requests</h3>
<h1>${data.pending_requests}</h1>
</div>
<div class="card">
<h3>Matched</h3>
<h1>${data.matched_requests}</h1>
</div>

<div class="card">
<h3>Accepted</h3>
<h1>${data.accepted_requests}</h1>
</div>

<div class="card">
<h3>Completed</h3>
<h1>${data.completed_requests}</h1>
</div>

`;
}

// ================================
// USERS
// ================================

async function loadUsers() {
  const users = await api(`${API_URL}/users`);

  let html = `

<table>

<tr>

<th>ID</th>
<th>Name</th>
<th>Email</th>
<th>Role</th>
<th>Status</th>
<th>Actions</th>

</tr>

`;

  users.forEach((user) => {
    html += `

<tr>

<td>${user.user_id}</td>

<td>${user.full_name}</td>

<td>${user.email}</td>

<td>${user.role}</td>

<td>${user.active ? "Active" : "Blocked"}</td>

<td>

<button
class="${user.active ? "block-btn" : "unblock-btn"}"
onclick="toggleUser(${user.user_id},${user.active})">

${user.active ? "Block" : "Unblock"}

</button>

<button
class="delete-btn"
onclick="deleteUser(${user.user_id})">

Delete

</button>

</td>

</tr>

`;
  });

  html += "</table>";

  document.getElementById("usersTable").innerHTML = html;
}

// ================================
// BLOCK / UNBLOCK USER
// ================================

async function toggleUser(id, active) {
  const endpoint = active ? "block" : "unblock";

  await fetch(
    `${API_URL}/users/${id}/${endpoint}`,

    {
      method: "PATCH",

      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  loadUsers();
}

// ================================
// DELETE USER
// ================================

async function deleteUser(id) {
  if (!confirm("Delete user?")) return;

  const response = await fetch(`${API_URL}/users/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadUsers();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete user.");
}
// ================================
// DONORS
// ================================

async function loadDonors() {
  const donors = await api(`${API_URL}/donors`);

  let html = `

<table>

<tr>

<th>ID</th>
<th>Blood</th>
<th>Age</th>
<th>Phone</th>
<th>Availability</th>
<th>Reliability</th>
<th>Action</th>

</tr>

`;

  donors.forEach((donor) => {
    html += `

<tr>

<td>${donor.donor_id}</td>

<td>${donor.blood_group}</td>

<td>${donor.age}</td>

<td>${donor.phone}</td>

<td>${donor.availability ? "Available" : "Unavailable"}</td>

<td>${donor.reliability_score}</td>

<td>

<button
class="delete-btn"
onclick="deleteDonor(${donor.donor_id})">

Delete

</button>

</td>

</tr>

`;
  });

  html += "</table>";

  document.getElementById("donorsTable").innerHTML = html;
}

// ================================
// DELETE DONOR
// ================================

async function deleteDonor(id) {
  if (!confirm("Delete donor?")) return;

  const response = await fetch(`${API_URL}/donors/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadDonors();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete donor.");
}

// ================================
// PATIENTS
// ================================

async function loadPatients() {
  const patients = await api(`${API_URL}/patients`);

  let html = `

<table>

<tr>

<th>ID</th>
<th>Blood</th>
<th>Age</th>
<th>Hospital</th>
<th>Action</th>

</tr>

`;

  patients.forEach((patient) => {
    html += `

<tr>

<td>${patient.patient_id}</td>

<td>${patient.blood_group}</td>

<td>${patient.age}</td>

<td>${patient.hospital_name}</td>

<td>

<button
class="delete-btn"
onclick="deletePatient(${patient.patient_id})">

Delete

</button>
</td>

</tr>

`;
  });

  html += "</table>";

  document.getElementById("patientsTable").innerHTML = html;
}

// ================================
// DELETE PATIENT
// ================================

async function deletePatient(id) {
  if (!confirm("Delete patient?")) return;

  const response = await fetch(`${API_URL}/patients/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadPatients();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete patient.");
}

// ================================
// BLOOD REQUESTS
// ================================

async function loadRequests() {
  const requests = await api(`${API_URL}/requests`);

  let html = `

<table>

<tr>

<th>ID</th>
<th>Blood</th>
<th>Units</th>
<th>Status</th>
<th>Emergency</th>
<th>Action</th>

</tr>

`;

  requests.forEach((req) => {
    html += `

<tr>

<td>${req.request_id}</td>

<td>${req.blood_group}</td>

<td>${req.units_needed}</td>

<td>${req.status}</td>

<td>${req.emergency_level}</td>

<td>

<button
class="delete-btn"
onclick="deleteRequest(${req.request_id})">

Delete

</button>

</td>

</tr>

`;
  });

  html += "</table>";

  document.getElementById("requestsTable").innerHTML = html;
}

// ================================
// DELETE REQUEST
// ================================

async function deleteRequest(id) {
  if (!confirm("Delete Request?")) return;

  const response = await fetch(`${API_URL}/requests/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadRequests();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete request.");
}
// ================================
// DONATIONS
// ================================

async function loadDonations() {
  const donations = await api(`${API_URL}/donations`);

  let html = `

<table>

<tr>

<th>ID</th>
<th>Donor</th>
<th>Patient</th>
<th>Date</th>
<th>Units</th>
<th>Action</th>
<th>Status</th>

</tr>

`;

  donations.forEach((donation) => {
    html += `

<tr>

<td>${donation.donation_id}</td>

<td>${donation.donor_id}</td>

<td>${donation.patient_id}</td>

<td>${donation.donation_date}</td>

<td>${donation.units_donated}</td>
<td>${donation.donation_status}</td>

<td>

<button
class="delete-btn"
onclick="deleteDonation(${donation.donation_id})">

Delete

</button>

</td>

</tr>

`;
  });

  html += "</table>";

  document.getElementById("donationsTable").innerHTML = html;
}

// ================================
// DELETE DONATION
// ================================

async function deleteDonation(id) {
  if (!confirm("Delete Donation?")) return;

  const response = await fetch(`${API_URL}/donations/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadDonations();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete donation.");
}

// ================================
// MATCHES
// ================================

async function loadMatches() {
  const matches = await api(`${API_URL}/matches`);

  let html = `

<table>

<tr>

<th>ID</th>
<th>Request</th>
<th>Donor</th>
<th>Score</th>
<th>Distance</th>
<th>Status</th>
<th>Action</th>

</tr>

`;

  matches.forEach((match) => {
    html += `

<tr>

<td>${match.match_id}</td>

<td>${match.request_id}</td>

<td>${match.donor_id}</td>

<td>${match.ranking_score}</td>

<td>${match.distance_km} km</td>

<td>${match.donor_response}</td>

<td>
<button
class="delete-btn"
onclick="deleteMatch(${match.match_id})">

Delete

</button>

</td>

</tr>

`;
  });

  html += "</table>";

  document.getElementById("matchesTable").innerHTML = html;
}

// ================================
// DELETE MATCH
// ================================

async function deleteMatch(id) {
  if (!confirm("Delete Match?")) return;

  const response = await fetch(`${API_URL}/matches/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    loadMatches();
    return;
  }

  const data = await response.json();
  alert(data.message || "Failed to delete match.");
}

// ================================
// HOSPITAL INVENTORY MANAGEMENT
// ================================

async function loadInventory() {
  const inventory = await api(`${HOSPITAL_API_URL}/inventory`);

  let html = `

<table>

<tr>

<th>Hospital</th>
<th>Blood Group</th>
<th>Available Units</th>
<th>Updated</th>
<th>Action</th>

</tr>

`;

  inventory.forEach((item) => {
    html += `

<tr>

<td>${item.hospital_name || item.hospital_id}</td>

<td>${item.blood_group}</td>

<td>${item.available_units}</td>

<td>${item.last_updated || "N/A"}</td>

<td>

<button
class="block-btn"
onclick="addInventoryUnits(${item.hospital_id}, '${item.blood_group}')">
Add Units
</button>

<button
class="delete-btn"
onclick="useInventoryUnits(${item.hospital_id}, '${item.blood_group}')">
Use Units
</button>

</td>

</tr>

`;
  });

  html += "</table>";

  document.getElementById("inventoryTable").innerHTML = html;
}

async function addInventoryUnits(hospitalId, bloodGroup) {
  const units = Number(
    prompt(
      `How many units of ${bloodGroup} would you like to add to this hospital inventory?`,
      "1",
    ),
  );

  if (!units || units <= 0 || Number.isNaN(units)) {
    return;
  }

  const response = await fetch(
    `${HOSPITAL_API_URL}/${hospitalId}/inventory/add`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ blood_group: bloodGroup, units }),
    },
  );

  const data = await response.json();

  if (!response.ok) {
    alert(data.message || "Failed to add inventory units.");
    return;
  }

  alert(`${units} units of ${bloodGroup} added successfully.`);
  loadInventory();
}

async function useInventoryUnits(hospitalId, bloodGroup) {
  const units = Number(
    prompt(
      `How many units of ${bloodGroup} should be deducted from this hospital inventory?`,
      "1",
    ),
  );

  if (!units || units <= 0 || Number.isNaN(units)) {
    return;
  }

  const response = await fetch(
    `${HOSPITAL_API_URL}/${hospitalId}/inventory/use`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ blood_group: bloodGroup, units }),
    },
  );

  const data = await response.json();

  if (!response.ok) {
    alert(data.message || "Failed to use inventory units.");
    return;
  }

  alert(`${units} units of ${bloodGroup} used successfully.`);
  loadInventory();
}

// ================================
// ANALYTICS
// ================================

async function loadAnalytics() {
  const analytics = await api(`${API_URL}/analytics`);

  document.getElementById("analyticsCards").innerHTML = `

<div class="summary-grid">

<div class="summary-card">

<h3>Total Users</h3>

<h2>${analytics.users}</h2>

</div>

<div class="card">

<h3>Total Donors</h3>

<h2>${analytics.donors}</h2>

</div>

<div class="card">

<h3>Total Patients</h3>

<h2>${analytics.patients}</h2>

</div>

<div class="card">

<h3>Total Requests</h3>

<h2>${analytics.requests}</h2>

</div>

<div class="card">

<h3>Pending</h3>

<h2>${analytics.pending_requests}</h2>

</div>

<div class="card">

<h3>Matched</h3>

<h2>${analytics.matched_requests}</h2>

</div>

<div class="card">

<h3>Accepted</h3>

<h2>${analytics.accepted_requests}</h2>

</div>

<div class="card">

<h3>Completed</h3>

<h2>${analytics.completed_requests}</h2>

</div>

<div class="card">

<h3>Cancelled</h3>

<h2>${analytics.cancelled_requests}</h2>

</div>

<div class="card">

<h3>Donations</h3>

<h2>${analytics.total_donations}</h2>

</div>

</div>

`;
}

// ================================
// REPORTS
// ================================

//document.getElementById(
//  "downloadDonorReport"
//).onclick = () => {

// window.open(
//   `${API_URL}/reports/donors`,
// "_blank"
//);

//};
// ================================
// REPORTS
// ================================

async function downloadReport(url, filename) {
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    alert("Failed to download report");
    return;
  }

  const blob = await response.blob();

  const link = document.createElement("a");

  link.href = URL.createObjectURL(blob);

  link.download = filename;

  link.click();
}

document.getElementById("downloadDonorReport").onclick = () => {
  downloadReport(`${API_URL}/reports/donors`, "donor_report.csv");
};

document.getElementById("downloadPatientReport").onclick = () => {
  downloadReport(`${API_URL}/reports/patients`, "patient_report.csv");
};

document.getElementById("downloadRequestReport").onclick = () => {
  downloadReport(`${API_URL}/reports/requests`, "request_report.csv");
};

document.getElementById("downloadDonationReport").onclick = () => {
  downloadReport(`${API_URL}/reports/donations`, "donation_report.csv");
};
// ================================
// INITIAL LOAD
// ================================

async function initializeDashboard() {
  try {
    await loadSummary();

    await loadUsers();

    await loadDonors();

    await loadPatients();

    await loadRequests();

    await loadDonations();

    await loadMatches();

    await loadInventory();
  } catch (error) {
    console.error(error);

    alert("Unable to load admin dashboard.");
  }
}

initializeDashboard();

// ================================
// AUTO REFRESH
// ================================
document.getElementById("refreshBtn").addEventListener("click", () => {
  initializeDashboard();
});

setInterval(() => {
  initializeDashboard();
}, 30000);
// ==========================================
// SEARCH USERS
// ==========================================

function searchUsers() {
  const input = document.getElementById("userSearch");

  if (!input) {
    console.error("userSearch element not found");
    return;
  }

  const searchValue = input.value.trim().toLowerCase();

  const table = document.querySelector("#usersTable table");

  if (!table) {
    return;
  }

  const rows = table.querySelectorAll("tbody tr");

  rows.forEach((row) => {
    const rowText = row.innerText.toLowerCase();

    if (rowText.includes(searchValue)) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}
// ==========================================
// USER SEARCH
// ==========================================

const searchUser = document.getElementById("searchUser");

if (searchUser) {
  searchUser.addEventListener("input", function () {
    const searchText = this.value.trim().toLowerCase();

    const table = document.querySelector("#usersTable table");

    if (!table) {
      return;
    }

    const rows = table.querySelectorAll("tbody tr");

    rows.forEach((row) => {
      const rowText = row.innerText.toLowerCase();

      row.style.display = rowText.includes(searchText) ? "" : "none";
    });
  });
}

// ==========================================
// REFRESH USERS
// ==========================================

const refreshBtn = document.getElementById("refreshBtn");

if (refreshBtn) {
  refreshBtn.addEventListener("click", async function () {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "Refreshing...";

    try {
      await loadUsers();
    } catch (error) {
      console.error("Refresh Users Error:", error);
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "Refresh";
    }
  });
}
