# Domain rules: Israeli invoices and receipts

Reference for the business rules in `domain/`. Sources to check before
changing a rule: Israel Tax Authority (gov.il, רשות המסים).

## Document types
| Hebrew | English | Purpose |
|---|---|---|
| חשבונית מס | Tax invoice | Charges VAT. Lets the customer deduct input VAT. |
| קבלה | Receipt | Proof of payment. No VAT breakdown required. |
| חשבונית מס קבלה | Tax invoice-receipt | Both at once (payment at time of sale). |

Out of scope for v1: credit notes (חשבונית מס זיכוי), proforma invoices.

## Dealer types
- **עוסק מורשה** (licensed dealer): VAT-registered, issues tax invoices.
- **עוסק פטור** (exempt dealer): small business, **cannot** issue tax invoices,
  only receipts, with no VAT.
- **חברה בע"מ** (company): VAT-registered, number usually starts with `51`.

## VAT number check digit
Israeli business / ID numbers (ח.פ, ע.מ, ת.ז) have 9 digits; shorter numbers
are left-padded with zeros. The last digit is a check digit:
1. Multiply digits alternately by 1, 2, 1, 2, ... (from the left).
2. If a product is greater than 9, sum its digits (e.g. 14 -> 1 + 4 = 5).
3. The number is valid if the total is divisible by 10.

## VAT rate (by issue date)
| From | Rate |
|---|---|
| 2015-10-01 | 17% |
| 2025-01-01 | 18% |

A 0% rate is legal in some cases (Eilat, exports). Treat an unexpected rate as
a warning, not an error.

## Allocation number (מספר הקצאה)
Reform "Invoices Israel" (חשבוניות ישראל). A tax invoice between businesses
needs an allocation number from the Tax Authority when the amount **before
VAT** is above a threshold, otherwise the customer cannot deduct the input VAT.

| From | Threshold (ILS, before VAT) |
|---|---|
| 2024-05-05 | 25,000 |
| 2025-01-01 | 20,000 |
| 2026-01-01 | 10,000 |
| 2026-06-01 | 5,000 |

TODO: confirm exact dates and amounts on gov.il before relying on them.

## Amounts
- `total = subtotal + vat_amount`, with a small tolerance for rounding to
  agorot (0.01 ILS).
- `vat_amount ≈ subtotal × vat_rate`, same tolerance.
- Most documents are in ILS; foreign currencies (USD, EUR) exist.
