import { api, fill, formatEuro, formatMinutes, h, treatmentMedia } from "/js/api.js";
import { t } from "/js/i18n.js";

const BADGE_REFRESH_MS = 60 * 1000;

// Show "Open now" / "Closed now" next to the opening hours. With no open_now value
// (null or missing) there is no badge at all and the hours stay as they are.
function renderOpenBadge(openNow) {
  const hours = document.getElementById("studio-hours");
  let badge = document.querySelector("[data-testid=open-badge]");
  if (typeof openNow !== "boolean") {
    if (badge) badge.remove();
    return;
  }
  if (!badge) {
    badge = h("span", { class: "open-badge", "data-testid": "open-badge", role: "status" });
    hours.after(badge);
  }
  badge.dataset.state = openNow ? "open" : "closed";
  badge.textContent = t(openNow ? "home.open_now" : "home.closed_now");
}

async function refreshOpenBadge() {
  try {
    const studio = await api("/public/studio");
    renderOpenBadge(studio.open_now);
  } catch { /* keep the last state until the next try */ }
}

async function loadStudio() {
  try {
    const studio = await api("/public/studio");
    renderOpenBadge(studio.open_now);
    document.title = `${studio.name} · ${t("home.title")}`;
    document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
    document.getElementById("studio-address").textContent = studio.address;
    const phone = document.getElementById("studio-phone");
    phone.textContent = studio.phone;
    phone.href = `tel:${studio.phone.replace(/\s+/g, "")}`;
    // "Mon 10:00–19:00 · Tue–Fri …" reads best as one line per part on small screens.
    fill(document.getElementById("studio-hours"), 
      ...studio.opening_hours_text.split(" · ").map((part) => h("span", { class: "hours-part" }, part)),
    );
    const policy = document.getElementById("studio-policy");
    policy.textContent = t("home.policy", { hours: studio.free_cancellation_hours });
    policy.hidden = false;
  } catch {
    document.querySelectorAll("h1[data-studio-name]").forEach((el) => (el.textContent = t("home.title")));
  }
}

function serviceRow(service, category) {
  // tabindex: on a phone, tapping the tile focuses it and reveals the description.
  return h("article", { class: "service", tabindex: "0" },
    treatmentMedia(service, category),
    h("div", {},
      h("div", { class: "service-name" },
        service.name,
        service.popular && h("span", { class: "service-popular" }, t("home.popular")),
      ),
      service.description && h("div", { class: "service-desc" }, service.description),
    ),
    h("div", { class: "service-meta" },
      h("div", { class: "service-price" }, formatEuro(service.price)),
      h("div", { class: "service-duration" }, formatMinutes(service.duration_minutes)),
    ),
    service.add_ons.length > 0 && h("ul", { class: "service-addons", "aria-label": t("home.addons") },
      service.add_ons.map((a) =>
        h("li", {}, `+ ${a.name}`, a.extra_minutes ? ` · +${formatMinutes(a.extra_minutes)}` : "", ` · ${formatEuro(a.price)}`),
      ),
    ),
    h("div", { class: "service-actions" },
      h("a", {
        class: "btn btn-ghost btn-small",
        href: `/book.html?service=${encodeURIComponent(service.id)}`,
        "aria-label": t("home.book_aria", { name: service.name }),
      }, t("home.book")),
    ),
  );
}

async function loadMenu() {
  const target = document.getElementById("menu");
  try {
    const categories = await api("/public/services");
    if (categories.length === 0) {
      fill(target, h("p", { class: "state" }, t("home.menu_empty")));
      return;
    }
    fill(target, 
      ...categories.map((category) =>
        h("section", { class: "menu-category", "aria-label": category.name },
          h("h2", {}, category.label || category.name),
          // compute the numeric minimum price of the services and always show the line
          category.services.length > 0 && h("div", { class: "category-from" },
            t("home.from_price", { price: formatEuro(Math.min(...category.services.map((s) => Number(s.price)))) }),
          ),
          // render a count line after the heading: singular/plural, omit for zero services
          category.services.length > 0 && h("div", { class: "category-count" },
            category.services.length === 1
              ? t("home.treatment_count_one")
              : t("home.treatment_count_other", { n: category.services.length }),
          ),
          category.services.map((service) => serviceRow(service, category.name)),
        ),
      ),
    );
  } catch {
    fill(target, h("p", { class: "state" }, t("home.menu_error")));
  }
}

// "Our team" below the menu: one card per therapist from /public/team. With no cards
// (empty list or a failed request) the whole section, heading included, stays hidden.
async function loadTeam() {
  const section = document.getElementById("team");
  const list = document.getElementById("team-list");
  try {
    const team = await api("/public/team");
    if (!Array.isArray(team) || team.length === 0) {
      section.hidden = true;
      return;
    }
    fill(list,
      ...team.map((member) =>
        h("article", { class: "team-card service" },
          h("h3", { class: "team-name" }, member.first_name),
          h("ul", { class: "team-treatments" },
            member.treatments.map((name) => h("li", {}, name)),
          ),
        ),
      ),
    );
    section.hidden = false;
  } catch {
    section.hidden = true;
  }
}

loadStudio();
loadMenu();
loadTeam();
setInterval(refreshOpenBadge, BADGE_REFRESH_MS);
