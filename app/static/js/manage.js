import { api, fill, formatEuro, h } from "/js/api.js";

const params = new URLSearchParams(location.search);
const token = params.get("token") || "";
const action = params.get("action"); // "confirm" | "cancel" from the reminder email
const target = document.getElementById("manage");

const BERLIN = "Europe/Berlin";
const longDate = new Intl.DateTimeFormat("en-GB", {
  weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
});
const shortDateTime = new Intl.DateTimeFormat("en-GB", {
  weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: BERLIN,
});
const STATUS_LABELS = {
  booked: "Booked", confirmed: "Confirmed", done: "Completed", no_show: "Missed", cancelled: "Cancelled",
};

let studio = null;
let message = null; // { text, kind } shown above the booking after an action
let askingToCancel = action === "cancel";

const bookingUrl = () => `/public/bookings/${encodeURIComponent(token)}`;

function showError(text) {
  fill(target, 
    h("h1", {}, "Booking not found"),
    h("p", { class: "muted" }, text),
    h("a", { class: "btn btn-block", href: "/" }, "Back to home"),
  );
}

function render(booking) {
  const isLateNow = new Date() > new Date(booking.free_cancellation_until);
  const policy = booking.can_cancel
    ? h("p", { class: `policy-note${isLateNow ? " late" : ""}` },
        isLateNow
          ? "Free cancellation has ended. You can still cancel, but it counts as a late cancellation."
          : `Free cancellation until ${shortDateTime.format(new Date(booking.free_cancellation_until))}.`)
    : null;

  const cancelBlock = booking.can_cancel && (askingToCancel
    ? h("div", { class: "confirm-cancel", role: "group", "aria-label": "Confirm cancellation" },
        h("p", {}, isLateNow ? "Are you sure? This counts as a late cancellation." : "Are you sure you want to cancel?"),
        h("div", { class: "row" },
          h("button", { class: "btn", type: "button", style: "background: var(--danger)", onclick: () => act("cancel") }, "Yes, cancel booking"),
          h("button", { class: "btn btn-ghost", type: "button", onclick: () => { askingToCancel = false; render(booking); } }, "Keep my booking"),
        ))
    : h("button", { class: "btn btn-danger-ghost btn-block", type: "button", onclick: () => { askingToCancel = true; render(booking); } }, "Cancel booking"));

  fill(target, 
    message && h("p", { class: message.kind === "error" ? "alert" : "success-note", role: "status" }, message.text),
    h("span", { class: `status-badge ${booking.status}` }, STATUS_LABELS[booking.status] || booking.status),
    h("h1", {}, "Your booking"),
    h("dl", { class: "facts" },
      h("dt", {}, "Date"), h("dd", {}, longDate.format(new Date(`${booking.date}T12:00:00Z`))),
      h("dt", {}, "Time"), h("dd", {}, `${booking.time} (${booking.total_minutes} min)`),
      h("dt", {}, "Therapist"), h("dd", {}, booking.therapist_name),
      studio && h("dt", {}, "Where"), studio && h("dd", {}, studio.address),
    ),
    h("table", { class: "lines" },
      booking.items.map((item) =>
        h("tr", {},
          h("td", { class: item.item_type === "add_on" ? "sub" : "" },
            item.item_type === "add_on" ? `+ ${item.name}` : item.name,
            item.quantity > 1 ? ` × ${item.quantity}` : ""),
          h("td", {}, formatEuro(item.line_total)),
        ),
      ),
      h("tr", { class: "total" }, h("td", {}, "Total"), h("td", {}, formatEuro(booking.total_price))),
    ),
    booking.receipt_number
      ? h("p", { class: "success-note" }, `Receipt ${booking.receipt_number} `, h("a", { href: `/receipt.html?token=${encodeURIComponent(token)}` }, "View or print receipt"))
      : h("p", { class: "pay-note" }, "Pay at the studio"),
    booking.status === "cancelled" && h("p", { class: "muted" },
      booking.late_cancellation ? "This booking was cancelled late." : "This booking was cancelled."),
    h("div", { class: "actions" },
      booking.can_confirm && h("button", { class: "btn btn-block", type: "button", onclick: () => act("confirm") }, "Confirm I'm coming"),
      cancelBlock,
      h("a", { class: "btn btn-ghost btn-block", href: "/book.html" }, "Book again"),
    ),
    policy,
  );
}

async function act(kind) {
  target.querySelectorAll("button").forEach((b) => (b.disabled = true));
  try {
    const booking = await api(`${bookingUrl()}/${kind}`, { method: "POST" });
    message = kind === "confirm"
      ? { text: "Thank you! Your booking is confirmed. See you soon.", kind: "ok" }
      : { text: booking.late_cancellation ? "Your booking is cancelled (late cancellation)." : "Your booking is cancelled.", kind: "ok" };
    askingToCancel = false;
    render(booking);
  } catch (error) {
    message = { text: error.message, kind: "error" };
    load();
  }
}

async function load() {
  if (!token) {
    showError("This link is incomplete. Please use the link in your confirmation email.");
    return;
  }
  try {
    const booking = await api(bookingUrl());
    render(booking);
    return booking;
  } catch (error) {
    showError(error.message);
    return null;
  }
}

async function init() {
  studio = await api("/public/studio").catch(() => null);
  if (studio) document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
  // Drop ?action= from the address bar so a reload doesn't repeat it.
  if (action) history.replaceState(null, "", `${location.pathname}?token=${encodeURIComponent(token)}`);
  const booking = await load();
  if (booking && action === "confirm" && booking.can_confirm) act("confirm");
}

init();
