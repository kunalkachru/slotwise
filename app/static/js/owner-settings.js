import { ApiError, fill, h } from "/js/api.js";
import { field, toast } from "/js/owner-forms.js";
import { ownerApi, showPageError, startOwnerPage } from "/js/owner-shell.js";

const form = document.getElementById("settings-form");

const text = (name, label, value, attrs = {}, hint) => field(name, label, h("input", { value: value ?? "", ...attrs }), hint);
const number = (name, label, value, min, max, hint) => field(name, label, h("input", { type: "number", value, min, max, step: "1", required: true }), hint);

function render(s) {
  const error = h("p", { class: "alert", role: "alert", hidden: true });
  fill(form,
    h("fieldset", {},
      h("legend", {}, "Studio details"),
      h("p", { class: "lead" }, "Shown on the home page, on receipts and in every email. Customer replies to emails go to the email address below."),
      text("name", "Studio name", s.name, { required: true, maxlength: "120" }),
      text("address", "Address", s.address, { required: true, maxlength: "255" }),
      h("div", { class: "grid-2" },
        text("phone", "Phone", s.phone, { type: "tel", required: true, maxlength: "40" }),
        text("email", "Email (reply-to)", s.email, { type: "email", required: true, maxlength: "255" })),
      text("opening_hours_text", "Opening hours (as shown on the home page)", s.opening_hours_text, { maxlength: "255" },
        "Separate parts with ' · ', e.g. Mon 10:00–19:00 · Sat 9:00–17:00 · Sun closed. Bookable times come from Therapists & hours."),
      text("opening_hours_text_de", "Opening hours (German)", s.opening_hours_text_de, { maxlength: "255" },
        "e.g. Mo 10–19 Uhr · Sa 9–17 Uhr · So geschlossen. Leave empty to use the English text.")),
    h("fieldset", {},
      h("legend", {}, "Booking rules"),
      h("p", { class: "lead" }, "Apply from now on. Existing bookings keep their times and prices."),
      h("div", { class: "grid-2" },
        number("min_notice_hours", "Minimum notice (hours)", s.min_notice_hours, 0, 72, "Customers can't book later than this; phone bookings can."),
        number("booking_window_days", "Book up to (days ahead)", s.booking_window_days, 1, 365),
        number("free_cancellation_hours", "Free cancellation until (hours before)", s.free_cancellation_hours, 0, 168, "Later cancellations are allowed but marked late."),
        number("waitlist_offer_minutes", "Waitlist offer lasts (minutes)", s.waitlist_offer_minutes, 5, 240))),
    h("fieldset", {},
      h("legend", {}, "Receipts"),
      text("receipt_prefix", "Receipt number prefix", s.receipt_prefix, { required: true, maxlength: "10", pattern: "[A-Za-z0-9]{1,10}" },
        "Receipts are numbered PREFIX-YEAR-0001. A new prefix starts again at 0001.")),
    error,
    h("div", { class: "actions-row" }, h("button", { class: "btn", type: "submit" }, "Save settings")),
  );
  form.onsubmit = async (event) => {
    event.preventDefault();
    error.hidden = true;
    form.querySelectorAll("[aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
    const value = (name) => form.elements[name].value;
    try {
      const saved = await ownerApi("/owner/studio", { method: "PUT", body: {
        name: value("name"), address: value("address"), phone: value("phone"), email: value("email"),
        opening_hours_text: value("opening_hours_text"),
        opening_hours_text_de: value("opening_hours_text_de") || null,
        min_notice_hours: Number(value("min_notice_hours")), booking_window_days: Number(value("booking_window_days")),
        free_cancellation_hours: Number(value("free_cancellation_hours")), waitlist_offer_minutes: Number(value("waitlist_offer_minutes")),
        receipt_prefix: value("receipt_prefix"),
      } });
      toast("Settings saved");
      render(saved);
    } catch (e) {
      error.textContent = e.message;
      error.hidden = false;
      const name = e instanceof ApiError && e.body?.fields?.[0]?.field;
      if (name && form.elements[name]) {
        form.elements[name].setAttribute("aria-invalid", "true");
        form.elements[name].focus();
      }
    }
  };
}

async function init() {
  await startOwnerPage("settings");
  render(await ownerApi("/owner/studio"));
}

init().catch((error) => showPageError(error));
