const API_URL = "http://127.0.0.1:5000";
const requestForm = document.getElementById("requestForm");
const requestMessage = document.getElementById("requestMessage");

let selectedLatitude = null;
let selectedLongitude = null;

const mapButton = document.getElementById("selectLocation");
if (mapButton) {
  mapButton.addEventListener("click", () => {
    window.open("https://www.google.com/maps/search/hospitals", "_blank");
    alert(
      "Open Google Maps.\n\nRight Click your hospital location -> What's Here?\n\nCopy Latitude & Longitude and paste below.",
    );
  });
}

requestForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  requestMessage.textContent = "";
  requestMessage.style.color = "";

  const token = localStorage.getItem("token");

  if (!token) {
    requestMessage.style.color = "red";
    requestMessage.textContent = "Please Login.";
    return;
  }

  selectedLatitude = parseFloat(
    document.getElementById("hospital_latitude").value,
  );
  selectedLongitude = parseFloat(
    document.getElementById("hospital_longitude").value,
  );

  if (isNaN(selectedLatitude) || isNaN(selectedLongitude)) {
    requestMessage.style.color = "red";
    requestMessage.textContent = "Please enter Hospital Latitude & Longitude.";
    return;
  }

  const data = {
    blood_group: document.getElementById("blood_group").value,
    units_needed: Number(document.getElementById("units_needed").value),
    emergency_level: document.getElementById("emergency_level").value,
    hospital_name: document.getElementById("hospital_name").value,
    hospital_latitude: selectedLatitude,
    hospital_longitude: selectedLongitude,
    notes: document.getElementById("notes").value,
  };

  try {
    const response = await fetch(`${API_URL}/api/requests/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok) {
      requestMessage.style.color = "red";
      requestMessage.textContent =
        result.message || "Failed to create request.";
      return;
    }

    const requestDetails = result.request || {};
    const requestStatus = requestDetails.status || "Pending";
    const matchingStatus = result.matching_status || "Pending";

    requestMessage.style.color = "green";
    requestMessage.innerHTML = `
      <strong>Blood Request Created Successfully.</strong><br>
      Status: ${requestStatus}<br>
      Matching Status: ${matchingStatus}<br>
      Blood Group: ${requestDetails.blood_group || data.blood_group}<br>
      Emergency Level: ${requestDetails.emergency_level || data.emergency_level}
    `;

    requestForm.reset();

    setTimeout(() => {
      window.location.href = "my-requests.html";
    }, 1500);
  } catch (error) {
    console.error(error);
    requestMessage.style.color = "red";
    requestMessage.textContent = "Unable to connect to backend.";
  }
});
