const API_BASE_URL = "http://127.0.0.1:5000/api/hospitals";

// ==========================================
// GET JWT TOKEN
// ==========================================

const token =
  localStorage.getItem("token") || localStorage.getItem("access_token");

let hospitalId = null;

// ==========================================
// AUTH HEADERS
// ==========================================

function getHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

// ==========================================
// CHECK LOGIN
// ==========================================

function checkAuthentication() {
  if (!token) {
    alert("Please login first.");
    window.location.href = "login.html";
    return false;
  }

  return true;
}

// ==========================================
// LOAD HOSPITAL PROFILE
// ==========================================

async function loadHospitalProfile() {
  try {
    const response = await fetch(`${API_BASE_URL}/my-profile`, {
      headers: getHeaders(),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.message || "Unable to load hospital profile");
    }

    const hospital = data.hospital;

    // Save hospital ID
    hospitalId = hospital.hospital_id;

    // Display profile
    document.getElementById("hospitalName").textContent =
      hospital.hospital_name || "-";

    document.getElementById("hospitalCity").textContent = hospital.city || "-";

    document.getElementById("hospitalPhone").textContent =
      hospital.phone || "-";

    document.getElementById("hospitalEmail").textContent =
      hospital.email || "-";

    document.getElementById("hospitalAddress").textContent =
      hospital.address || "-";

    // Load inventory after hospital ID is available
    await loadInventory();
  } catch (error) {
    console.error("Hospital Profile Error:", error);

    document.getElementById("hospitalName").textContent =
      "Profile not available";

    alert("Unable to load hospital profile: " + error.message);
  }
}

// ==========================================
// LOAD INVENTORY
// ==========================================

async function loadInventory() {
  if (!hospitalId) {
    console.error("Hospital ID not found");
    return;
  }

  const tableBody = document.getElementById("inventoryTableBody");

  try {
    tableBody.innerHTML = `
            <tr>
                <td colspan="4">Loading inventory...</td>
            </tr>
        `;

    const response = await fetch(`${API_BASE_URL}/${hospitalId}/inventory`, {
      headers: getHeaders(),
    });

    const inventory = await response.json();

    if (!response.ok) {
      throw new Error(inventory.message || "Unable to load inventory");
    }

    renderInventory(inventory);
  } catch (error) {
    console.error("Inventory Error:", error);

    tableBody.innerHTML = `
            <tr>
                <td colspan="4">
                    Unable to load inventory
                </td>
            </tr>
        `;
  }
}

// ==========================================
// RENDER INVENTORY
// ==========================================

function renderInventory(inventory) {
  const tableBody = document.getElementById("inventoryTableBody");

  tableBody.innerHTML = "";

  let totalUnits = 0;
  let lowStockCount = 0;

  if (!inventory || inventory.length === 0) {
    tableBody.innerHTML = `
            <tr>
                <td colspan="4">
                    No inventory available
                </td>
            </tr>
        `;

    document.getElementById("bloodGroupsCount").textContent = "0";

    document.getElementById("totalUnits").textContent = "0";

    document.getElementById("lowStockCount").textContent = "0";

    return;
  }

  inventory.forEach((item) => {
    const units = Number(item.available_units) || 0;

    totalUnits += units;

    let status = "";
    let statusClass = "";

    if (units === 0) {
      status = "Out of Stock";
      statusClass = "danger";
    } else if (units <= 2) {
      status = "Low Stock";
      statusClass = "warning";

      lowStockCount++;
    } else {
      status = "Available";
      statusClass = "success";
    }

    const row = document.createElement("tr");

    row.innerHTML = `
            <td>
                <strong>${item.blood_group}</strong>
            </td>

            <td>${units}</td>

            <td>
                ${item.last_updated || "-"}
            </td>

            <td>
                <span class="inventory-status ${statusClass}">
                    ${status}
                </span>
            </td>
        `;

    tableBody.appendChild(row);
  });

  // Update statistics

  document.getElementById("bloodGroupsCount").textContent = inventory.length;

  document.getElementById("totalUnits").textContent = totalUnits;

  document.getElementById("lowStockCount").textContent = lowStockCount;
}

// ==========================================
// ADD BLOOD UNITS
// ==========================================

async function addBloodUnits() {
  const bloodGroup = document.getElementById("addBloodGroup").value;

  const units = document.getElementById("addUnits").value;

  if (!bloodGroup || !units) {
    alert("Please select blood group and enter units");

    return;
  }

  if (Number(units) <= 0) {
    alert("Units must be greater than zero");

    return;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/${hospitalId}/inventory/add`,
      {
        method: "POST",

        headers: getHeaders(),

        body: JSON.stringify({
          blood_group: bloodGroup,
          units: Number(units),
        }),
      },
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Unable to add blood units");
    }

    alert("Blood units added successfully!");

    // Clear inputs
    document.getElementById("addBloodGroup").value = "";

    document.getElementById("addUnits").value = "";

    // Refresh inventory
    await loadInventory();
  } catch (error) {
    console.error("Add Inventory Error:", error);

    alert("Error: " + error.message);
  }
}

// ==========================================
// USE BLOOD UNITS
// ==========================================

async function useBloodUnits() {
  const bloodGroup = document.getElementById("useBloodGroup").value;

  const units = document.getElementById("useUnits").value;

  if (!bloodGroup || !units) {
    alert("Please select blood group and enter units");

    return;
  }

  if (Number(units) <= 0) {
    alert("Units must be greater than zero");

    return;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/${hospitalId}/inventory/use`,
      {
        method: "POST",

        headers: getHeaders(),

        body: JSON.stringify({
          blood_group: bloodGroup,
          units: Number(units),
        }),
      },
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Unable to use blood units");
    }

    alert("Blood units updated successfully!");

    // Clear inputs
    document.getElementById("useBloodGroup").value = "";

    document.getElementById("useUnits").value = "";

    // Refresh inventory
    await loadInventory();
  } catch (error) {
    console.error("Use Inventory Error:", error);

    alert("Error: " + error.message);
  }
}

// ==========================================
// LOGOUT
// ==========================================

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("access_token");

  window.location.href = "login.html";
}

// ==========================================
// EVENT LISTENERS
// ==========================================

document.addEventListener("DOMContentLoaded", async () => {
  if (!checkAuthentication()) {
    return;
  }

  document
    .getElementById("addUnitsBtn")
    .addEventListener("click", addBloodUnits);

  document
    .getElementById("useUnitsBtn")
    .addEventListener("click", useBloodUnits);

  document.getElementById("logoutBtn").addEventListener("click", logout);

  // Load dashboard
  await loadHospitalProfile();
});
