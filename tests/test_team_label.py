"""Home page team cards: each card starts with the "Meet your therapist" label (DE/EN), above the
therapist name. The label reuses the existing category-count subtitle look, inside the
.menu-category team section, so it adds no colours of its own."""

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_team_card_renders_the_label_before_the_name():
    home = (STATIC / "js" / "home.js").read_text(encoding="utf-8")
    card = home[home.index('h("article", { class: "team-card service" }'):]
    label = card.index('class: "category-count team-label"')
    name = card.index('h("h3", { class: "team-name" }')
    assert label < name
    assert 't("home.team_label")' in card[:name]


def test_team_label_is_translated_in_both_languages():
    i18n = (STATIC / "js" / "i18n.js").read_text(encoding="utf-8")
    assert '"home.team_label": "Meet your therapist"' in i18n
    assert '"home.team_label": "Lernen Sie Ihr Team kennen"' in i18n


def test_team_section_sits_inside_the_menu_category_look():
    # .menu-category .category-count is the existing subtitle style the label reuses.
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert re.search(r'<section class="menu-category" id="team"', html)
    css = (STATIC / "css" / "styles.css").read_text(encoding="utf-8")
    assert ".menu-category .category-count {" in css


def test_team_label_adds_no_new_colours():
    css = (STATIC / "css" / "styles.css").read_text(encoding="utf-8")
    assert ".team-label" not in css
