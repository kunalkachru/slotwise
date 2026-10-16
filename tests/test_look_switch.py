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


def test_calm_rules_only_apply_to_the_new_look():
    css = (STATIC / "css" / "calm.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@font-face\s*{[^}]*}", "", css)
    for block in re.findall(r"([^{}]+){", css):
        for selector in block.split(","):
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
