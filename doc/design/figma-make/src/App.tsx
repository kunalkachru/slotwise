import { useState, type ReactNode } from "react";
import CustomerScreens from "./CustomerScreens";
import OwnerScreens from "./OwnerScreens";

type IconName =
  | "calendar"
  | "check"
  | "chevron-left"
  | "chevron-right"
  | "clock"
  | "close"
  | "download"
  | "envelope"
  | "eye"
  | "map"
  | "phone"
  | "printer"
  | "user"
  | "warning";

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    calendar: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M16 3v4M8 3v4M3 10h18" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    "chevron-left": <path d="m15 18-6-6 6-6" />,
    "chevron-right": <path d="m9 18 6-6-6-6" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    close: <path d="M6 6l12 12M18 6 6 18" />,
    download: (
      <>
        <path d="M12 3v12m0 0 4-4m-4 4-4-4" />
        <path d="M5 20h14" />
      </>
    ),
    envelope: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m4 7 8 6 8-6" />
      </>
    ),
    eye: (
      <>
        <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
        <circle cx="12" cy="12" r="2.5" />
      </>
    ),
    map: (
      <>
        <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </>
    ),
    phone: (
      <path d="M7.2 3h3l1.5 4-2 1.5a15 15 0 0 0 5.8 5.8l1.5-2 4 1.5v3A3.2 3.2 0 0 1 17.8 20C10.2 19.5 4.5 13.8 4 6.2A3.2 3.2 0 0 1 7.2 3Z" />
    ),
    printer: (
      <>
        <path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
        <path d="M6 14h12v7H6z" />
      </>
    ),
    user: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </>
    ),
    warning: (
      <>
        <path d="M12 3 2.5 20h19L12 3Z" />
        <path d="M12 9v5m0 3h.01" />
      </>
    ),
  };

  return (
    <svg
      aria-hidden="true"
      className="icon"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
    >
      {paths[name]}
    </svg>
  );
}

const colors = [
  ["--green", "#1F5C45", "Primary"],
  ["--green-dark", "#164534", "Hover and pressed"],
  ["--accent", "#3E9C72", "Focus and highlights"],
  ["--accent-soft", "#E4F0EA", "Selected surfaces"],
  ["--warm", "#A0571A", "Totals only"],
  ["--warm-soft", "#FBEFE3", "Highlighted totals"],
  ["--ink", "#1C2621", "Main text"],
  ["--muted", "#5A645F", "Secondary text"],
  ["--line", "#E6E0D6", "Dividers"],
  ["--input-border", "#848F89", "Control borders"],
  ["--bg", "#FAF7F2", "Page background"],
  ["--card", "#FFFFFF", "Cards"],
  ["--success", "#1E6B45", "Success"],
  ["--success-soft", "#E5F3EA", "Success surface"],
  ["--warning", "#8A5300", "Warning"],
  ["--warning-soft", "#FFF3DC", "Warning surface"],
  ["--danger", "#B42318", "Errors"],
  ["--danger-soft", "#FDECEA", "Error surface"],
  ["--info", "#2C5AA0", "Information"],
  ["--info-soft", "#EAF0FA", "Information surface"],
  ["--chart-1", "#2A78D6", "No-shows"],
  ["--chart-2", "#EB6834", "Late cancellations"],
];

function SectionHead({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="section-head">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {children && <p>{children}</p>}
    </div>
  );
}

function Specimen({
  title,
  note,
  children,
  wide = false,
}: {
  title: string;
  note?: string;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <article className={`specimen ${wide ? "specimen--wide" : ""}`}>
      <div className="specimen__head">
        <h3>{title}</h3>
        {note && <p>{note}</p>}
      </div>
      <div className="specimen__body">{children}</div>
    </article>
  );
}

function State({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="state">
      <span className="state__label">{label}</span>
      {children}
    </div>
  );
}

function StatusBadge({
  tone,
  children,
  outlined = false,
}: {
  tone: string;
  children: ReactNode;
  outlined?: boolean;
}) {
  return (
    <span className={`badge badge--${tone} ${outlined ? "badge--outlined" : ""}`}>
      <span className="badge__dot" />
      {children}
    </span>
  );
}

function StyleGuide() {
  return (
    <main id="main-content" className="page">
      <section className="intro">
        <p className="eyebrow">Slotwise · Calm modern</p>
        <h1>A quieter way to book well</h1>
        <p>
          A warm, trustworthy visual foundation for Isar Wellness. Information
          stays easy to scan, while generous space and soft surfaces keep every
          interaction calm.
        </p>
      </section>

      <section className="guide-section" aria-labelledby="colour-title">
        <SectionHead eyebrow="01 · Foundation" title="Colour">
          A restrained spa palette with one warm accent reserved for totals.
        </SectionHead>
        <div className="swatch-grid">
          {colors.map(([token, value, use]) => (
            <article className="swatch" key={token}>
              <div
                className="swatch__colour"
                style={{ backgroundColor: `var(${token})` }}
              />
              <div className="swatch__copy">
                <strong>{token}</strong>
                <code>{value}</code>
                <span>{use}</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="guide-section">
        <SectionHead eyebrow="02 · Foundation" title="Typography">
          Inter with tabular numerals wherever time, price or data appears.
        </SectionHead>
        <div className="type-card">
          <div className="type-row">
            <span>Hero · 36 / 44</span>
            <p className="type-2xl">Make time for yourself.</p>
          </div>
          <div className="type-row">
            <span>Page title · 28 / 36</span>
            <p className="type-xl">Choose your treatment</p>
          </div>
          <div className="type-row">
            <span>Section title · 20 / 28</span>
            <p className="type-lg">Relaxation massage</p>
          </div>
          <div className="type-row">
            <span>Body · 16 / 24</span>
            <p className="type-md">Slow, flowing full-body massage to switch off.</p>
          </div>
          <div className="type-row">
            <span>Small · 14 / 20</span>
            <p className="type-sm">Kostenlose Stornierung bis 24 Stunden vorher</p>
          </div>
          <div className="type-row">
            <span>Tiny · 12 / 16</span>
            <p className="type-xs">TOTAL TIME</p>
          </div>
          <div className="type-row">
            <span>Price · 20 / 28</span>
            <p className="service-price">€65</p>
          </div>
          <div className="type-row">
            <span>Total · 24 / 32</span>
            <p className="total-price">€77</p>
          </div>
        </div>
      </section>

      <section className="guide-section foundation-pair">
        <div>
          <SectionHead eyebrow="03 · Foundation" title="Spacing" />
          <div className="token-card spacing-list">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((space) => (
              <div className="spacing-row" key={space}>
                <code>--space-{space}</code>
                <span className={`space-block space-block--${space}`} />
                <span>{[4, 8, 12, 16, 24, 32, 48, 64][space - 1]}px</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <SectionHead eyebrow="04 · Foundation" title="Shape & elevation" />
          <div className="token-card shape-grid">
            <div className="shape shape--sm">8px<br />--radius-sm</div>
            <div className="shape shape--md">12px<br />--radius</div>
            <div className="shape shape--lg">16px<br />--radius-lg</div>
            <div className="shape shape--pill">Pill<br />--radius-pill</div>
            <div className="shadow-sample">Card<br />--shadow</div>
            <div className="shadow-sample shadow-sample--lg">Dialog<br />--shadow-lg</div>
          </div>
        </div>
      </section>

      <section className="guide-section">
        <SectionHead eyebrow="05 · Foundation" title="Iconography">
          Simple 1.75px line icons, used only where they improve recognition.
        </SectionHead>
        <div className="icon-card">
          {(
            [
              "calendar",
              "clock",
              "user",
              "map",
              "phone",
              "envelope",
              "check",
              "close",
              "chevron-left",
              "chevron-right",
              "warning",
              "printer",
              "download",
            ] as IconName[]
          ).map((name) => (
            <div className="icon-sample" key={name}>
              <Icon name={name} size={24} />
              <span>{name}</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

function Field({
  label,
  state,
  value,
  error,
  optional,
}: {
  label: string;
  state: string;
  value?: string;
  error?: boolean;
  optional?: boolean;
}) {
  return (
    <label className="field">
      <span>
        {label} {optional && <em>(optional)</em>}
      </span>
      <input
        aria-invalid={error || undefined}
        className={state === "focus" ? "is-focus" : ""}
        defaultValue={value}
        disabled={state === "disabled"}
        type="text"
      />
      {error ? (
        <small className="field__error">
          <Icon name="warning" /> Please enter a valid email address
        </small>
      ) : (
        <small>We’ll send your confirmation here.</small>
      )}
    </label>
  );
}

function ComponentSheet() {
  return (
    <main id="main-content" className="page page--components">
      <section className="intro intro--compact">
        <p className="eyebrow">Slotwise · UI inventory</p>
        <h1>Component sheet</h1>
        <p>
          Responsive, accessible building blocks for customer and owner
          experiences. Every state is visible for implementation reference.
        </p>
      </section>

      <section className="guide-section">
        <SectionHead eyebrow="Actions" title="Buttons" />
        <div className="specimen-grid">
          <Specimen title="Primary" note="Normal and small sizes">
            <div className="states states--buttons">
              <State label="Normal"><button className="button">Confirm booking</button></State>
              <State label="Hover"><button className="button is-hover">Confirm booking</button></State>
              <State label="Focus"><button className="button is-focus">Confirm booking</button></State>
              <State label="Pressed"><button className="button is-pressed">Confirm booking</button></State>
              <State label="Disabled"><button className="button" disabled>Confirm booking</button></State>
              <State label="Loading"><button className="button" aria-busy="true">Booking…</button></State>
              <State label="Small"><button className="button button--small">Book now</button></State>
              <State label="Full width"><button className="button button--full">Buchung abschicken</button></State>
            </div>
          </Specimen>
          <Specimen title="Secondary & text">
            <div className="states states--buttons">
              <State label="Secondary"><button className="button button--ghost">Another day</button></State>
              <State label="Hover"><button className="button button--ghost is-hover">Another day</button></State>
              <State label="Focus"><button className="button button--ghost is-focus">Another day</button></State>
              <State label="Pressed"><button className="button button--ghost is-pressed">Another day</button></State>
              <State label="Disabled"><button className="button button--ghost" disabled>Another day</button></State>
              <State label="Loading"><button className="button button--ghost" aria-busy="true">Loading…</button></State>
              <State label="Text"><button className="button button--text">Classic look</button></State>
              <State label="Text hover"><button className="button button--text is-hover">Classic look</button></State>
              <State label="Text focus"><button className="button button--text is-focus">Classic look</button></State>
              <State label="Text disabled"><button className="button button--text" disabled>Classic look</button></State>
              <State label="Language"><button className="language-button">DE</button></State>
              <State label="Look switch"><button className="button button--text look-button"><Icon name="eye" /> Classic look</button></State>
            </div>
          </Specimen>
          <Specimen title="Danger & icon">
            <div className="states states--buttons">
              <State label="Danger"><button className="button button--danger">Cancel booking</button></State>
              <State label="Hover"><button className="button button--danger is-hover">Cancel booking</button></State>
              <State label="Focus"><button className="button button--danger is-focus">Cancel booking</button></State>
              <State label="Pressed"><button className="button button--danger is-pressed">Cancel booking</button></State>
              <State label="Disabled"><button className="button button--danger" disabled>Cancel booking</button></State>
              <State label="Loading"><button className="button button--danger" aria-busy="true">Cancelling…</button></State>
              <State label="Secondary"><button className="button button--danger-ghost">Cancel booking</button></State>
              <State label="Secondary hover"><button className="button button--danger-ghost is-hover">Cancel booking</button></State>
              <State label="Secondary focus"><button className="button button--danger-ghost is-focus">Cancel booking</button></State>
              <State label="Secondary disabled"><button className="button button--danger-ghost" disabled>Cancel booking</button></State>
              <State label="Close"><button aria-label="Close" className="icon-button"><Icon name="close" /></button></State>
              <State label="Previous / next"><div className="button-pair"><button aria-label="Previous" className="icon-button"><Icon name="chevron-left" /></button><button aria-label="Next" className="icon-button"><Icon name="chevron-right" /></button></div></State>
              <State label="Icon hover"><button aria-label="Close" className="icon-button is-hover"><Icon name="close" /></button></State>
              <State label="Icon focus"><button aria-label="Close" className="icon-button is-focus"><Icon name="close" /></button></State>
              <State label="Icon disabled"><button aria-label="Close" className="icon-button" disabled><Icon name="close" /></button></State>
            </div>
          </Specimen>
        </div>
      </section>

      <section className="guide-section">
        <SectionHead eyebrow="Forms" title="Fields and controls" />
        <div className="specimen-grid">
          <Specimen title="Text fields" note="The same treatment applies to email, phone, number, date and time." wide>
            <div className="field-grid">
              <State label="Empty"><Field label="Email address" state="empty" /></State>
              <State label="Filled"><Field label="Email address" state="filled" value="anna.mueller@example.com" /></State>
              <State label="Focus"><Field label="Phone" state="focus" value="+49 89 0000 0000" optional /></State>
              <State label="Disabled"><Field label="Email address" state="disabled" value="anna.mueller@example.com" /></State>
              <State label="Error"><Field label="Email address" state="error" value="anna.mueller@" error /></State>
              <State label="Textarea">
                <label className="field"><span>Note <em>(optional)</em></span><textarea defaultValue="Slow, flowing full-body massage to switch off." /><small>We’ll share this with the studio.</small></label>
              </State>
            </div>
          </Specimen>
          <Specimen title="Select" note="Empty, filled, focus, disabled and error states">
            <div className="states">
              <State label="Empty"><label className="field"><span>Therapist</span><select defaultValue=""><option value="">Select</option></select></label></State>
              <State label="Filled"><label className="field"><span>Therapist</span><select defaultValue="Lena"><option>Lena</option></select></label></State>
              <State label="Focus"><label className="field"><span>Therapist</span><select className="is-focus" defaultValue="Sofia"><option>Sofia</option></select></label></State>
              <State label="Disabled"><label className="field"><span>Therapist</span><select disabled defaultValue="Lena"><option>Lena</option></select></label></State>
              <State label="Error"><label className="field"><span>Therapist</span><select aria-invalid="true" defaultValue=""><option value="">Select</option></select><small className="field__error"><Icon name="warning" /> Please select a therapist</small></label></State>
            </div>
          </Specimen>
          <Specimen title="Checkbox">
            <div className="states">
              <State label="Unchecked"><label className="check-row"><input type="checkbox" /> Email confirmation</label></State>
              <State label="Checked"><label className="check-row"><input type="checkbox" defaultChecked /> Email confirmation</label></State>
              <State label="Focus"><label className="check-row is-focus"><input type="checkbox" /> Email confirmation</label></State>
              <State label="Disabled"><label className="check-row is-disabled"><input type="checkbox" disabled /> Email confirmation</label></State>
            </div>
          </Specimen>
          <Specimen title="Native date picker">
            <label className="field"><span>Another day</span><input type="date" defaultValue="2026-10-15" /></label>
          </Specimen>
        </div>
      </section>

      <section className="guide-section">
        <SectionHead eyebrow="Selection" title="Choices" />
        <div className="specimen-grid">
          <Specimen title="Option card" wide>
            <div className="option-list">
              <State label="Normal"><button className="option-card"><span className="fake-check" /><span className="option-card__copy"><strong>Deep tissue massage</strong><small>Firm pressure for tight muscles and knots.</small></span><span className="option-card__meta"><strong>€70</strong><small>60 min</small></span></button></State>
              <State label="Hover"><button className="option-card is-hover"><span className="fake-check" /><span className="option-card__copy"><strong>Back and neck massage</strong><small>Focused relief for desk shoulders.</small></span><span className="option-card__meta"><strong>€39</strong><small>30 min</small></span></button></State>
              <State label="Selected"><button className="option-card is-selected"><span className="fake-check"><Icon name="check" /></span><span className="option-card__copy"><strong>Hot stones</strong><small>Add-on</small></span><span className="option-card__meta"><strong>+€12</strong><small>+15 min</small></span></button></State>
              <State label="Focus"><button className="option-card is-focus"><span className="fake-check" /><span className="option-card__copy"><strong>Aromatherapy oil</strong><small>Add-on</small></span><span className="option-card__meta"><strong>+€5</strong><small>no extra time</small></span></button></State>
            </div>
          </Specimen>
          <Specimen title="Chips">
            <div className="states">
              <State label="Normal"><button className="chip">No preference</button></State>
              <State label="Hover"><button className="chip is-hover">Lena</button></State>
              <State label="Selected"><button className="chip is-selected">Sofia</button></State>
              <State label="Focus"><button className="chip is-focus">Gesichtsbehandlungen</button></State>
            </div>
          </Specimen>
          <Specimen title="Day chips">
            <div className="chip-row">
              <button className="day-chip is-selected"><small>Today</small><strong>15 Oct</strong></button>
              <button className="day-chip"><small>Tomorrow</small><strong>16 Oct</strong></button>
              <button className="day-chip"><small>Thu</small><strong>17 Oct</strong></button>
            </div>
          </Specimen>
          <Specimen title="Time slots" note="Four columns at mobile, six on desktop" wide>
            <div className="slot-grid">
              <button className="time-slot"><strong>09:00</strong><small>Lena</small></button>
              <button className="time-slot is-hover"><strong>10:15</strong><small>Sofia</small></button>
              <button className="time-slot is-selected"><strong>11:30</strong><small>Lena</small></button>
              <button className="time-slot is-focus"><strong>13:00</strong><small>Sofia</small></button>
              <button className="time-slot"><strong>14:15</strong><small>Lena</small></button>
              <button className="time-slot"><strong>16:30</strong><small>Sofia</small></button>
            </div>
          </Specimen>
          <Specimen title="Step markers">
            <div className="steps">
              <div className="step step--done"><span><Icon name="check" /></span><strong>Treatment</strong></div>
              <div className="step step--current"><span>2</span><strong>Therapist</strong></div>
              <div className="step"><span>3</span><strong>Day and time</strong></div>
            </div>
          </Specimen>
          <Specimen title="Segmented control">
            <div className="segmented" aria-label="Calendar view">
              <button className="is-selected">Day</button><button>Week</button><button>List</button>
            </div>
          </Specimen>
        </div>
      </section>

      <section className="guide-section">
        <SectionHead eyebrow="Feedback" title="Statuses and messages" />
        <div className="specimen-grid">
          <Specimen title="Booking badges" wide>
            <div className="status-groups">
              <div>
                <span className="state__label">Customer wording</span>
                <div className="badge-grid">
                  <StatusBadge tone="info">Awaiting your confirmation</StatusBadge>
                  <StatusBadge tone="warning">Booked</StatusBadge>
                  <StatusBadge tone="success">Confirmed</StatusBadge>
                  <StatusBadge tone="success" outlined>Completed</StatusBadge>
                  <StatusBadge tone="danger">Missed</StatusBadge>
                  <StatusBadge tone="danger">Cancelled</StatusBadge>
                  <StatusBadge tone="neutral">Not confirmed</StatusBadge>
                </div>
              </div>
              <div>
                <span className="state__label">Owner wording</span>
                <div className="badge-grid">
                  <StatusBadge tone="info">Awaiting email</StatusBadge>
                  <StatusBadge tone="warning">Booked</StatusBadge>
                  <StatusBadge tone="success">Confirmed</StatusBadge>
                  <StatusBadge tone="success" outlined>Done</StatusBadge>
                  <StatusBadge tone="danger">No-show</StatusBadge>
                  <StatusBadge tone="danger">Cancelled</StatusBadge>
                  <StatusBadge tone="neutral">Not confirmed</StatusBadge>
                  <StatusBadge tone="danger">Late cancellation</StatusBadge>
                </div>
              </div>
            </div>
          </Specimen>
          <Specimen title="Owner waitlist badges" wide>
            <div className="badge-grid">
              <StatusBadge tone="info">Awaiting email</StatusBadge>
              <StatusBadge tone="warning">Waiting</StatusBadge>
              <StatusBadge tone="success">Offered</StatusBadge>
              <StatusBadge tone="success" outlined>Booked</StatusBadge>
              <StatusBadge tone="neutral">Offer expired</StatusBadge>
              <StatusBadge tone="neutral">Removed / declined</StatusBadge>
            </div>
          </Specimen>
          <Specimen title="Goal badges">
            <div className="badge-grid badge-grid--stack">
              <span className="goal goal--success">✓ On target · goal &lt; 5%</span>
              <span className="goal goal--warning">▲ Off target · goal ≥ 50%</span>
              <span className="goal goal--neutral">No data yet</span>
            </div>
          </Specimen>
          <Specimen title="Alerts and notices" wide>
            <div className="notice-list">
              <div className="alert alert--danger"><Icon name="warning" /><span>That time was just taken. Please pick another.</span></div>
              <div className="alert alert--success"><Icon name="check" /><span>Your booking is confirmed.</span></div>
              <p className="notice">Loading the menu…</p>
              <p className="policy">Kostenlose Stornierung bis 24 Stunden vorher</p>
              <p className="policy policy--late">Late cancellation</p>
            </div>
          </Specimen>
          <Specimen title="Countdown">
            <div className="countdown"><span>24:13</span><small>left to claim</small></div>
            <div className="countdown countdown--danger"><Icon name="clock" /><span>04:51</span><small>left to claim</small></div>
          </Specimen>
          <Specimen title="Empty state">
            <div className="empty-state"><Icon name="calendar" size={24} /><p>No bookings in this range.</p></div>
          </Specimen>
          <Specimen title="Toast">
            <div className="toast-demo"><span>Settings saved</span></div>
          </Specimen>
          <Specimen title="Loading skeletons">
            <div className="skeletons" aria-busy="true"><span className="sr-only">Loading the menu…</span><div className="skeleton skeleton--card" /><div className="skeleton skeleton--row" /><div className="skeleton skeleton--tile" /></div>
          </Specimen>
        </div>
      </section>

      <section className="guide-section">
        <SectionHead eyebrow="Surfaces" title="Cards and structured data" />
        <div className="specimen-grid">
          <Specimen title="Standard card">
            <div className="card-demo"><p className="eyebrow">Massages</p><h4>Relaxation massage</h4><p>Slow, flowing full-body massage to switch off.</p><div className="service-meta"><strong>€65</strong><span>60 min</span></div></div>
          </Specimen>
          <Specimen title="Summary and item lines">
            <div className="summary-card">
              <h4>Booking summary</h4>
              <dl className="item-lines">
                <div><dt>Relaxation massage</dt><dd>€65</dd></div>
                <div className="item-lines__addon"><dt>+ Hot stones</dt><dd>€12</dd></div>
                <div className="item-lines__time"><dt>Total time</dt><dd>75 min</dd></div>
                <div className="item-lines__total"><dt>Total</dt><dd>€77</dd></div>
              </dl>
            </div>
          </Specimen>
          <Specimen title="Confirm card">
            <div className="confirm-card"><span className="confirm-icon"><Icon name="check" size={24} /></span><h4>Confirmed</h4><p>Your booking at Isar Wellness is confirmed.</p><button className="button button--full">Manage booking</button></div>
          </Specimen>
          <Specimen title="Facts list" wide>
            <dl className="facts">
              <div><dt>Date</dt><dd>15 Oct 2026</dd></div>
              <div><dt>Time</dt><dd>10:15</dd></div>
              <div><dt>Therapist</dt><dd>Lena</dd></div>
              <div><dt>Where</dt><dd>Isarstraße 12, 80469 München</dd></div>
            </dl>
          </Specimen>
          <Specimen title="Dashboard tiles" wide>
            <div className="tile-grid">
              <div className="dashboard-tile"><span>Bookings</span><strong>42</strong><small>Confirmed</small><span className="goal goal--success">✓ On target · goal &lt; 5%</span></div>
              <div className="dashboard-tile"><span>No-shows</span><strong>2</strong><small>This range</small><span className="goal goal--neutral">No data yet</span></div>
              <div className="dashboard-tile"><span>Late cancellations</span><strong>4</strong><small>This range</small><span className="goal goal--warning">▲ Off target · goal ≥ 50%</span></div>
            </div>
          </Specimen>
          <Specimen title="Data table" note="Scrolls horizontally on small screens" wide>
            <div className="table-scroll">
              <table>
                <thead><tr><th>Customer</th><th>Treatment</th><th>Status</th><th>Date</th><th className="number">Total</th></tr></thead>
                <tbody>
                  <tr><td>Anna Müller</td><td>Relaxation massage</td><td><StatusBadge tone="success">Confirmed</StatusBadge></td><td>15 Oct · 10:15</td><td className="number">€77</td></tr>
                  <tr><td>Ben Fischer ⚠</td><td>Deep tissue massage</td><td><StatusBadge tone="danger">No-show</StatusBadge></td><td>15 Oct · 11:30</td><td className="number">€70</td></tr>
                  <tr className="is-inactive"><td>Priya Shah</td><td>Classic facial</td><td><StatusBadge tone="neutral">Cancelled</StatusBadge></td><td>16 Oct · 09:00</td><td className="number">€59</td></tr>
                </tbody>
              </table>
            </div>
          </Specimen>
        </div>
      </section>

      <section className="guide-section">
        <SectionHead eyebrow="Overlays" title="Dialog and mobile surfaces" />
        <div className="specimen-grid">
          <Specimen title="Side panel" note="480px desktop panel; full screen on mobile" wide>
            <div className="dialog-stage">
              <div className="dialog-backdrop" />
              <aside className="dialog-panel" aria-label="Booking details">
                <header><div><p className="eyebrow">IW-2026-0042</p><h3>Booking details</h3></div><button className="icon-button" aria-label="Close"><Icon name="close" /></button></header>
                <div className="dialog-panel__body">
                  <StatusBadge tone="success">Confirmed</StatusBadge>
                  <dl className="facts facts--stack"><div><dt>Customer</dt><dd>Anna Müller</dd></div><div><dt>Treatment</dt><dd>Relaxation massage</dd></div><div><dt>Time</dt><dd>15 Oct 2026 · 10:15</dd></div></dl>
                </div>
              </aside>
            </div>
          </Specimen>
          <Specimen title="Mobile summary bar" wide>
            <div className="summary-bar"><div><span>Total</span><strong>€77</strong></div><button className="button">Continue</button></div>
          </Specimen>
        </div>
      </section>
    </main>
  );
}

export default function App() {
  const [view, setView] = useState<"guide" | "components" | "screens" | "owner">("guide");

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="site-header">
        <div className="brand" aria-label="Slotwise">
          <svg aria-hidden="true" viewBox="0 0 32 32">
            <path d="M26 5C15 6 7 12 6 24c7 2 15-2 18-9 2-4 2-8 2-10Z" />
            <path d="M7 24c4-5 9-9 16-13" />
          </svg>
          <span>Slotwise</span>
        </div>
        <nav aria-label="Reference pages" className="page-tabs">
          <button className={view === "guide" ? "is-active" : ""} onClick={() => setView("guide")}>Style guide</button>
          <button className={view === "components" ? "is-active" : ""} onClick={() => setView("components")}>Components</button>
          <button className={view === "screens" ? "is-active" : ""} onClick={() => setView("screens")}>Customer screens</button>
          <button className={view === "owner" ? "is-active" : ""} onClick={() => setView("owner")}>Owner screens</button>
        </nav>
        <div className="header-note">
          <span>Isar Wellness</span>
          <span>Design reference · v1</span>
        </div>
      </header>
      {view === "guide" ? <StyleGuide /> : view === "components" ? <ComponentSheet /> : view === "screens" ? <CustomerScreens /> : <OwnerScreens />}
      <footer className="site-footer">
        <span>Slotwise · Calm modern</span>
        <span>Mobile 390 · Desktop 1440</span>
      </footer>
    </>
  );
}
