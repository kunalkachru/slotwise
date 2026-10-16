> **Note (Slotwise):** this was `AGENTS.md` in the Figma Make export, renamed so AI tools don't load it as instructions for this repo. It describes Figma Make's own sandbox, not our rules; our rules are in the root CLAUDE.md. This folder is a reference-only library: never built, served, tested or deployed (see doc/design/figma-prompt.md, Stage C1).

## Changes made after the export (Slotwise)

Small fixes so this reference matches the brief (from the PR #14 review). Re-apply them if the folder is ever replaced by a new export.

1. `src/CustomerScreens.tsx` `BookingSummary`: in the "(g) Time just taken" frame, the booking is no longer "complete". Both Confirm buttons are disabled and the summary says "…, pick a time", because the slot is cleared when the times reload (as `book.js` does on a 400).
2. `src/CustomerScreens.tsx` `WaitlistBox`: both time selects offer 07:00–21:00 in 30-minute steps (as `book.js` `timeOptions()` does). The defaults stay 09:00 and 18:00.
3. `src/CustomerScreens.tsx` `CustomerHeader`: the look switch reads "Klassisches Design" on German pages.

## Notes for the port (not changed here)

- **German header at 390px:** with "EN", "Klassisches Design" and "Zurück zum Menü", the studio name shrinks to "I…". In `calm.css`, below about 400px, show the look switch as its icon only, with its text as the `aria-label`.
- **Home:** leave out the invented "Munich · Day spa" line.
- **Booking times:** the prototype shows therapist names under the times even when a therapist is chosen. Our `book.js` shows them only for "No preference"; keep our logic.
- **German texts:** a few differ slightly from `i18n.js`. The port always uses our word lists.
- **Mobile total bar:** in the prototype it sits at the end of the frame. On the real page it is fixed to the bottom of the screen.
- **Font:** the prototype loads Inter from Google Fonts. The port self-hosts it, because of GDPR rulings on Google Fonts in Germany.

# figma-make-app

React + Vite + Tailwind CSS project running inside Figma Make.

## Development Server

A Vite development server is **already running** on `$PORT` (default 8443). You don't need to start it manually.

- Preview URL: The user can access the running app through the preview panel
- Hot reload: Changes to source files are reflected immediately

## Project Structure

This is the canonical project structure. Start with task-relevant files below. Only follow imports or inspect other files when required, when a documented path is missing, or when the repository contradicts this guide.

- `src/main.tsx` - React entrypoint; imports `src/index.css` and mounts `src/App.tsx` into the `#root` element
- `src/App.tsx` - Primary application component and the usual starting point for UI work
- `src/index.css` - Global CSS entrypoint and Tailwind CSS v4 import
- `index.html` - Vite HTML shell containing the `#root` element and loading `src/main.tsx`
- `package.json` - Project dependencies and the Vite build, development, preview, and formatting scripts
- `vite.config.ts` - Vite configuration with React, Tailwind CSS v4, and Figma Make plugins plus the `@` alias for `src`
- `.mise.toml` - Toolchain versions for Node.js and pnpm

## Dependencies

- Runtime: React 19 and React DOM 19
- Styling: Tailwind CSS v4 with the `@tailwindcss/vite` plugin
- Build tooling: Vite 8, TypeScript 5.7, and `@vitejs/plugin-react`
- Formatting: oxfmt

## Styling

This project uses **Tailwind CSS v4** through the `@tailwindcss/vite` plugin configured in `vite.config.ts`. `src/index.css` imports Tailwind with `@import 'tailwindcss';`. Use Tailwind utility classes directly in JSX and put global CSS or Tailwind v4 theme customization in `src/index.css`. This scaffold does not need a Tailwind config file or PostCSS config.

`src/main.tsx` imports `src/index.css`, so global font wiring belongs in `src/index.css`. Keep CSS `@import` statements first, then add any `@font-face` rules and font-family defaults there.

## Code quality

- Use double quotes for strings containing apostrophes (`"We're here to help"`), or escape them in single-quoted strings. An unescaped apostrophe in a single-quoted string breaks the build.
- Ensure JSX tags are closed and braces are balanced.
- Export components as default exports.
