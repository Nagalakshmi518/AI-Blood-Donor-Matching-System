const API_URL = "https://ai-blood-donor-matching-system.onrender.com";
const form = document.getElementById("verifyOtpForm");
const emailInput = document.getElementById("email");
const otpInput = document.getElementById("otp");
const emailDisplay = document.getElementById("emailDisplay");
const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const verifyButton = document.getElementById("verifyButton");

function setError(message) {
  if (errorMessage) errorMessage.textContent = message || "";
  if (successMessage) successMessage.textContent = "";
}

function setSuccess(message) {
  if (successMessage) successMessage.textContent = message || "";
  if (errorMessage) errorMessage.textContent = "";
}

function setLoading(isLoading) {
  if (verifyButton) {
    verifyButton.disabled = isLoading;
    verifyButton.textContent = isLoading ? "Verifying..." : "Verify Email";
  }
}

function sanitizeOtp(value) {
  return value.replace(/\D/g, "").slice(0, 6);
}

const email = localStorage.getItem("pending_verification_email") || "";

if (!email) {
  setError("No verification email found. Please register again.");
  if (emailDisplay) {
    emailDisplay.textContent = "-";
  }
  if (form) {
    form.style.display = "none";
  }
  if (document.getElementById("verificationState")) {
    document.getElementById("verificationState").style.display = "none";
  }
} else {
  if (emailInput) {
    emailInput.value = email;
  }

  if (emailDisplay) {
    emailDisplay.textContent = email;
  }
}

if (otpInput) {
  otpInput.addEventListener("input", () => {
    otpInput.value = sanitizeOtp(otpInput.value);
  });
}

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const currentEmail = emailInput ? emailInput.value.trim() : "";
    const otp = otpInput ? otpInput.value.trim() : "";

    if (!currentEmail) {
      setError("No verification email found. Please register again.");
      return;
    }

    if (!/^\d{6}$/.test(otp)) {
      setError("Please enter a valid 6-digit OTP.");
      return;
    }

    setLoading(true);
    setError("Verifying email...");

    try {
      const response = await fetch(`${API_URL}/api/auth/verify-email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: currentEmail,
          otp,
        }),
      });

      let data = {};
      try {
        data = await response.json();
      } catch (jsonError) {
        console.error("Verification JSON parse error:", jsonError);
      }

      if (response.ok && data.success !== false) {
        localStorage.removeItem("pending_verification_email");
        setSuccess(data.message || "Email verified successfully.");
        setLoading(false);
        setTimeout(() => {
          window.location.href = "login.html";
        }, 1200);
        return;
      }

      const backendMessage =
        data && typeof data.message === "string" && data.message.trim()
          ? data.message.trim()
          : "Invalid or expired OTP. Please try again.";
      const userMessage =
        backendMessage === "OTP expired."
          ? "OTP expired. Please register again or request a new verification code."
          : backendMessage;

      setLoading(false);
      setError(userMessage);
      localStorage.setItem("pending_verification_email", currentEmail);
    } catch (error) {
      console.error("Verification error:", error);
      setLoading(false);
      setError("Unable to connect to the server. Please try again.");
    }
  });
}

const registerLink = document.querySelector('a[href="register.html"]');
if (registerLink && !email) {
  registerLink.textContent = "Register now";
}
