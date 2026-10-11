// Small helpers shared by the owner management pages.
import { ApiError, fill, h } from "/js/api.js";

export function toast(text) {
  const el = h("div", { class: "toast", role: "status" }, text);
  document.body.append(el);
  setTimeout(() => el.remove(), 3200);
}

export function field(name, label, input, hint) {
  input.id = input.id || name;
  input.name = name;
  return h("div", { class: "field" }, h("label", { for: input.id }, label), input, hint && h("p", { class: "field-hint" }, hint));
}

// Opens the shared <dialog id="editor"> with a form; `onSave(form)` returns a promise.
export function openEditor(title, children, onSave) {
  const dialog = document.getElementById("editor");
  const form = document.getElementById("editor-form");
  const error = h("p", { class: "alert", role: "alert", hidden: true });
  document.getElementById("editor-title").textContent = title;
  fill(form, children, error, h("button", { class: "btn btn-block", type: "submit" }, "Save"));
  form.onsubmit = async (event) => {
    event.preventDefault();
    error.hidden = true;
    form.querySelectorAll("[aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
    try {
      await onSave(form);
      dialog.close();
    } catch (e) {
      error.textContent = e.message;
      error.hidden = false;
      const fieldName = e instanceof ApiError && e.body?.fields?.[0]?.field;
      if (fieldName && form.elements[fieldName]) form.elements[fieldName].setAttribute("aria-invalid", "true");
    }
  };
  dialog.querySelector("[data-close]").onclick = () => dialog.close();
  dialog.showModal();
}
