# ADR 0004: Validation issues as structured objects

## Status
Accepted (2026-11-12)

## Context
Business validation (ADR 0001, level 2) does not reject a document: it
returns a list of problems and the document goes to `needs_review`.
We must decide how to represent one problem.

## Options
- A. A plain string message. Simple, but not machine-readable: no counting
  by type, no filtering, fragile tests.
- B. An enum code only. Machine-readable, but no detail (which field?
  what was expected?).
- C. A small model with a code, the field concerned and a human message.

## Decision
Option C: a frozen Pydantic model `ValidationIssue(code, field, message)`.
`code` is an enum (`IssueCode`), `field` is the name of the field concerned
or `None`, `message` is for humans.

The class is not called `Warning`, which is a Python built-in.

## Consequences
Good:
- Code for machines (metrics in phase 4, tests), field for the phase 5
  agent, message for the API client.
- Serializes to JSON for the database and the API.

Trade-offs:
- A new code must be added to the enum for each new rule.
