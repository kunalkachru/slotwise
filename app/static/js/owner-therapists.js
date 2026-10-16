import { fill, h } from "/js/api.js";
import { field, openEditor, toast } from "/js/owner-forms.js";
import { ownerApi, showPageError, startOwnerPage } from "/js/owner-shell.js";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const dayLabel = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
let therapists = [];
let services = [];
let daysOff = [];

async function load() {
  [therapists, services, daysOff] = await Promise.all([
    ownerApi("/owner/therapists"), ownerApi("/owner/services"), ownerApi("/owner/days-off"),
  ]);
  render();
}

const serviceName = (id) => services.find((s) => s.id === id)?.name || `#${id}`;
function hoursSummary(t) {
  if (!t.hours.length) return "No hours yet";
  return DAYS.map((d, i) => {
    const windows = t.hours.filter((w) => w.weekday === i);
    return windows.length ? `${d} ${windows.map((w) => `${w.start_time}–${w.end_time}`).join(", ")}` : null;
  }).filter(Boolean).join(" · ");
}

function render() {
  fill(document.getElementById("main"),
    h("div", { class: "page-head" }, h("h1", {}, "Therapists & hours"),
      h("button", { class: "btn btn-small", type: "button", onclick: () => editTherapist() }, "Add therapist")),
    h("div", { class: "table-wrap" }, h("table", { class: "data" },
      h("thead", {}, h("tr", {}, ["Name", "Services offered", "Weekly hours", "Active", ""].map((c) => h("th", { scope: "col" }, c)))),
      h("tbody", {}, therapists.map((t) => h("tr", { class: t.active ? "" : "inactive" },
        h("td", {}, h("strong", {}, t.display_name), t.short_bio && h("div", { class: "field-hint" }, t.short_bio)),
        h("td", {}, t.service_ids.map(serviceName).join(", ") || "—"),
        h("td", {}, hoursSummary(t)),
        h("td", {}, t.active ? "Yes" : "No"),
        h("td", {}, h("div", { class: "row" },
          h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => editTherapist(t) }, "Edit"),
          h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => editHours(t) }, "Hours"))),
      ))),
    )),
    h("div", { class: "page-head", style: "margin-top:2rem" }, h("h2", {}, "Days off"),
      h("button", { class: "btn btn-small", type: "button", onclick: addDayOff }, "Add day off")),
    daysOff.length
      ? h("div", { class: "table-wrap" }, h("table", { class: "data" },
          h("thead", {}, h("tr", {}, ["Date", "Who", "Reason", ""].map((c) => h("th", { scope: "col" }, c)))),
          h("tbody", {}, daysOff.map((d) => h("tr", {},
            h("td", {}, dayLabel.format(new Date(`${d.date}T12:00:00Z`))),
            h("td", {}, d.therapist_name || h("strong", {}, "Whole studio closed")),
            h("td", {}, d.reason || ""),
            h("td", {}, h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => removeDayOff(d) }, "Remove")),
          )))))
      : h("p", { class: "state" }, "No upcoming days off."),
  );
}

function editTherapist(therapist) {
  const t = therapist || { display_name: "", short_bio: "", short_bio_de: "", active: true, service_ids: [] };
  openEditor(therapist ? `Edit ${t.display_name}` : "Add therapist", [
    field("display_name", "Name", h("input", { value: t.display_name, required: true, maxlength: "80" })),
    field("short_bio", "Short bio", h("textarea", { maxlength: "500" }, t.short_bio || "")),
    field("short_bio_de", "Short bio (German)", h("textarea", { maxlength: "500" }, t.short_bio_de || ""), "Leave empty to use the English bio."),
    h("div", { class: "field" }, h("label", {}, "Services offered"),
      services.map((s) => h("label", { class: "check" },
        h("input", { type: "checkbox", name: "service", value: s.id, checked: t.service_ids.includes(s.id) }),
        s.name, !s.active && h("span", { class: "muted" }, " (inactive)")))),
    h("label", { class: "check" }, h("input", { type: "checkbox", name: "active", checked: t.active }), "Active (can be booked)"),
  ], async (form) => {
    const body = {
      display_name: form.display_name.value, short_bio: form.short_bio.value || null,
      short_bio_de: form.short_bio_de.value || null, active: form.active.checked,
      service_ids: [...form.querySelectorAll("input[name=service]:checked")].map((i) => Number(i.value)),
    };
    await ownerApi(therapist ? `/owner/therapists/${therapist.id}` : "/owner/therapists", { method: therapist ? "PUT" : "POST", body });
    toast(therapist ? "Therapist saved" : "Therapist added");
    load();
  });
}

function editHours(therapist) {
  const rows = DAYS.map((day, weekday) => {
    const w = therapist.hours.find((x) => x.weekday === weekday);
    const start = h("input", { type: "time", step: "900", value: w?.start_time || "", "aria-label": `${day} start` });
    const end = h("input", { type: "time", step: "900", value: w?.end_time || "", "aria-label": `${day} end` });
    const closed = h("input", { type: "checkbox", checked: !w, "aria-label": `${day} closed` });
    const sync = () => { start.disabled = closed.checked; end.disabled = closed.checked; };
    closed.onchange = sync;
    sync();
    return { weekday, day, start, end, closed };
  });
  const extra = therapist.hours.filter((w, i, all) => all.findIndex((x) => x.weekday === w.weekday) !== i);
  openEditor(`Weekly hours: ${therapist.display_name}`, [
    h("div", { class: "hours-grid" },
      h("strong", {}, "Day"), h("strong", {}, "Start"), h("strong", {}, "End"), h("strong", {}, "Closed"),
      rows.flatMap((r) => [h("span", {}, r.day), r.start, r.end, h("label", { class: "check" }, r.closed)])),
    extra.length > 0 && h("p", { class: "field-hint" }, "Split shifts on the same day are kept only for the first window when saved here."),
  ], async () => {
    const hours = rows.filter((r) => !r.closed.checked).map((r) => ({ weekday: r.weekday, start_time: r.start.value, end_time: r.end.value }));
    if (hours.some((x) => !x.start_time || !x.end_time)) throw new Error("Please enter a start and end time for each open day.");
    await ownerApi(`/owner/therapists/${therapist.id}/hours`, { method: "PUT", body: { hours } });
    toast("Hours saved");
    load();
  });
}

function addDayOff() {
  openEditor("Add day off", [
    field("therapist_id", "Who", h("select", {}, h("option", { value: "" }, "Whole studio (closed)"),
      therapists.map((t) => h("option", { value: t.id }, t.display_name)))),
    field("date", "Date", h("input", { type: "date", required: true })),
    field("reason", "Reason", h("input", { maxlength: "120", placeholder: "e.g. Holiday" })),
  ], async (form) => {
    if (!form.date.value) throw new Error("Please choose a date.");
    await ownerApi("/owner/days-off", { method: "POST", body: {
      therapist_id: form.therapist_id.value ? Number(form.therapist_id.value) : null,
      date: form.date.value, reason: form.reason.value || null,
    } });
    toast("Day off added");
    load();
  });
}

async function removeDayOff(dayOff) {
  try {
    await ownerApi(`/owner/days-off/${dayOff.id}`, { method: "DELETE" });
    toast("Day off removed");
    load();
  } catch (e) { toast(e.message); }
}

startOwnerPage("therapists").then(load).catch((error) => showPageError(error));
