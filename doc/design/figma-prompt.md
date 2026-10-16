# Slotwise redesign — Figma Make prompt ("Calm modern")

All texts, labels and messages in this file were taken from the code at commit `0646f34`.

## How to use this prompt — the whole workflow (read this first)

### What this file is

- **Figma Make** is Figma's AI tool. You describe an app in words, and it produces screen designs plus a clickable prototype.
- This file is that description, written so precisely that Figma can't invent things our app doesn't have.
- It has three parts to paste (Part 1, 2 and 3) and, at the end, one section only for us: **"How to port this design"**. That section explains how the design gets into our real app.

### The big picture: five stages

| Stage | Who | What happens | Result |
|---|---|---|---|
| A. Generate | You, in Figma Make | Paste Parts 1–3 one after another | Style guide, component sheet, all screens |
| B. Review and fix | You, in Figma Make | Check the screens against the checklist below and ask Figma for corrections | A design you're happy with |
| C. Hand over | You → me | Export the Make code into `doc/design/figma-make/`, plus a few screenshots if I ask | I can read the exact CSS and see the design |
| D. Port | Me, in this repo | Re-create the look in our HTML/CSS in 6 small PRs, behind the "Classic look / New look" switch | New look live, old look still available |
| E. Decide | You | Try both looks on your phone and laptop | Classic stays the default; later you may make New the default (or remove one look) |

**Nothing in the app changes during stages A–C.** Figma only produces pictures and a throwaway prototype. The real app changes only in stage D, through normal PRs that you review and merge.

### Stage A — Generate the design in Figma Make (about 30–60 minutes)

1. Open figma.com, choose **Make** (or "Figma Make") and start a **new Make file**. Name it "Slotwise — Calm modern".
2. Open this file on GitHub or in your editor. Copy everything **between** the lines `=== PROMPT START (Part 1 of 3) ===` and `=== PROMPT END (Part 1 of 3) ===`. Leave out those two marker lines themselves.
3. Paste it into the Make chat and send it.
4. Wait until it has built the **style guide** (colour swatches, fonts, spacing) and the **component sheet** (buttons, inputs, badges…).
5. Do a quick check now, before you continue. Fixing the style later means re-doing every screen.
   - **Colours:** deep green buttons, warm off-white background, white cards, and orange-brown (`--warm`) only on totals.
   - **Components:** every component appears with all its states, e.g. a button in normal, hover, focus, disabled and "Booking…".
   - **No Tailwind:** if Make shows code, the colours are defined as `--green`, `--warm` and so on, not as Tailwind classes. If you do see Tailwind, write: *"Please follow section 5 of Part 1: put all design values in CSS custom properties with the given names, no Tailwind classes."*
6. Paste **Part 2** (customer screens) the same way, in the **same chat**, so Figma remembers the style.
7. Paste **Part 3** (owner screens) the same way.
8. If Figma Make stops halfway, for example because the answer is too long, write **"Please continue with the next screen"**. You can also ask for one screen at a time: *"Now design Screen C4 — Manage booking, all frames."*

### Stage B — Review and correct (the important part)

Go through the screens with this checklist. For anything wrong, write a short correction in the same chat, e.g. *"In Screen C2 the mobile bottom bar must say 'Confirm booking', not 'Continue'."*

1. **Every screen exists at both sizes:** 390px (phone) and 1440px (desktop).
   - **Customer:** C1 Home, C2 Booking (frames a–i, the waitlist box C2-W and one German frame), C3 Booking result, C4 Manage booking (12 frames), C5 Offer, C6 Waitlist confirmed, C7 Receipt.
   - **Owner:** O1 Login, O2 Dashboard, O3 Bookings (Day, Week and List), O3-D Booking detail, O3-N Add phone booking, O4 Services (plus 2 dialogs), O5 Therapists (plus 3 dialogs), O6 Waitlist, O7 Settings.
2. **The booking page is still ONE page** with steps 1–6. There must be no "Next" or "Continue" buttons. On the phone there is a bottom bar like "2 items · 75 min · €82" with **Confirm booking**.
3. **The texts match exactly.** Figma likes to "improve" wording. Our wording must stay, because the real texts come from our code anyway; a mismatch only causes confusion when porting.
4. **Nothing extra.** Remove anything not in the brief: user accounts, online payment, star ratings, photos of therapists, search on the home page, dark mode, chat bubbles…
5. **The German frame:** long words like "Buchung abschicken" and "Wartet auf Ihre Bestätigung" fit without being cut off.
6. **Accessibility basics:**
   - buttons look big enough to tap with a thumb;
   - text is easy to read on its background;
   - every input has a label above it.
7. **Taste.** Does it feel calm, premium and friendly? This is your call. Ask for changes freely, e.g. *"Make the service cards airier"* or *"The green is too dark, try one step lighter"*. If you change a colour, ask Figma to update the **token** (e.g. `--green`) so that every screen changes together.

### Stage C — Hand the design over to me

#### C1. Export the code (main hand-over)

1. In Figma Make, open the code view and use its download or export option to get the project as a zip, if your plan allows it.
2. Unzip it into **`doc/design/figma-make/`** in this repo. Keep the `src/` folder, `index.html`, the CSS files and `package.json`. **Leave out** `node_modules/` and any `dist/` or `build/` folder; `.gitignore` excludes them anyway.
3. Tell me it's there. I commit it on its own branch and PR. A docs-only PR skips CI.

**This folder is a "dead" reference library.** Nothing builds, serves, tests or deploys it:

| Part of our pipeline | Why it ignores `doc/design/figma-make/` |
|---|---|
| CI (`ci.yml`) and deploy (`deploy.yml`) | both skip changes under `doc/**` |
| Docker image | `.dockerignore` excludes `doc`, and the image copies only `app/` |
| The live website | only `app/static/` is served |
| pytest / ruff | pytest only looks in `tests/`; ruff only checks Python files |

I **read** it to get the exact values (CSS variables, spacing, sizes, inline SVG icons, hover, focus and disabled styles) and re-create them in our own files. I never copy the React code into the app.

If you agree at that point, I can also **run it locally** (`npm install`, then `npm run dev`) and open it in the browser pane at 390px and 1440px, next to our pages. That needs Node on your Mac and downloads the packages listed in its `package.json`, so I'll ask first. If it runs, I take most screenshots myself.

#### C2. Screenshots (only what the code can't tell me)

If the code runs locally, I need **none, or only a few** from you. If it doesn't run, or you couldn't export the code, this is the set I need: **about 20 images, not one per frame.**

| # | What | Width | Why |
|---|---|---|---|
| 1 | Style guide page | desktop | overall feel, colours together |
| 2 | Component sheet (all states) | desktop | buttons, inputs, chips, badges, alerts |
| 3–4 | C1 Home | 390 and 1440 | the first impression |
| 5–6 | C2 Booking, frame (d) "time chosen" | 390 (with the bottom bar) and 1440 (with the summary card) | the most important page |
| 7 | C2 Booking, frame (f) field errors | 390 | the error styling |
| 8 | C2 Booking, German frame | 390 | long words |
| 9 | C2-W Waitlist box with success message | 390 | |
| 10 | C3 Booking result "Almost done" | 390 | |
| 11–12 | C4 Manage: "Awaiting your confirmation", and "Cancel question open" | 390 | key states |
| 13 | C5 Offer with countdown | 390 | |
| 14 | C7 Receipt | 1440 | print layout |
| 15 | O1 Login | 390 | |
| 16–17 | O2 Dashboard | 1440 and 390 | tiles, chart, table |
| 18 | O3 Bookings, Day view | 1440 | calendar cards |
| 19 | O3 Bookings, Week view | 390 | sideways scrolling |
| 20 | O3-D Booking detail dialog | 1440 | panel layout |
| 21 | Owner menu open on mobile | 390 | the collapsed menu |
| 22 | Owner page error state | 1440 | |

The other screens (services, therapists, waitlist, settings, the other dialogs and states) follow the same components, so I only ask if something is unclear.

**How to take them:**
- **If Make shows design frames:** select a frame, then in the right panel choose Export → PNG, 2x → Export.
- **If Make shows a live preview:** set the preview width to 390 or 1440. On a Mac, press Cmd+Shift+4, then Space, then click the preview window.
- **Name** each file `<screen>-<width>-<frame>.png`, for example `C2-390-d.png` or `O2-1440.png`.
- **Deliver** them by pasting into our chat, or by dropping them into `doc/design/screens/`.

#### C3. The Figma link (optional)

**Share → Copy link** lets me read tokens or a component directly through the Figma connection. That costs some of your **20 calls per month**, so with the exported code I'll rarely need it.

### Stage D — Port the design into the app (my job, 6 PRs)

The details are in the last section of this file. In short:

1. The current look (`styles.css`) stays untouched as the **Classic look**.
2. The new look goes into a separate file, `calm.css`, which only applies when you switch to **New look**.
3. A small **"Classic look" / "New look"** button in the top bar (customer pages) and in the side menu (owner area) switches between them. Your browser remembers the choice.
4. The work is split into six PRs: tokens and switch, base styles, components, customer pages, owner pages, polish.
5. **Each PR:** you see screenshots in both looks. CI must be green (the server tests don't change). You merge it, and it goes live automatically on Render.
6. **Decided:** the **Classic look is the default** for everyone. **Both customers and the owner** can switch to the New look with the button, and each browser remembers its own choice. So half-finished steps never confuse real customers.

### Stage E — Decide

1. Use both looks on your phone and laptop for a few days. Book a test appointment and try the manage, cancel and waitlist flows.
2. The Classic look stays the default (decided). If you later want the New look as the default, tell me; it's a one-line change.
3. Later you can also decide to **remove** the other look. That is one clean-up PR, and it makes future UI changes cheaper, because every change then needs checking in only one look.

### Quick answers

- **"Why not just use Figma's React code as our front end?"** That would be a rewrite of every page and would need a Node build step, which our CI/CD setup deliberately avoids. The exported code stays a reference library in `doc/design/figma-make/`. A React front end is possible later as a **separate project** (see PLAN.md, "Later"), and the CSS tokens from this redesign would carry over to it.
- **"Will Figma change my live app?"** No. Figma Make only produces designs and a prototype. Only the PRs in stage D change the app.
- **"Can I edit the prompt?"** Yes, but keep the texts and the "Technology rules" section unchanged. If you add a feature to the prompt, tell me, because the server would need it too.
- **"What if Figma ignores an instruction?"** Quote the section number back to it, e.g. *"Please follow Part 1, section 5, rule 4: no icon packages, inline SVG only."*
- **"What does a Make prompt cost?"** Figma Make runs on your Figma plan's AI allowance; check the limit for your plan in Figma's settings. Long prompts and many correction rounds use more of it, which is one more reason to fix the style (step A5) before the screens.

---

## PART 1 — Context, visual style, components, rules

```text
=== PROMPT START (Part 1 of 3) ===
```

You are designing a complete, high-fidelity UI for an existing web app called **Slotwise**. The app already works in production. You are redesigning how it **looks**, not what it **does**. Do not add features, screens, fields, data or texts that are not described here. If something is not described, leave it out.

I will send this brief in three parts. This part sets the context, the visual style, the components and the technical rules. Part 2 describes the customer screens. Part 3 describes the owner screens. Please start now with **a style guide page and a component sheet**, and wait for Part 2 before designing screens.

### 1. App context

1. **What Slotwise is:** online booking for one small wellness studio. Customers see the treatment menu with prices, pick treatments, a therapist, a day and a time, and book. They pay at the studio, never online.
2. **Who uses it:**
   - **Customers.** They have no accounts and no passwords. Every booking is managed through a private link in their emails.
   - **One owner.** The owner logs in to a separate owner area to manage bookings, the menu, the team, the waitlist and the studio settings.
3. **Demo studio for all screens:**
   - **Name:** Isar Wellness, a day spa in Munich, Germany.
   - **Address:** Isarstraße 12, 80469 München.
   - **Phone:** +49 89 0000 0000.
   - **Email:** hello@isar-wellness.example.com.
   - **Opening hours:** Mon 10:00–19:00 · Tue–Fri 9:00–19:00 · Sat 9:00–17:00 · Sun closed.
   - **Therapists:** **Lena** (massages and foot reflexology) and **Sofia** (facials and relaxation massage).
   - **Owner name:** "Studio owner" (shown in "Welcome back, …").
4. **The demo menu.** Use exactly these items:
   - **Massages:**
     - Relaxation massage, 60 min, €65: "Slow, flowing full-body massage to switch off."
     - Deep tissue massage, 60 min, €70: "Firm pressure for tight muscles and knots."
     - Back and neck massage, 30 min, €39: "Focused relief for desk shoulders."
     - Add-ons on each massage: **Hot stones** (+15 min, €12) and **Aromatherapy oil** (no extra time, €5).
   - **Facials:**
     - Classic facial, 45 min, €59: "Cleanse, exfoliate, mask and moisturise."
     - Express facial, 30 min, €39: "A quick refresh for busy days."
     - Add-on on each facial: **Eye mask treatment** (+10 min, €9).
   - **Reflexology:**
     - Foot reflexology, 30 min, €42: "Pressure-point foot treatment."
5. **Demo customers:** Anna Müller, Jonas Klein, Priya Shah, Tom Becker, Mia Wagner, Lukas Schmidt, Sara Rossi and Ben Fischer. Ben has repeat no-shows and carries a ⚠ flag in the owner area. Customer emails look like `anna.mueller@example.com`.
6. **Receipt numbers** look like `IW-2026-0042`: a prefix, the year, then a 4-digit counter.
7. **Three core ideas the design must make obvious and trustworthy:**
   1. **Itemized prices, locked at booking time.** Every booking shows its lines (treatment, add-ons, extras) with prices and a total. Later menu price changes never change an existing booking.
   2. **Reminder emails with one-click confirm or cancel.** The customer's email links open a "Manage booking" page with big, clear actions.
   3. **An automatic waitlist that refills cancelled times.** When a day is full, customers can join a waitlist. When someone cancels, the first person gets an email offer they can claim within 30 minutes.
8. **Email confirmation.**
   - New online bookings start as **"Awaiting your confirmation"**. The customer must click a link in an email within **30 minutes**. Until then the time is held for them.
   - If they don't confirm, the booking becomes **"Not confirmed"** and the time is released.
   - Waitlist requests are also confirmed by an email link.
9. **Two languages (customer side only):**
   - Every customer page has a small language switch in the top bar. It shows the **other** language: **"DE"** on English pages and **"EN"** on German pages.
   - German words are long, so design for them: "Gesichtsbehandlungen", "Buchung abschicken", "Wartet auf Ihre Bestätigung", "Auf die Warteliste setzen", "Kostenlose Stornierung bis 24 Stunden vorher".
   - Buttons, chips, badges and table headers must wrap or grow. They must never cut text off.
   - The owner area is English only.
10. **Look switch (new, requested by the studio).** The studio wants to keep the current "Classic" look available next to the new design.
    - Add one small, quiet text button to the customer top bar, next to the language switch. It reads **"Classic look"** (German: "Klassisches Design").
    - In the owner area, put the same button at the bottom of the side menu, above "Log out".
    - **Both customers and the owner** can switch. The Classic look is the default; the New look (your design) is opt-in.
    - You only design the new look, so this button always shows "Classic look". Keep it visually secondary: it must never compete with "Book now".

### 2. Visual style: "Calm modern"

1. **Feel:** calm, trustworthy, premium but friendly. Lots of whitespace, few borders and soft surfaces. It should feel like a quiet spa reception, not a software dashboard. Prices and durations are the most important information and should be large and easy to scan.
2. **Light mode only.** No dark mode.
3. **Colour palette.** Every colour must be defined as a CSS custom property with exactly these names. The names that already exist in the app are kept; the new ones are marked "new".

   | Token | Value | Use |
   |---|---|---|
   | `--green` | `#1F5C45` | Primary: main buttons, links, selected states, logo leaf |
   | `--green-dark` | `#164534` | Primary hover/pressed, text on soft green |
   | `--accent` | `#3E9C72` | Focus ring and small green highlights (never body text) |
   | `--accent-soft` | `#E4F0EA` | Soft green surfaces: selected option cards, "Confirmed" badge, success notes |
   | `--warm` (new) | `#A0571A` | The ONE warm accent. Use it **only** for price totals and tiny highlights, e.g. the total row, the running total in the summary bar, or the "Today" marker. Never for buttons. |
   | `--warm-soft` (new) | `#FBEFE3` | Background behind a highlighted total |
   | `--ink` | `#1C2621` | Main text |
   | `--muted` | `#5A645F` | Secondary text, hints, table headers |
   | `--line` | `#E6E0D6` | Dividers and card borders (warm grey) |
   | `--input-border` (new) | `#848F89` | Input, select and checkbox borders (at least 3:1 against white) |
   | `--bg` | `#FAF7F2` | Page background (warm off-white) |
   | `--card` | `#FFFFFF` | Cards, dialogs, tables |
   | `--success` (new) | `#1E6B45` | Success text and icons |
   | `--success-soft` (new) | `#E5F3EA` | Success backgrounds |
   | `--warning` (new) | `#8A5300` | Warning text ("Booked" badge, late-cancellation notes, "Off target") |
   | `--warning-soft` (new) | `#FFF3DC` | Warning backgrounds |
   | `--danger` | `#B42318` | Errors, cancel actions, "Cancelled" and "No-show" |
   | `--danger-soft` | `#FDECEA` | Error backgrounds |
   | `--info` (new) | `#2C5AA0` | "Awaiting email" / "Awaiting your confirmation" badge text |
   | `--info-soft` (new) | `#EAF0FA` | That badge's background |
   | `--chart-1` (new) | `#2A78D6` | Chart series "No-shows" |
   | `--chart-2` (new) | `#EB6834` | Chart series "Late cancellations" |

4. **Typography.**
   - Font: **Inter**, falling back to system fonts. The token is `--font: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;`.
   - Size tokens (new):

     | Token | Value | Use |
     |---|---|---|
     | `--text-xs` | 12px | Tiny labels |
     | `--text-sm` | 14px | Hints, table cells, badges |
     | `--text-md` | 16px | Body text and inputs. Inputs must never go below 16px, to avoid zoom on iPhone |
     | `--text-lg` | 20px | Card titles, section titles |
     | `--text-xl` | 28px | Page titles |
     | `--text-2xl` | 36px | The large hero headline on the home page |

   - Prices and durations are prominent:
     - service price at 20px semibold;
     - totals at 24px bold in `--warm`;
     - time-slot buttons at 18px semibold.
   - Use tabular numbers (`font-variant-numeric: tabular-nums`) for every price, time and table number.
5. **Spacing:** an 8px grid. Tokens (new): `--space-1` 4px, `--space-2` 8px, `--space-3` 12px, `--space-4` 16px, `--space-5` 24px, `--space-6` 32px, `--space-7` 48px, `--space-8` 64px.
6. **Corner radii:**
   - `--radius-sm` 8px: inputs, chips, small buttons;
   - `--radius` 12px: buttons, option cards;
   - `--radius-lg` (new) 16px: cards, dialogs;
   - `--radius-pill` (new) 999px: badges and the language switch.
7. **Shadows:** soft and warm, never grey and harsh.
   - `--shadow` = `0 1px 2px rgba(28,38,33,.05), 0 4px 16px rgba(28,38,33,.06)` for cards.
   - `--shadow-lg` (new) = `0 8px 32px rgba(28,38,33,.14)` for dialogs, toasts and the mobile summary bar.
8. **Icons:** simple line icons drawn as inline SVG, 1.75px stroke, 20px or 24px, using `currentColor`.
   - Keep the existing logo, a single green leaf next to the studio name.
   - Use icons sparingly: calendar, clock, user, map pin, phone, envelope, check, x, chevron left/right, warning triangle, printer and download.
9. **Motion:** only short colour and shadow transitions (150ms). No sliding, bouncing or page animations.

### 3. Components (each with all its states)

Draw each component on the component sheet with every state listed. Use only the tokens above.

1. **Buttons:**
   - Variants:
     - **Primary:** filled green, white text.
     - **Secondary** (called "ghost" in our code): white with a `--line` border and green text.
     - **Danger:** filled `--danger`, white text.
     - **Danger secondary:** white with red text and border.
     - **Text button:** no box.
   - Sizes: normal (48px high) and small (40px high on desktop, still a 44px tap area on mobile). There is also a full-width version.
   - States: normal, hover, focus (a 3px `--accent` ring with a 2px offset), pressed, disabled (40% opacity, no pointer) and loading.
   - **Loading** replaces the label with the loading text. Example: "Confirm booking" becomes "Booking…".
2. **Icon button:** the "×" close button for dialogs and the "‹" / "›" arrows. 44×44px tap area.
3. **Text input, email, phone, number, date, time and textarea:**
   - Always a visible label above the field.
   - Optional fields show "(optional)" after the label in `--muted`.
   - A hint line can sit below the field in `--muted` at 14px.
   - States: empty, filled, focus, disabled, and **error**: red border, `aria-invalid`, and a red message below. Example message: "Please enter a valid email address".
4. **Select (dropdown):** the same states as text inputs.
5. **Checkbox with label:** a 20px box inside a 44px tap row. States: unchecked, checked, focus and disabled.
6. **Option card:** a selectable row for a treatment or add-on.
   - Layout: checkbox on the left, then the name (and an optional small second line), with the price large on the right and the duration small under it.
   - States: normal, hover, selected (`--accent-soft` background with a green border) and focus.
   - Example: "Deep tissue massage · €70 · 60 min".
   - Add-on example: "Hot stones · +€12 · +15 min". An add-on with no extra time shows "no extra time" under its price.
7. **Chip:** a pill-shaped single choice, used for therapists ("No preference", "Lena", "Sofia") and for days.
   - States: normal, hover, selected (filled green, white text) and focus.
   - A **day chip** has two lines: a small top line ("Today", "Tomorrow" or "Thu") and a bigger bottom line ("15 Oct").
8. **Time-slot button:**
   - Shows a time ("10:15") and sometimes a second small line with the therapist name ("Lena").
   - States: normal, hover, selected (filled green) and focus.
   - Arrange slots in a grid: 4 columns at 390px wide, 6 columns on desktop.
9. **Date picker:** a native date input styled like a text input, labelled "Another day".
10. **Step marker:** a 28px circle with a number 1–6 in front of a section heading. States: upcoming (outlined), current (filled green) and done (filled green with a check). The number stays readable.
11. **Status badges** (pill-shaped, 14px, with a small dot or icon so colour is never the only signal):

    | Badge | Customer text | Owner text | Colours |
    |---|---|---|---|
    | pending | Awaiting your confirmation | Awaiting email | info |
    | booked | Booked | Booked | warning |
    | confirmed | Confirmed | Confirmed | success |
    | done | Completed | Done | success (outlined) |
    | no_show | Missed | No-show | danger |
    | cancelled | Cancelled | Cancelled | danger |
    | expired | Not confirmed | Not confirmed | neutral grey |

    The owner waitlist uses these extra badges, with their own colours (they don't borrow the booking badges): "Awaiting email" (info), "Waiting" (warning), "Offered" (success), "Booked" (success, outlined), "Offer expired" (neutral) and "Removed / declined" (neutral).

    There is also a special badge, "Late cancellation" (danger).

    The dashboard uses goal badges:
    - "✓ On target · goal < 5%" (success);
    - "▲ Off target · goal ≥ 50%" (warning);
    - "No data yet" (neutral).
12. **Cards:**
    - The standard card: white, `--radius-lg`, `--shadow`, 24px padding (16px on mobile).
    - The **summary card**: the booking summary, a white card with a highlighted total row.
    - The **confirm card**: a centred, 560px-wide card for result pages (booking result, manage, offer, waitlist confirmation).
13. **Item lines table:**
    - A two-column list: item name on the left, price on the right.
    - Add-on lines start with "+ " and are indented and muted. Example: "+ Hot stones … €12".
    - A "Total time" line is muted.
    - The **Total row** has a top border and a bold 24px total in `--warm`.
14. **Facts list:** label/value pairs (Date, Time, Therapist, Where). Two columns on desktop; stacked label-over-value on mobile.
15. **Data table** (owner area):
    - The header row is muted, 14px, uppercase off.
    - Rows are 52px tall with a hover background, and clickable rows show a pointer.
    - Number columns are right-aligned.
    - Inactive rows are dimmed.
    - On mobile, the table scrolls sideways inside its card. It must not squash the columns.
16. **Dialog (side panel):**
    - On desktop, a right-hand panel 480px wide and full height. On mobile, a full-screen sheet.
    - The head has a title and an "×" close button; the body scrolls.
    - The backdrop is `rgba(28,38,33,.4)`.
17. **Toast:** a small dark-green pill at the bottom centre, white text, visible for about 3 seconds. Example: "Settings saved".
18. **Alert / notices:**
    - **Error alert:** `--danger-soft` background, red text, warning icon. Example: "That time was just taken. Please pick another."
    - **Success note:** `--success-soft` background with a check icon.
    - **Neutral notice:** muted text for loading and empty messages.
    - **Policy note:** muted. Its "late" version uses warning colours.
19. **Empty state:** a centred muted line, with an optional simple line icon. Example: "No bookings in this range."
20. **Loading skeletons:** soft grey (`--line`) rounded blocks shaped like the content they replace: option cards, table rows, tiles. A visually hidden loading text stays in the page for screen readers, e.g. "Loading the menu…".
21. **Segmented control:** "Day | Week | List". The selected segment is filled green.
22. **Dashboard tile:** a small card with a label (14px, muted), a big value (28px bold), a muted note line and an optional goal badge.
23. **Countdown:** large tabular text, e.g. "24:13 left to claim". Under 5 minutes left, it switches to danger colour and adds a clock icon.
24. **Language switch:** a pill button showing "DE" or "EN", at least 44×44px.
25. **"Classic look" button:** a text button with a small palette or eye icon, muted until hovered.

### 4. Accessibility (applies to every screen)

1. Text contrast must be at least **4.5:1**. Borders of inputs and controls must be at least **3:1**. The colours above already meet this; keep them.
2. Every tap target is at least **44×44px**, including chips, time buttons, the language switch, table row actions and the dialog close button.
3. **Visible focus** on every interactive element: a 3px `--accent` ring with a 2px offset. Never remove focus outlines.
4. **Every input has a visible label.** Placeholders never replace labels.
5. **Colour is never the only signal.** Badges have text, errors have an icon and a message, and the selected chip also changes its fill and weight.
6. Headings follow a logical order: one H1 per page.

### 5. Technology rules (very important)

Our app is **plain HTML, CSS and JavaScript** served by a Python (FastAPI) server. There is **no framework, no Tailwind and no build step**, and it must stay that way. We will **read** your generated code and CSS as an exact reference, but we will **not** run your React code in our app. We will re-create the look in our own HTML and CSS. Clean CSS custom properties make that easy.

So please:

1. **Keep the markup simple and semantic:** `header`, `main`, `section`, `form`, `fieldset`, `label`, `button`, `table`, `dialog` and `details`. Keep components shallow and component logic minimal.
2. **Put every design value (colours, font sizes, spacing, radii, shadows) in CSS custom properties** on `:root` in **one stylesheet**, using **exactly** the token names from section 2. Components must use the tokens, never raw hex values.
3. If you generate React, use plain CSS (or CSS modules) that reads these custom properties. **Do not use Tailwind utility classes** for the design values.
4. **No heavy UI libraries** (no MUI, no shadcn, no Radix, no Chakra). **No icon packages:** draw icons as inline SVG.
5. **No complex animations:** only 150ms colour and shadow transitions.
6. **No invented features, data or screens.** Use only the texts, fields, columns and states given in this brief. When you need sample data, use the demo studio, menu and customers above.
7. Design **mobile first at 390px wide**, and also show **desktop at 1440px wide** for every screen.

Now please create:

- **(a)** a style guide page with all tokens: colour swatches with names, the type scale, spacing, radii and shadows;
- **(b)** a component sheet with every component in section 3 and all its states.

Wait for Part 2 before designing screens.

```text
=== PROMPT END (Part 1 of 3) ===
```

---

## PART 2 — Customer screens

```text
=== PROMPT START (Part 2 of 3) ===
```

This is Part 2 of 3. **Keep exactly the same "Calm modern" style, tokens and components from Part 1.** Don't introduce new colours, fonts or components. Design every screen below at **390px (mobile)** and **1440px (desktop)**. On desktop, customer pages use a centred content column (max 1040px for the booking page, 720px for the home page and 560px for result pages).

All customer screens are shown in **English**. Also make **one German version of Screen C2 (booking)** so we can check that long words fit. The German texts are given in brackets.

### Shared customer parts

1. **Top bar** (all customer pages except the receipt):
   - Left: the leaf logo plus the studio name "Isar Wellness" (links to the home page).
   - Right, in this order: the language switch "DE" ("EN" on German pages), the "Classic look" text button, then one page-specific action:
     - home page: "Book now" (primary, small; German "Jetzt buchen");
     - booking page: "Back to menu" (secondary, small; German "Zurück zum Menü");
     - Manage booking page: "Book again" (primary, small; German "Erneut buchen");
     - other pages: no action.
   - On mobile the top bar stays one row. The studio name may shorten with an ellipsis, but the buttons never do.
2. **Footer** (home page only): "Online booking by [leaf] Slotwise" on the left, the link "Studio login" on the right.

### Screen C1 — Home (studio page and treatment menu)

**Purpose:** customers see who the studio is, the full menu with prices, and start a booking.
**Who:** everyone. It is the public landing page at `/`.

From top to bottom:

1. Top bar with "Book now".
2. **Studio block:**
   - H1 "Isar Wellness".
   - Facts list:
     - **Address:** Isarstraße 12, 80469 München.
     - **Phone:** +49 89 0000 0000 (a tap-to-call link).
     - **Hours:** each part on its own line on mobile: "Mon 10:00–19:00", "Tue–Fri 9:00–19:00", "Sat 9:00–17:00", "Sun closed".
   - A policy line under it: "Free cancellation up to 24 hours before".
3. **Treatment menu:** one section per category (H2 "Massages", "Facials", "Reflexology"). Each service is a card with:
   - name, for example "Relaxation massage";
   - a one-line description, for example "Slow, flowing full-body massage to switch off.";
   - the price, large on the right ("€65"), with the duration under it ("60 min");
   - an add-on list, for example "+ Hot stones · +15 min · €12" and "+ Aromatherapy oil · €5";
   - a secondary small button "Book" (its screen-reader label is "Book Relaxation massage"), which opens the booking page with this treatment pre-selected.
4. **"Manage my booking"**: a collapsible section (closed by default). When opened it shows: "Open the link in your confirmation email to view, confirm or cancel your booking and to see your receipt."
5. Footer.

**States:**

- **Loading:** skeleton service cards, plus the hidden text "Loading the menu…".
- **Empty menu:** "The menu is being prepared. Please call us to book."
- **Error:** "Could not load the menu. Please refresh."
- **Studio details failed to load:** the H1 shows "Book online" and the facts stay empty.

### Screen C2 — Book a treatment (ONE page, six numbered steps)

**Purpose:** pick treatments, add-ons, therapist, day and time, enter details, and confirm, all on **one scrolling page**. This is not a multi-page wizard: there is no "Continue" or "Next" button, and every step stays visible once it has appeared.
**Who:** customers. The page is `/book.html` and can be opened with a treatment pre-selected.

**Layout:**

- **Desktop:** two columns. On the left, the form with steps 1–6. On the right, a 320px **summary card** that sticks to the top while scrolling.
- **Mobile:** one column, plus a **sticky bottom bar** that is always visible:
  - Left: the running summary on one line, for example **"2 items · 75 min · €82"**, with the total in `--warm`. German: "2 Positionen · 75 Min. · 82 €".
  - Right: the primary button **"Confirm booking"** (German "Buchung abschicken"). It is disabled until a time is picked.
  - Tapping the summary text scrolls to the full summary card, which sits after step 6 on mobile.
  - Before any treatment is chosen, the bar shows "Choose a treatment to start." with the button disabled.

**From top to bottom:**

1. Top bar with "Back to menu".
2. H1 **"Book a treatment"** (German: "Behandlung buchen"). Lead text: "Choose your treatment, a therapist and a free time. You pay at the studio." (German: "Wählen Sie Ihre Behandlung, eine Therapeutin und eine freie Zeit. Bezahlt wird im Studio.")
3. **Step 1, "Treatments"** ("Behandlungen"):
   - Option cards grouped under small category titles ("Massages", "Facials", "Reflexology").
   - Several treatments can be chosen. Each card shows the name, the price ("€70") and the duration ("60 min").
4. **Step 2, "Add-ons (optional)"** ("Extras (optional)"):
   - Appears only when the chosen treatments have add-ons.
   - Option cards, for example "Hot stones · +€12 · +15 min" and "Aromatherapy oil · +€5 · no extra time".
   - When more than one treatment is chosen, each add-on gets a second line naming its treatment, e.g. " · with Deep tissue massage".
5. **Step 3, "Therapist"** ("Therapeutin"):
   - Chips in a single-choice group. The choices are "No preference" ("Keine Präferenz"), "Lena" and "Sofia".
   - "No preference" appears only when more than one therapist offers the chosen treatments. If only one does, only her chip is shown, already selected.
   - Hovering a chip shows the therapist's short bio as a tooltip.
   - **Error under the chips:** "No therapist offers this combination. Please remove a service."
6. **Step 4, "Day"** ("Tag"):
   - A horizontally scrolling row of 14 day chips:
     - "Today / 13 Oct";
     - "Tomorrow / 14 Oct";
     - "Thu / 15 Oct", and so on.
   - Below the chips, a date input labelled "Another day" ("Anderer Tag"), limited to today up to 60 days ahead.
7. **Step 5, "Time"** ("Uhrzeit"):
   - A grid of time-slot buttons every 15 minutes, for example 10:00, 10:15, 10:30, 11:45 or 14:00.
   - When "No preference" is selected, each slot shows the therapist's name as a second line ("Lena" or "Sofia").
8. **Step 6, "Your details"** ("Ihre Angaben"): a form, two columns on desktop and one on mobile.
   - "First name" ("Vorname") and "Last name" ("Nachname").
   - "Email" and "Phone" ("Telefon").
   - "Note for your therapist (optional)". This is a full-width textarea with the hint "Please don't enter medical details. Max 300 characters."
9. **Summary card "Your booking"** ("Ihre Buchung"):
   - A "when" line, which changes as the customer goes:
     - "Choose a treatment to start.";
     - "Pick a day and time";
     - "Tuesday 13 October, pick a time";
     - **"Tuesday 13 October at 10:00 with Lena"**.
   - Item lines, for example:
     - "Deep tissue massage … €70";
     - "+ Hot stones … €12" (muted);
     - "Total time … 75 min" (muted);
     - **"Total … €82"** (bold, in `--warm`).
   - "Pay at the studio" ("Bezahlung im Studio").
   - An error alert, hidden unless there is an error.
   - The full-width primary button **"Confirm booking"**. On mobile this button lives in the sticky bottom bar instead.

**Show these frames (mobile and desktop):**

- **(a) Start:** nothing chosen. The summary reads "Choose a treatment to start.", the button is disabled, and only step 1 is visible.
- **(b) Treatment chosen:**
  - Deep tissue massage and Hot stones are checked.
  - Steps 2–6 are visible.
  - Day step: "Pick a day to see free times." (German "Wählen Sie einen Tag, um freie Zeiten zu sehen.")
- **(c) Day chosen, times loading:** "Looking for free times…" with skeleton time buttons.
- **(d) Time chosen:**
  - Lena and 10:00 are selected.
  - The summary is complete and "Confirm booking" is enabled.
  - Mobile bar: "2 items · 75 min · €82".
- **(e) Submitting:** the button shows "Booking…" and is disabled.
- **(f) Field errors from the server:**
  - The email field is red with "Please enter a valid email address".
  - The phone field shows "Please enter your phone number."
  - Other possible messages: "Please enter your first name.", "Please enter your last name.", "Please use only letters in your name." and "Please keep the note under 300 characters."
- **(g) General error in the summary alert:** "That time was just taken. Please pick another." The times reload.
  - Other possible messages: "Please choose a time between 2 hours and 60 days from now.", "Too many bookings in a short time. Please call the studio.", "Please pick one of the offered times.", "One of the chosen treatments is no longer available. Please refresh." and "Could not reach the server. Please check your connection."
- **(h) No free times + waitlist:** see Screen C2-W below.
- **(i) Menu failed to load:** step 1 shows "Could not load services."

#### Screen C2-W — The waitlist box (inside step 5 when a day is full)

This appears in place of the time grid when a day has no free times.

1. A notice: "No free times on this day. Try another day, or join the waitlist below." (German: "An diesem Tag ist keine Zeit frei. Wählen Sie einen anderen Tag oder tragen Sie sich unten auf die Warteliste ein.")
2. A soft card titled **"Join the waitlist"** (German: "Auf die Warteliste"):
   - The hint "Tell us when you could come. If someone cancels, the first person on the list gets an email and can claim the time."
   - One row of controls: "Between" [select 09:00] "and" [select 18:00]. The selects offer 07:00 to 21:00 in steps of 30 minutes; their screen-reader labels are "Earliest start" and "Latest start".
   - The hint "Uses your details from step 6."
   - The button **"Join the waitlist"** (German: "Auf die Warteliste setzen").
   - A message line below the button.
3. **States:**
   - **Details missing:** "Please fill in your details below first." in red. The page scrolls to step 6.
   - **Success** (green note): "Almost done! We've emailed anna.mueller@example.com a link. Click it to confirm your place on the waitlist for this day."
   - **Possible errors:**
     - "Please choose an earliest time before the latest time."
     - "You already have 5 open waitlist requests. Please call the studio to change them."
     - "Nobody offers this treatment on that day, so no time can free up."
   - **Joining:** the button is disabled while the request runs.

### Screen C3 — Booking result (after "Confirm booking")

**Purpose:** confirm what happened right after booking.
**Who:** the customer who just booked.

The page is one centred confirm card, with a large round icon at the top. There are three versions:

1. **Pending: email confirmation needed.** This is the normal case for online bookings.
   - Icon: an envelope.
   - H1: "Almost done, Anna!" (German "Fast geschafft, Anna!").
   - Success note: "We've emailed you a link. Click it to confirm your booking by 14:35; until then we're holding the time for you."
   - Facts:
     - **Date:** Tuesday 13 October 2026.
     - **Time:** 10:00 (75 min).
     - **Therapist:** Lena.
     - **Where:** Isarstraße 12, 80469 München.
   - Item lines: Deep tissue massage €70, + Hot stones €12, **Total €82**.
   - "Pay at the studio".
   - Muted text: "No email? Check your spam folder. If you don't confirm in time, the time is released for others."
   - A full-width primary button: "Back to home".
2. **Booked:**
   - Icon: a check mark.
   - H1: "You're booked, Anna!"
   - The same facts and lines.
   - Success note: "A confirmation has been emailed to you. Use the link in your email to confirm, cancel or view your receipt."
   - "Back to home".
3. **Details missing** (e.g. the page was reloaded in a private window):
   - H1: "Booking details not available".
   - Muted text: "Your booking may still have gone through. Please check with the studio if you're unsure."
   - "Back to home".
4. **Loading:** "Loading your booking…"

### Screen C4 — Manage booking (opened from the email link)

**Purpose:** view one booking and act on it with one click: confirm the email, confirm attendance, or cancel. Also shows the receipt link after the visit.
**Who:** the customer, through the private link in any of their emails (`/manage.html?token=…`). The email links can also carry an action:

- "verify" (from the booking email) confirms the booking automatically;
- "confirm" (from the reminder) confirms attendance automatically;
- "cancel" (from the reminder) opens the cancel question directly.

From top to bottom (inside one confirm card):

1. An optional **message line** at the very top: a green success note or a red alert (see the states).
2. The **status badge**, for example "Booked".
3. H1 **"Your booking"** (German "Ihre Buchung").
4. The facts list (Date, Time, Therapist, Where), as in C3.
5. The item lines with the total. A quantity shows as "× 2" after the name.
6. Either the receipt line or "Pay at the studio":
   - **With a receipt:** "Receipt IW-2026-0042" plus the link "View or print receipt".
7. Status notes (muted), when relevant:
   - "This booking was cancelled." or "This booking was cancelled late.";
   - "This booking request wasn't confirmed in time, so the time was released."
8. **Action buttons**, stacked full width; only the ones that apply are shown:
   - **"Confirm my booking"** (primary). Shown only while the booking is "Awaiting your confirmation".
   - **"Confirm I'm coming"** (primary). Shown when the booking can be confirmed.
   - **"Cancel booking"** (danger secondary). Shown when the booking can be cancelled.
   - **"Book again"** (secondary). Always shown.
9. **Inline cancel question.** It replaces the "Cancel booking" button inside a soft red box:
   - The text "Are you sure you want to cancel?". If free cancellation has ended, the text is "Are you sure? This counts as a late cancellation."
   - Two buttons in a row: **"Yes, cancel booking"** (danger, filled) and **"Keep my booking"** (secondary).
10. **Policy note** at the bottom (only while the booking can be cancelled):
    - Before the limit: "Free cancellation until Mon 12 Oct, 10:00."
    - After it (warning colours): "Free cancellation has ended. You can still cancel, but it counts as a late cancellation."

**Show these frames:**

1. **Awaiting your confirmation:**
   - Badge "Awaiting your confirmation".
   - Buttons: "Confirm my booking", "Cancel booking" and "Book again", with the policy note.
2. **Booked:**
   - Badge "Booked".
   - Buttons: "Confirm I'm coming", "Cancel booking" and "Book again", with the policy note.
3. **Just confirmed:**
   - Top note: "Thank you! Your booking is confirmed. See you soon."
   - Badge "Confirmed".
   - After the email confirmation, the note reads instead: "Thank you! Your booking is confirmed, and we've emailed you the details."
4. **Cancel question open:** the inline red box.
5. **Late cancel question:** the late text, with the late policy note in warning colours.
6. **Just cancelled:**
   - Top note: "Your booking is cancelled." (or "Your booking is cancelled (late cancellation).").
   - Badge "Cancelled", the note "This booking was cancelled." and only "Book again".
7. **Not confirmed (expired):**
   - Badge "Not confirmed".
   - The note "This booking request wasn't confirmed in time, so the time was released."
   - Only "Book again".
8. **Completed with receipt:**
   - Badge "Completed".
   - "Receipt IW-2026-0042 · View or print receipt", and only "Book again".
   - For reference, the badge reads "Missed" for a no-show.
9. **Action failed:**
   - A red alert at the top, for example "This booking can no longer be confirmed." or "This booking is already cancelled or finished.", plus the current booking below it.
10. **Not found:**
    - H1 "Booking not found".
    - Muted text: "Booking not found. Please check the link in your email."
    - For an incomplete link: "This link is incomplete. Please use the link in your confirmation email."
    - For an expired request: "This booking request has expired because it wasn't confirmed in time. Please book again."
    - Button: "Back to home".
11. **Loading:** "Loading your booking…"
12. **Busy:** all buttons are disabled while an action runs.

### Screen C5 — Waitlist offer ("A time is free for you")

**Purpose:** a customer on the waitlist got an email because a time freed up. They claim it or decline it before the offer runs out.
**Who:** a waitlisted customer, through the offer link (`/offer.html?token=…`).

Inside one confirm card:

1. H1 **"A time is free for you"** (German "Ein Termin ist für Sie frei").
2. Facts:
   - **Date:** Thursday 15 October.
   - **Time:** 11:00 (60 min).
   - **Therapist:** Sofia.
   - **Where:** Isarstraße 12, 80469 München.
3. Item lines: Relaxation massage €65, + Aromatherapy oil €5, **Total €70**.
4. "Pay at the studio".
5. **Countdown**, large: "24:13 left to claim". Under 5 minutes it turns urgent (danger colour), e.g. "4:59 left to claim".
6. An error alert (hidden unless there is an error).
7. Buttons:
   - **"Claim this time"** (primary, full width);
   - **"No thanks"** (secondary, full width).

**Other states**, each a simple card with an H1, muted text and a "Back to home" button:

1. **Claimed (success):**
   - H1 "You're booked, Anna!"
   - Text: "Thursday 15 October at 11:00 with Sofia. A confirmation with your booking link has been emailed to you."
   - The line "Total €70 · Pay at the studio".
2. **Declined:** H1 "No problem", with "We've offered the time to the next person on the waitlist."
3. **Expired:** H1 "Sorry, this offer has expired.", with "The time has gone to the next person on the waitlist."
4. **Already claimed:** H1 "Already claimed", with "This time has already been booked through this link."
5. **Not found:** H1 "Offer not found", with "Offer not found."
6. **Loading:** "Loading the offer…"
7. **Busy:** both buttons are disabled while an action runs.

### Screen C6 — Waitlist confirmed

**Purpose:** the page behind the link in the "confirm your waitlist request" email.
**Who:** a customer who just joined the waitlist.

Inside one confirm card:

1. **Loading:** "Confirming your waitlist request…"
2. **Success:**
   - H1 "You're on the waitlist" (German "Sie stehen auf der Warteliste").
   - Text: "For Thursday 15 October you're number 2. If a time frees up, we'll email you a link to claim it; the first to claim gets it."
   - Button "Back to home".
3. **Already handled:**
   - H1 "You're on the waitlist".
   - Text: "Your request for Thursday 15 October is already handled."
   - Button "Back to home".
4. **Failed:**
   - H1 "Couldn't confirm".
   - Muted text, for example "Waitlist request not found. Please check the link in your email." or "You already have 5 open waitlist requests. Please call the studio to change them."
   - Button **"Book or join again"**.

### Screen C7 — Receipt (printable, A4)

**Purpose:** a clean receipt the customer or owner can print or save as a PDF.
**Who:**
- the customer, from "View or print receipt";
- the owner, from "Print receipt" in the owner area. The owner version adds the customer's name.

Design it as a **white A4 page** (210×297mm proportion) centred on the warm background on screen, with no top bar and no language switch.

1. **On screen only** (hidden when printing), a small bar above the page with:
   - "Back" (secondary, small);
   - "Print / Save as PDF" (primary, small, printer icon).
2. **Receipt header:**
   - Left: the studio name "Isar Wellness" (large), the address, and "+49 89 0000 0000 · hello@isar-wellness.example.com".
   - Right: "Receipt" (muted), **IW-2026-0042** (bold) and "Issued 13 October 2026" (muted).
3. **Facts:**
   - **Customer:** Anna Müller (owner version only).
   - **Appointment:** 13 October 2026, 10:00.
   - **Therapist:** Lena.
4. **Item lines:**
   - Deep tissue massage €70;
   - + Hot stones €12;
   - + Massage oil (product) × 2 at €5 … €10. This is an example "extra" line added on the day.
   - **Total (EUR) €92**.
5. Footer line: "Paid at the studio. Thank you for your visit!"
6. **Print version:** no background, no buttons, black text and thin grey rules, fitting one A4 page.

**States:**

- **Loading:** "Loading receipt…"
- **No receipt yet:** H1 "No receipt yet", with "The studio sends the receipt after your visit."
- **Not found:** H1 "Receipt not found", with "Booking not found. Please check the link in your email."

### Customer flows to show (as simple arrows between frames)

1. **Booking flow:**
   1. Home.
   2. "Book" on Deep tissue massage opens C2 with it pre-selected.
   3. Check Hot stones.
   4. Choose therapist Lena.
   5. Choose the day "Today / 13 Oct".
   6. Choose 10:00.
   7. Fill in the details.
   8. "Confirm booking" ("Booking…").
   9. C3 pending ("Almost done, Anna!").
   10. The email link leads to C4, which confirms automatically: "Thank you! Your booking is confirmed, and we've emailed you the details." The badge reads "Confirmed".
2. **Manage flow from the reminder email:**
   - The email's **Confirm** link leads to C4: "Thank you! Your booking is confirmed. See you soon."
   - The email's **Cancel** link leads to C4 with the cancel question already open, then "Yes, cancel booking", then "Your booking is cancelled."
3. **Waitlist flow:**
   1. C2: a full day.
   2. "Join the waitlist" shows "Almost done! We've emailed … a link…".
   3. The email link leads to C6: "You're on the waitlist … number 2".
   4. Later, when someone cancels, an offer email arrives and leads to C5 with the countdown.
   5. "Claim this time" gives "You're booked, Anna!". "No thanks" gives "No problem".

```text
=== PROMPT END (Part 2 of 3) ===
```

---

## PART 3 — Owner screens

```text
=== PROMPT START (Part 3 of 3) ===
```

This is Part 3 of 3. **Keep exactly the same "Calm modern" style, tokens and components from Parts 1 and 2.** The owner area is used by one studio owner on a laptop and on a phone between treatments. It is **English only** and has no language switch. Design every screen at **390px** and **1440px**.

### Owner shell (all owner screens except login)

1. **Desktop:** a fixed **left side menu**, 240px wide, on a white surface with a right border.
   - At the top, the leaf logo and "Slotwise".
   - Navigation links, each with a line icon:
     1. Dashboard
     2. Bookings
     3. Services & add-ons
     4. Therapists & hours
     5. Waitlist
     6. Studio settings
   - The current page is highlighted (`--accent-soft` background, green text and a left bar).
   - At the bottom: the "Classic look" text button, then a **"Log out"** button.
   - The menu's screen-reader label is "Owner menu".
2. **Mobile:** the side menu collapses into a **top bar**: the logo on the left, and the current page name plus a menu button on the right. The menu button opens the same links, "Classic look" and "Log out" as a dropdown panel under the bar.
3. The main area has a page head: the H1 on the left and page actions on the right (wrapping under the H1 on mobile).
4. **Loading:** while the owner session is checked, show nothing but a centred spinner or skeleton. Without a session, the owner is sent to the login screen.
5. **Page error state (shared by every owner page).** When a page can't load its data, the main area shows this instead of the content. It must explain **why** and offer **ways around it**. Design it once, inside the shell, at both sizes:
   - A warning-triangle icon and the H2 **"This page couldn't load"**.
   - **The reason**, in normal text: the app's own message. Show two examples:
     - "Could not reach the server. Please check your connection." (no answer at all);
     - "Something went wrong. Please try again." (server error).
   - **A details line**, small and muted, for whoever helps the owner. Examples:
     - "Details: no response from the server · 14:32";
     - "Details: status 500 · /owner/dashboard · 14:32".
   - **"What you can try:"**, a short list:
     1. "Wait a moment and try again. On the free hosting plan the server sleeps when nobody uses it and can take up to a minute to wake up."
     2. "Check your internet connection."
     3. "Switch to the Classic look. If only the new look has a problem, the classic one keeps working." (Only shown in the New look.)
     4. "If it keeps happening, send the details line above to your developer."
   - **Buttons:** **"Try again"** (primary; reloads the page) and **"Switch to Classic look"** (secondary; only in the New look).
   - If the very first check (the owner session) fails for a reason other than "not logged in", show this same state on a page without the side menu.

### Screen O1 — Studio login

**Purpose:** owner sign-in.
**Who:** the owner. The page is `/owner/login.html` and is linked from "Studio login" in the home page footer.

There is no shell. A single centred card (max 400px) sits on the warm background:

1. Leaf logo and "Slotwise".
2. H1 **"Studio login"**.
3. Muted text: "Sign in to manage bookings, the menu and your team."
4. An error alert (hidden unless there is an error).
5. "Email" input.
6. "Password" input.
7. The full-width primary button **"Log in"**.
8. Below the card, the link "Back to studio page".

**States:**

- empty;
- **missing fields:** "Please enter your email and password.";
- **wrong login:** "Email or password is wrong.";
- **locked:** "Too many attempts. Try again in 5 minutes.";
- **submitting:** the button is disabled.

### Screen O2 — Dashboard

**Purpose:** the owner's daily overview and whether the system works (fewer no-shows, refilled cancellations, online share).
**Who:** the owner.

From top to bottom:

1. **Page head:**
   - H1 "Welcome back, Studio owner".
   - Under it, the muted date "Tuesday 13 October 2026".
   - On the right, a "Day" label with a date input to look at another day.
2. **Three tiles for the chosen day:**
   1. "Bookings on this day": **6**, note "not counting cancellations".
   2. "Expected revenue": **€398**, note "pay at the studio".
   3. "Confirmed by customer": **67%**, note "via the reminder link".
3. **Section H2 "Is it working? (last 30 days)":**
   - Muted text: "13 Sep – 13 Oct, by appointment date. Goals from the project plan."
   - Four tiles:
     1. "No-show rate": **3.8%**, note "no-shows ÷ (done + no-shows)", badge "✓ On target · goal < 5%".
     2. "Refilled from waitlist": **40%**, note "waitlist bookings ÷ cancellations", badge "▲ Off target · goal ≥ 50%".
     3. "Booked online": **72%**, note "online ÷ all bookings", badge "✓ On target · goal ≥ 60%".
     4. "Revenue recovered": **€134**, note "through the waitlist", no badge.
   - When there is no data, the value is "–" and the badge reads "No data yet".
4. **Section H2 "Appointments on this day":**
   - A data table with the columns: Time | Customer | Therapist | Services | Total | Status.
   - Example rows:
     - 10:00 | Anna Müller | Lena | Deep tissue massage | €82 | Confirmed
     - 11:30 | Ben Fischer ⚠ | Lena | Back and neck massage | €39 | Booked
     - 12:00 | Priya Shah | Sofia | Classic facial | €68 | Awaiting email
   - The ⚠ has the tooltip "2 or more no-shows".
   - Rows are clickable and open that booking in Bookings.
   - **Empty:** "No appointments on this day."
5. **Section H2 "No-shows and late cancellations per week":**
   - Muted text: "The last 8 weeks. Hover or focus a week for the numbers."
   - A **grouped bar chart** with 8 weeks on the x-axis (labels like "17 Aug") and a y-axis from 0 with 4 grid lines.
   - Two thin bars per week: "No-shows" (`--chart-1`) and "Late cancellations" (`--chart-2`), with a legend above the chart.
   - A tooltip on hover or focus: "Week of 5 Oct", "No-shows: 1", "Late cancellations: 2".
   - Below the chart, a collapsible "Show as table" with the columns Week of | No-shows | Late cancellations.

**States:**

- loading ("Loading…" with skeleton tiles);
- empty day (zeros, "–" and "No data yet");
- load error: the shared page error state (owner shell, item 5).

### Screen O3 — Bookings (calendar and list)

**Purpose:** see and find bookings by day, week or list, and open one to manage it.
**Who:** the owner.

1. **Page head:**
   - H1 "Bookings".
   - Actions: "Export CSV" (secondary, small, download icon) and "Add booking" (primary, small).
2. **Toolbar, row 1:**
   - the segmented control "Day | Week | List" (screen-reader label "View");
   - the buttons "‹" (label "Previous"), "Today" and "›" (label "Next");
   - the range label, for example "Tuesday 13 October 2026" in Day view, or "Mon 12 Oct – Sun 18 Oct" in Week view.
3. **Toolbar, row 2 (filters):**
   - a select with "All therapists", Lena and Sofia;
   - a select with "All statuses", Awaiting email, Booked, Confirmed, Done, No-show, Cancelled and Not confirmed;
   - a search input with the placeholder "Search name, email or phone" (screen-reader label "Search").
   - On mobile, the two toolbars wrap into stacked full-width rows.
4. **Day view:**
   - One column per therapist (H3 "Lena", "Sofia").
   - Each booking is a **calendar card** (a button) with a coloured left edge by status:
     - "**10:00** · 75 min";
     - the customer name, plus ⚠ for repeat no-shows;
     - the services, e.g. "Deep tissue massage";
     - a status word, only when the status is not Booked or Confirmed, e.g. "Awaiting email" or "Cancelled".
   - Left edge colours:
     - Booked: warning;
     - Confirmed: success;
     - Awaiting email: info, dashed;
     - Done: muted green;
     - Cancelled and No-show: danger, dimmed;
     - Not confirmed: grey, dimmed.
   - An empty column shows "No bookings".
5. **Week view:**
   - Seven day columns, Monday to Sunday (H3 like "Tue 13 Oct"). Today's column is highlighted with a small `--warm` marker.
   - The cards are the same as in Day view, plus the therapist name.
   - Empty days show "No bookings".
   - **On mobile**, the week scrolls sideways, about 1.3 columns visible at a time.
6. **List view (two weeks):**
   - A data table with the columns: Date | Time | Customer | Therapist | Services | Total | Status (badge).
   - Example row: "Tue 13 Oct | 10:00 | Anna Müller | Lena | Deep tissue massage | €82 | Confirmed".
   - Rows are clickable and keyboard-focusable.
   - **Empty:** "No bookings in this range."

**States:**

- loading ("Loading…");
- error alert inside the page, for a problem with the chosen filters or range (e.g. "Please choose a range of up to 3 months.");
- load error (the page itself can't load): the shared page error state (owner shell, item 5);
- empty, as described above.

#### Screen O3-D — Booking detail (dialog)

This opens when a card or row is clicked.

1. **Title:** the customer's name, e.g. "Anna Müller", with a "×" close button (label "Close").
2. **Header section:**
   - The status badge, e.g. "Confirmed", plus a "Late cancellation" badge when relevant.
   - Facts:
     - **When:** Tuesday 13 October 2026, 10:00 (75 min).
     - **Therapist:** Lena.
     - **Email:** anna.mueller@example.com (a mailto link).
     - **Phone:** +49 151 0000 0001 (a tel link).
     - **No-shows:** 0. For Ben it reads "2 ⚠ repeat no-show" in danger colour.
     - **Source:** online, phone or waitlist.
     - **Note:** shown only if the customer left one.
3. **Section H3 "Status":**
   - A select with Awaiting email, Not confirmed, Booked, Confirmed, Done, No-show and Cancelled.
   - Next to it, the small primary button "Save status". It is disabled once a receipt is sent.
   - Hint, shown before the start time: "Done and no-show can be set once the appointment has started."
   - Error alert, for example "This status change is not allowed." or "A booking can only be marked done or no-show after it starts."
   - Success toast: "Status: Done".
4. **Section H3 "Items":**
   - The item lines with the Total.
   - The small secondary button "Adjust items". It is hidden for cancelled bookings and after a receipt was sent.
   - **Items editor state** (replaces the table):
     - H3 "Adjust items" and the hint "Lines done on the day, e.g. extra time or a product sold. Prices in EUR."
     - An editable row per line with these controls:
       - "Type" select: service, add-on or extra;
       - "Name" text input (wide);
       - "Price EUR" number input;
       - "Quantity" number input (1–99);
       - an "×" remove button (label "Remove Hot stones").
     - Buttons: "+ Add line" (secondary), "Save items" (primary) and "Cancel" (secondary).
     - Error, for example "Please check the item lines." or "The receipt was already sent; this booking can't be changed."
     - Toast: "Items saved".
5. **Section H3 "Receipt":**
   - Before the booking is done: the button "Send receipt" (disabled) with the hint "Mark the booking done to send a receipt."
   - When done: "Send receipt" is enabled.
   - After sending: "Receipt IW-2026-0042 sent" with the link "Print receipt" (opens C7, owner version), and the button "Resend receipt".
   - Toast: "Receipt IW-2026-0042 sent". Error: "Only bookings marked done can get a receipt."
6. **States:** "Loading…" and an error alert, e.g. "Booking not found."

#### Screen O3-N — Add phone booking (dialog)

This opens from "Add booking". Title: **"Add phone booking"**, with "×" to close.

1. **"Services":** a checkbox list of active services, e.g. "Deep tissue massage · 60 min · €70".
2. **Add-on checkboxes** for the checked services, e.g. "+ Hot stones (€12)".
3. **Two columns:**
   - "Therapist": a select with "No preference" and only the therapists who offer all checked services;
   - "Day": a date input, defaulting to today.
4. **"Time":** a select whose options look like "10:00 · Lena".
   - Placeholder states: "Pick services and a day", "Loading…" and "No free times".
5. **Two columns:** "First name", "Last name", "Email" and "Phone".
6. **"Note (optional)":** a textarea.
7. An error alert, e.g. "That time was just taken. Please pick another." (the times reload) or "Please enter a valid email address".
8. The full-width primary button **"Save booking"**.
9. **Success:** the dialog closes and a toast reads "Booked 10:00 with Lena; confirmation emailed". The calendar jumps to that day and the new booking's detail opens.

### Screen O4 — Services & add-ons

**Purpose:** manage the menu: treatments, prices, durations and add-ons.
**Who:** the owner.

1. **Page head:** H1 "Services & add-ons" with the action "Add service" (primary, small).
2. Muted text: "Inactive services are hidden from customers. Existing bookings always keep the name and price they were booked with."
3. **A data table** with the columns: Category | Service | Duration | Price | Buffer after | Active | (actions).
   - **Service row:**
     - "Massages | **Deep tissue massage**", with the description "Firm pressure for tight muscles and knots." as a small second line;
     - "60 min | €70 | 10 min";
     - an Active checkbox with the text "Yes" or "No" (label "Deep tissue massage active");
     - the actions "Edit" and "+ Add-on" (secondary, small).
   - **Add-on rows** directly under their service, indented:
     - "+ Hot stones | +15 min | +€12 | (empty) | Yes";
     - the action "Edit add-on".
   - Inactive rows are dimmed.
   - **Toasts:** "Deep tissue massage is now hidden" or "… is now shown".
4. **Service editor (dialog):**
   - Title: "Add service" or "Edit Deep tissue massage".
   - "Category": a select with Massages, Facials and Reflexology.
   - "Name".
   - "One-line description".
   - Two columns:
     - "Name (German)", with the hint "Shown to German-speaking customers; leave empty to use the English name.";
     - "Description (German)".
   - Two columns:
     - "Duration (minutes)", with the hint "15 to 240, steps of 15";
     - "Price (EUR)".
   - "Cleanup buffer after (minutes)", with the hint "0 to 30".
   - A checkbox "Shown to customers".
   - An error alert, with the related field outlined red. Examples:
     - "Please enter a name."
     - "A service with this name already exists."
     - "Duration must be 15 to 240 minutes in steps of 15."
     - "Please enter a price between 0 and 10,000 EUR with 2 decimals."
     - "Buffer must be 0 to 30 minutes."
   - The full-width primary button **"Save"**.
   - **Toasts:** "Service added" or "Service saved".
5. **Add-on editor (dialog):**
   - Title: "Add-on for Deep tissue massage" or "Edit add-on: Hot stones".
   - "Name".
   - "Name (German)", with the hint "Leave empty to use the English name."
   - Two columns:
     - "Extra time (minutes)", with the hint "0 to 60";
     - "Price (EUR)".
   - A checkbox "Shown to customers".
   - The button "Save".
   - Error: "Extra time must be 0 to 60 minutes."
   - **Toasts:** "Add-on added" or "Add-on saved".
6. **Loading:** "Loading…". **Load error:** the shared page error state (owner shell, item 5).

### Screen O5 — Therapists & hours

**Purpose:** manage the team, which treatments each person offers, weekly working hours, and days off.
**Who:** the owner.

1. **Page head:** H1 "Therapists & hours" with the action "Add therapist" (primary, small).
2. **A data table** with the columns: Name | Services offered | Weekly hours | Active | (actions).
   - **Lena:**
     - bio as a second line;
     - services "Relaxation massage, Deep tissue massage, Back and neck massage, Foot reflexology";
     - hours "Mon 10:00–19:00 · Tue 10:00–19:00 · Wed 10:00–19:00 · Thu 10:00–19:00 · Fri 10:00–19:00 · Sat 10:00–14:00";
     - Active "Yes";
     - actions "Edit" and "Hours".
   - **Sofia:**
     - services "Relaxation massage, Classic facial, Express facial";
     - hours "Tue 09:00–17:00 · … · Sat 09:00–17:00".
   - When there are no hours, show "No hours yet". When there are no services, show "—".
3. **Section H2 "Days off"** with the action "Add day off" (primary, small):
   - A table with the columns: Date | Who | Reason | (action).
   - Example rows:
     - "Thu 24 Dec 2026 | **Whole studio closed** | Christmas Eve | Remove";
     - "Mon 19 Oct 2026 | Sofia | Holiday | Remove".
   - **Empty:** "No upcoming days off."
4. **Therapist editor (dialog):**
   - Title: "Add therapist" or "Edit Lena".
   - "Name".
   - "Short bio" (textarea).
   - "Short bio (German)" (textarea), with the hint "Leave empty to use the English bio."
   - "Services offered": a checkbox for each service. Inactive services carry the muted suffix " (inactive)".
   - A checkbox "Active (can be booked)".
   - The button "Save".
   - **Errors:** "Please enter a name." and "A therapist with this name already exists."
   - **Toasts:** "Therapist added" or "Therapist saved".
5. **Weekly hours editor (dialog):**
   - Title: "Weekly hours: Lena".
   - A 4-column grid with the header row **Day | Start | End | Closed**.
   - One row per day, Mon to Sun: time inputs in 15-minute steps, plus a "Closed" checkbox. When "Closed" is checked, the time inputs are disabled.
   - A hint that appears only in a special case: "Split shifts on the same day are kept only for the first window when saved here."
   - The button "Save".
   - **Errors:**
     - "Please enter a start and end time for each open day."
     - "Each day needs a start time before its end time."
     - "Working hours on the same day overlap."
   - **Toast:** "Hours saved".
6. **Add day off (dialog):**
   - Title: "Add day off".
   - "Who": a select with "Whole studio (closed)", Lena and Sofia.
   - "Date".
   - "Reason", with the placeholder "e.g. Holiday".
   - The button "Save".
   - **Error:** "Please choose a date."
   - **Toasts:** "Day off added" and "Day off removed".
7. **Loading:** "Loading…". **Load error:** the shared page error state (owner shell, item 5).

### Screen O6 — Waitlist

**Purpose:** see who is waiting for which day, what was offered, and remove entries.
**Who:** the owner.

1. **Page head:** H1 "Waitlist".
2. **Toolbar:** a "Day" label with a date input, and the button "All upcoming" (secondary, small).
3. **A data table** with the columns: Customer | Services | Day and window | Therapist | Joined | Status | (action).
   - **Customer cell:** the name in bold, then the email and phone as small muted lines, e.g. "**Mia Wagner** / mia.wagner@example.com / +49 151 0000 0005".
   - **Services:** "Relaxation massage".
   - **Day and window:** "Thu 15 Oct, 09:00–18:00".
   - **Therapist:** "Sofia", or "Any".
   - **Joined:** "12 Oct, 18:40".
   - **Status cell:** a badge, plus small lines when relevant:
     - "Offered 11:00";
     - "until 13 Oct, 10:30" (while an offer is open);
     - a link "View booking" (after it was booked).
   - **Statuses:** Awaiting email, Waiting, Offered, Booked, Offer expired and Removed / declined.
   - **Action:** "Remove" (secondary, small), only for Awaiting email, Waiting and Offered.
   - **Toast:** "Mia Wagner removed from the waitlist".
4. **Empty:**
   - "Nobody is on the waitlist." (all upcoming);
   - "Nobody is waiting for this day." (one day).
5. **Loading:** "Loading…". **Load error:** the shared page error state (owner shell, item 5).

### Screen O7 — Studio settings

**Purpose:** studio details shown to customers, booking rules and receipt numbering.
**Who:** the owner.

1. **Page head:** H1 "Studio settings".
2. **A form in three cards (fieldsets):**
   1. **"Studio details":**
      - Lead text: "Shown on the home page, on receipts and in every email. Customer replies to emails go to the email address below."
      - "Studio name".
      - "Address".
      - Two columns: "Phone" and "Email (reply-to)".
      - "Opening hours (as shown on the home page)", with the hint "Separate parts with ' · ', e.g. Mon 10:00–19:00 · Sat 9:00–17:00 · Sun closed. Bookable times come from Therapists & hours."
      - "Opening hours (German)", with the hint "e.g. Mo 10–19 Uhr · Sa 9–17 Uhr · So geschlossen. Leave empty to use the English text."
   2. **"Booking rules":**
      - Lead text: "Apply from now on. Existing bookings keep their times and prices."
      - A 2×2 grid:
        - "Minimum notice (hours)": 2, with the hint "Customers can't book later than this; phone bookings can.";
        - "Book up to (days ahead)": 60;
        - "Free cancellation until (hours before)": 24, with the hint "Later cancellations are allowed but marked late.";
        - "Waitlist offer lasts (minutes)": 30.
   3. **"Receipts":**
      - "Receipt number prefix": IW, with the hint "Receipts are numbered PREFIX-YEAR-0001. A new prefix starts again at 0001."
3. An error alert, with the related field outlined red. Examples:
   - "Please enter the studio address."
   - "Minimum notice must be 0 to 72 hours."
   - "Free cancellation must be 0 to 168 hours."
   - "Booking window must be 1 to 365 days."
   - "Receipt prefix: 1 to 10 letters or digits."
4. The primary button **"Save settings"**, right-aligned on desktop and full width on mobile.
5. **Toast:** "Settings saved".
6. **Loading:** "Loading…". **Load error:** the shared page error state (owner shell, item 5).

### Owner flows to show

1. **Login to dashboard:** Login, then "Log in", then the Dashboard. A click on an appointment row opens Bookings with that booking's detail dialog.
2. **Phone booking:** Bookings, then "Add booking", then fill the form, then "Save booking". A toast appears and the new booking's detail opens.
3. **After the visit:**
   1. Open the booking detail.
   2. Status "Done", then "Save status".
   3. "Adjust items", then "+ Add line" for an extra, then "Save items".
   4. "Send receipt" gives "Receipt IW-2026-0042 sent".
   5. "Print receipt" opens the A4 receipt.

```text
=== PROMPT END (Part 3 of 3) ===
```

---

## How to port this design (for us, not for Figma)

### 1. What we take from Figma

- **Main source: the exported code** in `doc/design/figma-make/`. It's a reference-only library, never built, served or tested (see Stage C1).
  - **CSS:** its custom properties should use our token names (Part 1, section 5). They become the `:root[data-theme="calm"]` block in `calm.css`, almost one to one.
  - **Component styles:** buttons, cards, chips and so on are translated into rules on our existing classes (see the mapping in section 4), scoped under `[data-theme="calm"]`.
  - **Icons:** its inline SVGs are copied into our markup or scripts.
  - **Never:** its React components, state logic or Tailwind classes are never copied into `app/static/`. Our HTML structure, IDs and scripts stay, and every hook listed in [`doc/ui-inventory.md`](../ui-inventory.md) must survive the port.
- **Seeing it rendered:** with your OK, I run the export locally (`npm install && npm run dev`, outside the app) and compare it with our pages in the browser pane at 390px and 1440px. Otherwise I use the screenshots from Stage C2.
- **Figma connection (optional):** at most 1–3 of the 20 monthly calls, e.g. `get_variable_defs` if the exported CSS doesn't carry the tokens.

### 2. Keeping the classic look switchable

The current design stays exactly as it is. The new design is an extra layer that is only switched on when `<html data-theme="calm">` is set.

1. **`css/styles.css` stays the classic look.** Its rules and colours are not changed, apart from moving the few hard-coded colours into tokens (see 3.2). It keeps working on its own.
2. **New file: `css/calm.css`,** loaded after `styles.css` on every page. Every rule in it is scoped under `:root[data-theme="calm"]`:
   - the new token values: `:root[data-theme="calm"] { --green: #1F5C45; … }`;
   - component overrides, for example `[data-theme="calm"] .btn { … }`.

   Because the old file is never edited for the new look, switching back is always the original.
3. **New file: `js/theme.js`,** a tiny normal (non-module) script in `<head>` before the stylesheet's first paint.
   - It reads `localStorage["slotwise:theme"]`, which holds `classic` or `calm`, and sets `document.documentElement.dataset.theme`.
   - It runs before the page draws, so there is no flash of the wrong look.
   - Storage access is wrapped in try/catch, like `slotwise:lang`.
4. **The switch button:**
   - A `<span data-theme-switch>` slot next to `data-lang-switch` in each customer top bar, plus one in the owner side menu (built in `owner-shell.js`).
   - It shows "Classic look" or "New look" (German "Klassisches Design" / "Neues Design"; new keys `theme.classic` and `theme.calm` in `i18n.js`).
   - It flips the stored value and the attribute without a page reload.
5. **New markup must not break the classic look.** A few new parts don't exist in the classic design. They are added to the HTML but hidden by default in `styles.css`, and shown only by `calm.css`:
   - the mobile booking total bar;
   - the owner mobile menu button;
   - the icons inside buttons.
6. **Decided:**
   - **The default look is `classic`.** `theme.js` uses `calm` only when the browser has chosen it.
   - **Customers and the owner both get the switch.**
   - **The waitlist statuses get their own badge classes:** `wl-pending`, `wl-waiting`, `wl-offered`, `wl-booked`, `wl-expired` and `wl-removed`, instead of borrowing the booking classes. In `styles.css` they reproduce today's colours exactly, so the classic look doesn't change; `calm.css` gives them the new colours.
   - **Owner pages get a real error state** instead of staying on "Loading…" (see 2.8).
7. **Cost:** every later UI change must be checked in both looks. If one look is clearly preferred after a while, we delete the other file and the switch. That is a one-PR clean-up.
8. **The owner page error state** (decided; useful in both looks, so it comes first):
   - **Today:**
     - Most owner scripts end with `init().catch(() => {})`, so a failed load leaves "Loading…" on screen forever.
     - `owner-shell.js` replaces the whole body with the bare message.
   - **New helper** `showPageError(error, path)` in `owner-shell.js`. It builds the state described in Part 3, owner shell, item 5:
     - the reason: `error.message`, which is already translated and friendly;
     - the details line: `error.status`, where `0` means no response (`api.js` already uses `0` for network failures), plus the request path and the time;
     - the "What you can try" list;
     - "Try again", which reloads;
     - "Switch to Classic look", only while `data-theme="calm"`.
   - **Wiring:**
     - each owner page's `.catch(() => {})` becomes `.catch(showPageError)`;
     - the shell uses the helper too when `/auth/me` fails for a reason other than 401.
   - **Tests:** none on the server side; checked in the browser by stopping the server and by forcing a 500.

### 3. Token mapping (Figma tokens → our stylesheet)

1. **The existing tokens keep their names.** In `calm.css` they only get new values: `--green`, `--green-dark`, `--accent`, `--accent-soft`, `--ink`, `--muted`, `--line`, `--bg`, `--card`, `--danger`, `--danger-soft`, `--radius`, `--radius-sm`, `--shadow` and `--font`.
2. **New tokens** go into `styles.css` `:root` **with values that reproduce today's look exactly**, so the classic look stays identical. `calm.css` then overrides them:

   | New token | Classic value (today's hard-coded colour) | Replaces |
   |---|---|---|
   | `--warm` / `--warm-soft` | `var(--ink)` / `transparent` | total rows (today they are ink) |
   | `--input-border` | `#cbd5cf` | input borders (`#cbd5cf`, `#b9cfc2`) |
   | `--warning` / `--warning-soft` | `#8a5300` / `#fff4e0` | "booked" badge, `.target.warn` |
   | `--info` / `--info-soft` | `#2c5aa0` / `#eef3fb` | "pending" badge |
   | `--success` / `--success-soft` | `var(--green-dark)` / `var(--accent-soft)` | success notes, "confirmed"/"done" badges |
   | `--chart-1` / `--chart-2` | `#2a78d6` / `#eb6834` | chart series. These also live in `owner-dashboard.js` `SERIES[].color`, so read them via `getComputedStyle` |
   | `--cal-booked` | `#e0a100` | `.cal-card.booked` edge |
   | `--radius-lg` / `--radius-pill` | `var(--radius)` / `999px` | cards / badges |
   | `--shadow-lg` | the current dialog/toast shadow | dialogs, toasts |
   | `--text-*`, `--space-*` | today's rem values | font sizes, gaps |

3. **Inter font:** load it only in the calm look, either self-hosted in `app/static/fonts/` or from Google Fonts. Self-hosting avoids a third-party request. The classic look keeps the system font.

### 4. Screen and component mapping (Figma → our files)

| Figma | Our page / script | Main elements |
|---|---|---|
| Top bar, language switch, "Classic look" | every customer `*.html` `.topbar`; `i18n.js` `languageSwitch()`; new `theme.js` | `.topbar`, `.topbar-actions`, `[data-lang-switch]`, new `[data-theme-switch]` |
| C1 Home | `index.html` + `js/home.js` | `.studio`, `.studio-facts`, `#menu` → `.menu-category` → `.service` |
| C2 Booking | `book.html` + `js/book.js` | `.book-layout`, `.step` + `.step-number`, `.choice`, `.chip`, `.time-btn`, `.form-grid`, `.summary`; new mobile total bar |
| C2-W Waitlist box | `js/book.js` `waitlistBox()` | `.waitlist-box` |
| C3 Booking result | `confirmation.html` + `js/confirmation.js` | `.confirm-card`, `.confirm-icon`, `.facts`, `.lines` |
| C4 Manage booking | `manage.html` + `js/manage.js` | `.status-badge`, `.actions`, `.confirm-cancel`, `.policy-note` |
| C5 Offer | `offer.html` + `js/offer.js` | `.countdown` (+`.urgent`) |
| C6 Waitlist confirmed | `waitlist-confirm.html` + `js/waitlist-confirm.js` | `#result` card |
| C7 Receipt | `receipt.html` + `js/receipt.js` | `.no-print`, `.receipt`, `@media print` |
| Owner shell | `js/owner-shell.js` + every `owner/*.html` | `.owner-layout`, `#sidebar`, `.owner-main`, `.page-head` |
| O1 Login | `owner/login.html` + `js/owner-login.js` | `.center-page`, `.card` |
| O2 Dashboard | `owner/dashboard.html` + `js/owner-dashboard.js` | `.tiles`/`.tile`, `.target`, `.chart-*`, `.table-view` |
| O3 Bookings + dialogs | `owner/bookings.html` + `js/owner-bookings.js` | `.toolbar`, `.segmented`, `.cal`/`.cal-col`/`.cal-card`, `table.data`, `dialog.panel`, `.items-editor` |
| O4 Services | `owner/services.html` + `js/owner-services.js` + `js/owner-forms.js` | `table.data`, `dialog#editor` |
| O5 Therapists | `owner/therapists.html` + `js/owner-therapists.js` | `.hours-grid`, `dialog#editor` |
| O6 Waitlist | `owner/waitlist.html` + `js/owner-waitlist.js` | `.toolbar`, `table.data` |
| O7 Settings | `owner/settings.html` + `js/owner-settings.js` | `form.settings fieldset`, `.actions-row` |
| Buttons | everywhere | `.btn`, `.btn-ghost`, `.btn-small`, `.btn-block`, `.btn-danger-ghost`, `.icon-btn`; new `.btn-danger` replaces the inline `style="background: var(--danger)"` in `manage.js` |
| Alerts / notes / states | everywhere | `.alert`, `.success-note`, `.notice`, `.state`, `.field-error`, `.field-hint`, `.pay-note`, `.toast` |
| Skeletons | new | `.skeleton` class; scripts keep their loading texts as screen-reader text |

### 5. Order of work (each step is its own branch and PR)

**Status: done.** Shipped as:
- PR #15: step 0, the owner error state;
- PR #16: step 1, tokens and the switch;
- PR #17: steps 2+3, font, base and components, combined because they depend on each other;
- PR #18: step 4, customer pages;
- PR #19: step 5, owner pages;
- the polish PR: step 6.

Deviations from the plan below:
- Tokens the new look adds (`--warm`, `--space-*`, `--text-*`, `--radius-lg`…) live only in `calm.css`. `styles.css` got just the tokens whose classic values had to stay (input border, success, warning, info, chart).
- A few new-look parts needed small markup or script changes, all hidden or neutral in classic:
  - the mobile total bar;
  - the owner Menu button and icons;
  - `fact()` wrappers;
  - `.is-loading`;
  - `.btn-danger`;
  - the `wl-*` waitlist badges.

  The list is in `doc/ui-inventory.md`.

0. **Owner page error state** (see 2.8): a small behaviour fix, styled in the classic look. It can ship before the Figma design is ready.
1. **Tokens and switch:**
   - add the new tokens to `styles.css` with classic values (no visual change);
   - add an empty `calm.css`, `theme.js` and the switch button;
   - add a test that every page links `calm.css` and `theme.js`.
2. **Base styles:** in `calm.css`, the calm token values, the font, page background, headings, links, focus ring, cards and containers.
3. **Components:** buttons, inputs, option cards, chips, time buttons, badges, tables, dialogs, toasts, alerts, skeletons and step markers.
4. **Customer pages:**
   - home, then booking (including the new mobile total bar and its small script change in `book.js`), then confirmation, manage, offer, waitlist-confirm and the receipt with its print styles;
   - check each page in DE and EN, and in both looks.
5. **Owner pages:** the shell (including the mobile menu button in `owner-shell.js`), then dashboard, bookings and dialogs, services, therapists, waitlist and settings.
6. **Polish:**
   - check contrast, tap targets and focus on 390px and 1440px;
   - print the receipt;
   - check every flow in both looks;
   - Classic stays the default; you decide later whether to make the New look the default.

The tests (`pytest`) cover the server and pass unchanged through all six steps. For the visual checks I'll use the browser at 390px and 1440px.
