# ADR 0003: Time-based tax rules as data tables

## Status
Accepted (2026-11-10)

## Context
Some rules depend on the document's issue date (ADR 0001, decision 4):
the VAT rate and the allocation number threshold. They change about once
a year when the law changes.

## Options
- A. `if/elif` chains: quick, but data and logic are mixed.
- B. A table of `(start_date, value)` rows plus one lookup function.
- C. Rules in a config file or the database: editable without a deploy,
  but too much for two rules that change once a year.

## Decision
Option B. Each rule is a list of `(start_date, value)` rows sorted by date.
One generic function returns the value in force on a given date, or `None`
if the date is before the first row.

## Consequences
Good:
- A law change means adding one row, no logic change.
- One lookup function, tested once, serves every time-based rule.

Trade-offs:
- Still a code change and a deploy when the law changes (fine for now;
  revisit with option C if rules start changing often).
