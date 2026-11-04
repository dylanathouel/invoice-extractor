# ADR 0002: Required but nullable fields in the extraction schema

## Status
Accepted (2026-11-04)

## Context
ADR 0001 splits validation in two: schema errors mean the LLM failed (retry),
business errors mean the document has a problem (warning, `needs_review`).

A field can be missing for two different reasons:
- the LLM forgot to return it (a system error), or
- the document really does not contain it (a document problem).

We must decide which fields the Pydantic model makes mandatory.

## Options
- A. All fields optional with a `None` default. Simple, but a forgotten field
  is silently accepted.
- B. Key fields required and non-null. A document that truly lacks a field
  is retried for nothing and finally lost, which breaks ADR 0001.
- C. Every field required as a key, but its value may be `null`.

## Decision
Option C. Every field must be present in the LLM output; its value may be
`null` when the document does not contain it. In Pydantic: `field: T | None`
with no default. Unknown extra fields are rejected.

## Consequences
Good:
- Missing key -> schema error -> retry. `null` value -> business warning.
- Maps directly to a JSON Schema where every property is required and
  nullable, which LLM structured-output APIs support.

Trade-offs:
- The prompt must tell the LLM to return `null` instead of omitting a field.
- Business validation must handle `None` everywhere.
