// Shared helpers for every page: JSON API calls, safe DOM building, formatting.

export class ApiError extends Error {
  constructor(status, message, body) {
    super(message);
    this.status = status;
    this.body = body;
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
    throw new ApiError(0, "Could not reach the server. Please check your connection.");
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = (data && data.detail) || "Something went wrong. Please try again.";
    throw new ApiError(response.status, message, data);
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

// Replace an element's children, skipping false/null/undefined (from `cond && h(...)`).
export function fill(target, ...children) {
  target.replaceChildren(...children.flat().filter((c) => c != null && c !== false));
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
