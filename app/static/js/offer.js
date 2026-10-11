import { api, fill, formatEuro, h } from "/js/api.js";

const token = new URLSearchParams(location.search).get("token") || "";
const target = document.getElementById("offer");
const longDate = new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });
const offerUrl = `/public/waitlist/offers/${encodeURIComponent(token)}`;
let timer = null;

function done(title, text, extra) {
  clearInterval(timer);
  fill(target, h("h1", {}, title), h("p", { class: "muted" }, text), extra, h("a", { class: "btn btn-block", href: "/" }, "Back to home"));
}

function render(offer, studio) {
  const countdown = h("p", { class: "countdown", "aria-live": "off" });
  const error = h("p", { class: "alert", role: "alert", hidden: true });
  const tick = () => {
    const left = Math.max(0, new Date(offer.expires_at) - Date.now());
    const minutes = Math.floor(left / 60000);
    const seconds = Math.floor((left % 60000) / 1000);
    countdown.textContent = `${minutes}:${String(seconds).padStart(2, "0")} left to claim`;
    countdown.classList.toggle("urgent", left < 5 * 60000);
    if (left === 0) done("Sorry, this offer has expired.", "The time has gone to the next person on the waitlist.");
  };
  const act = async (kind, button) => {
    target.querySelectorAll("button").forEach((b) => (b.disabled = true));
    error.hidden = true;
    try {
      const result = await api(`${offerUrl}/${kind}`, { method: "POST" });
      if (kind === "claim") {
        done(`You're booked, ${result.customer_first_name}!`,
          `${longDate.format(new Date(`${result.date}T12:00:00Z`))} at ${result.time} with ${result.therapist_name}. A confirmation with your booking link has been emailed to you.`,
          h("p", { class: "pay-note" }, `Total ${formatEuro(result.total_price)} · Pay at the studio`));
      } else {
        done("No problem", "We've offered the time to the next person on the waitlist.");
      }
    } catch (e) {
      if (e.status === 410) return done("Sorry, this offer has expired.", "The time has gone to the next person on the waitlist.");
      error.textContent = e.message;
      error.hidden = false;
      target.querySelectorAll("button").forEach((b) => (b.disabled = false));
      button.focus();
    }
  };
  fill(target,
    h("h1", {}, "A time is free for you"),
    h("dl", { class: "facts" },
      h("dt", {}, "Date"), h("dd", {}, longDate.format(new Date(`${offer.date}T12:00:00Z`))),
      h("dt", {}, "Time"), h("dd", {}, `${offer.time} (${offer.total_minutes} min)`),
      h("dt", {}, "Therapist"), h("dd", {}, offer.therapist_name),
      studio && h("dt", {}, "Where"), studio && h("dd", {}, studio.address)),
    h("table", { class: "lines" },
      offer.lines.map((l) => h("tr", {}, h("td", { class: l.name.startsWith("+") ? "sub" : "" }, l.name), h("td", {}, formatEuro(l.price)))),
      h("tr", { class: "total" }, h("td", {}, "Total"), h("td", {}, formatEuro(offer.total_price)))),
    h("p", { class: "pay-note" }, "Pay at the studio"),
    countdown,
    error,
    h("div", { class: "actions" },
      h("button", { class: "btn btn-block", type: "button", onclick: (e) => act("claim", e.currentTarget) }, "Claim this time"),
      h("button", { class: "btn btn-ghost btn-block", type: "button", onclick: (e) => act("decline", e.currentTarget) }, "No thanks")),
  );
  tick();
  timer = setInterval(tick, 1000);
}

async function init() {
  const studio = await api("/public/studio").catch(() => null);
  if (studio) document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
  try {
    const offer = await api(offerUrl);
    if (offer.status === "claimed") return done("Already claimed", "This time has already been booked through this link.");
    render(offer, studio);
  } catch (e) {
    if (e.status === 410) return done("Sorry, this offer has expired.", "The time has gone to the next person on the waitlist.");
    done("Offer not found", e.message);
  }
}

init();
