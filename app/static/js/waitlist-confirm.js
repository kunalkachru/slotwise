import { api, fill, h } from "/js/api.js";
import { locale, t } from "/js/i18n.js";

const token = new URLSearchParams(location.search).get("token") || "";
const target = document.getElementById("result");
const longDate = new Intl.DateTimeFormat(locale, { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });

async function init() {
  const studio = await api("/public/studio").catch(() => null);
  if (studio) document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
  // Drop the token from the address bar once it has been used.
  history.replaceState(null, "", location.pathname);
  try {
    const result = await api(`/public/waitlist/confirm/${encodeURIComponent(token)}`, { method: "POST" });
    const day = longDate.format(new Date(`${result.preferred_date}T12:00:00Z`));
    fill(target,
      h("h1", {}, t("wlc.on")),
      result.position
        ? h("p", {}, t("wlc.position", { day, position: result.position }))
        : h("p", {}, t("wlc.handled", { day })),
      h("a", { class: "btn btn-block", href: "/" }, t("nav.back_home")));
  } catch (e) {
    fill(target, h("h1", {}, t("wlc.failed")), h("p", { class: "muted" }, e.message),
      h("a", { class: "btn btn-block", href: "/book.html" }, t("wlc.again")));
  }
}

init();
