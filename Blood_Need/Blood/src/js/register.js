const API_URL = "https://ai-blood-donor-matching-system.onrender.com";

const registerForm = document.getElementById("registerForm");
const roleSelect = document.getElementById("role");

const donorFields = document.getElementById("donorFields");
const hospitalFields = document.getElementById("hospitalFields");

const locationMessage = document.getElementById("locationMessage");

const getLocationButton = document.getElementById("getLocation");
const retryLocationButton = document.getElementById("retryLocation");

const getHospitalLocationButton = document.getElementById(
  "getHospitalLocation",
);

const formMessage = document.getElementById("formMessage");
const successMessage = document.getElementById("successMessage");

const submitButton = document.getElementById("registerButton");

// =====================================================
// FIELD ERROR
// =====================================================

function setFieldError(fieldId, message) {
  const field = document.getElementById(fieldId);

  const errorNode = document.getElementById(`${fieldId}_error`);

  if (field) {
    field.setAttribute("aria-invalid", message ? "true" : "false");
  }

  if (errorNode) {
    errorNode.textContent = message || "";
  }
}

// =====================================================
// CLEAR FIELD ERRORS
// =====================================================

function clearFieldErrors() {
  const fields = [
    // Common
    "full_name",
    "email",
    "phone",
    "role",
    "password",
    "confirm_password",

    // Donor
    "age",
    "gender",
    "weight",
    "blood_group",
    "address",
    "latitude",
    "longitude",

    // Hospital
    "hospital_name",
    "hospital_phone",
    "hospital_email",
    "hospital_address",
    "city",
    "state",
    "pincode",
    "hospital_latitude",
    "hospital_longitude",
  ];

  fields.forEach((fieldId) => {
    setFieldError(fieldId, "");
  });
}

// =====================================================
// FORM MESSAGE
// =====================================================

function setFormMessage(message, type = "error") {
  if (formMessage) {
    formMessage.textContent = type === "error" ? message || "" : "";
  }

  if (successMessage) {
    successMessage.textContent = type === "success" ? message || "" : "";
  }
}

// =====================================================
// LOADING BUTTON
// =====================================================

function setLoading(isLoading) {
  if (!submitButton) return;

  submitButton.disabled = isLoading;

  submitButton.textContent = isLoading ? "Creating account..." : "Register";
}

// =====================================================
// DONOR LOCATION MESSAGE
// =====================================================

function setLocationMessage(message, tone = "info") {
  if (!locationMessage) return;

  locationMessage.textContent = message || "";

  locationMessage.className = `location-message ${tone}`;
}

// =====================================================
// RESET DONOR FIELDS
// =====================================================

function resetDonorFields() {
  if (!donorFields) return;

  const donorInputs = donorFields.querySelectorAll("input, select");

  donorInputs.forEach((input) => {
    if (input.id === "availability") {
      input.value = "true";
      return;
    }

    input.value = "";

    input.setAttribute("aria-invalid", "false");
  });

  setLocationMessage(
    "Location is optional. You can enter your address manually.",
    "info",
  );
}

// =====================================================
// RESET HOSPITAL FIELDS
// =====================================================

function resetHospitalFields() {
  if (!hospitalFields) return;

  const hospitalInputs = hospitalFields.querySelectorAll("input, select");

  hospitalInputs.forEach((input) => {
    input.value = "";

    input.setAttribute("aria-invalid", "false");
  });
}

// =====================================================
// TOGGLE ROLE FIELDS
// =====================================================

function toggleRoleFields() {
  const selectedRole = roleSelect ? roleSelect.value : "";

  const isDonor = selectedRole === "DONOR";

  const isHospital = selectedRole === "HOSPITAL";

  // Donor Fields

  if (donorFields) {
    donorFields.hidden = !isDonor;
  }

  // Hospital Fields

  if (hospitalFields) {
    hospitalFields.hidden = !isHospital;
  }

  // Reset fields when switching role

  if (!isDonor) {
    resetDonorFields();
  }

  if (!isHospital) {
    resetHospitalFields();
  }
}

// =====================================================
// GET DONOR CURRENT LOCATION
// =====================================================

function getCurrentLocation() {
  if (!navigator.geolocation) {
    setLocationMessage("Location is not supported by this browser.", "error");

    return;
  }

  setLocationMessage("Fetching your current location...", "info");

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const latitude = position.coords.latitude;

      const longitude = position.coords.longitude;

      const latitudeInput = document.getElementById("latitude");

      const longitudeInput = document.getElementById("longitude");

      if (latitudeInput) {
        latitudeInput.value = latitude;
      }

      if (longitudeInput) {
        longitudeInput.value = longitude;
      }

      setLocationMessage("Current location captured successfully.", "success");
    },

    (error) => {
      console.warn("Location error:", error);

      let message =
        "Location permission was denied. Please allow location access and try again.";

      if (error.code === error.POSITION_UNAVAILABLE) {
        message = "Your current location could not be determined.";
      } else if (error.code === error.TIMEOUT) {
        message = "Location request timed out. Please try again.";
      }

      setLocationMessage(message, "error");
    },

    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0,
    },
  );
}

// =====================================================
// GET HOSPITAL LOCATION
// =====================================================

function getHospitalLocation() {
  if (!navigator.geolocation) {
    alert("Location is not supported by this browser.");

    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const latitudeInput = document.getElementById("hospital_latitude");

      const longitudeInput = document.getElementById("hospital_longitude");

      if (latitudeInput) {
        latitudeInput.value = position.coords.latitude;
      }

      if (longitudeInput) {
        longitudeInput.value = position.coords.longitude;
      }

      alert("Hospital location captured successfully.");
    },

    () => {
      alert(
        "Unable to get location. Please enter latitude and longitude manually.",
      );
    },

    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0,
    },
  );
}

// =====================================================
// VALIDATE REGISTRATION FORM
// =====================================================

function validateRegistrationForm() {
  let isValid = true;

  clearFieldErrors();

  setFormMessage("");

  // -----------------------------------
  // COMMON FIELDS
  // -----------------------------------

  const fullName = document.getElementById("full_name").value.trim();

  const email = document.getElementById("email").value.trim();

  const phone = document.getElementById("phone").value.trim();

  const password = document.getElementById("password").value;

  const confirmPassword = document.getElementById("confirm_password").value;

  const selectedRole = roleSelect ? roleSelect.value : "";

  if (!fullName) {
    setFieldError("full_name", "Full name is required.");

    isValid = false;
  }

  if (!email) {
    setFieldError("email", "Email is required.");

    isValid = false;
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    setFieldError("email", "Please enter a valid email address.");

    isValid = false;
  }

  if (!phone) {
    setFieldError("phone", "Phone number is required.");

    isValid = false;
  }

  if (!selectedRole) {
    setFieldError("role", "Please select a role.");

    isValid = false;
  }

  if (!password) {
    setFieldError("password", "Password is required.");

    isValid = false;
  } else if (password.length < 6) {
    setFieldError("password", "Password must be at least 6 characters long.");

    isValid = false;
  }

  if (!confirmPassword) {
    setFieldError("confirm_password", "Please confirm your password.");

    isValid = false;
  } else if (password !== confirmPassword) {
    setFieldError("confirm_password", "Passwords do not match.");

    isValid = false;
  }

  // ===================================
  // DONOR VALIDATION
  // ===================================

  if (selectedRole === "DONOR") {
    const age = document.getElementById("age").value.trim();

    const gender = document.getElementById("gender").value;

    const weight = document.getElementById("weight").value.trim();

    const bloodGroup = document.getElementById("blood_group").value;

    const address = document.getElementById("address").value.trim();

    const latitude = document.getElementById("latitude").value.trim();

    const longitude = document.getElementById("longitude").value.trim();

    if (!age) {
      setFieldError("age", "Age is required for donors.");

      isValid = false;
    } else if (Number(age) < 18) {
      setFieldError("age", "Donor must be at least 18 years old.");

      isValid = false;
    }

    if (!gender) {
      setFieldError("gender", "Gender is required.");

      isValid = false;
    }

    if (!bloodGroup) {
      setFieldError("blood_group", "Blood group is required.");

      isValid = false;
    }

    if (!address) {
      setFieldError("address", "Address is required.");

      isValid = false;
    }

    if (weight && Number(weight) < 50) {
      setFieldError("weight", "Weight must be at least 50 kg.");

      isValid = false;
    }

    if (
      (latitude && !Number.isFinite(Number(latitude))) ||
      Number(latitude) < -90 ||
      Number(latitude) > 90
    ) {
      setFieldError("latitude", "Latitude must be between -90 and 90.");

      isValid = false;
    }

    if (
      (longitude && !Number.isFinite(Number(longitude))) ||
      Number(longitude) < -180 ||
      Number(longitude) > 180
    ) {
      setFieldError("longitude", "Longitude must be between -180 and 180.");

      isValid = false;
    }

    if ((latitude && !longitude) || (!latitude && longitude)) {
      setFieldError(
        "latitude",
        "Both latitude and longitude should be provided together.",
      );

      setFieldError(
        "longitude",
        "Both latitude and longitude should be provided together.",
      );

      isValid = false;
    }
  }

  // ===================================
  // HOSPITAL VALIDATION
  // ===================================

  if (selectedRole === "HOSPITAL") {
    const hospitalName =
      document.getElementById("hospital_name")?.value.trim() || "";

    const hospitalAddress =
      document.getElementById("hospital_address")?.value.trim() || "";

    const city = document.getElementById("city")?.value.trim() || "";

    const state = document.getElementById("state")?.value.trim() || "";

    const pincode = document.getElementById("pincode")?.value.trim() || "";

    const latitude =
      document.getElementById("hospital_latitude")?.value.trim() || "";

    const longitude =
      document.getElementById("hospital_longitude")?.value.trim() || "";

    if (!hospitalName) {
      setFieldError("hospital_name", "Hospital name is required.");

      isValid = false;
    }

    if (!hospitalAddress) {
      setFieldError("hospital_address", "Hospital address is required.");

      isValid = false;
    }

    if (!city) {
      setFieldError("city", "City is required.");

      isValid = false;
    }

    if (!state) {
      setFieldError("state", "State is required.");

      isValid = false;
    }

    if (!pincode) {
      setFieldError("pincode", "Pincode is required.");

      isValid = false;
    }

    if (!latitude) {
      setFieldError("hospital_latitude", "Hospital location is required.");

      isValid = false;
    }

    if (!longitude) {
      setFieldError("hospital_longitude", "Hospital location is required.");

      isValid = false;
    }
  }

  return isValid;
}

// =====================================================
// EVENT LISTENERS
// =====================================================

if (roleSelect) {
  roleSelect.addEventListener("change", toggleRoleFields);
}

if (getLocationButton) {
  getLocationButton.addEventListener("click", getCurrentLocation);
}

if (retryLocationButton) {
  retryLocationButton.addEventListener("click", getCurrentLocation);
}

if (getHospitalLocationButton) {
  getHospitalLocationButton.addEventListener("click", getHospitalLocation);
}

// =====================================================
// REGISTER FORM SUBMIT
// =====================================================

if (registerForm) {
  registerForm.addEventListener(
    "submit",

    async (event) => {
      event.preventDefault();

      setFormMessage("");

      // Validate

      if (!validateRegistrationForm()) {
        setFormMessage(
          "Please correct the highlighted fields and try again.",
          "error",
        );

        return;
      }

      // =================================
      // COMMON USER DATA
      // =================================

      const fullName = document.getElementById("full_name").value.trim();

      const email = document.getElementById("email").value.trim();

      const phone = document.getElementById("phone").value.trim();

      const password = document.getElementById("password").value;

      const selectedRole = roleSelect ? roleSelect.value : "PATIENT";

      const userData = {
        full_name: fullName,

        email: email,

        phone: phone,

        password: password,

        role: selectedRole,
      };

      // =================================
      // DONOR DATA
      // =================================

      if (selectedRole === "DONOR") {
        const age = document.getElementById("age").value.trim();

        const gender = document.getElementById("gender").value;

        const weight = document.getElementById("weight").value.trim();

        const bloodGroup = document.getElementById("blood_group").value;

        const address = document.getElementById("address").value.trim();

        const availability =
          document.getElementById("availability").value === "true";

        const latitude = document.getElementById("latitude").value.trim();

        const longitude = document.getElementById("longitude").value.trim();

        userData.age = Number(age);

        userData.gender = gender;

        userData.weight = weight ? Number(weight) : null;

        userData.blood_group = bloodGroup;

        userData.address = address;

        userData.availability = availability;

        userData.latitude = latitude ? Number(latitude) : null;

        userData.longitude = longitude ? Number(longitude) : null;
      }

      // =================================
      // HOSPITAL DATA
      // =================================

      if (selectedRole === "HOSPITAL") {
        const hospitalName = document
          .getElementById("hospital_name")
          .value.trim();

        const hospitalPhone =
          document.getElementById("hospital_phone")?.value.trim() || "";

        const hospitalEmail =
          document.getElementById("hospital_email")?.value.trim() || "";

        const hospitalAddress = document
          .getElementById("hospital_address")
          .value.trim();

        const city = document.getElementById("city").value.trim();

        const state = document.getElementById("state").value.trim();

        const pincode = document.getElementById("pincode").value.trim();

        const latitude = document
          .getElementById("hospital_latitude")
          .value.trim();

        const longitude = document
          .getElementById("hospital_longitude")
          .value.trim();

        userData.hospital_name = hospitalName;

        userData.hospital_phone = hospitalPhone || phone;

        userData.hospital_email = hospitalEmail || email;

        userData.address = hospitalAddress;

        userData.city = city;

        userData.state = state;

        userData.pincode = pincode;

        userData.latitude = Number(latitude);

        userData.longitude = Number(longitude);
      }

      console.log("Registration Data:", userData);

      // =================================
      // API CALL
      // =================================

      setLoading(true);

      try {
        const response = await fetch(
          `${API_URL}/api/auth/register`,

          {
            method: "POST",

            headers: {
              "Content-Type": "application/json",
            },

            body: JSON.stringify(userData),
          },
        );

        let result = {};

        try {
          result = await response.json();
        } catch (jsonError) {
          console.error("Invalid backend response:", jsonError);
        }

        // =================================
        // SUCCESS
        // =================================

        if (response.ok && result.success !== false) {
          localStorage.setItem("pending_verification_email", email);

          if (
            result.verification_required === true ||
            (result.message &&
              result.message.toLowerCase().includes("verify your email"))
          ) {
            setFormMessage(
              "Registration successful. Check your email for the OTP.",

              "success",
            );

            setTimeout(() => {
              window.location.href = "verify-otp.html";
            }, 1000);

            return;
          }

          setFormMessage(
            result.message || "Registration successful. You can now login.",

            "success",
          );

          setTimeout(() => {
            window.location.href = "login.html";
          }, 1000);

          return;
        }

        // =================================
        // ERROR RESPONSE
        // =================================

        const backendMessage =
          result.message ||
          result.error ||
          "Registration failed. Please try again.";

        setFormMessage(backendMessage, "error");
      } catch (error) {
        console.error("Registration error:", error);

        setFormMessage(
          "Unable to connect to the server. Please make sure the backend is running.",

          "error",
        );
      } finally {
        setLoading(false);
      }
    },
  );
}

// =====================================================
// INITIAL LOAD
// =====================================================

if (roleSelect) {
  toggleRoleFields();
}
