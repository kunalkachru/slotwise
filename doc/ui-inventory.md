# UI inventory — what the JavaScript depends on

This file lists every element ID, class, data attribute and ARIA attribute that our scripts **look up** or **create**. It covers each page in `app/static/`. Use it as the checklist for the UI redesign (see [`design/figma-prompt.md`](design/figma-prompt.md)):

- **Hooks the script looks up** (marked 🔒) must keep their exact name and element type. Otherwise the page breaks.
- **Classes the script creates** (marked 🎨) are styling targets. Restyle them freely in CSS, but renaming them means changing the script too.
- Everything else in the HTML is free to change.

Recorded at commit `0646f34`.

## Shared (all pages)

| Hook | Where | Used by | Notes |
|---|---|---|---|
| 🔒 `<html lang>` | every customer page | `i18n.js` sets it; `api.js` `pageLang()` reads it for the `X-Lang` header | Don't hard-code it |
| 🔒 `<html data-i18n-title="…">` | customer pages | `i18n.js` `translatePage()` | The document title key |
| 🔒 `[data-i18n="key"]` | customer HTML | `i18n.js` replaces `textContent` | **The whole text content is replaced**, so put icons *outside* this element, e.g. `<svg/><span data-i18n="…">` |
| 🔒 `[data-i18n-aria="key"]` | (supported, not used yet) | `i18n.js` sets `aria-label` | |
| 🔒 `[data-lang-switch]` | `.topbar-actions` on customer pages except the receipt | `i18n.js` `mountLanguageSwitch()` puts a `button.lang-switch` inside | An empty `<span>` slot |
| 🔒 `[data-studio-name]` | the logo text and the home page `<h1>` | every customer script sets the studio name | `home.js` looks up `h1[data-studio-name]` specifically |
| 🎨 `.lang-switch` | created by `i18n.js` | | Hidden in print |
| localStorage `slotwise:lang` | | `i18n.js` | `"de"` or `"en"` |
| localStorage `slotwise:view` | | `owner-bookings.js` | `"day"`, `"week"` or `"list"` |
| sessionStorage `slotwise:lastBooking` | | `book.js` writes, `confirmation.js` reads | |
| sessionStorage `slotwise:details` | | `book.js` writes after booking and reads on `book.html?again=1` ("Book another treatment") | name, email and phone, this tab only |
| 🎨 Shared classes created by scripts | | | `.btn`, `.btn-block`, `.btn-ghost`, `.btn-small`, `.btn-danger-ghost`, `.muted`, `.notice`, `.state`, `.alert`, `.success-note`, `.pay-note`, `.facts` (`dl`), `.lines` (`table` with `tr.total` and `td.sub`), `.row`, `.actions`, `.field`, `.field-hint`, `.field-error`, `.status-badge <status>` |

**Status classes** on `.status-badge` and `.cal-card` are the raw status values: `pending`, `expired`, `booked`, `confirmed`, `done`, `no_show` and `cancelled`. Today the owner waitlist maps its own statuses onto these same classes. **Decided:** the redesign replaces this mapping with its own classes, `wl-pending`, `wl-waiting`, `wl-offered`, `wl-booked`, `wl-expired` and `wl-removed`, in `owner-waitlist.js` `BADGE`. The current mapping:

| Waitlist status | Class it uses |
|---|---|
| pending | `pending` |
| waiting | `booked` |
| offered | `confirmed` |
| booked | `done` |
| expired | `cancelled` |
| removed | `cancelled` |

## Customer pages

### `index.html` — Home (`js/home.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#studio-address` | `span` | sets the text |
| 🔒 `#studio-phone` | `a` | sets the text and `href="tel:…"` |
| 🔒 `#studio-hours` | `span` | filled with 🎨 `span.hours-part` (one per " · " part) |
| 🔒 `#studio-policy` | `p[hidden]` | sets the text and un-hides it |
| 🔒 `#menu` | `div` | filled with the menu, an empty state or an error |
| 🎨 inside `#menu` | | `section.menu-category` > `h2` + `article.service` > (`div` > `.service-name`, `.service-desc`) + `.service-meta` > (`.service-price`, `.service-duration`) + `ul.service-addons` > `li` + `.service-actions` > `a.btn.btn-ghost.btn-small` |
| `#studio-name`, `#manage` | | referenced only by HTML (`aria-labelledby`, `<details>`); free to change |

### `book.html` — Booking (`js/book.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#book-form` | `form` | submit handler; read via `form.first_name/last_name/email/phone/note` (**name attributes required**) |
| 🔒 `#services` | `div` | filled with step 1 option cards |
| 🔒 `#addons-step` / `#addons` | `section[hidden]` / `div` | toggles `hidden`; filled with option cards |
| 🔒 `#therapist-step`, `#date-step`, `#time-step`, `#details-step` | `section[hidden]` | `hidden` toggled together; `#details-step` is scrolled into view by the waitlist |
| 🔒 `#therapist-hint` | `p.step-hint[hidden]` | shown with two or more treatments |
| 🔒 `#therapists` | `div` | one treatment: a 🎨 `div.chips[role=radiogroup]` of `button.chip[role=radio][aria-pressed][aria-checked][title=bio]`; several: 🎨 `div.therapist-rows` > `div.therapist-row` > `p.therapist-row-name` (> `span.therapist-row-number`) + the same chips, one row per treatment |
| 🔒 `#therapist-error` | `p.field-error[hidden]` | error text |
| 🔒 `#days` | `div.chips.scroll` | filled with 🎨 `button.chip.day[aria-pressed][aria-label]` > `small` + text |
| 🔒 `#date-input` | `input[type=date]` | `min`, `max`, `value` and a change handler |
| 🔒 `#times` | `div[aria-live]` | filled with 🎨 `p.notice`, `p.field-error`, `div.times` > `button.time-btn[aria-pressed]` (> `small` for the therapist), or the waitlist box. Several treatments: 🎨 `div.time-modes` (two `button.chip[aria-pressed]`: Suggested times / Choose times myself, + `p.step-hint`); suggested chains in `div.times.times-chains` (`small` = "Lena → Sofia"); "Choose times myself" = one 🎨 `div.pick-strip` (`.is-waiting` until the previous pick) per treatment |
| 🔒 `#first_name`, `#last_name`, `#email`, `#phone`, `#note` | inputs with matching `name` | the server's field errors are matched by **ID** (`showFieldError`), so the IDs must equal the API field names |
| 🔒 `.field` | the wrapper of each input | the error is appended into `input.closest(".field")` |
| 🔒 `#summary-when` | `p` | text |
| 🔒 `#summary-plan` | `ol.summary-plan[hidden]` | several treatments: one `li` per treatment (`span.plan-time` + name + `small` therapist), `li.plan-break` for a break |
| 🔒 `#summary-lines` | `table` | filled with `tr` > `td`(`.sub`) rows + `tr.total` |
| 🔒 `#book-error` | `div.alert[role=alert][hidden]` | the general error |
| 🔒 `#confirm` | `button[type=submit][form=book-form]` | `disabled` toggled; text switches to "Booking…". It lives **outside** the form, linked by the `form` attribute |
| 🎨 Option cards | | `label.choice` > `input[type=checkbox]` + `span` > `.choice-name` (+ `small.muted`) + `.choice-meta` > `small`; group titles `p.choice-group-title` |
| 🎨 Waitlist box | | `div.waitlist-box` > `h3`, `p.step-hint`, `.row` > `label[for=wl-earliest]`, 🔒 `select#wl-earliest`, `label[for=wl-latest]`, 🔒 `select#wl-latest`; `p.field-hint`; `button.btn`; `p[role=status]` (class becomes `success-note` or `field-error`) |
| `.step`, `.step-number`, `.book-layout`, `.summary`, `.form-grid`, `.full`, `.date-other`, `.optional` | | HTML-only styling; free to restyle |

**Redesign note:** the new mobile sticky bar ("2 items · 75 min · €82" + Confirm booking) needs a small change in `renderSummary()` to fill it. Either keep the single `#confirm` button and move it into the bar with CSS on mobile, or add a second button with `form="book-form"` that mirrors `#confirm`'s `disabled` state.

### `confirmation.html` — Booking result (`js/confirmation.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#confirmation` | `section` | the whole card content is rebuilt |
| 🎨 inside | | `div.confirm-icon` (inline SVG envelope or check), `h1`, `p.success-note`, `dl.facts`, `table.lines`, `p.pay-note`, `p.muted`, `a.btn.btn-block` |

### `manage.html` — Manage booking (`js/manage.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#manage` | `section` | rebuilt; `#manage button` elements are all disabled during an action |
| 🎨 inside | | `p.success-note` or `p.alert` (message), `span.status-badge.<status>`, `h1`, `dl.facts`, `table.lines`, `p.success-note` with the receipt link, `p.pay-note`, `p.muted`, `div.actions` > `button.btn.btn-block`, `button.btn.btn-danger-ghost.btn-block`, `a.btn.btn-ghost.btn-block`; `div.confirm-cancel[role=group]` > `p` + `.row` > `button.btn` (currently with inline `style="background: var(--danger)"`; replace with a `.btn-danger` class) + `button.btn.btn-ghost`; `p.policy-note` (+ `.late`) |

### `offer.html` — Waitlist offer (`js/offer.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#offer` | `section.card.confirm-card` | rebuilt; its buttons are disabled during an action |
| 🎨 inside | | `h1`, `dl.facts`, `table.lines`, `p.pay-note`, `p.countdown` (gets 🔒 class **`.urgent`** under 5 minutes), `p.alert[role=alert]`, `div.actions` > buttons |

### `waitlist-confirm.html` — Waitlist confirmed (`js/waitlist-confirm.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#result` | `section.card.confirm-card` | rebuilt: `h1`, `p`, `p.muted`, `a.btn.btn-block` |

### `receipt.html` — Receipt (`js/receipt.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#receipt` | `main.receipt` | rebuilt: `header` > (`div` > `h1`, `div.studio` ×2) + `div.meta` > (`span.muted`, `strong`, `span.muted`); `dl.facts`; `table.lines` with `tr.total`; `p.pay-note` |
| `.no-print` | `div` | the Back and Print buttons (inline `onclick`); hidden by `@media print` |

There is no top bar and no language switch on the receipt, but `i18n.js` is still loaded, through `receipt.js`.

## Owner pages

### Shell — all owner pages except login (`js/owner-shell.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#owner-layout` | `div.owner-layout[hidden]` | un-hidden after the session check |
| 🔒 `#sidebar` | `aside.sidebar` | filled with `a.logo` (inline leaf SVG) + `nav[aria-label="Owner menu"]` > `a[aria-current=page]` links + a "Log out" `button` |
| 🎨 `.soon`, `.badge` | | for menu items without an `href` (none at the moment) |
| `.owner-main`, `.page-head`, `.toolbar` | | HTML structure; free to restyle |

**Redesign notes:**
- The mobile top-menu button and the "Classic look" switch get added here, in `startOwnerPage()`.
- **Built (step 0):** `showPageError(error, target?)` renders 🎨 `section.page-error[role=alert]` > `span.page-error-icon` (inline SVG), `h2`, `p`, `p.page-error-details`, `p.page-error-tips-title`, `ul` > `li`, `.row` > `button.btn` (+ `button.btn.btn-ghost` only when `data-theme="calm"`). It goes into `.owner-main` (or the given `target`, e.g. `#dashboard` when only the day changed), or into `body > main.center-page` when the session check failed. It reads `ApiError.status` (`0` = no response) and `ApiError.path` (new in `api.js`; the query string is never shown). It replaces the silent `init().catch(() => {})` on every owner page and the bare `document.body.textContent = error.message` in the shell (see the porting section 2.8 of the Figma prompt).

### `owner/login.html` (`js/owner-login.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#login-form` | `form` | submit handler; reads `form.email` and `form.password` (**name attributes required**) |
| 🔒 `#login-error` | `div.alert[hidden]` | error text |
| 🔒 `button[type=submit]` | inside the form | disabled while submitting |

### `owner/dashboard.html` (`js/owner-dashboard.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#welcome` | `h1` | "Welcome back, …" |
| 🔒 `#today` | `p` | the long date (note: on `bookings.html`, `#today` is a button; that's a different page, so there's no clash) |
| 🔒 `#dash-date` | `input[type=date]` | change handler |
| 🔒 `#dashboard` | `div[aria-live]` | rebuilt |
| 🎨 inside | | `section.tiles` > `div.tile` > `.tile-label`, `.tile-value.live`, `.tile-note`, `span.target.(good\|warn\|none)`; `section.dash-section` > `h2`, `p.muted`; `div.table-wrap` > `table.data` with `tr.clickable[tabindex=0]`, `td.num`, `span.flag`; chart: `div.chart-card` > `div.chart-legend` > `span` > `span.swatch`; `div.chart` > `div.chart-y` > `span`, `div.chart-plot` > `div.chart-grid` + `div.chart-week[tabindex=0][role=img]` > `div.chart-bar.s1/.s2(.zero)`, `div.chart-x` > `span`, `div.chart-tooltip[role=tooltip]`; `details.table-view` > `summary` + `table.data` |
| Chart colours | | hard-coded in `SERIES[].color` (`#2a78d6`, `#eb6834`) as inline `background` on `.swatch`; the bars use classes `.s1` and `.s2` from CSS. To theme them, read `--chart-1` and `--chart-2` with `getComputedStyle` |

### `owner/bookings.html` (`js/owner-bookings.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#export` | `a` | `href` set to the CSV URL with the filters |
| 🔒 `#add-booking` | `button` | opens the phone-booking dialog |
| 🔒 `[data-view="day\|week\|list"]` | `button`s in `.segmented` | click handlers; `aria-pressed` set |
| 🔒 `#prev`, `#today`, `#next` | `button` | navigation |
| 🔒 `#range-label` | `span` | text |
| 🔒 `#filter-therapist`, `#filter-status` | `select` | change handlers; the therapist options are filled by the script; the status option **values** must stay (`pending`, `booked`, `confirmed`, `done`, `no_show`, `cancelled`, `expired`) |
| 🔒 `#search` | `input[type=search]` | input handler (debounced) |
| 🔒 `#bookings` | `div[aria-live]` | rebuilt |
| 🎨 Day/Week views | | `div.cal` > `div.cal-col(.today)` > `h3` + `button.cal-card.<status>` > `strong`, `small` ×2–4, `span.flag`; `p.cal-empty` |
| 🎨 List view | | `div.table-wrap` > `table.data` > `tr.clickable[tabindex=0]`, `td.num`, `span.status-badge.<status>`; empty `p.state` |
| 🔒 `#detail` | `dialog.panel` | `showModal()` |
| 🔒 `#detail-title`, `#detail-body` | `h2`, `div.panel-body` | title and rebuilt body |
| 🔒 `#new-booking` | `dialog.panel` | `showModal()` / `close()` |
| 🔒 `#new-form` | `form.panel-body` | rebuilt; read via `form.first_name/last_name/email/phone/note` |
| 🔒 `dialog [data-close]` | `button.icon-btn` | close handlers (`closest("dialog")`) |
| 🎨 Detail body | | `section` > `span.status-badge`, `dl.facts`, `dd.flag`; `h3`; `.row` > `select` + `button.btn.btn-small`; `p.field-hint`; `p.alert[role=alert]`; `table.lines`; items editor: `table.items-editor` > `select`, `input.w-name`, `input.w-num`, `input.w-qty`, `button.icon-btn` |
| 🎨 New-booking form | | `div.field` > `label` + `label.check` > checkbox; `div.grid-2`; 🎨 `div.nb-therapists` (one therapist `select` per treatment, 🔒 IDs `#nb-therapist-<service id>`); 🔒 IDs `#nb-date`, `#nb-time` (made by the script; only the labels point at them); `span.optional`; `button.btn.btn-block` |
| 🎨 Day view parts | | a visit with several therapists: one `button.cal-card.cal-part` per part in each therapist's column, with `small.cal-link` ("1 of 2 · continues with Sofia 11:15"); the detail's "Visit" is an `ol.visit-plan` |
| 🎨 `.toast[role=status]` | | appended to `<body>` for 3.2 seconds |

### `owner/services.html` (`js/owner-services.js` + `js/owner-forms.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#main` | `main.owner-main` | the whole page is rebuilt: `div.page-head`, `p.muted`, `div.table-wrap` > `table.data` with `tr.inactive`, `td.num`, `label.check`, `.row` of `button.btn.btn-ghost.btn-small` |
| 🔒 `#editor` | `dialog.panel` | the shared editor dialog (`owner-forms.js` `openEditor()`) |
| 🔒 `#editor-title`, `#editor-form` | `h2`, `form.panel-body` | title; the form is rebuilt; fields are read via `form.<name>` / `form.elements[name]` |
| 🔒 `#editor [data-close]` | `button.icon-btn` | close |
| 🎨 Editor fields | | `div.field` > `label` + input + `p.field-hint`; `div.grid-2`; `label.check`; `p.alert[role=alert]`; inputs get `aria-invalid="true"` on a server error |

### `owner/therapists.html` (`js/owner-therapists.js` + `js/owner-forms.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#main` | `main.owner-main` | rebuilt (two `div.page-head`, two tables, empty `p.state`) |
| 🔒 `#editor`, `#editor-title`, `#editor-form`, `[data-close]` | | as on Services |
| 🔒 `input[name=service]` | checkboxes in the therapist editor | read with `:checked` |
| 🎨 Hours editor | | `div.hours-grid` (a 4-column grid: `strong` headers, `span` day, two `input[type=time]`, `label.check` > checkbox) |

### `owner/waitlist.html` (`js/owner-waitlist.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#wl-date` | `input[type=date]` | change handler |
| 🔒 `#wl-all` | `button` | clears the date |
| 🔒 `#waitlist` | `div[aria-live]` | rebuilt: `table.data`, `span.status-badge.<mapped>`, `div.field-hint`, `p.state` |

### `owner/settings.html` (`js/owner-settings.js`)

| Hook | Element | What the script does |
|---|---|---|
| 🔒 `#settings-form` | `form.settings` | rebuilt: `fieldset` > `legend`, `p.lead`, `div.field` (via `owner-forms.js` `field()`), `div.grid-2`; `p.alert`; `div.actions-row` > `button.btn` |
| 🔒 input names | | `name`, `address`, `phone`, `email`, `opening_hours_text`, `opening_hours_text_de`, `min_notice_hours`, `booking_window_days`, `free_cancellation_hours`, `waitlist_offer_minutes`, `receipt_prefix`, which must equal the API field names (errors are matched by name) |

## Added by the redesign port (steps 0–6)

| Hook | Where | Used by | Notes |
|---|---|---|---|
| 🔒 `<script src="/js/theme.js">` | every page, top of `<head>`, before the stylesheets | sets `<html data-theme="classic\|calm">` before the first paint; exposes `window.slotwiseTheme.current()` / `.set()` | a normal script, not a module; `tests/test_look_switch.py` checks the order |
| 🔒 `<link href="/css/calm.css">` | every page, after `styles.css` | the new look; every rule is scoped to `[data-theme="calm"]` | a test fails on any unscoped rule |
| localStorage `slotwise:theme` | | `theme.js` | `"classic"` or anything else (calm). **The Figma design (calm) is the default** |
| 🔒 `[data-theme-switch]` | `.topbar-actions` on customer pages (not the receipt) | `i18n.js` `mountThemeSwitch()` mounts `api.js` `themeSwitch()` | labels `theme.classic` / `theme.calm` (EN + DE): "Classic look" / "Figma design" |
| 🎨 `button.theme-switch` > svg + `span.theme-switch-label` | top bars and the owner menu | | the label names the look it switches to; under 480 px only the icon shows, and the label stays as the accessible name |
| 🎨 `.calm-only` | new-look-only markup | `styles.css` hides it; `calm.css` shows it | keeps the classic look unchanged |
| 🔒 `#mobile-bar` > `#mobile-bar-text` + `#mobile-confirm` | `book.html` (`.calm-only`) | `book.js` `renderSummary()` and `setConfirm()` | `#mobile-confirm` is a second submit button (`form="book-form"`); both Confirm buttons always share the same state |
| 🔒 `#owner-menu-toggle`, `#owner-nav`, `.owner-page-name` | made by `owner-shell.js` | Menu button (`aria-expanded`, Escape, outside click) and `#sidebar.is-open` | phones and tablets in the new look; hidden in classic |
| 🎨 `.nav-icon` | owner menu links | | `.calm-only` line icons |
| 🎨 `.is-loading` | every "Loading…" placeholder (HTML, `book.js` times, `owner-bookings.js` detail) | | a spinner in the new look; nothing in classic |
| 🎨 `ol.visit-plan` | confirmation, manage, receipt, offer pages; owner booking detail | `visitFact()` in `api.js` (customer pages) | a visit with several therapists: "Your visit" with one `li` per part (`span.plan-time`, names, `small` therapist) and `li.plan-break`; one-therapist bookings keep the plain Therapist fact |
| 🎨 `dl.facts > div` | `api.js` `fact()`, used by confirmation, manage, offer and receipt | | classic: `display: contents` (same layout as before) |
| 🎨 `.btn-danger` | "Yes, cancel booking" in `manage.js` | | replaces an inline style |
| 🎨 `.status-badge.wl-*` | `owner-waitlist.js` `BADGE` | | `wl-pending`, `wl-waiting`, `wl-offered`, `wl-booked`, `wl-expired`, `wl-removed`; classic colours unchanged |
| `/fonts/inter-latin-wght-normal.woff2` + `Inter-OFL.txt` | `calm.css` `@font-face` | | self-hosted Inter (no Google Fonts); `main.py` registers `font/woff2` |

## Rules for the redesign

1. **Never rename** a 🔒 ID, `name` or data attribute without changing the script in the same PR.
2. **Keep the element types** of 🔒 hooks: a `<dialog>` stays a dialog (for `showModal()`), a `<form>` stays a form, and `#confirm` stays a submit button.
3. **Keep `hidden` attributes** as the way sections are shown and hidden. CSS must not force `display` on elements that use `[hidden]`, or add `[hidden] { display: none !important; }`.
4. **Texts stay in the scripts and in `i18n.js`.** A redesign that changes wording changes `i18n.js` (both EN and DE) or the owner scripts, never only the CSS.
5. **New elements for the new look** (the mobile total bar, the owner mobile menu button, icons, skeletons) are added hidden by default in `styles.css`, so the classic look stays unchanged. They are shown only in `calm.css`.
