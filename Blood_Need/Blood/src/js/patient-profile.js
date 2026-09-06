const API_URL = "https://ai-blood-donor-matching-system.onrender.com";
const token = localStorage.getItem("token");
const user = JSON.parse(localStorage.getItem("user") || "null");
const locationMessage = document.getElementById("locationMessage");

if (!token || !user) {
  window.location.href = "login.html";
}

const form = document.getElementById("patientProfileForm");
const message = document.getElementById("profileMessage");

form.addEventListener("submit", async function (event) {
  event.preventDefault();

  const data = {
    user_id: user.user_id,
    blood_group: document.getElementById("blood_group").value,
    age: Number(document.getElementById("age").value),
    gender: document.getElementById("gender").value,
    hospital_name: document.getElementById("hospital_name").value,
    latitude: document.getElementById("latitude").value || null,
    longitude: document.getElementById("longitude").value || null,
  };

  try {
    const response = await fetch(`${API_URL}/api/patients/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (response.ok) {
      message.textContent = "Profile saved successfully.";
      window.location.href = "patient-dashboard.html";
    } else {
      message.textContent = result.message || "Unable to save profile.";
    }
  } catch (error) {
    console.error(error);
    message.textContent = "Unable to connect to backend.";
  }
});

document
  .getElementById("getLocationButton")
  .addEventListener("click", function () {
    if (!navigator.geolocation) {
      locationMessage.textContent =
        "Location is not supported by this browser. You can enter your location manually.";
      locationMessage.style.color = "orange";
      return;
    }

    navigator.geolocation.getCurrentPosition(
      function (position) {
        document.getElementById("latitude").value = position.coords.latitude;
        document.getElementById("longitude").value = position.coords.longitude;
        locationMessage.textContent = "Location captured successfully.";
        locationMessage.style.color = "green";
      },
      function () {
        locationMessage.textContent =
          "Location permission unavailable. You can enter your location manually.";
        locationMessage.style.color = "orange";
      },
    );
  });
