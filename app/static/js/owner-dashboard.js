import { fill, formatEuro, h } from "/js/api.js";
import { ownerApi, startOwnerPage } from "/js/owner-shell.js";

const BERLIN = "Europe/Berlin";
const isoDay = new Intl.DateTimeFormat("en-CA", { timeZone: BERLIN });
const longDay = new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const shortDay = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
const asDate = (iso) => new Date(`${iso}T12:00:00Z`);
const percent = (rate) => (rate === null || rate === undefined ? "–" : `${Math.round(rate * 1000) / 10}%`);
const STATUS = { booked: "Booked", confirmed: "Confirmed", done: "Done", no_show: "No-show", cancelled: "Cancelled" };
const SERIES = [
  { key: "no_shows", label: "No-shows", cls: "s1", color: "#2a78d6" },
  { key: "late_cancellations", label: "Late cancellations", cls: "s2", color: "#eb6834" },
];

// ---------- Tiles ----------
function targetBadge(rate, target, lowerIsBetter) {
  if (rate === null || rate === undefined) return h("span", { class: "target none" }, "No data yet");
  const good = lowerIsBetter ? rate < target : rate >= target;
  const goal = `${lowerIsBetter ? "<" : "≥"} ${percent(target)}`;
  return h("span", { class: `target ${good ? "good" : "warn"}`, title: `Goal: ${lowerIsBetter ? "below" : "at least"} ${percent(target)}` },
    good ? "✓ On target" : "▲ Off target", ` · goal ${goal}`);
}

function tile(label, value, note, badge) {
  return h("div", { class: "tile" },
    h("div", { class: "tile-label" }, label),
    h("div", { class: "tile-value live" }, value),
    note && h("div", { class: "tile-note" }, note),
    badge);
}

// ---------- Weekly chart ----------
function niceMax(max) {
  if (max <= 4) return 4;
  const step = Math.ceil(max / 4);
  return step * 4;
}

function weeklyChart(weeks) {
  const max = niceMax(Math.max(0, ...weeks.flatMap((w) => [w.no_shows, w.late_cancellations])));
  const ticks = [0, max / 4, max / 2, (3 * max) / 4, max];
  const tooltip = h("div", { class: "chart-tooltip", hidden: true, role: "tooltip" });
  const plot = h("div", { class: "chart-plot" },
    ticks.slice(1).map((t) => h("div", { class: "chart-grid", style: `bottom:${(t / max) * 100}%` })));

  const show = (event, week) => {
    const chart = plot.parentElement;
    const chartBox = chart.getBoundingClientRect();
    const col = event.currentTarget.getBoundingClientRect();
    const barTop = Math.min(...[...event.currentTarget.children].map((bar) => bar.getBoundingClientRect().top));
    fill(tooltip,
      h("strong", {}, `Week of ${shortDay.format(asDate(week.week_start))}`),
      SERIES.map((s) => h("div", {}, h("span", { class: "swatch", style: `background:${s.color}` }), `${s.label}: ${week[s.key]}`)));
    tooltip.hidden = false;
    // Above the week's tallest bar, kept inside the chart horizontally.
    const half = tooltip.offsetWidth / 2;
    const centre = col.left - chartBox.left + col.width / 2;
    tooltip.style.left = `${Math.min(Math.max(centre, half), chartBox.width - half)}px`;
    tooltip.style.top = `${Math.max(tooltip.offsetHeight + 8, barTop - chartBox.top)}px`;
  };
  const hide = () => { tooltip.hidden = true; };
  // A tooltip left open (touch screens, layout changes) must never stick out.
  window.addEventListener("resize", hide, { passive: true });
  window.addEventListener("scroll", hide, { passive: true });

  for (const week of weeks) {
    const label = `Week of ${shortDay.format(asDate(week.week_start))}: ${week.no_shows} no-shows, ${week.late_cancellations} late cancellations`;
    plot.append(h("div", {
      class: "chart-week", tabindex: "0", role: "img", "aria-label": label,
      onmouseenter: (e) => show(e, week), onmouseleave: hide, onfocus: (e) => show(e, week), onblur: hide,
    },
    SERIES.map((s) => {
      const value = week[s.key];
      return h("div", { class: `chart-bar ${s.cls}${value === 0 ? " zero" : ""}`, style: `height:${(value / max) * 100}%` });
    })));
  }

  return h("div", { class: "chart-card" },
    h("div", { class: "chart-legend", "aria-hidden": "true" },
      SERIES.map((s) => h("span", {}, h("span", { class: "swatch", style: `background:${s.color}` }), s.label))),
    h("div", { class: "chart" },
      h("div", { class: "chart-y", "aria-hidden": "true" },
        ticks.map((t) => h("span", { style: `bottom:${(t / max) * 100}%` }, String(t)))),
      plot,
      h("div", { class: "chart-x", "aria-hidden": "true" }, weeks.map((w) => h("span", {}, shortDay.format(asDate(w.week_start))))),
      tooltip),
    h("details", { class: "table-view" },
      h("summary", {}, "Show as table"),
      h("table", { class: "data" },
        h("thead", {}, h("tr", {}, h("th", { scope: "col" }, "Week of"), SERIES.map((s) => h("th", { scope: "col", class: "num" }, s.label)))),
        h("tbody", {}, weeks.map((w) => h("tr", {},
          h("td", {}, shortDay.format(asDate(w.week_start))),
          SERIES.map((s) => h("td", { class: "num" }, String(w[s.key])))))))),
  );
}

// ---------- Today's appointments ----------
function appointments(rows) {
  if (!rows.length) return h("p", { class: "state" }, "No appointments on this day.");
  const open = (id) => window.location.assign(`/owner/bookings.html?booking=${id}`);
  return h("div", { class: "table-wrap" }, h("table", { class: "data" },
    h("thead", {}, h("tr", {}, ["Time", "Customer", "Therapist", "Services", "Total", "Status"].map((c) => h("th", { scope: "col" }, c)))),
    h("tbody", {}, rows.map((a) => h("tr", {
      class: "clickable", tabindex: "0", onclick: () => open(a.id), onkeydown: (e) => e.key === "Enter" && open(a.id),
    },
      h("td", {}, a.time),
      h("td", {}, a.customer_name, a.repeat_no_show && h("span", { class: "flag", title: "2 or more no-shows" }, " ⚠")),
      h("td", {}, a.therapist_name),
      h("td", {}, a.services.join(", ")),
      h("td", { class: "num" }, formatEuro(a.total_price)),
      h("td", {}, h("span", { class: `status-badge ${a.status}` }, STATUS[a.status]))))),
  ));
}

// ---------- Page ----------
async function load() {
  const input = document.getElementById("dash-date");
  const d = await ownerApi(`/owner/dashboard${input.value ? `?date=${input.value}` : ""}`);
  document.getElementById("welcome").textContent = `Welcome back, ${d.owner_name}`;
  document.getElementById("today").textContent = longDay.format(asDate(d.date));
  input.value = d.date;
  const window30 = `${shortDay.format(asDate(d.window_start))} – ${shortDay.format(asDate(d.date))}`;
  const t = d.targets;

  fill(document.getElementById("dashboard"),
    h("section", { class: "tiles", "aria-label": "Today" },
      tile("Bookings on this day", String(d.today_bookings), "not counting cancellations"),
      tile("Expected revenue", formatEuro(d.expected_revenue_today), "pay at the studio"),
      tile("Confirmed by customer", percent(d.confirmation_rate_today), "via the reminder link")),
    h("section", { class: "dash-section" },
      h("h2", {}, "Is it working? (last 30 days)"),
      h("p", { class: "muted" }, `${window30}, by appointment date. Goals from the project plan.`),
      h("div", { class: "tiles" },
        tile("No-show rate", percent(d.no_show_rate), "no-shows ÷ (done + no-shows)", targetBadge(d.no_show_rate, t.no_show_rate, true)),
        tile("Refilled from waitlist", percent(d.refill_rate), "waitlist bookings ÷ cancellations", targetBadge(d.refill_rate, t.refill_rate, false)),
        tile("Booked online", percent(d.online_share), "online ÷ all bookings", targetBadge(d.online_share, t.online_share, false)),
        tile("Revenue recovered", formatEuro(d.revenue_recovered), "through the waitlist"))),
    h("section", { class: "dash-section" },
      h("h2", {}, "Appointments on this day"),
      appointments(d.appointments)),
    h("section", { class: "dash-section" },
      h("h2", {}, "No-shows and late cancellations per week"),
      h("p", { class: "muted" }, "The last 8 weeks. Hover or focus a week for the numbers."),
      weeklyChart(d.weeks)),
  );
}

async function init() {
  await startOwnerPage("dashboard");
  const input = document.getElementById("dash-date");
  input.value = isoDay.format(new Date());
  input.onchange = () => load().catch(() => {});
  await load();
}

init().catch(() => {});
