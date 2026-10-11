import { api, fill, formatEuro, h } from "/js/api.js";

const longDate = new Intl.DateTimeFormat("en-GB", {
  weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
});
const ENVELOPE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" d="M3.5 6.5h17v11h-17z"/><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M4 7l8 6 8-6"/></svg>';
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
    fill(target, 
      h("h1", {}, "Booking details not available"),
      h("p", { class: "muted" }, "Your booking may still have gone through. Please check with the studio if you're unsure."),
      h("a", { class: "btn btn-block", href: "/" }, "Back to home"),
    );
    return;
  }
  const studio = await api("/public/studio").catch(() => null);
  if (studio) document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));

  const pending = booking.status === "pending";
  const holdUntil = booking.hold_until
    ? new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Berlin" }).format(new Date(booking.hold_until))
    : null;
  const icon = h("div", { class: "confirm-icon" });
  icon.innerHTML = pending ? ENVELOPE : CHECK; // static markup, no data
  document.title = `${pending ? "Check your email" : "Booking confirmed"} · ${studio ? studio.name : "Slotwise"}`;
  fill(target, 
    icon,
    h("h1", {}, pending ? `Almost done, ${booking.customer_first_name}!` : `You're booked, ${booking.customer_first_name}!`),
    pending && h("p", { class: "success-note" },
      `We've emailed you a link. Click it to confirm your booking${holdUntil ? ` by ${holdUntil}` : " within 30 minutes"}; until then we're holding the time for you.`),
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
    !pending && h("p", { class: "success-note" }, "A confirmation has been emailed to you. Use the link in your email to confirm, cancel or view your receipt."),
    pending && h("p", { class: "muted" }, "No email? Check your spam folder. If you don't confirm in time, the time is released for others."),
    h("a", { class: "btn btn-block", href: "/" }, "Back to home"),
  );
}

render();
