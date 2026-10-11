import { api, fill, formatEuro, formatMinutes, h } from "/js/api.js";
import { locale, t } from "/js/i18n.js";

const token = new URLSearchParams(location.search).get("token") || "";
const target = document.getElementById("offer");
const longDate = new Intl.DateTimeFormat(locale, { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });
const offerUrl = `/public/waitlist/offers/${encodeURIComponent(token)}`;
let timer = null;

function done(title, text, extra) {
  clearInterval(timer);
  fill(target, h("h1", {}, title), h("p", { class: "muted" }, text), extra, h("a", { class: "btn btn-block", href: "/" }, t("nav.back_home")));
}

function render(offer, studio) {
  const countdown = h("p", { class: "countdown", "aria-live": "off" });
  const error = h("p", { class: "alert", role: "alert", hidden: true });
  const tick = () => {
    const left = Math.max(0, new Date(offer.expires_at) - Date.now());
    const minutes = Math.floor(left / 60000);
    const seconds = Math.floor((left % 60000) / 1000);
    countdown.textContent = t("offer.countdown", { time: `${minutes}:${String(seconds).padStart(2, "0")}` });
    countdown.classList.toggle("urgent", left < 5 * 60000);
    if (left === 0) done(t("offer.expired"), t("offer.expired_text"));
  };
  const act = async (kind, button) => {
    target.querySelectorAll("button").forEach((b) => (b.disabled = true));
    error.hidden = true;
    try {
      const result = await api(`${offerUrl}/${kind}`, { method: "POST" });
      if (kind === "claim") {
        done(t("conf.booked", { name: result.customer_first_name }),
          t("offer.booked_text", { date: longDate.format(new Date(`${result.date}T12:00:00Z`)), time: result.time, therapist: result.therapist_name }),
          h("p", { class: "pay-note" }, t("offer.total_pay", { total: formatEuro(result.total_price) })));
      } else {
        done(t("offer.declined"), t("offer.declined_text"));
      }
    } catch (e) {
      if (e.status === 410) return done(t("offer.expired"), t("offer.expired_text"));
      error.textContent = e.message;
      error.hidden = false;
      target.querySelectorAll("button").forEach((b) => (b.disabled = false));
      button.focus();
    }
  };
  fill(target,
    h("h1", {}, t("offer.h1")),
    h("dl", { class: "facts" },
      h("dt", {}, t("common.date")), h("dd", {}, longDate.format(new Date(`${offer.date}T12:00:00Z`))),
      h("dt", {}, t("common.time")), h("dd", {}, `${t("common.at_time", { time: offer.time })} (${formatMinutes(offer.total_minutes)})`),
      h("dt", {}, t("common.therapist")), h("dd", {}, offer.therapist_name),
      studio && h("dt", {}, t("common.where")), studio && h("dd", {}, studio.address)),
    h("table", { class: "lines" },
      offer.lines.map((l) => h("tr", {}, h("td", { class: l.name.startsWith("+") ? "sub" : "" }, l.name), h("td", {}, formatEuro(l.price)))),
      h("tr", { class: "total" }, h("td", {}, t("common.total")), h("td", {}, formatEuro(offer.total_price)))),
    h("p", { class: "pay-note" }, t("common.pay")),
    countdown,
    error,
    h("div", { class: "actions" },
      h("button", { class: "btn btn-block", type: "button", onclick: (e) => act("claim", e.currentTarget) }, t("offer.claim")),
      h("button", { class: "btn btn-ghost btn-block", type: "button", onclick: (e) => act("decline", e.currentTarget) }, t("offer.no_thanks"))),
  );
  tick();
  timer = setInterval(tick, 1000);
}

async function init() {
  const studio = await api("/public/studio").catch(() => null);
  if (studio) document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
  try {
    const offer = await api(offerUrl);
    if (offer.status === "claimed") return done(t("offer.claimed"), t("offer.claimed_text"));
    render(offer, studio);
  } catch (e) {
    if (e.status === 410) return done(t("offer.expired"), t("offer.expired_text"));
    done(t("offer.not_found"), e.message);
  }
}

init();
