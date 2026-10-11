import { api, fill, formatEuro, formatMinutes, h } from "/js/api.js";
import { locale, t } from "/js/i18n.js";

const longDate = new Intl.DateTimeFormat(locale, {
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
      h("h1", {}, t("conf.missing")),
      h("p", { class: "muted" }, t("conf.missing_text")),
      h("a", { class: "btn btn-block", href: "/" }, t("nav.back_home")),
    );
    return;
  }
  const studio = await api("/public/studio").catch(() => null);
  if (studio) document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));

  const pending = booking.status === "pending";
  const holdUntil = booking.hold_until
    ? new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Berlin" }).format(new Date(booking.hold_until))
    : null;
  const icon = h("div", { class: "confirm-icon" });
  icon.innerHTML = pending ? ENVELOPE : CHECK; // static markup, no data
  document.title = `${t(pending ? "conf.title_pending" : "conf.title_booked")} · ${studio ? studio.name : "Slotwise"}`;
  fill(target, 
    icon,
    h("h1", {}, t(pending ? "conf.almost" : "conf.booked", { name: booking.customer_first_name })),
    pending && h("p", { class: "success-note" },
      t("conf.pending_note", { time: holdUntil || "" })),
    h("dl", { class: "facts" },
      h("dt", {}, t("common.date")), h("dd", {}, longDate.format(new Date(`${booking.date}T12:00:00Z`))),
      h("dt", {}, t("common.time")), h("dd", {}, `${t("common.at_time", { time: booking.time })} (${formatMinutes(booking.total_minutes)})`),
      h("dt", {}, t("common.therapist")), h("dd", {}, booking.therapist_name),
      studio && h("dt", {}, t("common.where")), studio && h("dd", {}, studio.address),
    ),
    h("table", { class: "lines" },
      booking.items.map((item) =>
        h("tr", {},
          h("td", { class: item.item_type === "add_on" ? "sub" : "" }, item.item_type === "add_on" ? `+ ${item.name}` : item.name),
          h("td", {}, formatEuro(item.line_total)),
        ),
      ),
      h("tr", { class: "total" }, h("td", {}, t("common.total")), h("td", {}, formatEuro(booking.total_price))),
    ),
    h("p", { class: "pay-note" }, t("common.pay")),
    !pending && h("p", { class: "success-note" }, t("conf.emailed")),
    pending && h("p", { class: "muted" }, t("conf.spam")),
    h("a", { class: "btn btn-block", href: "/" }, t("nav.back_home")),
  );
}

render();
