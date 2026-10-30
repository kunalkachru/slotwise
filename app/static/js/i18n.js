// German / English for the customer pages. Import this first on every customer page:
// it picks the language (saved choice, else the browser's), sets <html lang>, which
// api.js forwards to the server as X-Lang, and translates [data-i18n] elements.
import { themeSwitch } from "/js/api.js";

const KEY = "slotwise:lang";

function detect() {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "de" || saved === "en") return saved;
  } catch { /* private mode */ }
  return (navigator.language || "").toLowerCase().startsWith("de") ? "de" : "en";
}

export const lang = detect();
export const locale = lang === "de" ? "de-DE" : "en-GB";
document.documentElement.lang = lang;

const DICT = {
  en: {
    "brand.by": "Online booking by",
    "nav.book_now": "Book now", "nav.back_menu": "Back to menu", "nav.studio_login": "Studio login",
    "nav.book_again": "Book again", "nav.back_home": "Back to home", "nav.back": "Back",
    "lang.other": "DE", "lang.other_name": "Deutsch",
    "theme.classic": "Classic look", "theme.calm": "Figma design",
    "common.pay": "Pay at the studio", "common.total": "Total", "common.total_time": "Total time",
    "common.min": "{n} min", "common.date": "Date", "common.time": "Time",
    "common.therapist": "Therapist", "common.where": "Where", "common.at_time": "{time}",
    "common.loading_booking": "Loading your booking…", "common.loading": "Loading…", "common.optional": "(optional)",
    "home.title": "Book online", "home.address": "Address", "home.phone": "Phone", "home.hours": "Hours",
    "home.loading_menu": "Loading the menu…", "home.manage": "Manage my booking",
    "home.manage_text": "Open the link in your confirmation email to view, confirm or cancel your booking and to see your receipt.",
    "home.policy": "Free cancellation up to {hours} hours before",
    "home.tagline": "Book online, any time",
    "home.lead": "Massages, facials and foot reflexology in Munich.",
    "home.cta_book": "Book a treatment", "home.cta_menu": "See treatments",
    "home.book": "Book", "home.book_aria": "Book {name}", "home.addons": "Add-ons",
    "home.menu_empty": "The menu is being prepared. Please call us to book.",
    "home.menu_error": "Could not load the menu. Please refresh.",
    "home.from_price": "from {price}",
    "home.treatment_count_one": "1 treatment",
    "home.treatment_count_other": "{n} treatments",
    "home.popular": "Popular",
    "home.team": "Our team",
    "home.open_now": "Open now",
    "home.closed_now": "Closed now",
    "book.title": "Book", "book.h1": "Book a treatment",
    "book.lead": "Choose your treatment, a therapist and a free time. You pay at the studio.",
    "book.treatments": "Treatments", "book.addons": "Add-ons", "book.therapist": "Therapist",
    "book.day": "Day", "book.another_day": "Another day", "book.time": "Time",
    "book.details": "Your details", "book.first": "First name", "book.last": "Last name",
    "book.email": "Email", "book.phone": "Phone", "book.note": "Note for your therapist",
    "book.note_hint": "Please don't enter medical details. Max 300 characters.",
    "book.summary": "Your booking", "book.start": "Choose a treatment to start.",
    "book.pick_day_time": "Pick a day and time", "book.pick_time": "{date}, pick a time",
    "book.when": "{date} at {time} with {therapist}", "book.confirm": "Confirm booking",
    "book.booking": "Booking…", "book.bar": "{count} items · {minutes} · {total}", "book.bar_one": "1 item · {minutes} · {total}", "book.no_preference": "No preference", "book.today": "Today",
    "book.tomorrow": "Tomorrow", "book.pick_day": "Pick a day to see free times.",
    "book.looking": "Looking for free times…",
    "book.no_times": "No free times on this day. Try another day, or join the waitlist below.",
    "book.with_service": " · with {service}", "book.no_extra_time": "no extra time",
    "book.services_error": "Could not load services.",
    "book.therapist_hint": "Each treatment can have its own therapist.",
    "book.suggested": "Suggested times", "book.choose_myself": "Choose times myself",
    "book.suggested_hint": "Each time is your whole visit, one treatment right after the other.",
    "book.myself_hint": "Pick a time for each treatment, in order.",
    "book.pick_first": "Pick a time for {service} first.",
    "common.your_visit": "Your visit", "conf.book_another": "Book another treatment",
    "book.break": "15 min break", "book.when_chain": "{date}, from {time}",
    "wl.title": "Join the waitlist",
    "wl.hint": "Tell us when you could come. If someone cancels, the first person on the list gets an email and can claim the time.",
    "wl.between": "Between", "wl.and": "and", "wl.uses_details": "Uses your details from step 6.",
    "wl.join": "Join the waitlist", "wl.fill_details": "Please fill in your details below first.",
    "wl.joined": "Almost done! We've emailed {email} a link. Click it to confirm your place on the waitlist for this day.",
    "wl.earliest": "Earliest start", "wl.latest": "Latest start",
    "conf.title_pending": "Check your email", "conf.title_booked": "Booking confirmed",
    "conf.almost": "Almost done, {name}!", "conf.booked": "You're booked, {name}!",
    "conf.pending_note": "We've emailed you a link. Click it to confirm your booking by {time}; until then we're holding the time for you.",
    "conf.spam": "No email? Check your spam folder. If you don't confirm in time, the time is released for others.",
    "conf.emailed": "A confirmation has been emailed to you. Use the link in your email to confirm, cancel or view your receipt.",
    "conf.missing": "Booking details not available",
    "conf.missing_text": "Your booking may still have gone through. Please check with the studio if you're unsure.",
    "manage.title": "Manage booking", "manage.h1": "Your booking",
    "status.pending": "Awaiting your confirmation", "status.expired": "Not confirmed",
    "status.booked": "Booked", "status.confirmed": "Confirmed", "status.done": "Completed",
    "status.no_show": "Missed", "status.cancelled": "Cancelled",
    "manage.not_found": "Booking not found",
    "manage.incomplete": "This link is incomplete. Please use the link in your confirmation email.",
    "manage.late_policy": "Free cancellation has ended. You can still cancel, but it counts as a late cancellation.",
    "manage.free_until": "Free cancellation until {when}.",
    "manage.sure_late": "Are you sure? This counts as a late cancellation.",
    "manage.sure": "Are you sure you want to cancel?", "manage.yes_cancel": "Yes, cancel booking",
    "manage.keep": "Keep my booking", "manage.cancel": "Cancel booking",
    "manage.confirm_cancel": "Confirm cancellation", "manage.verify": "Confirm my booking",
    "manage.coming": "Confirm I'm coming",
    "manage.msg_verify": "Thank you! Your booking is confirmed, and we've emailed you the details.",
    "manage.msg_confirm": "Thank you! Your booking is confirmed. See you soon.",
    "manage.msg_cancel_late": "Your booking is cancelled (late cancellation).",
    "manage.msg_cancel": "Your booking is cancelled.",
    "manage.was_cancelled_late": "This booking was cancelled late.",
    "manage.was_cancelled": "This booking was cancelled.",
    "manage.expired_note": "This booking request wasn't confirmed in time, so the time was released.",
    "manage.receipt": "Receipt {number}", "manage.view_receipt": "View or print receipt",
    "offer.title": "Claim your time", "offer.loading": "Loading the offer…",
    "offer.h1": "A time is free for you", "offer.countdown": "{time} left to claim",
    "offer.claim": "Claim this time", "offer.no_thanks": "No thanks",
    "offer.expired": "Sorry, this offer has expired.",
    "offer.expired_text": "The time has gone to the next person on the waitlist.",
    "offer.claimed": "Already claimed",
    "offer.claimed_text": "This time has already been booked through this link.",
    "offer.booked_text": "{date} at {time} with {therapist}. A confirmation with your booking link has been emailed to you.",
    "offer.total_pay": "Total {total} · Pay at the studio",
    "offer.declined": "No problem",
    "offer.declined_text": "We've offered the time to the next person on the waitlist.",
    "offer.not_found": "Offer not found",
    "receipt.title": "Receipt", "receipt.print": "Print / Save as PDF",
    "receipt.loading": "Loading receipt…", "receipt.none": "No receipt yet",
    "receipt.none_text": "The studio sends the receipt after your visit.",
    "receipt.issued": "Issued {date}", "receipt.customer": "Customer",
    "receipt.appointment": "Appointment", "receipt.total": "Total (EUR)",
    "manage.calendar": "Add to calendar",
    "book.terms": "Free cancellation up to {hours} hours before. Later cancellations are marked late.",
    "legal.imprint": "Legal notice", "legal.privacy": "Privacy",
    "legal.imprint_h1": "Legal notice", "legal.privacy_h1": "Privacy",
    "legal.provider": "Provider", "legal.contact": "Contact", "legal.tax": "Tax number", "legal.responsible": "Responsible for the content",
    "legal.p_intro": "We only use your details to manage your booking. This page explains what we store, why, and your rights.",
    "legal.p_what_h": "What we store", "legal.p_what": "Your name, email address and phone number, the treatments you book and an optional note. We don't use advertising or tracking cookies; your browser only remembers your language and the look you chose.",
    "legal.p_why_h": "Why", "legal.p_why": "To carry out your booking: confirmation and reminder emails, receipts, and offers from the waitlist you joined (Art. 6(1)(b) GDPR).",
    "legal.p_keep_h": "How long", "legal.p_keep": "Customer details are anonymised automatically two years after your last booking. Receipts are kept as long as tax law requires.",
    "legal.p_rights_h": "Your rights", "legal.p_rights": "You can ask for a copy of your data, have it corrected or deleted, and complain to a data protection authority. Write to us at the address below.",
    "receipt.paid": "Paid at the studio. Thank you for your visit!",
    "receipt.vat": "incl. {rate}% VAT: {amount}",
    "receipt.vat_exempt": "No VAT is charged: small business under § 19 UStG.",
    "receipt.tax_number": "Tax number: {number}",
    "receipt.not_found": "Receipt not found",
    "wlc.title": "Confirm waitlist", "wlc.confirming": "Confirming your waitlist request…",
    "wlc.on": "You're on the waitlist",
    "wlc.position": "For {day} you're number {position}. If a time frees up, we'll email you a link to claim it; the first to claim gets it.",
    "wlc.handled": "Your request for {day} is already handled.",
    "wlc.failed": "Couldn't confirm", "wlc.again": "Book or join again",
  },
  de: {
    "brand.by": "Online-Buchung mit",
    "nav.book_now": "Jetzt buchen", "nav.back_menu": "Zurück zum Menü", "nav.studio_login": "Studio-Login",
    "nav.book_again": "Erneut buchen", "nav.back_home": "Zur Startseite", "nav.back": "Zurück",
    "lang.other": "EN", "lang.other_name": "English",
    "theme.classic": "Klassisches Design", "theme.calm": "Figma-Design",
    "common.pay": "Bezahlung im Studio", "common.total": "Gesamt", "common.total_time": "Gesamtdauer",
    "common.min": "{n} Min.", "common.date": "Datum", "common.time": "Uhrzeit",
    "common.therapist": "Therapeutin", "common.where": "Ort", "common.at_time": "{time} Uhr",
    "common.loading_booking": "Ihre Buchung wird geladen…", "common.loading": "Wird geladen…", "common.optional": "(optional)",
    "home.title": "Online buchen", "home.address": "Adresse", "home.phone": "Telefon",
    "home.hours": "Öffnungszeiten", "home.loading_menu": "Das Menü wird geladen…",
    "home.manage": "Meine Buchung verwalten",
    "home.manage_text": "Öffnen Sie den Link in Ihrer Bestätigungs-E-Mail, um Ihre Buchung anzusehen, zu bestätigen oder zu stornieren und Ihre Quittung zu sehen.",
    "home.policy": "Kostenlose Stornierung bis {hours} Stunden vorher",
    "home.tagline": "Jederzeit online buchen",
    "home.lead": "Massagen, Gesichtsbehandlungen und Fußreflexzonenmassage in München.",
    "home.cta_book": "Behandlung buchen", "home.cta_menu": "Behandlungen ansehen",
    "home.book": "Buchen", "home.book_aria": "{name} buchen", "home.addons": "Extras",
    "home.menu_empty": "Das Menü wird gerade vorbereitet. Bitte rufen Sie uns zur Buchung an.",
    "home.menu_error": "Das Menü konnte nicht geladen werden. Bitte laden Sie die Seite neu.",
    "home.from_price": "ab {price}",
    "home.treatment_count_one": "1 Behandlung",
    "home.treatment_count_other": "{n} Behandlungen",
    "home.popular": "Beliebt",
    "home.team": "Unser Team",
    "home.open_now": "Jetzt geöffnet",
    "home.closed_now": "Jetzt geschlossen",
    "book.title": "Buchen", "book.h1": "Behandlung buchen",
    "book.lead": "Wählen Sie Ihre Behandlung, eine Therapeutin und eine freie Zeit. Bezahlt wird im Studio.",
    "book.treatments": "Behandlungen", "book.addons": "Extras", "book.therapist": "Therapeutin",
    "book.day": "Tag", "book.another_day": "Anderer Tag", "book.time": "Uhrzeit",
    "book.details": "Ihre Angaben", "book.first": "Vorname", "book.last": "Nachname",
    "book.email": "E-Mail", "book.phone": "Telefon", "book.note": "Notiz für Ihre Therapeutin",
    "book.note_hint": "Bitte keine medizinischen Angaben. Max. 300 Zeichen.",
    "book.summary": "Ihre Buchung", "book.start": "Wählen Sie eine Behandlung, um zu beginnen.",
    "book.pick_day_time": "Wählen Sie Tag und Uhrzeit", "book.pick_time": "{date}, bitte Uhrzeit wählen",
    "book.when": "{date} um {time} Uhr bei {therapist}", "book.confirm": "Buchung abschicken",
    "book.booking": "Wird gebucht…", "book.bar": "{count} Positionen · {minutes} · {total}", "book.bar_one": "1 Position · {minutes} · {total}", "book.no_preference": "Keine Präferenz", "book.today": "Heute",
    "book.tomorrow": "Morgen", "book.pick_day": "Wählen Sie einen Tag, um freie Zeiten zu sehen.",
    "book.looking": "Freie Zeiten werden gesucht…",
    "book.no_times": "An diesem Tag ist keine Zeit frei. Wählen Sie einen anderen Tag oder tragen Sie sich unten auf die Warteliste ein.",
    "book.with_service": " · zu {service}", "book.no_extra_time": "ohne Zusatzzeit",
    "book.services_error": "Behandlungen konnten nicht geladen werden.",
    "book.therapist_hint": "Jede Behandlung kann eine eigene Therapeutin haben.",
    "book.suggested": "Vorgeschlagene Zeiten", "book.choose_myself": "Zeiten selbst wählen",
    "book.suggested_hint": "Jede Zeit ist Ihr ganzer Besuch, eine Behandlung direkt nach der anderen.",
    "book.myself_hint": "Wählen Sie für jede Behandlung eine Zeit, der Reihe nach.",
    "book.pick_first": "Wählen Sie zuerst eine Zeit für {service}.",
    "common.your_visit": "Ihr Besuch", "conf.book_another": "Weitere Behandlung buchen",
    "book.break": "15 Min. Pause", "book.when_chain": "{date}, ab {time} Uhr",
    "wl.title": "Auf die Warteliste",
    "wl.hint": "Sagen Sie uns, wann Sie kommen könnten. Sagt jemand ab, bekommt die erste Person auf der Liste eine E-Mail und kann sich den Termin sichern.",
    "wl.between": "Zwischen", "wl.and": "und", "wl.uses_details": "Verwendet Ihre Angaben aus Schritt 6.",
    "wl.join": "Auf die Warteliste setzen", "wl.fill_details": "Bitte füllen Sie zuerst unten Ihre Angaben aus.",
    "wl.joined": "Fast geschafft! Wir haben {email} einen Link geschickt. Klicken Sie darauf, um Ihren Platz auf der Warteliste für diesen Tag zu bestätigen.",
    "wl.earliest": "Frühester Beginn", "wl.latest": "Spätester Beginn",
    "conf.title_pending": "Bitte E-Mail prüfen", "conf.title_booked": "Buchung bestätigt",
    "conf.almost": "Fast geschafft, {name}!", "conf.booked": "Sie sind gebucht, {name}!",
    "conf.pending_note": "Wir haben Ihnen einen Link geschickt. Bitte bestätigen Sie Ihre Buchung bis {time} Uhr; bis dahin halten wir den Termin für Sie frei.",
    "conf.spam": "Keine E-Mail? Bitte prüfen Sie den Spam-Ordner. Ohne rechtzeitige Bestätigung wird der Termin wieder freigegeben.",
    "conf.emailed": "Eine Bestätigung wurde Ihnen per E-Mail gesendet. Über den Link darin können Sie bestätigen, stornieren oder Ihre Quittung ansehen.",
    "conf.missing": "Buchungsdetails nicht verfügbar",
    "conf.missing_text": "Ihre Buchung ist möglicherweise trotzdem eingegangen. Fragen Sie im Zweifel beim Studio nach.",
    "manage.title": "Buchung verwalten", "manage.h1": "Ihre Buchung",
    "status.pending": "Wartet auf Ihre Bestätigung", "status.expired": "Nicht bestätigt",
    "status.booked": "Gebucht", "status.confirmed": "Bestätigt", "status.done": "Abgeschlossen",
    "status.no_show": "Nicht erschienen", "status.cancelled": "Storniert",
    "manage.not_found": "Buchung nicht gefunden",
    "manage.incomplete": "Dieser Link ist unvollständig. Bitte verwenden Sie den Link aus Ihrer Bestätigungs-E-Mail.",
    "manage.late_policy": "Die kostenlose Stornierung ist abgelaufen. Sie können trotzdem stornieren; es gilt dann als kurzfristige Stornierung.",
    "manage.free_until": "Kostenlose Stornierung bis {when}.",
    "manage.sure_late": "Sind Sie sicher? Das gilt als kurzfristige Stornierung.",
    "manage.sure": "Möchten Sie wirklich stornieren?", "manage.yes_cancel": "Ja, Buchung stornieren",
    "manage.keep": "Buchung behalten", "manage.cancel": "Buchung stornieren",
    "manage.confirm_cancel": "Stornierung bestätigen", "manage.verify": "Buchung bestätigen",
    "manage.coming": "Ich komme",
    "manage.msg_verify": "Vielen Dank! Ihre Buchung ist bestätigt, die Details haben wir Ihnen gemailt.",
    "manage.msg_confirm": "Vielen Dank! Ihre Buchung ist bestätigt. Bis bald!",
    "manage.msg_cancel_late": "Ihre Buchung ist storniert (kurzfristige Stornierung).",
    "manage.msg_cancel": "Ihre Buchung ist storniert.",
    "manage.was_cancelled_late": "Diese Buchung wurde kurzfristig storniert.",
    "manage.was_cancelled": "Diese Buchung wurde storniert.",
    "manage.expired_note": "Diese Buchungsanfrage wurde nicht rechtzeitig bestätigt, daher wurde der Termin freigegeben.",
    "manage.receipt": "Quittung {number}", "manage.view_receipt": "Quittung ansehen oder drucken",
    "offer.title": "Termin sichern", "offer.loading": "Angebot wird geladen…",
    "offer.h1": "Ein Termin ist für Sie frei", "offer.countdown": "Noch {time} zum Sichern",
    "offer.claim": "Termin sichern", "offer.no_thanks": "Nein, danke",
    "offer.expired": "Leider ist dieses Angebot abgelaufen.",
    "offer.expired_text": "Der Termin ging an die nächste Person auf der Warteliste.",
    "offer.claimed": "Bereits gesichert",
    "offer.claimed_text": "Dieser Termin wurde über diesen Link bereits gebucht.",
    "offer.booked_text": "{date} um {time} Uhr bei {therapist}. Eine Bestätigung mit Ihrem Buchungslink wurde Ihnen gemailt.",
    "offer.total_pay": "Gesamt {total} · Bezahlung im Studio",
    "offer.declined": "Kein Problem",
    "offer.declined_text": "Wir haben den Termin der nächsten Person auf der Warteliste angeboten.",
    "offer.not_found": "Angebot nicht gefunden",
    "receipt.title": "Quittung", "receipt.print": "Drucken / Als PDF speichern",
    "receipt.loading": "Quittung wird geladen…", "receipt.none": "Noch keine Quittung",
    "receipt.none_text": "Das Studio sendet die Quittung nach Ihrem Besuch.",
    "receipt.issued": "Ausgestellt am {date}", "receipt.customer": "Kunde",
    "receipt.appointment": "Termin", "receipt.total": "Gesamt (EUR)",
    "manage.calendar": "Zum Kalender hinzufügen",
    "book.terms": "Kostenlose Stornierung bis {hours} Stunden vorher. Spätere Stornierungen gelten als verspätet.",
    "legal.imprint": "Impressum", "legal.privacy": "Datenschutz",
    "legal.imprint_h1": "Impressum", "legal.privacy_h1": "Datenschutz",
    "legal.provider": "Anbieter", "legal.contact": "Kontakt", "legal.tax": "Steuernummer", "legal.responsible": "Verantwortlich für den Inhalt",
    "legal.p_intro": "Wir verwenden Ihre Angaben nur, um Ihre Buchung zu verwalten. Hier steht, was wir speichern, warum, und welche Rechte Sie haben.",
    "legal.p_what_h": "Was wir speichern", "legal.p_what": "Ihren Namen, Ihre E-Mail-Adresse und Telefonnummer, die gebuchten Behandlungen und eine optionale Notiz. Wir verwenden keine Werbe- oder Tracking-Cookies; Ihr Browser merkt sich nur Ihre Sprache und das gewählte Design.",
    "legal.p_why_h": "Wozu", "legal.p_why": "Zur Durchführung Ihrer Buchung: Bestätigungs- und Erinnerungs-E-Mails, Quittungen und Angebote von der Warteliste, auf die Sie sich eingetragen haben (Art. 6 Abs. 1 lit. b DSGVO).",
    "legal.p_keep_h": "Wie lange", "legal.p_keep": "Kundendaten werden zwei Jahre nach Ihrer letzten Buchung automatisch anonymisiert. Quittungen bewahren wir so lange auf, wie es das Steuerrecht verlangt.",
    "legal.p_rights_h": "Ihre Rechte", "legal.p_rights": "Sie können Auskunft über Ihre Daten verlangen, sie berichtigen oder löschen lassen und sich bei einer Datenschutzbehörde beschweren. Schreiben Sie uns an die unten stehende Adresse.",
    "receipt.paid": "Im Studio bezahlt. Vielen Dank für Ihren Besuch!",
    "receipt.vat": "inkl. {rate} % MwSt.: {amount}",
    "receipt.vat_exempt": "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.",
    "receipt.tax_number": "Steuernummer: {number}",
    "receipt.not_found": "Quittung nicht gefunden",
    "wlc.title": "Warteliste bestätigen", "wlc.confirming": "Ihre Wartelisten-Anfrage wird bestätigt…",
    "wlc.on": "Sie stehen auf der Warteliste",
    "wlc.position": "Für {day} sind Sie auf Platz {position}. Wird ein Termin frei, senden wir Ihnen einen Link; wer zuerst zugreift, bekommt ihn.",
    "wlc.handled": "Ihre Anfrage für {day} ist bereits erledigt.",
    "wlc.failed": "Bestätigung nicht möglich", "wlc.again": "Erneut buchen oder eintragen",
  },
};

export function t(key, vars = {}) {
  let text = DICT[lang][key] ?? DICT.en[key] ?? key;
  for (const [name, value] of Object.entries(vars)) text = text.replaceAll(`{${name}}`, String(value));
  return text;
}

// Translate the fixed texts in the page: data-i18n (text), data-i18n-aria (aria-label),
// data-i18n-title on <html> for the document title.
export function translatePage() {
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-aria]").forEach((el) => el.setAttribute("aria-label", t(el.dataset.i18nAria)));
  const titleKey = document.documentElement.dataset.i18nTitle;
  if (titleKey) document.title = `${t(titleKey)} · Slotwise`;
}

// DE / EN switch for the top bar. Remembers the choice and reloads the page.
export function languageSwitch() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "lang-switch";
  button.textContent = t("lang.other");
  button.setAttribute("aria-label", t("lang.other_name"));
  button.title = t("lang.other_name");
  button.addEventListener("click", () => {
    try { localStorage.setItem(KEY, lang === "de" ? "en" : "de"); } catch { /* private mode */ }
    location.reload();
  });
  return button;
}

// Mount the switch into every element marked data-lang-switch.
export function mountLanguageSwitch() {
  document.querySelectorAll("[data-lang-switch]").forEach((slot) => slot.replaceChildren(languageSwitch()));
}

// Classic look / Figma design button into every element marked data-theme-switch.
export function mountThemeSwitch() {
  const labels = { classic: t("theme.classic"), calm: t("theme.calm") };
  document.querySelectorAll("[data-theme-switch]").forEach((slot) => slot.replaceChildren(themeSwitch(labels)));
}

translatePage();
mountLanguageSwitch();
mountThemeSwitch();
