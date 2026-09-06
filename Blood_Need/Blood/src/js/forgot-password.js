const API_URL = "https://ai-blood-donor-matching-system.onrender.com";
const forgotForm = document.getElementById("forgotForm");
const forgotMessage = document.getElementById("forgotMessage");
const successMessage = document.getElementById("successMessage");
const forgotButton = document.getElementById("forgotButton");

function setForgotError(message) {
  if (forgotMessage) {
    forgotMessage.textContent = message || "";
  }
  if (successMessage) {
    successMessage.textContent = "";
  }
}

function setForgotSuccess(message) {
  if (successMessage) {
    successMessage.textContent = message || "";
  }
  if (forgotMessage) {
    forgotMessage.textContent = "";
  }
}

function setForgotState(isLoading) {
  if (forgotButton) {
    forgotButton.disabled = isLoading;
    forgotButton.textContent = isLoading ? "Sending OTP..." : "Send OTP";
  }
}

if (forgotForm) {
  forgotForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const emailInput = document.getElementById("email");
    const email = emailInput ? emailInput.value.trim() : "";

    if (!email) {
      setForgotError("Please enter your email.");
      return;
    }

    setForgotState(true);
    setForgotError("Sending OTP...");

    try {
      const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      let data = {};
      try {
        data = await response.json();
      } catch (jsonError) {
        console.error("Forgot password parse error:", jsonError);
      }

      if (response.ok) {
        localStorage.setItem("reset_email", email);
        setForgotState(false);
        setForgotSuccess("OTP sent successfully. Please check your email.");
        setTimeout(() => {
          window.location.href = "reset-password.html";
        }, 1000);
        return;
      }

      setForgotState(false);
      setForgotError((data && data.message) || "Unable to send OTP.");
    } catch (error) {
      console.error("Forgot password error:", error);
      setForgotState(false);
      setForgotError("Unable to connect to the server. Please try again.");
    }
  });
}
