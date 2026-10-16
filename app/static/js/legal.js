// Legal notice (Impressum) and privacy page, filled from the studio's own details.
import { api, fill, h } from "/js/api.js";
import { t } from "/js/i18n.js";

const target = document.getElementById("legal");
const page = target.dataset.page;

function block(title, ...lines) {
  return h("section", {}, h("h2", {}, title), ...lines.filter(Boolean).map((line) => h("p", {}, line)));
}

async function init() {
  let studio;
  try {
    studio = await api("/public/studio");
  } catch (error) {
    fill(target, h("p", { class: "alert" }, error.message));
    return;
  }
  document.querySelectorAll("[data-studio-name]").forEach((el) => (el.textContent = studio.name));
  const contact = block(t("legal.contact"), studio.phone, h("a", { href: `mailto:${studio.email}` }, studio.email));
  if (page === "impressum") {
    fill(target,
      h("h1", {}, t("legal.imprint_h1")),
      block(t("legal.provider"), studio.name, studio.address),
      contact,
      studio.tax_number && block(t("legal.tax"), studio.tax_number),
      block(t("legal.responsible"), `${studio.name}, ${studio.address}`));
  } else {
    fill(target,
      h("h1", {}, t("legal.privacy_h1")),
      h("p", { class: "muted" }, t("legal.p_intro")),
      block(t("legal.p_what_h"), t("legal.p_what")),
      block(t("legal.p_why_h"), t("legal.p_why")),
      block(t("legal.p_keep_h"), t("legal.p_keep")),
      block(t("legal.p_rights_h"), t("legal.p_rights")),
      block(t("legal.provider"), studio.name, studio.address),
      contact);
  }
}

init();
