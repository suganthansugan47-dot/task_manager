// If already signed in, skip straight to the dashboard.
if (getToken()) {
  window.location.href = "dashboard.html";
}

function showError(message) {
  const banner = document.getElementById("error-banner");
  banner.textContent = message;
  banner.classList.add("visible");
}

function hideError() {
  document.getElementById("error-banner").classList.remove("visible");
}

const loginForm = document.getElementById("login-form");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
      const data = await apiRequest("/auth/login", {
        method: "POST",
        body: { username, password },
      });
      saveSession(data.token, data.user);
      window.location.href = "dashboard.html";
    } catch (err) {
      showError(err.message);
    }
  });
}

const registerForm = document.getElementById("register-form");
if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirm = document.getElementById("confirm-password").value;

    if (password !== confirm) {
      showError("Passwords do not match");
      return;
    }

    try {
      const data = await apiRequest("/auth/register", {
        method: "POST",
        body: { username, email, password },
      });
      saveSession(data.token, data.user);
      window.location.href = "dashboard.html";
    } catch (err) {
      showError(err.message);
    }
  });
}
