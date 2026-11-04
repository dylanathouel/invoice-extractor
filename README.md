# invoice-extractor

AI document extraction platform for Israeli financial documents: tax invoices
and receipts (חשבונית מס, קבלה, חשבונית מס קבלה), in Hebrew and English.

A client uploads a document; the system extracts structured, validated data
with an LLM, asynchronously, with multi-tenant isolation. The project includes
a public benchmark measuring the field-level accuracy of several LLMs on
Hebrew documents.

**Status:** early development. See [docs/PLAN.md](docs/PLAN.md) for the roadmap
and [docs/adr/](docs/adr/) for architecture decisions.

## Stack
Python (uv), FastAPI, Pydantic, PostgreSQL, SQLAlchemy, Alembic, Docker,
RabbitMQ / SQS, pytest, GitHub Actions, OpenTelemetry, AWS, Terraform.

## Development
```bash
uv sync          # install dependencies
uv run pytest    # run tests
```
