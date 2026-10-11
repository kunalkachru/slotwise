import { api, formatEuro, h } from "/js/api.js";

const longDate = new Intl.DateTimeFormat("en-GB", {
  weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
});
const CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.5 4.5L19 7.5"/></svg>';

function readBooking() {
  try {
    return JSON.parse(sessionStorage.getItem("slotwise:lastBooking"));
  } catch {
    return null;
  }
}

async function render() {
  const target = document.getElementById("confirmation");
  const booking = readBooking();
  if (!booking) {
    target.replaceChildren(
      h("h1", {}, "Booking details not available"),
      h("p", { class: "muted" }, "Your booking may still have gone through. Please check with the studio if you're unsure."),
      h("a", { class: "btn btn-block", href: "/" }, "Back to home"),
    );
    return;
  }
  const studio = await api("/public/studio").catch(() => null);
  if (studio) document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));

  const icon = h("div", { class: "confirm-icon" });
  icon.innerHTML = CHECK; // static markup, no data
  target.replaceChildren(
    icon,
    h("h1", {}, `You're booked, ${booking.customer_first_name}!`),
    h("dl", { class: "facts" },
      h("dt", {}, "Date"), h("dd", {}, longDate.format(new Date(`${booking.date}T12:00:00Z`))),
      h("dt", {}, "Time"), h("dd", {}, `${booking.time} (${booking.total_minutes} min)`),
      h("dt", {}, "Therapist"), h("dd", {}, booking.therapist_name),
      studio && h("dt", {}, "Where"), studio && h("dd", {}, studio.address),
    ),
    h("table", { class: "lines" },
      booking.items.map((item) =>
        h("tr", {},
          h("td", { class: item.item_type === "add_on" ? "sub" : "" }, item.item_type === "add_on" ? `+ ${item.name}` : item.name),
          h("td", {}, formatEuro(item.line_total)),
        ),
      ),
      h("tr", { class: "total" }, h("td", {}, "Total"), h("td", {}, formatEuro(booking.total_price))),
    ),
    h("p", { class: "pay-note" }, "Pay at the studio"),
    h("a", { class: "btn btn-block", href: "/" }, "Back to home"),
  );
}

render();
