import { api, fill, h } from "/js/api.js";

const token = new URLSearchParams(location.search).get("token") || "";
const target = document.getElementById("result");
const longDate = new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });

async function init() {
  const studio = await api("/public/studio").catch(() => null);
  if (studio) document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
  // Drop the token from the address bar once it has been used.
  history.replaceState(null, "", location.pathname);
  try {
    const result = await api(`/public/waitlist/confirm/${encodeURIComponent(token)}`, { method: "POST" });
    const day = longDate.format(new Date(`${result.preferred_date}T12:00:00Z`));
    fill(target,
      h("h1", {}, "You're on the waitlist"),
      result.position
        ? h("p", {}, `For ${day} you're number ${result.position}. If a time frees up, we'll email you a link to claim it; the first to claim gets it.`)
        : h("p", {}, `Your request for ${day} is already handled.`),
      h("a", { class: "btn btn-block", href: "/" }, "Back to home"));
  } catch (e) {
    fill(target, h("h1", {}, "Couldn't confirm"), h("p", { class: "muted" }, e.message),
      h("a", { class: "btn btn-block", href: "/book.html" }, "Book or join again"));
  }
}

init();
