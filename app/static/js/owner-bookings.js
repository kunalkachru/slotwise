import { ApiError, fill, formatEuro, h } from "/js/api.js";
import { ownerApi, showPageError, startOwnerPage } from "/js/owner-shell.js";

const $ = (id) => document.getElementById(id);
const BERLIN = "Europe/Berlin";
const isoDay = new Intl.DateTimeFormat("en-CA", { timeZone: BERLIN });
const dayLabel = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" });
const longDay = new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const STATUS = { pending: "Awaiting email", expired: "Not confirmed", booked: "Booked", confirmed: "Confirmed", done: "Done", no_show: "No-show", cancelled: "Cancelled" };

const state = {
  view: readPref("view", "day"),
  anchor: isoDay.format(new Date()), // a day inside the shown range
  therapists: [],
  services: [],
  bookings: [],
  request: 0,
};

function readPref(key, fallback) {
  try { return localStorage.getItem(`slotwise:${key}`) || fallback; } catch { return fallback; }
}
function writePref(key, value) {
  try { localStorage.setItem(`slotwise:${key}`, value); } catch { /* private mode */ }
}
function addDays(iso, days) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + days, 12)).toISOString().slice(0, 10);
}
const asDate = (iso) => new Date(`${iso}T12:00:00Z`);
function weekStart(iso) {
  const weekday = (asDate(iso).getUTCDay() + 6) % 7; // Monday = 0
  return addDays(iso, -weekday);
}
function toast(text) {
  const el = h("div", { class: "toast", role: "status" }, text);
  document.body.append(el);
  setTimeout(() => el.remove(), 3200);
}

// ---------- Range and filters ----------
function currentRange() {
  if (state.view === "day") return [state.anchor, state.anchor];
  if (state.view === "week") { const start = weekStart(state.anchor); return [start, addDays(start, 6)]; }
  const start = weekStart(state.anchor); return [start, addDays(start, 13)]; // list: two weeks
}

function filterParams() {
  const [from, to] = currentRange();
  const params = new URLSearchParams({ from, to });
  if ($("filter-therapist").value) params.set("therapist_id", $("filter-therapist").value);
  if ($("filter-status").value) params.set("status", $("filter-status").value);
  if ($("search").value.trim()) params.set("q", $("search").value.trim());
  return params;
}

function step(direction) {
  const days = state.view === "day" ? 1 : state.view === "week" ? 7 : 14;
  state.anchor = addDays(state.anchor, direction * days);
  load();
}

// The first load shows the full page error on failure; later ones (filters, range, after
// saving) keep the page and show the message inline.
async function load({ initial = false } = {}) {
  document.querySelectorAll("[data-view]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === state.view)));
  const [from, to] = currentRange();
  $("range-label").textContent = from === to ? longDay.format(asDate(from)) : `${dayLabel.format(asDate(from))} – ${dayLabel.format(asDate(to))}`;
  const params = filterParams();
  $("export").href = `/owner/bookings/export.csv?${params}`;
  const request = ++state.request;
  try {
    const bookings = await ownerApi(`/owner/bookings?${params}`);
    if (request !== state.request) return;
    state.bookings = bookings;
    render();
  } catch (e) {
    if (request !== state.request) return;
    if (initial) showPageError(e);
    else fill($("bookings"), h("p", { class: "alert" }, e.message));
  }
}

// ---------- Views ----------
const servicesOf = (b) => b.items.filter((i) => i.item_type === "service").map((i) => i.name).join(", ");
const customerName = (b) => `${b.customer.first_name} ${b.customer.last_name}`;
const flag = (b) => b.customer.repeat_no_show && h("span", { class: "flag", title: `${b.customer.no_show_count} no-shows` }, " ⚠");

function card(b, showTherapist) {
  return h("button", { type: "button", class: `cal-card ${b.status}`, onclick: () => openDetail(b.id) },
    h("strong", {}, b.time), ` · ${b.total_minutes} min`,
    h("small", {}, customerName(b), flag(b)),
    h("small", {}, servicesOf(b)),
    showTherapist && h("small", {}, b.therapist_name),
    b.status !== "booked" && b.status !== "confirmed" && h("small", {}, STATUS[b.status]),
  );
}

function render() {
  const target = $("bookings");
  if (state.view === "list") return renderList(target);
  if (state.view === "week") {
    const start = weekStart(state.anchor);
    const today = isoDay.format(new Date());
    return fill(target, h("div", { class: "cal" },
      Array.from({ length: 7 }, (_, i) => addDays(start, i)).map((day) => {
        const items = state.bookings.filter((b) => b.date === day);
        return h("div", { class: `cal-col${day === today ? " today" : ""}` },
          h("h3", {}, dayLabel.format(asDate(day))),
          items.length ? items.map((b) => card(b, true)) : h("p", { class: "cal-empty" }, "No bookings"));
      })));
  }
  // Day: one column per therapist
  const therapistFilter = $("filter-therapist").value;
  const columns = state.therapists.filter((t) => (t.active || state.bookings.some((b) => b.therapist_id === t.id)) && (!therapistFilter || String(t.id) === therapistFilter));
  fill(target, h("div", { class: "cal" },
    columns.map((t) => {
      const items = state.bookings.filter((b) => b.therapist_id === t.id);
      return h("div", { class: "cal-col" }, h("h3", {}, t.display_name),
        items.length ? items.map((b) => card(b, false)) : h("p", { class: "cal-empty" }, "No bookings"));
    })));
}

function renderList(target) {
  if (!state.bookings.length) return fill(target, h("p", { class: "state" }, "No bookings in this range."));
  fill(target, h("div", { class: "table-wrap" }, h("table", { class: "data" },
    h("thead", {}, h("tr", {}, ["Date", "Time", "Customer", "Therapist", "Services", "Total", "Status"].map((c) => h("th", { scope: "col" }, c)))),
    h("tbody", {}, state.bookings.map((b) =>
      h("tr", { class: "clickable", tabindex: "0", onclick: () => openDetail(b.id), onkeydown: (e) => e.key === "Enter" && openDetail(b.id) },
        h("td", {}, dayLabel.format(asDate(b.date))), h("td", {}, b.time),
        h("td", {}, customerName(b), flag(b)), h("td", {}, b.therapist_name),
        h("td", {}, servicesOf(b)), h("td", { class: "num" }, formatEuro(b.total_price)),
        h("td", {}, h("span", { class: `status-badge ${b.status}` }, STATUS[b.status])),
      ))),
  )));
}

// ---------- Detail panel ----------
async function openDetail(id) {
  const dialog = $("detail");
  fill($("detail-body"), h("p", { class: "notice is-loading" }, "Loading…"));
  if (!dialog.open) dialog.showModal();
  try {
    renderDetail(await ownerApi(`/owner/bookings/${id}`));
  } catch (e) {
    fill($("detail-body"), h("p", { class: "alert" }, e.message));
  }
}

function errorBox() {
  return h("p", { class: "alert", role: "alert", hidden: true });
}
function showError(box, error) {
  box.textContent = error.message;
  box.hidden = false;
}

function renderDetail(b) {
  $("detail-title").textContent = customerName(b);
  const statusError = errorBox();
  const statusSelect = h("select", { "aria-label": "Status" },
    Object.entries(STATUS).map(([value, label]) => h("option", { value, selected: value === b.status }, label)));
  const locked = Boolean(b.receipt_sent_at) || b.status === "cancelled";

  const saveStatus = async () => {
    statusError.hidden = true;
    try {
      const updated = await ownerApi(`/owner/bookings/${b.id}/status`, { method: "PUT", body: { status: statusSelect.value } });
      toast(`Status: ${STATUS[updated.status]}`);
      renderDetail(updated);
      load();
    } catch (e) { showError(statusError, e); statusSelect.value = b.status; }
  };

  const receiptError = errorBox();
  const sendReceipt = async (button) => {
    button.disabled = true;
    receiptError.hidden = true;
    try {
      const updated = await ownerApi(`/owner/bookings/${b.id}/receipt`, { method: "POST" });
      toast(`Receipt ${updated.receipt_number} sent`);
      renderDetail(updated);
      load();
    } catch (e) { showError(receiptError, e); button.disabled = false; }
  };

  fill($("detail-body"),
    h("section", {},
      h("span", { class: `status-badge ${b.status}` }, STATUS[b.status]),
      b.late_cancellation && h("span", { class: "status-badge cancelled" }, " Late cancellation"),
      h("dl", { class: "facts" },
        h("dt", {}, "When"), h("dd", {}, `${longDay.format(asDate(b.date))}, ${b.time} (${b.total_minutes} min)`),
        h("dt", {}, "Therapist"), h("dd", {}, b.therapist_name),
        h("dt", {}, "Email"), h("dd", {}, h("a", { href: `mailto:${b.customer.email}` }, b.customer.email)),
        h("dt", {}, "Phone"), h("dd", {}, h("a", { href: `tel:${b.customer.phone.replace(/\s+/g, "")}` }, b.customer.phone)),
        h("dt", {}, "No-shows"), h("dd", { class: b.customer.repeat_no_show ? "flag" : "" }, String(b.customer.no_show_count), b.customer.repeat_no_show ? " ⚠ repeat no-show" : ""),
        h("dt", {}, "Source"), h("dd", {}, b.source),
        b.customer_note && h("dt", {}, "Note"), b.customer_note && h("dd", {}, b.customer_note),
      ),
    ),
    h("section", {},
      h("h3", {}, "Status"),
      h("div", { class: "row" }, statusSelect, h("button", { class: "btn btn-small", type: "button", disabled: Boolean(b.receipt_sent_at), onclick: saveStatus }, "Save status")),
      !b.has_started && h("p", { class: "field-hint" }, "Done and no-show can be set once the appointment has started."),
      statusError,
    ),
    itemsSection(b, locked),
    h("section", {},
      h("h3", {}, "Receipt"),
      b.receipt_number && h("p", {}, `Receipt ${b.receipt_number} sent `, h("a", { href: `/receipt.html?booking=${b.id}`, target: "_blank", rel: "noopener" }, "Print receipt")),
      h("div", { class: "row" },
        h("button", { class: "btn btn-small", type: "button", disabled: b.status !== "done", onclick: (e) => sendReceipt(e.currentTarget) },
          b.receipt_number ? "Resend receipt" : "Send receipt"),
      ),
      b.status !== "done" && h("p", { class: "field-hint" }, "Mark the booking done to send a receipt."),
      receiptError,
    ),
  );
}

function itemsSection(b, locked) {
  const section = h("section", {});
  const showTable = () => fill(section,
    h("h3", {}, "Items"),
    h("table", { class: "lines" },
      b.items.map((i) => h("tr", {},
        h("td", { class: i.item_type === "service" ? "" : "sub" }, i.item_type === "service" ? i.name : `+ ${i.name}`, i.quantity > 1 ? ` × ${i.quantity}` : ""),
        h("td", {}, formatEuro(i.line_total)))),
      h("tr", { class: "total" }, h("td", {}, "Total"), h("td", {}, formatEuro(b.total_price)))),
    !locked && h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: showEditor }, "Adjust items"),
  );
  const showEditor = () => {
    const rows = b.items.map((i) => ({ ...i }));
    const error = errorBox();
    const tbody = h("tbody");
    const drawRows = () => fill(tbody, rows.map((row, index) => h("tr", {},
      h("td", {}, h("select", { "aria-label": "Type", onchange: (e) => (row.item_type = e.target.value) },
        ["service", "add_on", "extra"].map((t) => h("option", { value: t, selected: row.item_type === t }, t === "add_on" ? "add-on" : t)))),
      h("td", { style: "width:100%" }, h("input", { class: "w-name", value: row.name, "aria-label": "Name", oninput: (e) => (row.name = e.target.value) })),
      h("td", {}, h("input", { class: "w-num", type: "number", min: "0", step: "0.01", value: row.unit_price, "aria-label": "Price EUR", oninput: (e) => (row.unit_price = e.target.value) })),
      h("td", {}, h("input", { class: "w-qty", type: "number", min: "1", max: "99", value: row.quantity, "aria-label": "Quantity", oninput: (e) => (row.quantity = Number(e.target.value)) })),
      h("td", {}, h("button", { class: "icon-btn", type: "button", "aria-label": `Remove ${row.name}`, onclick: () => { rows.splice(index, 1); drawRows(); } }, "×")),
    )));
    drawRows();
    fill(section,
      h("h3", {}, "Adjust items"),
      h("p", { class: "field-hint" }, "Lines done on the day, e.g. extra time or a product sold. Prices in EUR."),
      h("table", { class: "items-editor" }, tbody),
      h("div", { class: "row", style: "margin-top:0.5rem" },
        h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => { rows.push({ item_type: "extra", name: "", minutes: 0, unit_price: "0.00", quantity: 1 }); drawRows(); } }, "+ Add line"),
        h("button", { class: "btn btn-small", type: "button", onclick: async () => {
          error.hidden = true;
          try {
            const updated = await ownerApi(`/owner/bookings/${b.id}/items`, { method: "PUT", body: { items: rows.map((r) => ({
              item_type: r.item_type, name: r.name, minutes: Number(r.minutes) || 0,
              unit_price: Number(r.unit_price).toFixed(2), quantity: Number(r.quantity) || 1,
            })) } });
            toast("Items saved");
            renderDetail(updated);
            load();
          } catch (e) { showError(error, e); }
        } }, "Save items"),
        h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: showTable }, "Cancel"),
      ),
      error,
    );
  };
  showTable();
  return section;
}

// ---------- Add phone booking ----------
async function openNewBooking() {
  const form = $("new-form");
  const chosen = { services: new Set(), addOns: new Set() };
  const active = state.services.filter((s) => s.active);
  const error = errorBox();
  const therapistSelect = h("select", { id: "nb-therapist" }, h("option", { value: "" }, "No preference"));
  const dateInput = h("input", { type: "date", id: "nb-date", value: isoDay.format(new Date()), min: isoDay.format(new Date()) });
  const timeSelect = h("select", { id: "nb-time", required: true }, h("option", { value: "" }, "Pick services and a day"));
  const addOnBox = h("div");

  const refreshTimes = async () => {
    fill(timeSelect, h("option", { value: "" }, "Loading…"));
    if (!chosen.services.size || !dateInput.value) return fill(timeSelect, h("option", { value: "" }, "Pick services and a day"));
    const params = new URLSearchParams({ date: dateInput.value, service_ids: [...chosen.services].join(","), add_on_ids: [...chosen.addOns].join(",") });
    if (therapistSelect.value) params.set("therapist_id", therapistSelect.value);
    try {
      const result = await ownerApi(`/owner/availability?${params}`);
      fill(timeSelect, result.slots.length
        ? result.slots.map((s) => h("option", { value: s.time }, `${s.time} · ${s.therapist_name}`))
        : h("option", { value: "" }, "No free times"));
    } catch (e) { fill(timeSelect, h("option", { value: "" }, e.message)); }
  };
  const refreshAddOns = () => {
    fill(addOnBox, active.filter((s) => chosen.services.has(s.id)).flatMap((s) => s.add_ons.filter((a) => a.active).map((a) =>
      h("label", { class: "check" }, h("input", { type: "checkbox", checked: chosen.addOns.has(a.id), onchange: (e) => { e.target.checked ? chosen.addOns.add(a.id) : chosen.addOns.delete(a.id); refreshTimes(); } }),
        `+ ${a.name} (${formatEuro(a.price)})`))));
  };
  const refreshTherapists = () => {
    const qualified = state.therapists.filter((t) => t.active && [...chosen.services].every((id) => t.service_ids.includes(id)));
    fill(therapistSelect, h("option", { value: "" }, "No preference"), qualified.map((t) => h("option", { value: t.id }, t.display_name)));
  };

  const field = (id, label, attrs = {}) => h("div", { class: "field" }, h("label", { for: id }, label), h("input", { id, name: id, ...attrs }));
  fill(form,
    h("div", { class: "field" }, h("label", {}, "Services"),
      active.map((s) => h("label", { class: "check" },
        h("input", { type: "checkbox", onchange: (e) => {
          e.target.checked ? chosen.services.add(s.id) : chosen.services.delete(s.id);
          for (const a of s.add_ons) if (!e.target.checked) chosen.addOns.delete(a.id);
          refreshAddOns(); refreshTherapists(); refreshTimes();
        } }), `${s.name} · ${s.duration_minutes} min · ${formatEuro(s.price)}`))),
    addOnBox,
    h("div", { class: "grid-2" },
      h("div", { class: "field" }, h("label", { for: "nb-therapist" }, "Therapist"), therapistSelect),
      h("div", { class: "field" }, h("label", { for: "nb-date" }, "Day"), dateInput)),
    h("div", { class: "field" }, h("label", { for: "nb-time" }, "Time"), timeSelect),
    h("div", { class: "grid-2" },
      field("first_name", "First name", { autocomplete: "off" }), field("last_name", "Last name", { autocomplete: "off" }),
      field("email", "Email", { type: "email", autocomplete: "off" }), field("phone", "Phone", { type: "tel", autocomplete: "off" })),
    h("div", { class: "field" }, h("label", { for: "note" }, "Note ", h("span", { class: "optional" }, "(optional)")), h("textarea", { id: "note", name: "note", maxlength: "300" })),
    error,
    h("button", { class: "btn btn-block", type: "submit" }, "Save booking"),
  );
  therapistSelect.onchange = refreshTimes;
  dateInput.onchange = refreshTimes;
  form.onsubmit = async (event) => {
    event.preventDefault();
    error.hidden = true;
    try {
      const booking = await ownerApi("/owner/bookings", { method: "POST", body: {
        service_ids: [...chosen.services], add_on_ids: [...chosen.addOns],
        therapist_id: therapistSelect.value ? Number(therapistSelect.value) : null,
        date: dateInput.value, start_time: timeSelect.value,
        first_name: form.first_name.value, last_name: form.last_name.value,
        email: form.email.value, phone: form.phone.value, note: form.note.value || null,
      } });
      $("new-booking").close();
      toast(`Booked ${booking.time} with ${booking.therapist_name}; confirmation emailed`);
      state.anchor = booking.date;
      await load();
      openDetail(booking.id);
    } catch (e) {
      showError(error, e);
      if (e instanceof ApiError && e.status === 400) refreshTimes();
    }
  };
  $("new-booking").showModal();
}

// ---------- Start ----------
async function init() {
  await startOwnerPage("bookings");
  document.querySelectorAll("dialog [data-close]").forEach((b) => b.addEventListener("click", () => b.closest("dialog").close()));
  document.querySelectorAll("[data-view]").forEach((b) => b.addEventListener("click", () => {
    state.view = b.dataset.view; writePref("view", state.view); load();
  }));
  $("prev").onclick = () => step(-1);
  $("next").onclick = () => step(1);
  $("today").onclick = () => { state.anchor = isoDay.format(new Date()); load(); };
  $("filter-therapist").onchange = () => load();
  $("filter-status").onchange = () => load();
  let timer;
  $("search").oninput = () => { clearTimeout(timer); timer = setTimeout(() => load(), 250); };
  $("add-booking").onclick = openNewBooking;

  [state.therapists, state.services] = await Promise.all([ownerApi("/owner/therapists"), ownerApi("/owner/services")]);
  fill($("filter-therapist"), h("option", { value: "" }, "All therapists"),
    state.therapists.map((t) => h("option", { value: t.id }, t.display_name)));
  const focus = Number(new URLSearchParams(location.search).get("booking"));
  await load({ initial: true });
  if (focus) openDetail(focus);
}

init().catch((error) => showPageError(error));
