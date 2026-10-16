// Shared helpers for every page: JSON API calls, safe DOM building, formatting.

export class ApiError extends Error {
  // status 0 = no response (network error or server unreachable).
  constructor(status, message, body, path) {
    super(message);
    this.status = status;
    this.body = body;
    this.path = path;
  }
}

export async function api(path, { method = "GET", body } = {}) {
  // Customer pages set <html lang> via i18n.js; the server answers messages in it.
  const options = { method, credentials: "same-origin", headers: { "X-Lang": pageLang() } };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new ApiError(0, "Could not reach the server. Please check your connection.", null, path);
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = (data && data.detail) || "Something went wrong. Please try again.";
    throw new ApiError(response.status, message, data, path);
  }
  return data;
}

// Owner pages: send the visitor to the login screen when the session is missing.
export function redirectToLoginOn401(error) {
  if (error instanceof ApiError && error.status === 401) {
    window.location.replace("/owner/login.html");
    return true;
  }
  return false;
}

// Build elements without innerHTML, so API data is always treated as text.
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === false || value == null) continue;
    if (key === "class") el.className = value;
    else if (key.startsWith("on")) el.addEventListener(key.slice(2), value);
    else el.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child == null || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return el;
}

// One label/value pair of a <dl class="facts">, wrapped in a <div> (valid inside <dl>) so
// the new look can lay pairs out in columns; the classic look ignores the wrapper.
export function fact(label, value) {
  return h("div", {}, h("dt", {}, label), h("dd", {}, value));
}

// Replace an element's children, skipping false/null/undefined (from `cond && h(...)`).
export function fill(target, ...children) {
  target.replaceChildren(...children.flat().filter((c) => c != null && c !== false));
}

const EYE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.75" stroke-linejoin="round" d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle fill="none" stroke="currentColor" stroke-width="1.75" cx="12" cy="12" r="2.5"/></svg>';

// The Classic look / Figma design button (state lives in theme.js). It names the look it
// switches to: labels = { classic: "Classic look", calm: "Figma design" } in the page's language.
// The label stays in the DOM (it may only be hidden visually), so screen readers always
// hear it.
export function themeSwitch(labels) {
  const theme = window.slotwiseTheme;
  const label = h("span", { class: "theme-switch-label" });
  const button = h("button", { type: "button", class: "theme-switch" }, label);
  button.insertAdjacentHTML("afterbegin", EYE); // static markup, no data
  const sync = () => {
    label.textContent = theme && theme.current() === "calm" ? labels.classic : labels.calm;
    button.title = label.textContent;
  };
  button.addEventListener("click", () => {
    if (!theme) return;
    theme.set(theme.current() === "calm" ? "classic" : "calm");
    sync();
  });
  sync();
  return button;
}

// Figma design: the picture for a treatment tile. Category artwork (img/art/) until the studio
// uploads its own photo. Decorative (aria-hidden); a visual copy of the description slides up
// over it on hover, focus or tap, while the real description stays in the page for screen
// readers. Hidden in the classic look (.calm-only).
export function treatmentMedia(service, category, tag = "div") {
  const art = String(category || "").toLowerCase().replace(/[^a-z]/g, "");
  const picture = service.photo_url || `/img/art/${art || "massages"}.svg`;
  // An uploaded photo with the owner's description is announced; artwork is decoration.
  const label = service.photo_url && service.photo_alt
    ? { role: "img", "aria-label": service.photo_alt } : { "aria-hidden": "true" };
  return h(tag, {
    class: `treatment-media calm-only${service.photo_url ? " has-photo" : ""}`, ...label,
    style: `--art: url("${picture.replace(/["\\]/g, "")}")`,
  }, service.description && h("span", { class: "treatment-media-desc", "aria-hidden": "true" }, service.description));
}

export function pageLang() {
  return document.documentElement.lang === "de" ? "de" : "en";
}

const numberLocale = () => (pageLang() === "de" ? "de-DE" : "en-IE");

// Prices arrive as strings like "70.00"; show "€70" / "€12.50" (English) or
// "70 €" / "12,50 €" (German).
export function formatEuro(amount) {
  const value = Number(amount);
  return new Intl.NumberFormat(numberLocale(), {
    style: "currency", currency: "EUR", minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
  }).format(value);
}

export function formatMinutes(minutes) {
  return pageLang() === "de" ? `${minutes} Min.` : `${minutes} min`;
}
