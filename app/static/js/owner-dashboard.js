import { ownerApi, startOwnerPage } from "/js/owner-shell.js";

const dateFormat = new Intl.DateTimeFormat("en-GB", {
  weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "Europe/Berlin",
});

async function load() {
  await startOwnerPage("dashboard");
  const dashboard = await ownerApi("/owner/dashboard");
  document.getElementById("welcome").textContent = `Welcome back, ${dashboard.owner_name}`;
  document.getElementById("today").textContent = dateFormat.format(new Date(`${dashboard.date}T12:00:00Z`));
}

load().catch(() => {});
