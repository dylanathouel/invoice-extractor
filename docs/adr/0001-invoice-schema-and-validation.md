# ADR 0001: Invoice schema and two-level validation

## Status
Accepted (2026-11-04)

## Context
The platform uses an LLM to extract data from Israeli invoices and receipts
(חשבונית מס, קבלה, חשבונית מס קבלה), in Hebrew and English.

Real documents are messy. Some are incomplete, some have calculation errors,
and the rules change over time: VAT went from 17% to 18% in 2025, and the
allocation number threshold went down several times. The LLM can also
return badly formatted output.

We need to decide which fields to extract first, how to store money,
and what to do when something is wrong.

## Decision
1. Version 1 extracts header fields only: document type, number, date,
   issuer name and VAT number, customer name and VAT number, subtotal,
   VAT rate, VAT amount, total, currency, allocation number, payment method.
   Line items are not extracted.
2. Money is stored as `Decimal`, never `float`.
3. Validation has two levels:
   - Schema validation (Pydantic) checks the shape of the LLM output.
     If it fails, the LLM made an error: we retry.
   - Business validation checks the content (total = subtotal + VAT,
     VAT number check digit, allocation number above the threshold...).
     If it fails, we do not reject the document. We save the result with
     a list of warnings and set its status to `needs_review`.
4. Rules that change over time (VAT rate, allocation threshold) use the
   document's issue date, not today's date.

## Consequences
Good:
- A real but imperfect invoice is never lost: the client gets the data
  and knows what to check.
- Clear split between "the system failed" (retry) and "the document has
  a problem" (warning).
- Business rules are plain Python, easy to test without calling an LLM.
- Header fields only make the benchmark simple to measure field by field.

Trade-offs:
- No line items in v1. Some clients will need them later.
- Documents in `needs_review` need a human (or the phase 5 agent).
- Time-based rules must be updated when the law changes.
