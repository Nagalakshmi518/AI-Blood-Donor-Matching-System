const API_URL = "http://127.0.0.1:5000";
const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");
const loginButton = document.getElementById("loginButton");
const passwordInput = document.getElementById("password");
const togglePasswordButton = document.getElementById("togglePassword");

if (togglePasswordButton && passwordInput) {
  togglePasswordButton.addEventListener("click", () => {
    const isHidden = passwordInput.type === "password";
    passwordInput.type = isHidden ? "text" : "password";
    togglePasswordButton.textContent = isHidden ? "Hide" : "Show";
  });
}

function setLoginState(isLoading, text = "") {
  if (loginButton) {
    loginButton.disabled = isLoading;
    loginButton.textContent = isLoading ? "Logging in..." : "Login";
  }

  if (loginMessage) {
    loginMessage.textContent = text;
  }
}
function getRedirectTarget(roleValue) {
  const normalizedRole = String(roleValue || "PATIENT")
    .trim()
    .toUpperCase();

  if (normalizedRole === "DONOR") {
    return "donor-dashboard.html";
  }

  if (normalizedRole === "ADMIN") {
    return "admin-dashboard.html";
  }

  if (normalizedRole === "HOSPITAL") {
    return "hospital-dashboard.html";
  }

  if (normalizedRole === "PATIENT" || normalizedRole === "REQUESTER") {
    return "patient-dashboard.html";
  }

  return "patient_dashboard.html";
}
if (loginForm) {
  loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    if (!email || !password) {
      setLoginState(false, "Please enter both email and password.");
      return;
    }

    setLoginState(true, "Logging in...");

    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      let result = {};
      try {
        result = await response.json();
      } catch (jsonError) {
        console.error("Login JSON parse error:", jsonError);
      }

      if (response.ok && result.success !== false) {
        const token = result.token;
        const user =
          result.user && typeof result.user === "object" ? result.user : {};
        const role = String(user.role || result.role || "PATIENT")
          .trim()
          .toUpperCase();

        if (token) {
          localStorage.setItem("token", token);
        }

        if (user && Object.keys(user).length) {
          localStorage.setItem("user", JSON.stringify(user));
        }

        if (role) {
          localStorage.setItem("role", role);
        }

        window.location.href = getRedirectTarget(role);
        return;
      }

      const backendMessage =
        result && typeof result.message === "string" && result.message.trim()
          ? result.message.trim()
          : `Login failed (${response.status})`;

      if (backendMessage.toLowerCase().includes("email not verified")) {
        localStorage.setItem("pending_verification_email", email);
        setLoginState(false, backendMessage);
        window.location.href = "verify-otp.html";
        return;
      }

      setLoginState(false, backendMessage);
    } catch (error) {
      console.error("Login Error:", error);
      setLoginState(false, "Unable to connect to server. Please try again.");
    }
  });
}
