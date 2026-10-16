import { useMemo, useState, type ReactNode } from "react";

type ScreenId = "home" | "book" | "book-de" | "result" | "manage" | "offer" | "waitlist" | "receipt" | "flows";

type MiniIconName = "leaf" | "phone" | "clock" | "check" | "envelope" | "warning" | "printer" | "chevron";

function MiniIcon({ name, size = 20 }: { name: MiniIconName; size?: number }) {
  const paths: Record<MiniIconName, ReactNode> = {
    leaf: (
      <>
        <path className="fill-path" d="M21 4C12 5 6 10 5 20c6 2 13-1 16-7 1-4 1-7 0-9Z" />
        <path d="M6 20c4-5 8-8 14-12" />
      </>
    ),
    phone: <path d="M7.2 3h3l1.5 4-2 1.5a15 15 0 0 0 5.8 5.8l1.5-2 4 1.5v3A3.2 3.2 0 0 1 17.8 20C10.2 19.5 4.5 13.8 4 6.2A3.2 3.2 0 0 1 7.2 3Z" />,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    envelope: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m4 7 8 6 8-6" /></>,
    warning: <><path d="M12 3 2.5 20h19L12 3Z" /><path d="M12 9v5m0 3h.01" /></>,
    printer: <><path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" /><path d="M6 14h12v7H6z" /></>,
    chevron: <path d="m9 6 6 6-6 6" />,
  };
  return <svg aria-hidden="true" className="c-icon" width={size} height={size} viewBox="0 0 24 24" fill="none">{paths[name]}</svg>;
}

const menu = [
  {
    category: "Massages",
    services: [
      { name: "Relaxation massage", description: "Slow, flowing full-body massage to switch off.", price: "€65", duration: "60 min", addons: ["+ Hot stones · +15 min · €12", "+ Aromatherapy oil · €5"] },
      { name: "Deep tissue massage", description: "Firm pressure for tight muscles and knots.", price: "€70", duration: "60 min", addons: ["+ Hot stones · +15 min · €12", "+ Aromatherapy oil · €5"] },
      { name: "Back and neck massage", description: "Focused relief for desk shoulders.", price: "€39", duration: "30 min", addons: ["+ Hot stones · +15 min · €12", "+ Aromatherapy oil · €5"] },
    ],
  },
  {
    category: "Facials",
    services: [
      { name: "Classic facial", description: "Cleanse, exfoliate, mask and moisturise.", price: "€59", duration: "45 min", addons: ["+ Eye mask treatment · +10 min · €9"] },
      { name: "Express facial", description: "A quick refresh for busy days.", price: "€39", duration: "30 min", addons: ["+ Eye mask treatment · +10 min · €9"] },
    ],
  },
  {
    category: "Reflexology",
    services: [
      { name: "Foot reflexology", description: "Pressure-point foot treatment.", price: "€42", duration: "30 min", addons: [] },
    ],
  },
];

const screenStates: Record<ScreenId, { value: string; label: string }[]> = {
  home: [
    { value: "default", label: "Default" }, { value: "loading", label: "Loading" },
    { value: "empty", label: "Empty menu" }, { value: "error", label: "Menu error" },
    { value: "studio-error", label: "Studio details error" },
  ],
  book: [
    { value: "start", label: "(a) Start" }, { value: "chosen", label: "(b) Treatment chosen" },
    { value: "times-loading", label: "(c) Times loading" }, { value: "selected", label: "(d) Time chosen" },
    { value: "submitting", label: "(e) Submitting" }, { value: "fields", label: "(f) Field errors" },
    { value: "name-error", label: "Name validation error" }, { value: "note-error", label: "Note validation error" },
    { value: "therapist-error", label: "No therapist combination" },
    { value: "general", label: "(g) Time just taken" }, { value: "general-window", label: "Time outside booking window" },
    { value: "general-rate", label: "Too many bookings" }, { value: "general-offered", label: "Time not offered" },
    { value: "general-service", label: "Treatment unavailable" }, { value: "general-network", label: "Connection error" },
    { value: "waitlist", label: "(h) Waitlist" },
    { value: "waitlist-missing", label: "Waitlist · details missing" }, { value: "waitlist-success", label: "Waitlist · success" },
    { value: "waitlist-error", label: "Waitlist · invalid range" }, { value: "waitlist-limit", label: "Waitlist · request limit" },
    { value: "waitlist-provider", label: "Waitlist · no provider" }, { value: "waitlist-joining", label: "Waitlist · joining" },
    { value: "menu-error", label: "(i) Menu error" },
  ],
  "book-de": [
    { value: "start", label: "Start" }, { value: "chosen", label: "Behandlung gewählt" },
    { value: "selected", label: "Zeit gewählt" }, { value: "waitlist", label: "Warteliste" },
  ],
  result: [
    { value: "pending", label: "Pending" }, { value: "booked", label: "Booked" },
    { value: "missing", label: "Details missing" }, { value: "loading", label: "Loading" },
  ],
  manage: [
    { value: "awaiting", label: "Awaiting confirmation" }, { value: "booked", label: "Booked" },
    { value: "confirmed", label: "Just confirmed" }, { value: "verified", label: "Email verified" },
    { value: "cancel-open", label: "Cancel question" }, { value: "late-cancel", label: "Late cancel question" },
    { value: "cancelled", label: "Just cancelled" }, { value: "cancelled-late", label: "Cancelled late" },
    { value: "expired", label: "Not confirmed" }, { value: "completed", label: "Completed + receipt" },
    { value: "missed", label: "Missed" }, { value: "failed", label: "Action failed" },
    { value: "failed-finished", label: "Action failed · finished" },
    { value: "not-found", label: "Not found" }, { value: "incomplete", label: "Incomplete link" },
    { value: "request-expired", label: "Expired request" }, { value: "loading", label: "Loading" },
    { value: "busy", label: "Busy" },
  ],
  offer: [
    { value: "default", label: "Offer" }, { value: "urgent", label: "Under 5 minutes" },
    { value: "error", label: "Error" }, { value: "claimed", label: "Claimed" },
    { value: "declined", label: "Declined" }, { value: "expired", label: "Expired" },
    { value: "already", label: "Already claimed" }, { value: "not-found", label: "Not found" },
    { value: "loading", label: "Loading" }, { value: "busy", label: "Busy" },
  ],
  waitlist: [
    { value: "loading", label: "Loading" }, { value: "success", label: "Success" },
    { value: "handled", label: "Already handled" }, { value: "failed", label: "Failed" },
    { value: "limit", label: "Five-request limit" },
  ],
  receipt: [
    { value: "customer", label: "Customer receipt" }, { value: "owner", label: "Owner receipt" },
    { value: "loading", label: "Loading" }, { value: "none", label: "No receipt yet" },
    { value: "not-found", label: "Not found" },
  ],
  flows: [{ value: "all", label: "All flows" }],
};

function CustomerHeader({ action, german = false }: { action?: "book" | "menu" | "again"; german?: boolean }) {
  const label = action === "book" ? (german ? "Jetzt buchen" : "Book now") : action === "menu" ? (german ? "Zurück zum Menü" : "Back to menu") : action === "again" ? (german ? "Erneut buchen" : "Book again") : "";
  return (
    <header className="c-header">
      <a className="c-brand" href="#" aria-label="Isar Wellness home"><MiniIcon name="leaf" size={28} /><span>Isar Wellness</span></a>
      <div className="c-header__actions">
        <button className="language-button">{german ? "EN" : "DE"}</button>
        <button className="button button--text button--small c-classic">{german ? "Klassisches Design" : "Classic look"}</button>
        {action && <button className={`button button--small ${action === "menu" ? "button--ghost" : ""}`}>{label}</button>}
      </div>
    </header>
  );
}

function CustomerFooter() {
  return <footer className="c-footer"><span>Online booking by <MiniIcon name="leaf" /> <strong>Slotwise</strong></span><a href="#">Studio login</a></footer>;
}

function BookingFacts({ offer = false }: { offer?: boolean }) {
  return (
    <dl className="facts c-facts">
      <div><dt>Date</dt><dd>{offer ? "Thursday 15 October" : "Tuesday 13 October 2026"}</dd></div>
      <div><dt>Time</dt><dd>{offer ? "11:00 (60 min)" : "10:00 (75 min)"}</dd></div>
      <div><dt>Therapist</dt><dd>{offer ? "Sofia" : "Lena"}</dd></div>
      <div><dt>Where</dt><dd>Isarstraße 12, 80469 München</dd></div>
    </dl>
  );
}

function BookingLines({ offer = false }: { offer?: boolean }) {
  return (
    <dl className="item-lines c-lines">
      <div><dt>{offer ? "Relaxation massage" : "Deep tissue massage"}</dt><dd>{offer ? "€65" : "€70"}</dd></div>
      <div className="item-lines__addon"><dt>+ {offer ? "Aromatherapy oil" : "Hot stones"}</dt><dd>{offer ? "€5" : "€12"}</dd></div>
      <div className="item-lines__total"><dt>Total</dt><dd>{offer ? "€70" : "€82"}</dd></div>
    </dl>
  );
}

function Status({ tone, children, outlined = false }: { tone: string; children: ReactNode; outlined?: boolean }) {
  return <span className={`badge badge--${tone} ${outlined ? "badge--outlined" : ""}`}><span className="badge__dot" />{children}</span>;
}

function ResultShell({ children, action }: { children: ReactNode; action?: "again" }) {
  return <div className="c-screen"><CustomerHeader action={action} /><main className="c-result-wrap">{children}</main></div>;
}

function SimpleResult({ title, text, button = "Back to home", icon }: { title: string; text?: string; button?: string; icon?: "check" | "envelope" }) {
  return (
    <div className="confirm-card c-result-card">
      {icon && <span className="c-result-icon"><MiniIcon name={icon} size={28} /></span>}
      <h1>{title}</h1>
      {text && <p className="c-muted">{text}</p>}
      <button className="button button--full">{button}</button>
    </div>
  );
}

function HomeScreen({ state }: { state: string }) {
  const studioFailed = state === "studio-error";
  return (
    <div className="c-screen">
      <CustomerHeader action="book" />
      <main className="c-home">
        <section className="c-studio">
          <p className="eyebrow">Munich · Day spa</p>
          <h1>{studioFailed ? "Book online" : "Isar Wellness"}</h1>
          {!studioFailed && <>
            <dl className="c-studio-facts">
              <div><dt>Address</dt><dd>Isarstraße 12, 80469 München</dd></div>
              <div><dt>Phone</dt><dd><a href="tel:+498900000000"><MiniIcon name="phone" /> +49 89 0000 0000</a></dd></div>
              <div><dt>Hours</dt><dd><span>Mon 10:00–19:00</span><span>Tue–Fri 9:00–19:00</span><span>Sat 9:00–17:00</span><span>Sun closed</span></dd></div>
            </dl>
            <p className="policy c-policy"><MiniIcon name="clock" /> Free cancellation up to 24 hours before</p>
          </>}
        </section>

        <section className="c-menu" aria-label="Treatment menu">
          {state === "loading" && <><span className="sr-only">Loading the menu…</span>{[1,2,3].map((n) => <div className="skeleton c-service-skeleton" key={n} />)}</>}
          {state === "empty" && <div className="empty-state"><p>The menu is being prepared. Please call us to book.</p></div>}
          {state === "error" && <div className="alert alert--danger"><MiniIcon name="warning" /><span>Could not load the menu. Please refresh.</span></div>}
          {!["loading", "empty", "error"].includes(state) && menu.map((category) => (
            <section className="c-menu-section" key={category.category}>
              <h2>{category.category}</h2>
              <div className="c-service-list">
                {category.services.map((service) => (
                  <article className="c-service-card" key={service.name}>
                    <div className="c-service-card__main">
                      <div><h3>{service.name}</h3><p>{service.description}</p></div>
                      <div className="c-service-card__price"><strong>{service.price}</strong><span>{service.duration}</span></div>
                    </div>
                    {service.addons.length > 0 && <ul>{service.addons.map((addon) => <li key={addon}>{addon}</li>)}</ul>}
                    <button className="button button--ghost button--small" aria-label={`Book ${service.name}`}>Book</button>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </section>
        <details className="c-manage-details"><summary>Manage my booking <MiniIcon name="chevron" /></summary><p>Open the link in your confirmation email to view, confirm or cancel your booking and to see your receipt.</p></details>
      </main>
      <CustomerFooter />
    </div>
  );
}

const dayLabels = [["Today","13 Oct"],["Tomorrow","14 Oct"],["Thu","15 Oct"],["Fri","16 Oct"],["Sat","17 Oct"],["Sun","18 Oct"],["Mon","19 Oct"],["Tue","20 Oct"],["Wed","21 Oct"],["Thu","22 Oct"],["Fri","23 Oct"],["Sat","24 Oct"],["Sun","25 Oct"],["Mon","26 Oct"]];
const times = ["10:00", "10:15", "10:30", "11:45", "12:00", "13:15", "14:00", "14:15", "15:30", "16:00", "16:15", "17:30"];

function Step({ number, title, active = false, children }: { number: number; title: string; active?: boolean; children: ReactNode }) {
  return <section className="c-book-step"><div className={`step ${active ? "step--current" : "step--done"}`}><span>{active ? number : <MiniIcon name="check" />}</span><h2>{title}</h2></div><div className="c-step-body">{children}</div></section>;
}

function TreatmentOption({ name, price, duration, selected = false, second }: { name: string; price: string; duration: string; selected?: boolean; second?: string }) {
  return <button className={`option-card ${selected ? "is-selected" : ""}`}><span className="fake-check">{selected && <MiniIcon name="check" />}</span><span className="option-card__copy"><strong>{name}</strong>{second && <small>{second}</small>}</span><span className="option-card__meta"><strong>{price}</strong><small>{duration}</small></span></button>;
}

function DetailsForm({ errors = false, nameError = false, noteError = false, german = false }: { errors?: boolean; nameError?: boolean; noteError?: boolean; german?: boolean }) {
  return (
    <div className="c-details-grid">
      <label className="field"><span>{german ? "Vorname" : "First name"}</span><input defaultValue="Anna" />{errors && <small className="field__error"><MiniIcon name="warning" /> Please enter your first name.</small>}</label>
      <label className="field"><span>{german ? "Nachname" : "Last name"}</span><input aria-invalid={nameError || undefined} defaultValue={nameError ? "Müller2" : "Müller"} />{nameError && <small className="field__error"><MiniIcon name="warning" /> Please use only letters in your name.</small>}</label>
      <label className="field"><span>Email</span><input aria-invalid={errors || undefined} defaultValue={errors ? "anna.mueller@" : "anna.mueller@example.com"} />{errors && <small className="field__error"><MiniIcon name="warning" /> Please enter a valid email address</small>}</label>
      <label className="field"><span>{german ? "Telefon" : "Phone"}</span><input aria-invalid={errors || undefined} defaultValue={errors ? "" : "+49 89 0000 0000"} />{errors && <small className="field__error"><MiniIcon name="warning" /> Please enter your phone number.</small>}</label>
      <label className="field c-details-note"><span>{german ? "Notiz für Ihre Therapeutin (optional)" : "Note for your therapist (optional)"}</span><textarea aria-invalid={noteError || undefined} maxLength={300} />{noteError ? <small className="field__error"><MiniIcon name="warning" /> Please keep the note under 300 characters.</small> : <small>Please don't enter medical details. Max 300 characters.</small>}</label>
    </div>
  );
}

// 07:00 to 21:00 in 30-minute steps (book.js timeOptions()).
const waitlistTimes = Array.from({ length: 29 }, (_, i) => `${String(7 + Math.floor(i / 2)).padStart(2, "0")}:${i % 2 ? "30" : "00"}`);

function WaitlistBox({ state, german }: { state: string; german: boolean }) {
  const joining = state === "waitlist-joining";
  return (
    <div className="c-waitlist-wrap">
      <div className="notice">{german ? "An diesem Tag ist keine Zeit frei. Wählen Sie einen anderen Tag oder tragen Sie sich unten auf die Warteliste ein." : "No free times on this day. Try another day, or join the waitlist below."}</div>
      <div className="c-waitlist-card">
        <h3>{german ? "Auf die Warteliste" : "Join the waitlist"}</h3>
        <p>{german ? "Sagen Sie uns, wann Sie kommen könnten. Wenn jemand absagt, erhält die erste Person auf der Liste eine E-Mail und kann den Termin buchen." : "Tell us when you could come. If someone cancels, the first person on the list gets an email and can claim the time."}</p>
        <div className="c-time-range">
          <span>{german ? "Zwischen" : "Between"}</span>
          <label className="sr-only" htmlFor="earliest">Earliest start</label><select id="earliest" defaultValue="09:00">{waitlistTimes.map(t => <option key={t}>{t}</option>)}</select>
          <span>{german ? "und" : "and"}</span>
          <label className="sr-only" htmlFor="latest">Latest start</label><select id="latest" defaultValue="18:00">{waitlistTimes.map(t => <option key={t}>{t}</option>)}</select>
        </div>
        <small>Uses your details from step 6.</small>
        <button className="button" disabled={joining}>{german ? "Auf die Warteliste setzen" : "Join the waitlist"}</button>
        {state === "waitlist-missing" && <p className="c-error-line">Please fill in your details below first.</p>}
        {state === "waitlist-success" && <div className="alert alert--success"><MiniIcon name="check" />Almost done! We've emailed anna.mueller@example.com a link. Click it to confirm your place on the waitlist for this day.</div>}
        {state === "waitlist-error" && <p className="c-error-line">Please choose an earliest time before the latest time.</p>}
        {state === "waitlist-limit" && <p className="c-error-line">You already have 5 open waitlist requests. Please call the studio to change them.</p>}
        {state === "waitlist-provider" && <p className="c-error-line">Nobody offers this treatment on that day, so no time can free up.</p>}
      </div>
    </div>
  );
}

function BookingSummary({ state, german, mobile = false }: { state: string; german: boolean; mobile?: boolean }) {
  const started = state !== "start" && state !== "menu-error";
  // "general" = "That time was just taken": the times reload with no slot picked, so confirming is disabled again.
  const complete = ["selected", "submitting", "fields", "name-error", "note-error"].includes(state) || (state.startsWith("general") && state !== "general");
  const loading = state === "submitting";
  const when = !started ? (german ? "Wählen Sie zuerst eine Behandlung." : "Choose a treatment to start.") : complete ? (german ? "Dienstag, 13. Oktober um 10:00 bei Lena" : "Tuesday 13 October at 10:00 with Lena") : state === "times-loading" || state === "general" ? (german ? "Dienstag, 13. Oktober, Uhrzeit wählen" : "Tuesday 13 October, pick a time") : (german ? "Tag und Uhrzeit wählen" : "Pick a day and time");
  if (mobile) return <div className="c-mobile-summary"><button className="c-mobile-summary__text">{started ? <>{german ? "2 Positionen · 75 Min. · " : "2 items · 75 min · "}<strong>{german ? "82 €" : "€82"}</strong></> : when}</button><button className="button" disabled={!complete || loading}>{loading ? "Booking…" : german ? "Buchung abschicken" : "Confirm booking"}</button></div>;
  return (
    <aside className="summary-card c-book-summary" id="booking-summary">
      <h3>{german ? "Ihre Buchung" : "Your booking"}</h3>
      <p className="c-summary-when">{when}</p>
      {started && <><dl className="item-lines"><div><dt>Deep tissue massage</dt><dd>{german ? "70 €" : "€70"}</dd></div><div className="item-lines__addon"><dt>+ Hot stones</dt><dd>{german ? "12 €" : "€12"}</dd></div><div className="item-lines__time"><dt>{german ? "Gesamtdauer" : "Total time"}</dt><dd>{german ? "75 Min." : "75 min"}</dd></div><div className="item-lines__total"><dt>Total</dt><dd>{german ? "82 €" : "€82"}</dd></div></dl><p className="c-pay">{german ? "Bezahlung im Studio" : "Pay at the studio"}</p></>}
      {state.startsWith("general") && <div className="alert alert--danger"><MiniIcon name="warning" /><span>{({
        general: "That time was just taken. Please pick another.",
        "general-window": "Please choose a time between 2 hours and 60 days from now.",
        "general-rate": "Too many bookings in a short time. Please call the studio.",
        "general-offered": "Please pick one of the offered times.",
        "general-service": "One of the chosen treatments is no longer available. Please refresh.",
        "general-network": "Could not reach the server. Please check your connection.",
      } as Record<string,string>)[state]}</span></div>}
      <button className="button button--full c-desktop-confirm" disabled={!complete || loading}>{loading ? "Booking…" : german ? "Buchung abschicken" : "Confirm booking"}</button>
    </aside>
  );
}

function BookScreen({ state, german = false }: { state: string; german?: boolean }) {
  const start = state === "start" || state === "menu-error";
  const dayPicked = ["times-loading", "selected", "submitting", "fields", "name-error", "note-error", "therapist-error", "waitlist", "waitlist-missing", "waitlist-success", "waitlist-error", "waitlist-limit", "waitlist-provider", "waitlist-joining"].includes(state) || state.startsWith("general");
  const selected = ["selected", "submitting", "fields", "name-error", "note-error"].includes(state);
  const waitlist = state.startsWith("waitlist");
  return (
    <div className="c-screen c-book-screen">
      <CustomerHeader action="menu" german={german} />
      <main className="c-book-page">
        <div className="c-book-intro"><h1>{german ? "Behandlung buchen" : "Book a treatment"}</h1><p>{german ? "Wählen Sie Ihre Behandlung, eine Therapeutin und eine freie Zeit. Bezahlt wird im Studio." : "Choose your treatment, a therapist and a free time. You pay at the studio."}</p></div>
        <div className="c-book-layout">
          <div className="c-book-form">
            <Step number={1} title={german ? "Behandlungen" : "Treatments"} active={start}>
              {state === "menu-error" ? <div className="notice">Could not load services.</div> : <>
                <h3>Massages</h3>
                <div className="c-option-stack">
                  <TreatmentOption name="Relaxation massage" price={german ? "65 €" : "€65"} duration="60 min" />
                  <TreatmentOption name="Deep tissue massage" price={german ? "70 €" : "€70"} duration="60 min" selected={!start} />
                  <TreatmentOption name="Back and neck massage" price={german ? "39 €" : "€39"} duration="30 min" />
                </div>
                <h3>Facials</h3>
                <div className="c-option-stack"><TreatmentOption name="Classic facial" price={german ? "59 €" : "€59"} duration="45 min" /><TreatmentOption name="Express facial" price={german ? "39 €" : "€39"} duration="30 min" /></div>
                <h3>Reflexology</h3>
                <div className="c-option-stack"><TreatmentOption name="Foot reflexology" price={german ? "42 €" : "€42"} duration="30 min" /></div>
              </>}
            </Step>
            {!start && <>
              <Step number={2} title={german ? "Extras (optional)" : "Add-ons (optional)"}>
                <div className="c-option-stack"><TreatmentOption name="Hot stones" price={german ? "+12 €" : "+€12"} duration="+15 min" selected second="with Deep tissue massage" /><TreatmentOption name="Aromatherapy oil" price={german ? "+5 €" : "+€5"} duration={german ? "keine zusätzliche Zeit" : "no extra time"} second="with Deep tissue massage" /></div>
              </Step>
              <Step number={3} title={german ? "Therapeutin" : "Therapist"}>
                <div className="chip-row"><button className="chip" title="The first available therapist">{german ? "Keine Präferenz" : "No preference"}</button><button className={`chip ${selected ? "is-selected" : ""}`} title="Massages and foot reflexology">Lena</button><button className="chip" title="Facials and relaxation massage">Sofia</button></div>
                {state === "therapist-error" && <p className="c-error-line">No therapist offers this combination. Please remove a service.</p>}
              </Step>
              <Step number={4} title={german ? "Tag" : "Day"}>
                <div className="c-day-scroll">{dayLabels.map(([top,bottom], index) => <button className={`day-chip ${dayPicked && index === 0 ? "is-selected" : ""}`} key={bottom}><small>{german && top === "Today" ? "Heute" : german && top === "Tomorrow" ? "Morgen" : top}</small><strong>{bottom}</strong></button>)}</div>
                <label className="field c-date-field"><span>{german ? "Anderer Tag" : "Another day"}</span><input type="date" min="2026-10-13" max="2026-12-12" /></label>
              </Step>
              <Step number={5} title={german ? "Uhrzeit" : "Time"} active={!dayPicked}>
                {!dayPicked && <p className="notice">{german ? "Wählen Sie einen Tag, um freie Zeiten zu sehen." : "Pick a day to see free times."}</p>}
                {state === "times-loading" && <div><p className="notice">Looking for free times…</p><div className="slot-grid">{times.slice(0,8).map(t => <div className="skeleton c-slot-skeleton" key={t} />)}</div></div>}
                {dayPicked && !waitlist && state !== "times-loading" && <div className="slot-grid">{times.map((time,index) => <button className={`time-slot ${selected && index === 0 ? "is-selected" : ""}`} key={time}><strong>{time}</strong><small>{index % 2 ? "Sofia" : "Lena"}</small></button>)}</div>}
                {waitlist && <WaitlistBox state={state} german={german} />}
              </Step>
              <Step number={6} title={german ? "Ihre Angaben" : "Your details"}><DetailsForm errors={state === "fields"} nameError={state === "name-error"} noteError={state === "note-error"} german={german} /></Step>
              <div className="c-mobile-full-summary"><BookingSummary state={state} german={german} /></div>
            </>}
          </div>
          <div className="c-desktop-summary"><BookingSummary state={state} german={german} /></div>
        </div>
      </main>
      <div className="c-mobile-summary-wrap"><BookingSummary state={state} german={german} mobile /></div>
    </div>
  );
}

function ResultScreen({ state }: { state: string }) {
  if (state === "loading") return <ResultShell><SimpleResult title="Loading your booking…" /></ResultShell>;
  if (state === "missing") return <ResultShell><SimpleResult title="Booking details not available" text="Your booking may still have gone through. Please check with the studio if you're unsure." /></ResultShell>;
  const pending = state === "pending";
  return (
    <ResultShell>
      <article className="confirm-card c-result-card">
        <span className="c-result-icon"><MiniIcon name={pending ? "envelope" : "check"} size={28} /></span>
        <h1>{pending ? "Almost done, Anna!" : "You're booked, Anna!"}</h1>
        <div className="alert alert--success"><MiniIcon name="check" /><span>{pending ? "We've emailed you a link. Click it to confirm your booking by 14:35; until then we're holding the time for you." : "A confirmation has been emailed to you. Use the link in your email to confirm, cancel or view your receipt."}</span></div>
        <BookingFacts /><BookingLines />
        <p className="c-pay">Pay at the studio</p>
        {pending && <p className="c-muted">No email? Check your spam folder. If you don't confirm in time, the time is released for others.</p>}
        <button className="button button--full">Back to home</button>
      </article>
    </ResultShell>
  );
}

function ManageScreen({ state }: { state: string }) {
  if (state === "loading") return <ResultShell action="again"><SimpleResult title="Loading your booking…" /></ResultShell>;
  const missing: Record<string,string> = {
    "not-found": "Booking not found. Please check the link in your email.",
    incomplete: "This link is incomplete. Please use the link in your confirmation email.",
    "request-expired": "This booking request has expired because it wasn't confirmed in time. Please book again.",
  };
  if (missing[state]) return <ResultShell action="again"><SimpleResult title="Booking not found" text={missing[state]} /></ResultShell>;
  const status = state === "awaiting" ? ["info","Awaiting your confirmation"] : state === "booked" || state === "cancel-open" || state === "late-cancel" || state === "busy" || state === "failed" || state === "failed-finished" ? ["warning","Booked"] : state === "confirmed" || state === "verified" ? ["success","Confirmed"] : state === "expired" ? ["neutral","Not confirmed"] : state === "completed" ? ["success","Completed"] : state === "missed" ? ["danger","Missed"] : ["danger","Cancelled"];
  const active = ["awaiting","booked","cancel-open","late-cancel","busy","failed","failed-finished"].includes(state);
  const cancelOpen = state === "cancel-open" || state === "late-cancel";
  const late = state === "late-cancel" || state === "cancelled-late";
  const busy = state === "busy";
  return (
    <ResultShell action="again">
      <article className="confirm-card c-result-card">
        {state === "confirmed" && <div className="alert alert--success"><MiniIcon name="check" />Thank you! Your booking is confirmed. See you soon.</div>}
        {state === "verified" && <div className="alert alert--success"><MiniIcon name="check" />Thank you! Your booking is confirmed, and we've emailed you the details.</div>}
        {(state === "cancelled" || state === "cancelled-late") && <div className="alert alert--success"><MiniIcon name="check" />Your booking is cancelled{late ? " (late cancellation)." : "."}</div>}
        {(state === "failed" || state === "failed-finished") && <div className="alert alert--danger"><MiniIcon name="warning" />{state === "failed" ? "This booking can no longer be confirmed." : "This booking is already cancelled or finished."}</div>}
        <Status tone={status[0]} outlined={state === "completed"}>{status[1]}</Status>
        <h1>Your booking</h1>
        <BookingFacts /><BookingLines />
        {state === "completed" ? <p className="c-receipt-line"><strong>Receipt IW-2026-0042</strong><a href="#">View or print receipt</a></p> : <p className="c-pay">Pay at the studio</p>}
        {(state === "cancelled" || state === "cancelled-late") && <p className="c-muted">This booking was cancelled{late ? " late" : ""}.</p>}
        {state === "expired" && <p className="c-muted">This booking request wasn't confirmed in time, so the time was released.</p>}
        <div className="c-action-stack">
          {state === "awaiting" && <button className="button" disabled={busy}>Confirm my booking</button>}
          {state === "booked" || state === "busy" || state === "failed" || state === "failed-finished" ? <button className="button" disabled={busy}>Confirm I'm coming</button> : null}
          {active && !cancelOpen && <button className="button button--danger-ghost" disabled={busy}>Cancel booking</button>}
          {cancelOpen && <div className="c-cancel-box"><p>{late ? "Are you sure? This counts as a late cancellation." : "Are you sure you want to cancel?"}</p><div><button className="button button--danger">Yes, cancel booking</button><button className="button button--ghost">Keep my booking</button></div></div>}
          <button className="button button--ghost" disabled={busy}>Book again</button>
        </div>
        {active && <p className={`policy ${late ? "policy--late" : ""}`}>{late ? "Free cancellation has ended. You can still cancel, but it counts as a late cancellation." : "Free cancellation until Mon 12 Oct, 10:00."}</p>}
      </article>
    </ResultShell>
  );
}

function OfferScreen({ state }: { state: string }) {
  if (state === "loading") return <ResultShell><SimpleResult title="Loading the offer…" /></ResultShell>;
  const simple: Record<string,[string,string]> = {
    claimed: ["You're booked, Anna!", "Thursday 15 October at 11:00 with Sofia. A confirmation with your booking link has been emailed to you.\nTotal €70 · Pay at the studio"],
    declined: ["No problem", "We've offered the time to the next person on the waitlist."],
    expired: ["Sorry, this offer has expired.", "The time has gone to the next person on the waitlist."],
    already: ["Already claimed", "This time has already been booked through this link."],
    "not-found": ["Offer not found", "Offer not found."],
  };
  if (simple[state]) return <ResultShell><SimpleResult title={simple[state][0]} text={simple[state][1]} /></ResultShell>;
  return (
    <ResultShell>
      <article className="confirm-card c-result-card">
        <h1>A time is free for you</h1>
        <BookingFacts offer /><BookingLines offer /><p className="c-pay">Pay at the studio</p>
        <div className={`countdown ${state === "urgent" ? "countdown--danger" : ""}`}>{state === "urgent" && <MiniIcon name="clock" />}<span>{state === "urgent" ? "4:59" : "24:13"}</span><small>left to claim</small></div>
        {state === "error" && <div className="alert alert--danger"><MiniIcon name="warning" />This time has already been booked through this link.</div>}
        <div className="c-action-stack"><button className="button" disabled={state === "busy"}>Claim this time</button><button className="button button--ghost" disabled={state === "busy"}>No thanks</button></div>
      </article>
    </ResultShell>
  );
}

function WaitlistConfirmScreen({ state }: { state: string }) {
  const content: Record<string,[string,string,string]> = {
    loading: ["Confirming your waitlist request…","","Back to home"],
    success: ["You're on the waitlist","For Thursday 15 October you're number 2. If a time frees up, we'll email you a link to claim it; the first to claim gets it.","Back to home"],
    handled: ["You're on the waitlist","Your request for Thursday 15 October is already handled.","Back to home"],
    failed: ["Couldn't confirm","Waitlist request not found. Please check the link in your email.","Book or join again"],
    limit: ["Couldn't confirm","You already have 5 open waitlist requests. Please call the studio to change them.","Book or join again"],
  };
  const [title,text,button] = content[state];
  return <ResultShell><SimpleResult title={title} text={text} button={button} icon={state === "success" ? "check" : undefined} /></ResultShell>;
}

function ReceiptScreen({ state }: { state: string }) {
  if (state === "loading") return <div className="c-screen c-receipt-screen"><SimpleResult title="Loading receipt…" /></div>;
  if (state === "none") return <div className="c-screen c-receipt-screen"><SimpleResult title="No receipt yet" text="The studio sends the receipt after your visit." /></div>;
  if (state === "not-found") return <div className="c-screen c-receipt-screen"><SimpleResult title="Receipt not found" text="Booking not found. Please check the link in your email." /></div>;
  const owner = state === "owner";
  return (
    <div className="c-screen c-receipt-screen">
      <div className="c-print-bar"><button className="button button--ghost button--small">Back</button><button className="button button--small"><MiniIcon name="printer" />Print / Save as PDF</button></div>
      <article className="c-receipt">
        <header className="c-receipt__header">
          <div><h1>Isar Wellness</h1><p>Isarstraße 12, 80469 München</p><p>+49 89 0000 0000 · hello@isar-wellness.example.com</p></div>
          <div><span>Receipt</span><strong>IW-2026-0042</strong><small>Issued 13 October 2026</small></div>
        </header>
        <dl className="c-receipt__facts">
          {owner && <div><dt>Customer</dt><dd>Anna Müller</dd></div>}
          <div><dt>Appointment</dt><dd>13 October 2026, 10:00</dd></div>
          <div><dt>Therapist</dt><dd>Lena</dd></div>
        </dl>
        <table className="c-receipt__table"><tbody><tr><td>Deep tissue massage</td><td>€70</td></tr><tr><td>Hot stones</td><td>€12</td></tr><tr><td>Massage oil (product) × 2 at €5</td><td>€10</td></tr><tr className="c-receipt__total"><th>Total (EUR)</th><th>€92</th></tr></tbody></table>
        <p className="c-receipt__thanks">Paid at the studio. Thank you for your visit!</p>
      </article>
    </div>
  );
}

function FlowNode({ children }: { children: ReactNode }) {
  return <span className="c-flow-node">{children}</span>;
}

function FlowArrow() { return <span className="c-flow-arrow">→</span>; }

function FlowsScreen() {
  return (
    <div className="c-screen c-flows">
      <main>
        <p className="eyebrow">Customer journeys</p><h1>Core flows</h1>
        <section><h2>Booking flow</h2><div className="c-flow-row"><FlowNode>Home</FlowNode><FlowArrow/><FlowNode>Book Deep tissue massage</FlowNode><FlowArrow/><FlowNode>Hot stones</FlowNode><FlowArrow/><FlowNode>Lena · Today · 10:00</FlowNode><FlowArrow/><FlowNode>Details</FlowNode><FlowArrow/><FlowNode>Booking…</FlowNode><FlowArrow/><FlowNode>Almost done, Anna!</FlowNode><FlowArrow/><FlowNode>Email link</FlowNode><FlowArrow/><FlowNode>Confirmed</FlowNode></div></section>
        <section><h2>Manage flow from reminder</h2><div className="c-flow-row"><FlowNode>Confirm link</FlowNode><FlowArrow/><FlowNode>Confirmed · See you soon</FlowNode></div><div className="c-flow-row"><FlowNode>Cancel link</FlowNode><FlowArrow/><FlowNode>Cancel question</FlowNode><FlowArrow/><FlowNode>Yes, cancel booking</FlowNode><FlowArrow/><FlowNode>Cancelled</FlowNode></div></section>
        <section><h2>Waitlist flow</h2><div className="c-flow-row"><FlowNode>Full day</FlowNode><FlowArrow/><FlowNode>Join waitlist</FlowNode><FlowArrow/><FlowNode>Almost done email</FlowNode><FlowArrow/><FlowNode>Number 2</FlowNode><FlowArrow/><FlowNode>Offer + countdown</FlowNode><FlowArrow/><FlowNode>Claim: You're booked</FlowNode></div><div className="c-flow-row"><FlowNode>Offer + countdown</FlowNode><FlowArrow/><FlowNode>No thanks</FlowNode><FlowArrow/><FlowNode>No problem</FlowNode></div></section>
      </main>
    </div>
  );
}

function ScreenRenderer({ screen, state }: { screen: ScreenId; state: string }) {
  if (screen === "home") return <HomeScreen state={state} />;
  if (screen === "book") return <BookScreen state={state} />;
  if (screen === "book-de") return <BookScreen state={state} german />;
  if (screen === "result") return <ResultScreen state={state} />;
  if (screen === "manage") return <ManageScreen state={state} />;
  if (screen === "offer") return <OfferScreen state={state} />;
  if (screen === "waitlist") return <WaitlistConfirmScreen state={state} />;
  if (screen === "receipt") return <ReceiptScreen state={state} />;
  return <FlowsScreen />;
}

export default function CustomerScreens() {
  const [screen, setScreen] = useState<ScreenId>("home");
  const [state, setState] = useState("default");
  const [viewport, setViewport] = useState<"desktop" | "mobile">("desktop");
  const states = useMemo(() => screenStates[screen], [screen]);
  const selectScreen = (next: ScreenId) => { setScreen(next); setState(screenStates[next][0].value); };
  return (
    <main id="main-content" className="customer-gallery">
      <header className="gallery-head">
        <div><p className="eyebrow">Part 2 · Customer experience</p><h1>Customer screens</h1><p>Select any screen, state and viewport. The preview uses the production spacing and responsive rules.</p></div>
        <div className="gallery-controls">
          <label className="field"><span>Screen</span><select value={screen} onChange={(event) => selectScreen(event.target.value as ScreenId)}>
            <option value="home">C1 · Home</option><option value="book">C2 · Booking</option><option value="book-de">C2 · Booking (German)</option><option value="result">C3 · Booking result</option><option value="manage">C4 · Manage booking</option><option value="offer">C5 · Waitlist offer</option><option value="waitlist">C6 · Waitlist confirmed</option><option value="receipt">C7 · Receipt</option><option value="flows">Customer flows</option>
          </select></label>
          <label className="field"><span>Frame / state</span><select value={state} onChange={(event) => setState(event.target.value)}>{states.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
          <div className="field"><span>Viewport</span><div className="segmented"><button className={viewport === "mobile" ? "is-selected" : ""} onClick={() => setViewport("mobile")}>390</button><button className={viewport === "desktop" ? "is-selected" : ""} onClick={() => setViewport("desktop")}>1440</button></div></div>
        </div>
      </header>
      <div className={`customer-preview customer-preview--${viewport}`}><div className="customer-preview__label">{viewport === "mobile" ? "390px · Mobile" : "1440px · Desktop"}</div><div className="customer-preview__canvas"><ScreenRenderer screen={screen} state={state} /></div></div>
    </main>
  );
}
