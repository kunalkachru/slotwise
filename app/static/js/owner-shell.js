// Shared owner-area frame: session check, side menu, log out.
import { api, ApiError, fill, h, redirectToLoginOn401, themeSwitch } from "/js/api.js";

const LEAF = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#33C375" d="M20 3C10 3 4 8.5 4 15.5c0 1.6.4 3 1 4.2C6.8 13 11 9.6 16 8c-4.3 2.6-7.4 6.6-8.6 12 1.2.6 2.6 1 4.1 1C18.6 21 21 14 20 3z"/></svg>';

// Line icons for the new look's menu (from the Figma export); hidden in the classic look.
const ICONS = {
  dashboard: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  bookings: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4m8-4v4M3 10h18"/>',
  services: '<path d="M4 7h16M4 12h16M4 17h16"/><circle cx="8" cy="7" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="10" cy="17" r="2"/>',
  therapists: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  waitlist: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6 7 7m10 10 1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
};
function icon(name) {
  const el = h("span", { class: "nav-icon calm-only" });
  el.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</svg>`; // static markup
  return el;
}

const PAGES = [
  { key: "dashboard", label: "Dashboard", href: "/owner/dashboard.html" },
  { key: "bookings", label: "Bookings", href: "/owner/bookings.html" },
  { key: "services", label: "Services & add-ons", href: "/owner/services.html" },
  { key: "therapists", label: "Therapists & hours", href: "/owner/therapists.html" },
  { key: "waitlist", label: "Waitlist", href: "/owner/waitlist.html" },
  { key: "settings", label: "Studio settings", href: "/owner/settings.html" },
];

export async function startOwnerPage(active) {
  let owner;
  try {
    owner = await api("/auth/me");
  } catch (error) {
    redirectToLoginOn401(error); // other errors: the page's catch shows showPageError()
    throw error;
  }
  const logo = h("a", { class: "logo", href: "/owner/dashboard.html" });
  logo.innerHTML = `${LEAF} Slotwise`; // static markup
  const sidebar = document.getElementById("sidebar");
  // New look on phones: the side menu becomes a top bar with the page name and a Menu
  // button that opens the links as a dropdown. Both are hidden in the classic look.
  const current = PAGES.find((p) => p.key === active);
  const menuButton = h("button", {
    type: "button", class: "owner-menu-toggle calm-only", id: "owner-menu-toggle",
    "aria-expanded": "false", "aria-controls": "owner-nav", "aria-label": "Menu",
  }, icon("menu"));
  const setOpen = (open) => {
    sidebar.classList.toggle("is-open", open);
    menuButton.setAttribute("aria-expanded", String(open));
  };
  menuButton.addEventListener("click", () => setOpen(!sidebar.classList.contains("is-open")));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && sidebar.classList.contains("is-open")) { setOpen(false); menuButton.focus(); } });
  document.addEventListener("click", (e) => { if (!sidebar.contains(e.target)) setOpen(false); });
  sidebar.replaceChildren(
    logo,
    h("span", { class: "owner-page-name calm-only", "aria-hidden": "true" }, current ? current.label : ""),
    menuButton,
    h("nav", { "aria-label": "Owner menu", id: "owner-nav" },
      PAGES.map((p) =>
        p.href
          ? h("a", { href: p.href, "aria-current": p.key === active ? "page" : null }, icon(p.key), h("span", {}, p.label))
          : h("a", { class: "soon", "aria-disabled": "true" }, p.label, " ", h("span", { class: "badge" }, "soon")),
      ),
      themeSwitch({ classic: "Classic look", calm: "New look" }),
      h("button", {
        type: "button",
        onclick: async () => {
          await api("/auth/logout", { method: "POST" }).catch(() => {});
          window.location.assign("/");
        },
      }, "Log out"),
    ),
  );
  document.getElementById("owner-layout").hidden = false;
  return owner;
}

// For owner API calls after the page started: a lost session goes back to login.
export async function ownerApi(path, options) {
  try {
    return await api(path, options);
  } catch (error) {
    redirectToLoginOn401(error);
    throw error;
  }
}

const WARNING = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" d="M12 3 2.5 20h19L12 3Z"/><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M12 9v5m0 3h.01"/></svg>';
const clockTime = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Berlin" });

// A page that couldn't load its data: say why, show details for whoever helps the owner,
// and offer ways around it. `target` defaults to the whole main area.
export function showPageError(error, target) {
  if (error instanceof ApiError && error.status === 401) return; // already redirecting to login
  const time = clockTime.format(new Date());
  // The path only, never the query: Bookings search terms can hold customer names or emails.
  const path = error instanceof ApiError && error.path ? error.path.split("?")[0] : null;
  const details = !(error instanceof ApiError)
    ? `Details: unexpected script error · ${time}`
    : error.status === 0
      ? `Details: no response from the server · ${time}`
      : `Details: status ${error.status}${path ? ` · ${path}` : ""} · ${time}`;
  const reason = error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
  const newLook = document.documentElement.dataset.theme === "calm";
  const switchToClassic = () => {
    window.slotwiseTheme?.set("classic");
    window.location.reload();
  };
  const icon = h("span", { class: "page-error-icon" });
  icon.innerHTML = WARNING; // static markup, no data

  const card = h("section", { class: "page-error", role: "alert" },
    icon,
    h("h2", {}, "This page couldn't load"),
    h("p", {}, reason),
    h("p", { class: "page-error-details" }, details),
    h("p", { class: "page-error-tips-title" }, "What you can try:"),
    h("ul", {},
      h("li", {}, "Wait a moment and try again. On the free hosting plan the server sleeps when nobody uses it and can take up to a minute to wake up."),
      h("li", {}, "Check your internet connection."),
      newLook && h("li", {}, "Switch to the Classic look. If only the new look has a problem, the classic one keeps working."),
      h("li", {}, "If it keeps happening, send the details line above to your developer."),
    ),
    h("div", { class: "row" },
      h("button", { class: "btn", type: "button", onclick: () => window.location.reload() }, "Try again"),
      newLook && h("button", { class: "btn btn-ghost", type: "button", onclick: switchToClassic }, "Switch to Classic look"),
    ),
  );

  const layout = document.getElementById("owner-layout");
  const main = layout && !layout.hidden && layout.querySelector(".owner-main");
  if (target || main) return fill(target || main, card);
  // The session check itself failed: no side menu, just the card on the page.
  document.body.replaceChildren(h("main", { class: "center-page" }, card));
}
