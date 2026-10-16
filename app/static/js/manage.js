import { api, fill, formatEuro, formatMinutes, h } from "/js/api.js";
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

const bookingUrl = () => `/public/bookings/${encodeURIComponent(token)}`;

function showError(text) {
  fill(target, 
    h("h1", {}, t("manage.not_found")),
    h("p", { class: "muted" }, text),
    h("a", { class: "btn btn-block", href: "/" }, t("nav.back_home")),
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
      h("dt", {}, t("common.date")), h("dd", {}, longDate.format(new Date(`${booking.date}T12:00:00Z`))),
      h("dt", {}, t("common.time")), h("dd", {}, `${t("common.at_time", { time: booking.time })} (${formatMinutes(booking.total_minutes)})`),
      h("dt", {}, t("common.therapist")), h("dd", {}, booking.therapist_name),
      studio && h("dt", {}, t("common.where")), studio && h("dd", {}, studio.address),
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

async function init() {
  studio = await api("/public/studio").catch(() => null);
  if (studio) document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
  // Drop ?action= from the address bar so a reload doesn't repeat it.
  if (action) history.replaceState(null, "", `${location.pathname}?token=${encodeURIComponent(token)}`);
  const booking = await load();
  if (booking && action === "verify" && booking.awaiting_email_confirmation) act("verify");
  if (booking && action === "confirm" && booking.can_confirm) act("confirm");
}

init();
