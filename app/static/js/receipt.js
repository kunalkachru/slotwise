import { api, fact, fill, formatEuro, h, visitFact } from "/js/api.js";
import { locale, t } from "/js/i18n.js";

const params = new URLSearchParams(location.search);
const token = params.get("token");
const bookingId = params.get("booking"); // owner view (needs the owner session)
const target = document.getElementById("receipt");
const longDate = new Intl.DateTimeFormat(locale, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const issued = new Intl.DateTimeFormat(locale, { day: "numeric", month: "long", year: "numeric", timeZone: "Europe/Berlin" });

// The VAT contained in a gross total, in whole cents with half-up rounding, so it matches the
// server (app/i18n.py vat_included). Receipts must show the rate or the § 19 note (§ 33 UStDV).
function vatLine(total, mode) {
  if (mode !== "19" && mode !== "7") return t("receipt.vat_exempt");
  const cents = Math.round(Number(total) * 100);
  const rate = Number(mode);
  const vat = Math.floor((2 * cents * rate + (100 + rate)) / (2 * (100 + rate)));
  return t("receipt.vat", { rate, amount: formatEuro((vat / 100).toFixed(2)) });
}

async function init() {
  try {
    const [studio, booking] = await Promise.all([
      api("/public/studio"),
      bookingId ? api(`/owner/bookings/${encodeURIComponent(bookingId)}`) : api(`/public/bookings/${encodeURIComponent(token || "")}`),
    ]);
    if (!booking.receipt_number) {
      fill(target, h("h1", {}, t("receipt.none")), h("p", { class: "muted" }, t("receipt.none_text")));
      return;
    }
    document.title = `${t("receipt.title")} ${booking.receipt_number} · ${studio.name}`;
    fill(target,
      h("header", {},
        h("div", {}, h("h1", {}, studio.name), h("div", { class: "studio" }, studio.address), h("div", { class: "studio" }, `${studio.phone} · ${studio.email}`),
          studio.tax_number && h("div", { class: "studio" }, t("receipt.tax_number", { number: studio.tax_number }))),
        h("div", { class: "meta" }, h("span", { class: "muted" }, t("receipt.title")), h("strong", {}, booking.receipt_number),
          booking.receipt_sent_at && h("span", { class: "muted" }, t("receipt.issued", { date: issued.format(new Date(booking.receipt_sent_at)) })))),
      h("dl", { class: "facts" },
        booking.customer && fact(t("receipt.customer"), `${booking.customer.first_name} ${booking.customer.last_name}`),
        fact(t("receipt.appointment"), `${longDate.format(new Date(`${booking.date}T12:00:00Z`))}, ${t("common.at_time", { time: booking.time })}`),
        visitFact(booking, { therapist: t("common.therapist"), visit: t("common.your_visit"), break: t("book.break") })),
      h("table", { class: "lines" },
        booking.items.map((i) => h("tr", {},
          h("td", {}, i.item_type === "service" ? i.name : `+ ${i.name}`, i.quantity > 1 ? ` × ${i.quantity} at ${formatEuro(i.unit_price)}` : ""),
          h("td", {}, formatEuro(i.line_total)))),
        h("tr", { class: "total" }, h("td", {}, t("receipt.total")), h("td", {}, formatEuro(booking.total_price)))),
      h("p", { class: "vat-note" }, vatLine(booking.total_price, studio.vat_mode)),
      h("p", { class: "pay-note" }, t("receipt.paid")),
    );
  } catch (error) {
    fill(target, h("h1", {}, t("receipt.not_found")), h("p", { class: "muted" }, error.message));
  }
}

init();
