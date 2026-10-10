import { api } from "/js/api.js";

const form = document.getElementById("login-form");
const errorBox = document.getElementById("login-error");

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

// Already logged in? Skip straight to the dashboard.
api("/auth/me").then(() => window.location.replace("/owner/dashboard.html")).catch(() => {});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const email = form.email.value.trim();
  const password = form.password.value;
  if (!email || !password) {
    showError("Please enter your email and password.");
    return;
  }
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  errorBox.hidden = true;
  try {
    await api("/auth/login", { method: "POST", body: { email, password } });
    window.location.assign("/owner/dashboard.html");
  } catch (error) {
    showError(error.message);
    form.password.select();
  } finally {
    button.disabled = false;
  }
});
