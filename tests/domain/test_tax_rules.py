"""Tests for time-based tax rules (ADR 0003).

Boundary values: for each rule change we test the day before and the
first day, because off-by-one bugs (> instead of >=) hide there.
"""

from datetime import date
from decimal import Decimal

import pytest

from invoice_extractor.domain.tax_rules import allocation_threshold_at, vat_rate_at


# parametrize with 2 names: each tuple gives (d, expected).
@pytest.mark.parametrize(
    ("d", "expected"),
    [
        (date(2015, 9, 30), None),  # before the first row
        (date(2015, 10, 1), Decimal("0.17")),  # first day of 17%
        (date(2024, 12, 31), Decimal("0.17")),  # last day of 17%
        (date(2025, 1, 1), Decimal("0.18")),  # first day of 18%
        (date(2026, 11, 10), Decimal("0.18")),  # recent date
    ],
)
def test_vat_rate_at(d, expected):
    assert vat_rate_at(d) == expected


@pytest.mark.parametrize(
    ("d", "expected"),
    [
        (date(2024, 5, 4), None),  # before the reform: no threshold
        (date(2024, 5, 5), Decimal(25000)),  # reform starts
        (date(2024, 12, 31), Decimal(25000)),
        (date(2025, 1, 1), Decimal(20000)),
        (date(2025, 12, 31), Decimal(20000)),
        (date(2026, 1, 1), Decimal(10000)),
        (date(2026, 5, 31), Decimal(10000)),
        (date(2026, 6, 1), Decimal(5000)),
        (date(2026, 11, 10), Decimal(5000)),  # recent date
    ],
)
def test_allocation_threshold_at(d, expected):
    assert allocation_threshold_at(d) == expected
