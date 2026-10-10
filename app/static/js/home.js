import { api, formatEuro, formatMinutes, h } from "/js/api.js";

async function loadStudio() {
  try {
    const studio = await api("/public/studio");
    document.title = `${studio.name} · Book online`;
    document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
    document.getElementById("studio-address").textContent = studio.address;
    const phone = document.getElementById("studio-phone");
    phone.textContent = studio.phone;
    phone.href = `tel:${studio.phone.replace(/\s+/g, "")}`;
    // "Mon 10:00–19:00 · Tue–Fri …" reads best as one line per part on small screens.
    document.getElementById("studio-hours").replaceChildren(
      ...studio.opening_hours_text.split(" · ").map((part) => h("span", { class: "hours-part" }, part)),
    );
    const policy = document.getElementById("studio-policy");
    policy.textContent = `Free cancellation up to ${studio.free_cancellation_hours} hours before`;
    policy.hidden = false;
  } catch {
    document.querySelector("h1[data-studio-name]").textContent = "Book online";
  }
}

function serviceRow(service) {
  return h("article", { class: "service" },
    h("div", {},
      h("div", { class: "service-name" }, service.name),
      service.description && h("div", { class: "service-desc" }, service.description),
    ),
    h("div", { class: "service-meta" },
      h("div", { class: "service-price" }, formatEuro(service.price)),
      h("div", { class: "service-duration" }, formatMinutes(service.duration_minutes)),
    ),
    service.add_ons.length > 0 && h("ul", { class: "service-addons", "aria-label": "Add-ons" },
      service.add_ons.map((a) =>
        h("li", {}, `+ ${a.name}`, a.extra_minutes ? ` · +${a.extra_minutes} min` : "", ` · ${formatEuro(a.price)}`),
      ),
    ),
    h("div", { class: "service-actions" },
      h("a", {
        class: "btn btn-ghost btn-small",
        href: `/book.html?service=${encodeURIComponent(service.id)}`,
        "aria-label": `Book ${service.name}`,
      }, "Book"),
    ),
  );
}

async function loadMenu() {
  const target = document.getElementById("menu");
  try {
    const categories = await api("/public/services");
    if (categories.length === 0) {
      target.replaceChildren(h("p", { class: "state" }, "The menu is being prepared. Please call us to book."));
      return;
    }
    target.replaceChildren(
      ...categories.map((category) =>
        h("section", { class: "menu-category", "aria-label": category.name },
          h("h2", {}, category.name),
          category.services.map(serviceRow),
        ),
      ),
    );
  } catch {
    target.replaceChildren(h("p", { class: "state" }, "Could not load the menu. Please refresh."));
  }
}

loadStudio();
loadMenu();
