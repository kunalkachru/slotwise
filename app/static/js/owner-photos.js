// Treatment photos: one page for all of them. Photos are resized here in the browser (longest
// side 1600 px, JPEG) before upload, so the server needs no image library and Neon stays small.
import { fill, h } from "/js/api.js";
import { toast } from "/js/owner-forms.js";
import { ownerApi, showPageError, startOwnerPage } from "/js/owner-shell.js";

const MAX_SIDE = 1600;
const MAX_BYTES = 600 * 1024;
const CATEGORIES = ["Massages", "Facials", "Reflexology"];
const target = document.getElementById("photos");

function canvasBlob(canvas, quality) {
  return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
}

async function resize(file) {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  for (const quality of [0.82, 0.72, 0.6, 0.5]) {
    const blob = await canvasBlob(canvas, quality);
    if (blob && blob.size <= MAX_BYTES) return blob;
  }
  throw new Error("This photo is too detailed to shrink under 600 KB. Please choose a smaller one.");
}

async function upload(service, file) {
  if (!/^image\/(jpeg|png|webp)$/.test(file.type)) throw new Error("Please choose a JPEG, PNG or WebP photo.");
  const blob = await resize(file);
  const response = await fetch(`/owner/services/${service.id}/photo`, {
    method: "PUT", credentials: "same-origin", headers: { "Content-Type": "image/jpeg" }, body: blob,
  });
  if (response.status === 401) { window.location.replace("/owner/login.html"); return; }
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error((data && data.detail) || "Something went wrong. Please try again.");
  }
}

function card(service) {
  const status = h("p", { class: "photo-status", role: "status" });
  const fileInput = h("input", { type: "file", accept: "image/jpeg,image/png,image/webp", class: "visually-hidden", id: `photo-file-${service.id}` });
  const busy = (on) => { cardEl.classList.toggle("is-busy", on); };
  const handle = async (file) => {
    if (!file) return;
    busy(true);
    status.textContent = "Uploading…";
    try {
      await upload(service, file);
      toast(`Photo saved for ${service.name}`);
      await load();
    } catch (e) {
      status.textContent = e.message;
      status.className = "photo-status field-error";
      busy(false);
    }
  };
  fileInput.onchange = () => handle(fileInput.files[0]);

  const altEn = h("input", { value: service.alt_text || "", maxlength: "200", id: `alt-${service.id}`, placeholder: "e.g. Warm stones on a towel" });
  const altDe = h("input", { value: service.alt_text_de || "", maxlength: "200", id: `alt-de-${service.id}`, placeholder: "z. B. Warme Steine auf einem Handtuch" });
  const saveTexts = async () => {
    try {
      await ownerApi(`/owner/services/${service.id}/photo/text`, { method: "PUT", body: { alt_text: altEn.value, alt_text_de: altDe.value } });
      toast("Description saved");
    } catch (e) { status.textContent = e.message; status.className = "photo-status field-error"; }
  };
  const remove = async () => {
    try {
      await ownerApi(`/owner/services/${service.id}/photo`, { method: "DELETE" });
      toast(`Photo removed from ${service.name}`);
      load();
    } catch (e) { status.textContent = e.message; status.className = "photo-status field-error"; }
  };

  const preview = service.photo_url
    ? h("div", { class: "photo-preview", style: `background-image: url("${service.photo_url.replace(/["\\]/g, "")}")` })
    : h("div", { class: "photo-preview is-empty" }, h("span", {}, "No photo yet"));
  const cardEl = h("article", { class: "photo-card", "aria-label": service.name },
    preview,
    h("div", { class: "photo-card-body" },
      h("h3", {}, service.name, !service.active && h("span", { class: "muted" }, " (inactive)")),
      service.is_demo && h("span", { class: "status-badge pending" }, "Demo photo"),
      h("div", { class: "row" },
        fileInput, // before its label: the label shows the input's keyboard focus
        h("label", { class: "btn btn-small", for: fileInput.id }, service.photo_url ? "Replace photo" : "Upload photo"),
        service.photo_url && h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: remove }, "Remove")),
      h("p", { class: "field-hint photo-drop-hint" }, "Or drop a photo on this card."),
      service.photo_url && !service.is_demo && h("div", { class: "photo-texts" },
        h("div", { class: "field" }, h("label", { for: altEn.id }, "Description for screen readers"), altEn),
        h("div", { class: "field" }, h("label", { for: altDe.id }, "Description (German)"), altDe),
        h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: saveTexts }, "Save description")),
      status,
    ),
  );
  cardEl.addEventListener("dragover", (e) => { e.preventDefault(); cardEl.classList.add("is-dragover"); });
  cardEl.addEventListener("dragleave", () => cardEl.classList.remove("is-dragover"));
  cardEl.addEventListener("drop", (e) => { e.preventDefault(); cardEl.classList.remove("is-dragover"); handle(e.dataTransfer.files[0]); });
  return cardEl;
}

async function load() {
  let data;
  try {
    data = await ownerApi("/owner/photos");
  } catch (error) {
    showPageError(error, target);
    return;
  }
  const toggle = h("input", { type: "checkbox", id: "show-photos", checked: data.show_photos, onchange: async (e) => {
    try {
      await ownerApi("/owner/photos/settings", { method: "PUT", body: { show_photos: e.target.checked } });
      toast(e.target.checked ? "Photos are shown to customers" : "Photos are hidden from customers");
    } catch (err) { toast(err.message); e.target.checked = !e.target.checked; }
  } });
  const demo = async (method) => {
    try {
      const result = await ownerApi("/owner/photos/demo", { method });
      toast(method === "POST" ? `${result.added} demo photos added` : `${result.removed} demo photos removed`);
      load();
    } catch (e) { toast(e.message); }
  };
  fill(target,
    h("div", { class: "photos-toolbar" },
      h("label", { class: "check", for: "show-photos" }, toggle, "Show treatment photos to customers"),
      h("div", { class: "row" },
        h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => demo("POST") }, "Use demo photos"),
        h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => demo("DELETE") }, "Remove demo photos"))),
    h("p", { class: "muted" }, "Only upload photos you own. If people are recognisable, you need their consent. Photos are shrunk to 1600 px before upload."),
    CATEGORIES.map((category) => {
      const services = data.services.filter((s) => s.category === category);
      return services.length > 0 && h("section", { class: "photo-group" },
        h("h2", {}, category),
        h("div", { class: "photo-grid" }, services.map(card)));
    }),
  );
}

startOwnerPage("photos").then(load).catch((error) => showPageError(error));
