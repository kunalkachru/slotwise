import { fill, h } from "/js/api.js";
import { toast } from "/js/owner-forms.js";
import { ownerApi, showPageError, startOwnerPage } from "/js/owner-shell.js";

const dayLabel = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" });
const timeLabel = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Berlin" });
const STATUS = { pending: "Awaiting email", waiting: "Waiting", offered: "Offered", booked: "Booked", expired: "Offer expired", removed: "Removed / declined" };
const BADGE = { pending: "pending", waiting: "booked", offered: "confirmed", booked: "done", expired: "cancelled", removed: "cancelled" };

// Also called on a day change, "All upcoming" and after Remove: a failed load shows the
// page error in the list area (the day filter stays usable) instead of old rows.
async function load() {
  const day = document.getElementById("wl-date").value;
  const target = document.getElementById("waitlist");
  let entries;
  try {
    entries = await ownerApi(`/owner/waitlist${day ? `?date=${day}` : ""}`);
  } catch (error) {
    showPageError(error, target);
    return;
  }
  if (!entries.length) return fill(target, h("p", { class: "state" }, day ? "Nobody is waiting for this day." : "Nobody is on the waitlist."));
  fill(target, h("div", { class: "table-wrap" }, h("table", { class: "data" },
    h("thead", {}, h("tr", {}, ["Customer", "Services", "Day and window", "Therapist", "Joined", "Status", ""].map((c) => h("th", { scope: "col" }, c)))),
    h("tbody", {}, entries.map((e) => h("tr", {},
      h("td", {}, h("strong", {}, e.customer_name), h("div", { class: "field-hint" }, e.email), h("div", { class: "field-hint" }, e.phone)),
      h("td", {}, e.services.join(", ")),
      h("td", {}, `${dayLabel.format(new Date(`${e.preferred_date}T12:00:00Z`))}, ${e.earliest_time}–${e.latest_time}`),
      h("td", {}, e.therapist_name || "Any"),
      h("td", {}, timeLabel.format(new Date(e.joined_at))),
      h("td", {},
        h("span", { class: `status-badge ${BADGE[e.status]}` }, STATUS[e.status]),
        e.offer_time && h("div", { class: "field-hint" }, `Offered ${e.offer_time}`),
        e.status === "offered" && e.offer_expires_at && h("div", { class: "field-hint" }, `until ${timeLabel.format(new Date(e.offer_expires_at))}`),
        e.booking_id && h("div", {}, h("a", { href: `/owner/bookings.html?booking=${e.booking_id}` }, "View booking"))),
      h("td", {}, ["pending", "waiting", "offered"].includes(e.status) &&
        h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => remove(e) }, "Remove")),
    ))),
  )));
}

async function remove(entry) {
  try {
    await ownerApi(`/owner/waitlist/${entry.id}`, { method: "DELETE" });
    toast(`${entry.customer_name} removed from the waitlist`);
    load();
  } catch (e) { toast(e.message); }
}

async function init() {
  await startOwnerPage("waitlist");
  document.getElementById("wl-date").onchange = load;
  document.getElementById("wl-all").onclick = () => { document.getElementById("wl-date").value = ""; load(); };
  await load();
}

init().catch((error) => showPageError(error));
