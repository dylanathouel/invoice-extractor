"""Tests for the Israeli VAT number check digit."""

import pytest

from invoice_extractor.domain.vat_number import is_valid_vat_number


@pytest.mark.parametrize(
    "number",
    [
        "515555555",  # company number (starts with 51), total = 30
        "514321983",  # total = 40
        "18",  # short number, valid once padded to 000000018
        "000000018",  # same number, already padded
    ],
)
def test_valid_numbers(number):
    assert is_valid_vat_number(number) is True


@pytest.mark.parametrize(
    "number",
    [
        "515555556",  # wrong check digit (one digit misread)
        "5155555550",  # too long (10 digits)
        "",  # empty
        "12-3",  # hyphen
        " 18",  # leading space
        "51555555a",  # letter
        "12²",  # Unicode superscript: isdigit() is True, int() crashes
        "١٨",  # Arabic-Indic digits: not ASCII
        "000000000",  # passes the maths, but never a real number
        "0",  # same, before padding
    ],
)
def test_invalid_numbers(number):
    assert is_valid_vat_number(number) is False
