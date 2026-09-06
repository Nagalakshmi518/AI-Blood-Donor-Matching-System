const API_URL = "https://ai-blood-donor-matching-system.onrender.com";
const requestForm = document.getElementById("requestForm");

const requestMessage = document.getElementById("requestMessage");

const latitudeInput = document.getElementById("hospital_latitude");

const longitudeInput = document.getElementById("hospital_longitude");

const selectedLocation = document.getElementById("selectedLocation");

// Inject CSS for map and selected location styling
const style = document.createElement("style");
style.textContent = `
#hospitalMap {
  width: 100%;
  height: 380px;
  margin-top: 10px;
  margin-bottom: 12px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #ddd;
}

.map-help-text {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.selected-location {
  font-size: 14px;
  color: #666;
  margin-bottom: 18px;
  font-weight: 500;
}
`;
document.head.appendChild(style);
// =====================================================
// MAP INITIALIZATION
// =====================================================

// Default location: Guntur, Andhra Pradesh
const defaultLatitude = 16.3067;
const defaultLongitude = 80.4365;

// Create map
const hospitalMap = L.map("hospitalMap").setView(
  [defaultLatitude, defaultLongitude],
  13,
);

// Add OpenStreetMap tiles
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
}).addTo(hospitalMap);

// Marker variable
let hospitalMarker = null;

// =====================================================
// SELECT LOCATION BY CLICKING MAP
// =====================================================

hospitalMap.on("click", function (event) {
  const latitude = event.latlng.lat;
  const longitude = event.latlng.lng;

  // Save coordinates
  latitudeInput.value = latitude.toFixed(6);
  longitudeInput.value = longitude.toFixed(6);

  // Remove previous marker
  if (hospitalMarker) {
    hospitalMap.removeLayer(hospitalMarker);
  }

  // Add new marker
  hospitalMarker = L.marker([latitude, longitude]).addTo(hospitalMap);

  hospitalMarker.bindPopup("Selected Hospital Location").openPopup();

  // Show selected location
  selectedLocation.textContent = `Selected Location: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
  selectedLocation.style.color = "green";
});

// =====================================================
// SUBMIT BLOOD REQUEST
// =====================================================

requestForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  // Get JWT token
  const token = localStorage.getItem("token");

  if (!token) {
    requestMessage.textContent = "Please login first.";

    return;
  }

  // Check location selected
  if (!latitudeInput.value || !longitudeInput.value) {
    requestMessage.textContent =
      "Please select the hospital location on the map.";

    requestMessage.style.color = "red";

    return;
  }

  // Prepare request data
  const data = {
    blood_group: document.getElementById("blood_group").value,

    units_needed: Number(document.getElementById("units_needed").value),

    emergency_level: document.getElementById("emergency_level").value,

    hospital_name: document.getElementById("hospital_name").value,

    hospital_latitude: Number(latitudeInput.value),

    hospital_longitude: Number(longitudeInput.value),

    notes: document.getElementById("notes").value,
  };

  console.log("Sending Blood Request:", data);

  try {
    const response = await fetch(
      `${API_URL}/api/requests/`,

      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",

          Authorization: `Bearer ${token}`,
        },

        body: JSON.stringify(data),
      },
    );

    const result = await response.json();

    if (!response.ok) {
      requestMessage.textContent =
        result.message || "Failed to create blood request.";

      requestMessage.style.color = "red";

      return;
    }

    requestMessage.textContent = "Blood request created successfully!";

    requestMessage.style.color = "green";

    // Reset form
    requestForm.reset();

    // Remove marker
    if (hospitalMarker) {
      hospitalMap.removeLayer(hospitalMarker);

      hospitalMarker = null;
    }

    selectedLocation.textContent =
      "Please select the hospital location on the map.";

    // Redirect
    setTimeout(function () {
      window.location.href = "patient-dashboard.html";
    }, 1500);
  } catch (error) {
    console.error("Error:", error);

    requestMessage.textContent = "Unable to connect to backend.";

    requestMessage.style.color = "red";
  }
});
