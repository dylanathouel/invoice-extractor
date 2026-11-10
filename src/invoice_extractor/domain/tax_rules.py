from datetime import date
from decimal import Decimal

# Each row: (start date, value in force from that date). Sorted oldest first.
# See ADR 0003 and docs/domain-rules.md.

# VAT rate as a fraction: 0.18 means 18%.
VAT_RATES: list[tuple[date, Decimal]] = [
    (date(2015, 10, 1), Decimal("0.17")),
    (date(2025, 1, 1), Decimal("0.18")),
]

# Allocation number threshold, in ILS before VAT. None before the reform.
ALLOCATION_THRESHOLDS: list[tuple[date, Decimal]] = [
    (date(2024, 5, 5), Decimal(25000)),
    (date(2025, 1, 1), Decimal(20000)),
    (date(2026, 1, 1), Decimal(10000)),
    (date(2026, 6, 1), Decimal(5000)),
]


def _value_at(table: list[tuple[date, Decimal]], d: date) -> Decimal | None:
    current = None
    for start, value in table:
        if d >= start:
            current = value
        else:
            break
    return current


def vat_rate_at(d: date) -> Decimal | None:
    return _value_at(VAT_RATES, d)


def allocation_threshold_at(d: date) -> Decimal | None:
    return _value_at(ALLOCATION_THRESHOLDS, d)
