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

  if (normalizedRole === "PATIENT") {
    return "patient-dashboard.html";
  }

  if (normalizedRole === "ADMIN") {
    return "admin-dashboard.html";
  }

  return "donor-dashboard.html";
}

function goBackToDashboard() {
  const role = getStoredRole();

  if (role === "PATIENT") {
    window.location.href = "patient-dashboard.html";
    return;
  }

  if (role === "ADMIN") {
    window.location.href = "admin-dashboard.html";
    return;
  }

  window.location.href = "donor-dashboard.html";
}

function getAuthToken() {
  return localStorage.getItem("token");
}

const profileForm = document.getElementById("profileForm");
const profileMessage = document.getElementById("profileMessage");
const updateLocationButton = document.getElementById("updateLocationButton");
const locationMessage = document.getElementById("locationMessage");

const token = getAuthToken();
if (!token) {
  window.location.href = "login.html";
}

const currentRole = getStoredRole();
if (currentRole && currentRole !== "DONOR") {
  window.location.href = getDashboardForRole(currentRole);
}

async function loadDonorProfile() {
  const token = getAuthToken();

  if (!token) {
    window.location.href = "login.html";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/api/donors/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (response.status === 401) {
      console.warn("Token is invalid or expired");
      window.location.href = "login.html";
      return;
    }

    const data = await response.json();

    if (!response.ok) {
      console.error("Error loading profile:", data);
      if (profileMessage) {
        profileMessage.textContent = data.message || "Unable to load profile";
        profileMessage.style.color = "red";
      }
      return;
    }

    const donor = data;

    if (donor.blood_group) {
      const bloodGroupSelect = document.getElementById("blood_group");
      if (bloodGroupSelect) {
        bloodGroupSelect.value = donor.blood_group;
      }
    }

    if (donor.age) {
      const ageInput = document.getElementById("age");
      if (ageInput) {
        ageInput.value = donor.age;
      }
    }

    if (donor.gender) {
      const genderSelect = document.getElementById("gender");
      if (genderSelect) {
        genderSelect.value = donor.gender;
      }
    }

    if (donor.weight) {
      const weightInput = document.getElementById("weight");
      if (weightInput) {
        weightInput.value = donor.weight;
      }
    }

    if (donor.address) {
      const addressInput = document.getElementById("address");
      if (addressInput) {
        addressInput.value = donor.address;
      }
    }

    if (donor.latitude) {
      const latInput = document.getElementById("latitude");
      if (latInput) {
        latInput.value = donor.latitude;
      }
    }

    if (donor.longitude) {
      const lonInput = document.getElementById("longitude");
      if (lonInput) {
        lonInput.value = donor.longitude;
      }
    }
  } catch (error) {
    console.error("Error loading profile:", error);
    if (profileMessage) {
      profileMessage.textContent =
        "Unable to connect to backend. Please check your connection.";
      profileMessage.style.color = "red";
    }
  }
}

if (profileForm) {
  profileForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const token = getAuthToken();
    if (!token) {
      window.location.href = "login.html";
      return;
    }

    const data = {
      blood_group: document.getElementById("blood_group").value,
      age: Number(document.getElementById("age").value),
      gender: document.getElementById("gender").value,
      weight: document.getElementById("weight").value
        ? Number(document.getElementById("weight").value)
        : null,
      address: document.getElementById("address").value || null,
      latitude: document.getElementById("latitude").value
        ? Number(document.getElementById("latitude").value)
        : null,
      longitude: document.getElementById("longitude").value
        ? Number(document.getElementById("longitude").value)
        : null,
    };

    if (!data.blood_group || !data.age || !data.gender) {
      if (profileMessage) {
        profileMessage.textContent = "Please fill in all required fields.";
        profileMessage.style.color = "orange";
      }
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/donors/me`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (response.status === 401) {
        console.warn("Token is invalid or expired during profile update");
        window.location.href = "login.html";
        return;
      }

      const result = await response.json();

      if (!response.ok) {
        console.error("Error updating profile:", result);
        if (profileMessage) {
          profileMessage.textContent =
            result.message || "Failed to update profile.";
          profileMessage.style.color = "red";
        }
        return;
      }

      if (profileMessage) {
        profileMessage.textContent = "✓ Profile updated successfully!";
        profileMessage.style.color = "green";
      }

      setTimeout(() => {
        loadDonorProfile();
      }, 1000);
    } catch (error) {
      console.error("Error updating profile:", error);
      if (profileMessage) {
        profileMessage.textContent =
          "Unable to connect to backend. Please check your connection.";
        profileMessage.style.color = "red";
      }
    }
  });
}

if (updateLocationButton) {
  updateLocationButton.addEventListener("click", function () {
    if (!navigator.geolocation) {
      if (locationMessage) {
        locationMessage.textContent =
          "Geolocation is not supported by your browser. You can enter coordinates manually.";
        locationMessage.style.color = "orange";
      }
      return;
    }

    if (locationMessage) {
      locationMessage.textContent = "Getting your location...";
      locationMessage.style.color = "blue";
    }

    navigator.geolocation.getCurrentPosition(
      function (position) {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        document.getElementById("latitude").value = lat;
        document.getElementById("longitude").value = lon;

        if (locationMessage) {
          locationMessage.textContent = `✓ Location captured: ${lat.toFixed(4)}, ${lon.toFixed(4)}`;
          locationMessage.style.color = "green";
        }
      },
      function (error) {
        console.error("Geolocation error:", error);
        if (locationMessage) {
          locationMessage.textContent =
            "Unable to access your location. You can enter coordinates manually.";
          locationMessage.style.color = "orange";
        }
      },
    );
  });
}

loadDonorProfile();
