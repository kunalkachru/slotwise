import { api, fact, fill, formatEuro, formatMinutes, h, visitFact } from "/js/api.js";
import { locale, t } from "/js/i18n.js";

const params = new URLSearchParams(location.search);
const token = params.get("token") || "";
const action = params.get("action"); // "verify" (booking email) | "confirm" | "cancel" (reminder)
const target = document.getElementById("manage");

const BERLIN = "Europe/Berlin";
const longDate = new Intl.DateTimeFormat(locale, {
  weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
});
const shortDateTime = new Intl.DateTimeFormat(locale, {
  weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: BERLIN,
});
const statusLabel = (status) => t(`status.${status}`);

let studio = null;
let message = null; // { text, kind } shown above the booking after an action
let askingToCancel = action === "cancel";
let listMode = !action;
let customerBookings = [];

const bookingUrl = () => `/public/bookings/${encodeURIComponent(token)}`;

function showError(text) {
  fill(target, 
    h("h1", {}, t("manage.not_found")),
    h("p", { class: "muted" }, text),
    h("a", { class: "btn btn-block", href: "/" }, t("nav.back_home")),
  );
}

function bookingDetails(booking) {
  return h("dl", { class: "facts" },
    fact(t("common.date"), longDate.format(new Date(`${booking.date}T12:00:00Z`))),
    fact(t("common.time"), `${t("common.at_time", { time: booking.time })} (${formatMinutes(booking.total_minutes)})`),
    visitFact(booking, { therapist: t("common.therapist"), visit: t("common.your_visit"), break: t("book.break") }),
  );
}

function renderCustomerBooking(booking) {
  const cancel = booking.can_cancel
    ? h("button", {
        class: "btn btn-danger-ghost btn-block", type: "button",
        onclick: () => cancelCustomerBooking(booking),
      }, t("manage.cancel"))
    : h("p", { class: "muted booking-list-reason", role: "status" },
        booking.status === "cancelled"
          ? t("manage.already_cancelled")
          : t("manage.already_started"));

  return h("article", { class: "booking-list-item", "data-booking-id": booking.id },
    h("div", { class: "booking-list-head" },
      h("span", { class: `status-badge ${booking.status}` }, statusLabel(booking.status)),
      h("h2", {}, t("manage.booking_on", { date: longDate.format(new Date(`${booking.date}T12:00:00Z`)) }))),
    bookingDetails(booking),
    h("ul", { class: "booking-list-services" }, booking.items.map((item) =>
      h("li", {}, item.item_type === "add_on" ? `+ ${item.name}` : item.name))),
    booking.status === "cancelled" && h("p", { class: "muted" },
      t(booking.late_cancellation ? "manage.was_cancelled_late" : "manage.was_cancelled")),
    cancel,
  );
}

function renderCustomerBookings(bookings) {
  fill(target,
    message && h("p", { class: message.kind === "error" ? "alert" : "success-note", role: "status" }, message.text),
    h("h1", {}, t("manage.bookings_h1")),
    bookings.length
      ? h("div", { id: "manage-bookings", class: "booking-list" }, bookings.map(renderCustomerBooking))
      : h("p", { class: "muted" }, t("manage.no_bookings")),
  );
}

function render(booking) {
  const isLateNow = new Date() > new Date(booking.free_cancellation_until);
  const policy = booking.can_cancel
    ? h("p", { class: `policy-note${isLateNow ? " late" : ""}` },
        isLateNow
          ? t("manage.late_policy")
          : t("manage.free_until", { when: shortDateTime.format(new Date(booking.free_cancellation_until)) }))
    : null;

  const cancelBlock = booking.can_cancel && (askingToCancel
    ? h("div", { class: "confirm-cancel", role: "group", "aria-label": t("manage.confirm_cancel") },
        h("p", {}, t(isLateNow ? "manage.sure_late" : "manage.sure")),
        h("div", { class: "row" },
          h("button", { class: "btn btn-danger", type: "button", onclick: () => act("cancel") }, t("manage.yes_cancel")),
          h("button", { class: "btn btn-ghost", type: "button", onclick: () => { askingToCancel = false; render(booking); } }, t("manage.keep")),
        ))
    : h("button", { class: "btn btn-danger-ghost btn-block", type: "button", onclick: () => { askingToCancel = true; render(booking); } }, t("manage.cancel")));

  fill(target, 
    message && h("p", { class: message.kind === "error" ? "alert" : "success-note", role: "status" }, message.text),
    h("span", { class: `status-badge ${booking.status}` }, statusLabel(booking.status)),
    h("h1", {}, t("manage.h1")),
    h("dl", { class: "facts" },
      fact(t("common.date"), longDate.format(new Date(`${booking.date}T12:00:00Z`))),
      fact(t("common.time"), `${t("common.at_time", { time: booking.time })} (${formatMinutes(booking.total_minutes)})`),
      visitFact(booking, { therapist: t("common.therapist"), visit: t("common.your_visit"), break: t("book.break") }),
      studio && fact(t("common.where"), studio.address),
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
      h("tr", { class: "total" }, h("td", {}, t("common.total")), h("td", {}, formatEuro(booking.total_price))),
    ),
    booking.receipt_number
      ? h("p", { class: "success-note" }, `${t("manage.receipt", { number: booking.receipt_number })} `, h("a", { href: `/receipt.html?token=${encodeURIComponent(token)}` }, t("manage.view_receipt")))
      : h("p", { class: "pay-note" }, t("common.pay")),
    booking.status === "cancelled" && h("p", { class: "muted" },
      t(booking.late_cancellation ? "manage.was_cancelled_late" : "manage.was_cancelled")),
    booking.status === "expired" && h("p", { class: "muted" }, t("manage.expired_note")),
    h("div", { class: "actions" },
      booking.awaiting_email_confirmation && h("button", { class: "btn btn-block", type: "button", onclick: () => act("verify") }, t("manage.verify")),
      booking.can_confirm && h("button", { class: "btn btn-block", type: "button", onclick: () => act("confirm") }, t("manage.coming")),
      cancelBlock,
      ["pending", "booked", "confirmed"].includes(booking.status) && h("a", {
        class: "btn btn-ghost btn-block", href: `${bookingUrl()}/calendar.ics`, download: "",
      }, t("manage.calendar")),
      h("a", { class: "btn btn-ghost btn-block", href: "/book.html" }, t("nav.book_again")),
    ),
    policy,
  );
}

async function act(kind) {
  target.querySelectorAll("button").forEach((b) => (b.disabled = true));
  try {
    const booking = await api(`${bookingUrl()}/${kind}`, { method: "POST" });
    message = kind === "verify"
      ? { text: t("manage.msg_verify"), kind: "ok" }
      : kind === "confirm"
      ? { text: t("manage.msg_confirm"), kind: "ok" }
      : { text: t(booking.late_cancellation ? "manage.msg_cancel_late" : "manage.msg_cancel"), kind: "ok" };
    askingToCancel = false;
    render(booking);
  } catch (error) {
    message = { text: error.message, kind: "error" };
    load();
  }
}

async function cancelCustomerBooking(booking) {
  target.querySelectorAll("button").forEach((button) => (button.disabled = true));
  try {
    const cancelled = await api(`/public/bookings/${booking.id}/cancel?token=${encodeURIComponent(token)}`, { method: "POST" });
    message = { text: t(cancelled.late_cancellation ? "manage.msg_cancel_late" : "manage.msg_cancel"), kind: "ok" };
    customerBookings = customerBookings.map((booking) => booking.id === cancelled.id ? cancelled : booking);
    renderCustomerBookings(customerBookings);
  } catch (error) {
    message = { text: error.message, kind: "error" };
    loadCustomerBookings();
  }
}

async function load() {
  if (!token) {
    showError(t("manage.incomplete"));
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

async function loadCustomerBookings() {
  if (!token) {
    showError(t("manage.incomplete"));
    return;
  }
  try {
    customerBookings = await api(`/public/bookings?token=${encodeURIComponent(token)}`);
    renderCustomerBookings(customerBookings);
    return customerBookings;
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
  const booking = listMode ? await loadCustomerBookings() : await load();
  if (listMode) return;
  if (booking && action === "verify" && booking.awaiting_email_confirmation) act("verify");
  if (booking && action === "confirm" && booking.can_confirm) act("confirm");
}

init();
