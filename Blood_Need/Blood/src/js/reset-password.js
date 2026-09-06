const API_URL = "http://127.0.0.1:5000";
const resetForm = document.getElementById("resetForm");
const resetEmailInput = document.getElementById("resetEmail");
const resetEmailDisplay = document.getElementById("resetEmailDisplay");
const resetMessage = document.getElementById("resetMessage");
const successMessage = document.getElementById("successMessage");
const resetButton = document.getElementById("resetButton");
const missingEmailActions = document.getElementById("missingEmailActions");

const resetEmail = localStorage.getItem("reset_email") || "";

function showError(message) {
  if (resetMessage) {
    resetMessage.textContent = message || "";
  }
  if (successMessage) {
    successMessage.textContent = "";
  }
}

function showSuccess(message) {
  if (successMessage) {
    successMessage.textContent = message || "";
  }
  if (resetMessage) {
    resetMessage.textContent = "";
  }
}

function setResetButtonState(isLoading) {
  if (!resetButton) {
    return;
  }

  resetButton.disabled = isLoading;
  resetButton.textContent = isLoading
    ? "Resetting Password..."
    : "Reset Password";
}

if (resetEmailInput) {
  resetEmailInput.value = resetEmail;
}

if (resetEmailDisplay) {
  resetEmailDisplay.textContent = resetEmail || "Not available";
}

if (!resetEmail) {
  showError("Reset email not found. Please request a new OTP.");
  if (resetForm) {
    resetForm.hidden = true;
  }
  if (missingEmailActions) {
    missingEmailActions.hidden = false;
  }
}

if (resetForm) {
  resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const currentEmail = (
      resetEmailInput
        ? resetEmailInput.value
        : localStorage.getItem("reset_email") || ""
    ).trim();
    const otp = document.getElementById("otp")
      ? document.getElementById("otp").value.trim()
      : "";
    const password = document.getElementById("password")
      ? document.getElementById("password").value
      : "";
    const confirmPassword = document.getElementById("confirm")
      ? document.getElementById("confirm").value
      : "";

    if (!currentEmail) {
      showError("Reset email not found. Please request a new OTP.");
      if (missingEmailActions) {
        missingEmailActions.hidden = false;
      }
      return;
    }

    if (!/^\d{6}$/.test(otp)) {
      showError("OTP must contain exactly 6 digits.");
      return;
    }

    if (!password) {
      showError("Please enter a new password.");
      return;
    }

    if (!confirmPassword) {
      showError("Please confirm your new password.");
      return;
    }

    if (password !== confirmPassword) {
      showError("Passwords do not match.");
      return;
    }

    setResetButtonState(true);
    showError("Resetting Password...");

    try {
      const response = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: currentEmail,
          otp,
          new_password: password,
        }),
      });

      let data = {};
      try {
        data = await response.json();
      } catch (jsonError) {
        console.error("Reset password parse error:", jsonError);
      }

      if (response.ok) {
        localStorage.removeItem("reset_email");
        setResetButtonState(false);
        showSuccess(
          data.message || "Password reset successfully. Please login.",
        );

        setTimeout(() => {
          window.location.href = "login.html";
        }, 1200);
        return;
      }

      setResetButtonState(false);
      showError(
        (data && data.message) ||
          "Unable to connect to the server. Please try again.",
      );
    } catch (error) {
      console.error("Reset password error:", error);
      setResetButtonState(false);
      showError("Unable to connect to the server. Please try again.");
    }
  });
}
