import { api, fill, formatEuro, h } from "/js/api.js";

const params = new URLSearchParams(location.search);
const token = params.get("token");
const bookingId = params.get("booking"); // owner view (needs the owner session)
const target = document.getElementById("receipt");
const longDate = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const issued = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "Europe/Berlin" });

async function init() {
  try {
    const [studio, booking] = await Promise.all([
      api("/public/studio"),
      bookingId ? api(`/owner/bookings/${encodeURIComponent(bookingId)}`) : api(`/public/bookings/${encodeURIComponent(token || "")}`),
    ]);
    if (!booking.receipt_number) {
      fill(target, h("h1", {}, "No receipt yet"), h("p", { class: "muted" }, "The studio sends the receipt after your visit."));
      return;
    }
    document.title = `Receipt ${booking.receipt_number} · ${studio.name}`;
    fill(target,
      h("header", {},
        h("div", {}, h("h1", {}, studio.name), h("div", { class: "studio" }, studio.address), h("div", { class: "studio" }, `${studio.phone} · ${studio.email}`)),
        h("div", { class: "meta" }, h("span", { class: "muted" }, "Receipt"), h("strong", {}, booking.receipt_number),
          booking.receipt_sent_at && h("span", { class: "muted" }, `Issued ${issued.format(new Date(booking.receipt_sent_at))}`))),
      h("dl", { class: "facts" },
        booking.customer && h("dt", {}, "Customer"), booking.customer && h("dd", {}, `${booking.customer.first_name} ${booking.customer.last_name}`),
        h("dt", {}, "Appointment"), h("dd", {}, `${longDate.format(new Date(`${booking.date}T12:00:00Z`))}, ${booking.time}`),
        h("dt", {}, "Therapist"), h("dd", {}, booking.therapist_name)),
      h("table", { class: "lines" },
        booking.items.map((i) => h("tr", {},
          h("td", {}, i.item_type === "service" ? i.name : `+ ${i.name}`, i.quantity > 1 ? ` × ${i.quantity} at ${formatEuro(i.unit_price)}` : ""),
          h("td", {}, formatEuro(i.line_total)))),
        h("tr", { class: "total" }, h("td", {}, "Total (EUR)"), h("td", {}, formatEuro(booking.total_price)))),
      h("p", { class: "pay-note" }, "Paid at the studio. Thank you for your visit!"),
    );
  } catch (error) {
    fill(target, h("h1", {}, "Receipt not found"), h("p", { class: "muted" }, error.message));
  }
}

init();
