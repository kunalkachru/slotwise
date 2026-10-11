// Shared owner-area frame: session check, side menu, log out.
import { api, h, redirectToLoginOn401 } from "/js/api.js";

const LEAF = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#33C375" d="M20 3C10 3 4 8.5 4 15.5c0 1.6.4 3 1 4.2C6.8 13 11 9.6 16 8c-4.3 2.6-7.4 6.6-8.6 12 1.2.6 2.6 1 4.1 1C18.6 21 21 14 20 3z"/></svg>';

const PAGES = [
  { key: "dashboard", label: "Dashboard", href: "/owner/dashboard.html" },
  { key: "bookings", label: "Bookings", href: "/owner/bookings.html" },
  { key: "services", label: "Services & add-ons", href: "/owner/services.html" },
  { key: "therapists", label: "Therapists & hours", href: "/owner/therapists.html" },
  { key: "waitlist", label: "Waitlist", href: null }, // slice 5
];

export async function startOwnerPage(active) {
  let owner;
  try {
    owner = await api("/auth/me");
  } catch (error) {
    if (!redirectToLoginOn401(error)) document.body.textContent = error.message;
    throw error;
  }
  const logo = h("a", { class: "logo", href: "/owner/dashboard.html" });
  logo.innerHTML = `${LEAF} Slotwise`; // static markup
  document.getElementById("sidebar").replaceChildren(
    logo,
    h("nav", { "aria-label": "Owner menu" },
      PAGES.map((p) =>
        p.href
          ? h("a", { href: p.href, "aria-current": p.key === active ? "page" : null }, p.label)
          : h("a", { class: "soon", "aria-disabled": "true" }, p.label, " ", h("span", { class: "badge" }, "soon")),
      ),
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
