"""VAT on receipts (§33 UStDV): the rate and the VAT contained in the gross total, or the
small-business note (§19 UStG)."""

from decimal import Decimal

import pytest

from app.i18n import vat_included, vat_line


@pytest.mark.parametrize("total, mode, vat", [
    ("82.00", "19", "13.09"),   # 82 × 19 / 119 = 13.0924…
    ("68.00", "19", "10.86"),   # 10.857… rounds up
    ("82.00", "7", "5.36"),     # 82 × 7 / 107 = 5.3644…
    ("0.00", "19", "0.00"),
    ("82.00", "small_business", None),
])
def test_vat_contained_in_the_gross_total(total, mode, vat):
    assert vat_included(Decimal(total), mode) == (Decimal(vat) if vat else None)


def test_vat_line_in_both_languages():
    assert vat_line(Decimal("82.00"), "19", "en") == "incl. 19% VAT: €13.09"
    assert vat_line(Decimal("82.00"), "19", "de") == "inkl. 19 % MwSt.: 13,09 €"
    assert vat_line(Decimal("82.00"), "small_business", "de") == \
        "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."
