import { api, ApiError, formatEuro, h } from "/js/api.js";

// ---------- State ----------
const state = {
  services: new Map(), // id -> service (with category and add_ons)
  addOns: new Map(), // id -> add-on (with service_id)
  selectedServices: [], // ids, in the order chosen
  selectedAddOns: new Set(),
  therapists: [], // offering every selected service
  therapistId: null, // null = no preference
  date: null, // "YYYY-MM-DD"
  slot: null, // { time, therapist_id, therapist_name }
  windowDays: 60,
  timesRequest: 0,
};

const $ = (id) => document.getElementById(id);
const BERLIN = "Europe/Berlin";
const isoDay = new Intl.DateTimeFormat("en-CA", { timeZone: BERLIN }); // YYYY-MM-DD
const dayName = new Intl.DateTimeFormat("en-GB", { weekday: "short", timeZone: "UTC" });
const dayNumber = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
const longDate = new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });

const cents = (amount) => Math.round(Number(amount) * 100);
const euros = (c) => formatEuro((c / 100).toFixed(2));

// Dates are handled as noon UTC so adding days never trips over DST.
function addDays(isoDate, days) {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + days, 12)).toISOString().slice(0, 10);
}
const asDate = (isoDate) => new Date(`${isoDate}T12:00:00Z`);
const todayBerlin = () => isoDay.format(new Date());

// ---------- Step 1: services ----------
function renderServices(menu) {
  const target = $("services");
  target.replaceChildren(
    ...menu.flatMap((category) => [
      h("p", { class: "choice-group-title" }, category.name),
      ...category.services.map((service) =>
        h("label", { class: "choice" },
          h("input", {
            type: "checkbox", value: service.id, name: "service",
            checked: state.selectedServices.includes(service.id),
            onchange: (e) => toggleService(service.id, e.target.checked),
          }),
          h("span", {}, h("span", { class: "choice-name" }, service.name)),
          h("span", { class: "choice-meta" }, formatEuro(service.price), h("small", {}, `${service.duration_minutes} min`)),
        ),
      ),
    ]),
  );
}

function toggleService(id, checked) {
  const others = state.selectedServices.filter((s) => s !== id);
  state.selectedServices = checked ? [...others, id] : others;
  // Drop add-ons whose service is no longer selected.
  for (const addOnId of [...state.selectedAddOns]) {
    if (!state.selectedServices.includes(state.addOns.get(addOnId).service_id)) {
      state.selectedAddOns.delete(addOnId);
    }
  }
  state.slot = null;
  renderAddOns();
  loadTherapists();
  renderSummary();
}

// ---------- Step 2: add-ons ----------
function renderAddOns() {
  const available = state.selectedServices.flatMap((id) =>
    state.services.get(id).add_ons.map((a) => ({ ...a, serviceName: state.services.get(id).name })),
  );
  $("addons-step").hidden = available.length === 0;
  $("addons").replaceChildren(
    ...available.map((addOn) =>
      h("label", { class: "choice" },
        h("input", {
          type: "checkbox", value: addOn.id,
          checked: state.selectedAddOns.has(addOn.id),
          onchange: (e) => {
            e.target.checked ? state.selectedAddOns.add(addOn.id) : state.selectedAddOns.delete(addOn.id);
            state.slot = null;
            renderSummary();
            loadTimes();
          },
        }),
        h("span", {},
          h("span", { class: "choice-name" }, addOn.name),
          available.length > 1 && state.selectedServices.length > 1 && h("small", { class: "muted" }, ` · with ${addOn.serviceName}`),
        ),
        h("span", { class: "choice-meta" }, `+${formatEuro(addOn.price)}`, h("small", {}, addOn.extra_minutes ? `+${addOn.extra_minutes} min` : "no extra time")),
      ),
    ),
  );
}

// ---------- Step 3: therapist ----------
async function loadTherapists() {
  const hasServices = state.selectedServices.length > 0;
  for (const id of ["therapist-step", "date-step", "time-step", "details-step"]) $(id).hidden = !hasServices;
  if (!hasServices) return;

  const error = $("therapist-error");
  error.hidden = true;
  try {
    state.therapists = await api(`/public/therapists?service_ids=${state.selectedServices.join(",")}`);
  } catch (e) {
    state.therapists = [];
    error.textContent = e.message;
    error.hidden = false;
  }
  if (!state.therapists.some((t) => t.id === state.therapistId)) state.therapistId = null;
  renderTherapists();
  loadTimes();
}

function renderTherapists() {
  const options = state.therapists.length > 1
    ? [{ id: null, display_name: "No preference" }, ...state.therapists]
    : state.therapists;
  $("therapists").replaceChildren(
    ...options.map((t) =>
      h("button", {
        type: "button", class: "chip", role: "radio",
        "aria-pressed": String(t.id === state.therapistId || (state.therapists.length === 1 && t.id === state.therapists[0].id)),
        "aria-checked": String(t.id === state.therapistId),
        title: t.short_bio || "",
        onclick: () => {
          state.therapistId = t.id;
          state.slot = null;
          renderTherapists();
          renderSummary();
          loadTimes();
        },
      }, t.display_name),
    ),
  );
}

// ---------- Step 4: day ----------
function renderDays() {
  const today = todayBerlin();
  const dateInput = $("date-input");
  dateInput.min = today;
  dateInput.max = addDays(today, state.windowDays);
  dateInput.value = state.date || "";
  $("days").replaceChildren(
    ...Array.from({ length: 14 }, (_, i) => addDays(today, i)).map((day) =>
      h("button", {
        type: "button", class: "chip day", "aria-pressed": String(day === state.date),
        "aria-label": longDate.format(asDate(day)),
        onclick: () => selectDate(day),
      }, h("small", {}, i18nDay(day, today)), dayNumber.format(asDate(day))),
    ),
  );
}

function i18nDay(day, today) {
  if (day === today) return "Today";
  if (day === addDays(today, 1)) return "Tomorrow";
  return dayName.format(asDate(day));
}

function selectDate(day) {
  state.date = day;
  state.slot = null;
  renderDays();
  renderSummary();
  loadTimes();
}

// ---------- Step 5: times ----------
async function loadTimes() {
  const target = $("times");
  if (!state.date || state.selectedServices.length === 0 || state.therapists.length === 0) {
    target.replaceChildren(h("p", { class: "notice" }, state.date ? "" : "Pick a day to see free times."));
    return;
  }
  const request = ++state.timesRequest; // ignore answers to outdated requests
  target.replaceChildren(h("p", { class: "notice" }, "Looking for free times…"));
  const params = new URLSearchParams({
    date: state.date,
    service_ids: state.selectedServices.join(","),
    add_on_ids: [...state.selectedAddOns].join(","),
  });
  if (state.therapistId !== null) params.set("therapist_id", state.therapistId);
  try {
    const result = await api(`/public/availability?${params}`);
    if (request !== state.timesRequest) return;
    renderTimes(result.slots);
  } catch (e) {
    if (request !== state.timesRequest) return;
    target.replaceChildren(h("p", { class: "field-error" }, e.message));
  }
}

function renderTimes(slots) {
  const target = $("times");
  if (slots.length === 0) {
    target.replaceChildren(h("p", { class: "notice" }, "No free times on this day. Please try another day."));
    return;
  }
  const showName = state.therapistId === null && state.therapists.length > 1;
  target.replaceChildren(
    h("div", { class: "times" },
      slots.map((slot) =>
        h("button", {
          type: "button", class: "time-btn",
          "aria-pressed": String(state.slot?.time === slot.time),
          onclick: () => {
            state.slot = slot;
            renderTimes(slots);
            renderSummary();
          },
        }, slot.time, showName && h("small", {}, slot.therapist_name)),
      ),
    ),
  );
}

// ---------- Summary ----------
function chosenLines() {
  const lines = [];
  for (const id of state.selectedServices) {
    const s = state.services.get(id);
    lines.push({ name: s.name, minutes: s.duration_minutes, price: cents(s.price) });
    for (const a of s.add_ons) {
      if (state.selectedAddOns.has(a.id)) lines.push({ name: a.name, minutes: a.extra_minutes, price: cents(a.price), addOn: true });
    }
  }
  return lines;
}

function renderSummary() {
  const lines = chosenLines();
  const minutes = lines.reduce((sum, l) => sum + l.minutes, 0);
  const total = lines.reduce((sum, l) => sum + l.price, 0);
  const when = $("summary-when");
  if (lines.length === 0) when.textContent = "Choose a treatment to start.";
  else if (state.slot) when.textContent = `${longDate.format(asDate(state.date))} at ${state.slot.time} with ${state.slot.therapist_name}`;
  else if (state.date) when.textContent = `${longDate.format(asDate(state.date))}, pick a time`;
  else when.textContent = "Pick a day and time";

  $("summary-lines").replaceChildren(
    ...lines.map((l) => h("tr", {}, h("td", { class: l.addOn ? "sub" : "" }, l.addOn ? `+ ${l.name}` : l.name), h("td", {}, euros(l.price)))),
    lines.length > 0 && h("tr", {}, h("td", { class: "sub" }, "Total time"), h("td", { class: "sub" }, `${minutes} min`)),
    lines.length > 0 && h("tr", { class: "total" }, h("td", {}, "Total"), h("td", {}, euros(total))),
  );
  $("confirm").disabled = !(lines.length && state.slot);
}

// ---------- Confirm ----------
function clearFieldErrors() {
  document.querySelectorAll("[aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
  document.querySelectorAll(".field .field-error").forEach((el) => el.remove());
}

function showFieldError(field, message) {
  const input = document.getElementById(field);
  if (!input) return false;
  input.setAttribute("aria-invalid", "true");
  input.closest(".field").append(h("p", { class: "field-error" }, message));
  input.focus();
  return true;
}

async function confirmBooking(event) {
  event.preventDefault();
  const form = $("book-form");
  const errorBox = $("book-error");
  errorBox.hidden = true;
  clearFieldErrors();
  if (!state.slot) return;

  const body = {
    service_ids: state.selectedServices,
    add_on_ids: [...state.selectedAddOns],
    therapist_id: state.therapistId,
    date: state.date,
    start_time: state.slot.time,
    first_name: form.first_name.value,
    last_name: form.last_name.value,
    email: form.email.value,
    phone: form.phone.value,
    note: form.note.value || null,
  };
  const button = $("confirm");
  button.disabled = true;
  button.textContent = "Booking…";
  try {
    const booking = await api("/public/bookings", { method: "POST", body });
    try {
      sessionStorage.setItem("slotwise:lastBooking", JSON.stringify(booking));
    } catch {
      /* private mode: the confirmation page falls back to a short message */
    }
    window.location.assign("/confirmation.html");
    return;
  } catch (e) {
    const field = e instanceof ApiError && e.body?.fields?.[0]?.field;
    if (!(field && showFieldError(field, e.message))) {
      errorBox.textContent = e.message;
      errorBox.hidden = false;
    }
    if (e instanceof ApiError && e.status === 400) {
      state.slot = null; // that time was just taken: show fresh times
      loadTimes();
    }
  } finally {
    button.textContent = "Confirm booking";
    renderSummary();
  }
}

// ---------- Start ----------
async function init() {
  $("book-form").addEventListener("submit", confirmBooking);
  $("date-input").addEventListener("change", (e) => e.target.value && selectDate(e.target.value));
  api("/public/studio").then((studio) => {
    state.windowDays = studio.booking_window_days;
    document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
    document.title = `Book · ${studio.name}`;
    renderDays();
  }).catch(() => renderDays());

  try {
    const menu = await api("/public/services");
    for (const category of menu) {
      for (const service of category.services) {
        state.services.set(service.id, service);
        for (const a of service.add_ons) state.addOns.set(a.id, { ...a, service_id: service.id });
      }
    }
    const preselect = Number(new URLSearchParams(location.search).get("service"));
    if (state.services.has(preselect)) state.selectedServices = [preselect];
    renderServices(menu);
    if (state.selectedServices.length) toggleService(state.selectedServices[0], true);
    renderSummary();
  } catch {
    $("services").replaceChildren(h("p", { class: "field-error" }, "Could not load services."));
  }
}

init();
