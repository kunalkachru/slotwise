import { api, redirectToLoginOn401 } from "/js/api.js";

const dateFormat = new Intl.DateTimeFormat("en-GB", {
  weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "Europe/Berlin",
});

async function load() {
  try {
    const dashboard = await api("/owner/dashboard");
    document.getElementById("welcome").textContent = `Welcome back, ${dashboard.owner_name}`;
    document.getElementById("today").textContent = dateFormat.format(new Date(`${dashboard.date}T12:00:00Z`));
    document.getElementById("owner-layout").hidden = false;
  } catch (error) {
    if (!redirectToLoginOn401(error)) {
      document.body.textContent = error.message;
    }
  }
}

document.getElementById("logout").addEventListener("click", async () => {
  await api("/auth/logout", { method: "POST" }).catch(() => {});
  window.location.assign("/");
});

load();
