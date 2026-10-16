"""Classic / New look switch: every page loads theme.js before the styles and calm.css after
them; customer top bars have the switch; the new look only applies under data-theme="calm"."""

import re
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"
PAGES = sorted(STATIC.glob("*.html")) + sorted(STATIC.glob("owner/*.html"))


@pytest.mark.parametrize("page", PAGES, ids=lambda p: str(p.relative_to(STATIC)))
def test_every_page_loads_the_look_files_in_order(page):
    html = page.read_text(encoding="utf-8")
    head = html.split("</head>")[0]
    theme = head.index('<script src="/js/theme.js"></script>')
    styles = head.index('href="/css/styles.css"')
    calm = head.index('href="/css/calm.css"')
    assert theme < styles < calm  # look chosen before first paint; calm overrides classic


@pytest.mark.parametrize("page", [p for p in PAGES if "data-lang-switch" in p.read_text("utf-8")],
                         ids=lambda p: p.name)
def test_customer_top_bars_have_the_look_switch(page):
    assert "<span data-theme-switch></span>" in page.read_text(encoding="utf-8")


def top_level_split(selector_list):
    """Split "a, :is(b, c)" on the commas outside brackets: ["a", ":is(b, c)"]."""
    parts, depth, current = [], 0, ""
    for char in selector_list:
        depth += {"(": 1, ")": -1}.get(char, 0)
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    return [*parts, current]


def test_calm_rules_only_apply_to_the_new_look():
    css = (STATIC / "css" / "calm.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@font-face\s*{[^}]*}", "", css)
    # Animation steps ("to { … }") are not selectors.
    css = re.sub(r"@keyframes[^{]*{(?:[^{}]*{[^{}]*})*[^{}]*}", "", css)
    for block in re.findall(r"([^{}]+){", css):
        for selector in top_level_split(block):
            selector = selector.strip()
            if selector.startswith("@media") or selector.startswith("@supports") or not selector:
                continue
            assert '[data-theme="calm"]' in selector, selector


def test_look_switch_labels_exist_in_both_languages():
    i18n = (STATIC / "js" / "i18n.js").read_text(encoding="utf-8")
    for label in ('"theme.classic": "Classic look"', '"theme.calm": "New look"',
                  '"theme.classic": "Klassisches Design"', '"theme.calm": "Neues Design"'):
        assert label in i18n


def test_look_files_are_served(client):
    for path in ("/js/theme.js", "/css/calm.css"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"


def test_self_hosted_font_is_served_as_woff2(client):
    response = client.get("/fonts/inter-latin-wght-normal.woff2")
    assert response.status_code == 200
    assert response.headers["content-type"] == "font/woff2"
    assert response.content[:4] == b"wOF2"
    licence = client.get("/fonts/Inter-OFL.txt")  # the OFL requires shipping it with the font
    assert licence.status_code == 200
    # ...including the font's own copyright notice (its name table, nameID 0)
    assert licence.text.startswith("Copyright 2016 The Inter Project Authors")


def test_no_third_party_font_requests():
    # GDPR: the font is self-hosted, never loaded from Google Fonts or another CDN.
    for path in [*PAGES, *STATIC.glob("css/*.css")]:
        text = path.read_text(encoding="utf-8")
        assert "fonts.googleapis.com" not in text and "fonts.gstatic.com" not in text, path
