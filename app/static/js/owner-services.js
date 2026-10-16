import { fill, formatEuro, h } from "/js/api.js";
import { field, openEditor, toast } from "/js/owner-forms.js";
import { ownerApi, showPageError, startOwnerPage } from "/js/owner-shell.js";

const CATEGORIES = ["Massages", "Facials", "Reflexology"];
let services = [];

async function load() {
  services = await ownerApi("/owner/services");
  render();
}

function render() {
  fill(document.getElementById("main"),
    h("div", { class: "page-head" }, h("h1", {}, "Services & add-ons"),
      h("button", { class: "btn btn-small", type: "button", onclick: () => editService() }, "Add service")),
    h("p", { class: "muted" }, "Inactive services are hidden from customers. Existing bookings always keep the name and price they were booked with."),
    h("div", { class: "table-wrap" }, h("table", { class: "data" },
      h("thead", {}, h("tr", {}, ["Category", "Service", "Duration", "Price", "Buffer after", "Active", ""].map((c) => h("th", { scope: "col" }, c)))),
      h("tbody", {}, services.flatMap((s) => [
        h("tr", { class: s.active ? "" : "inactive" },
          h("td", {}, s.category), h("td", {}, h("strong", {}, s.name), s.description && h("div", { class: "field-hint" }, s.description)),
          h("td", { class: "num" }, `${s.duration_minutes} min`), h("td", { class: "num" }, formatEuro(s.price)),
          h("td", { class: "num" }, `${s.buffer_minutes} min`),
          h("td", {}, h("label", { class: "check" }, h("input", { type: "checkbox", checked: s.active, "aria-label": `${s.name} active`, onchange: (e) => toggle(s, e.target) }), s.active ? "Yes" : "No")),
          h("td", {}, h("div", { class: "row" },
            h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => editService(s) }, "Edit"),
            h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => editAddOn(s) }, "+ Add-on"))),
        ),
        ...s.add_ons.map((a) => h("tr", { class: a.active ? "" : "inactive" },
          h("td", {}), h("td", {}, `+ ${a.name}`), h("td", { class: "num" }, `+${a.extra_minutes} min`),
          h("td", { class: "num" }, `+${formatEuro(a.price)}`), h("td", {}), h("td", {}, a.active ? "Yes" : "No"),
          h("td", {}, h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => editAddOn(s, a) }, "Edit add-on")))),
      ])),
    )),
  );
}

async function toggle(service, checkbox) {
  try {
    await ownerApi(`/owner/services/${service.id}`, { method: "PUT", body: { ...serviceBody(service), active: checkbox.checked } });
    toast(`${service.name} is now ${checkbox.checked ? "shown" : "hidden"}`);
    load();
  } catch (e) { toast(e.message); checkbox.checked = !checkbox.checked; }
}

const serviceBody = (s) => ({ category: s.category, name: s.name, description: s.description, name_de: s.name_de, description_de: s.description_de, duration_minutes: s.duration_minutes, price: s.price, buffer_minutes: s.buffer_minutes, active: s.active });

function editService(service) {
  const s = service || { category: "Massages", name: "", description: "", duration_minutes: 60, price: "0.00", buffer_minutes: 10, active: true };
  openEditor(service ? `Edit ${s.name}` : "Add service", [
    field("category", "Category", h("select", {}, CATEGORIES.map((c) => h("option", { value: c, selected: c === s.category }, c)))),
    field("name", "Name", h("input", { value: s.name, required: true, maxlength: "120" })),
    field("description", "One-line description", h("input", { value: s.description || "", maxlength: "500" })),
    h("div", { class: "grid-2" },
      field("name_de", "Name (German)", h("input", { value: s.name_de || "", maxlength: "120" }), "Shown to German-speaking customers; leave empty to use the English name."),
      field("description_de", "Description (German)", h("input", { value: s.description_de || "", maxlength: "500" }))),
    h("div", { class: "grid-2" },
      field("duration_minutes", "Duration (minutes)", h("input", { type: "number", min: "15", max: "240", step: "15", value: s.duration_minutes }), "15 to 240, steps of 15"),
      field("price", "Price (EUR)", h("input", { type: "number", min: "0", step: "0.01", value: s.price }))),
    field("buffer_minutes", "Cleanup buffer after (minutes)", h("input", { type: "number", min: "0", max: "30", value: s.buffer_minutes }), "0 to 30"),
    h("label", { class: "check" }, h("input", { type: "checkbox", name: "active", checked: s.active }), "Shown to customers"),
  ], async (form) => {
    const body = {
      category: form.category.value, name: form.name.value, description: form.description.value || null,
      name_de: form.name_de.value || null, description_de: form.description_de.value || null,
      duration_minutes: Number(form.duration_minutes.value), price: Number(form.price.value).toFixed(2),
      buffer_minutes: Number(form.buffer_minutes.value), active: form.active.checked,
    };
    await ownerApi(service ? `/owner/services/${service.id}` : "/owner/services", { method: service ? "PUT" : "POST", body });
    toast(service ? "Service saved" : "Service added");
    load();
  });
}

function editAddOn(service, addOn) {
  const a = addOn || { name: "", extra_minutes: 0, price: "0.00", active: true };
  openEditor(addOn ? `Edit add-on: ${a.name}` : `Add-on for ${service.name}`, [
    field("name", "Name", h("input", { value: a.name, required: true, maxlength: "120" })),
    field("name_de", "Name (German)", h("input", { value: a.name_de || "", maxlength: "120" }), "Leave empty to use the English name."),
    h("div", { class: "grid-2" },
      field("extra_minutes", "Extra time (minutes)", h("input", { type: "number", min: "0", max: "60", value: a.extra_minutes }), "0 to 60"),
      field("price", "Price (EUR)", h("input", { type: "number", min: "0", step: "0.01", value: a.price }))),
    h("label", { class: "check" }, h("input", { type: "checkbox", name: "active", checked: a.active }), "Shown to customers"),
  ], async (form) => {
    const body = { service_id: service.id, name: form.name.value, name_de: form.name_de.value || null, extra_minutes: Number(form.extra_minutes.value), price: Number(form.price.value).toFixed(2), active: form.active.checked };
    await ownerApi(addOn ? `/owner/add-ons/${addOn.id}` : "/owner/add-ons", { method: addOn ? "PUT" : "POST", body });
    toast(addOn ? "Add-on saved" : "Add-on added");
    load();
  });
}

startOwnerPage("services").then(load).catch((error) => showPageError(error));
