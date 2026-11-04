# Plan

Tick `[x]` when a step is done. Add short notes (date, ADR link) when useful.

## Phase 0 — Setup
- [x] `uv init --package`, Python 3.12
- [x] Add dependencies (runtime + dev group: pytest, ruff)
- [x] `CLAUDE.md` and `docs/PLAN.md`
- [x] ADR 0001 — invoice schema and validation (`docs/adr/0001-invoice-schema-and-validation.md`)
- [x] `.gitignore`: `.env`, `data/`, tool caches
- [x] `.env.example` and `data/` folder
- [x] README (one-paragraph pitch)
- [x] Initial commit
- [x] GitHub repo + first push

## Phase 1 — Core
- [ ] (a) Pydantic models + business rules in `domain/`, with tests
  - [x] `ExtractedDocument` model + enums, shape tests ([ADR 0002](adr/0002-required-but-nullable-fields.md))
  - [ ] Date-based rules: `vat_rate_at(date)`, `allocation_threshold_at(date)`
  - [ ] VAT number check digit
  - [ ] `validate_business(doc) -> list[Warning]`
- [ ] (b) LLM extraction, output validated by Pydantic
- [ ] (c) PostgreSQL with Docker + SQLAlchemy + Alembic migrations
- [ ] (d) FastAPI endpoints + file storage

## Phase 2 — Async
- [ ] Split API and worker
- [ ] Message queue (RabbitMQ)
- [ ] Retries
- [ ] Idempotency
- [ ] Dead-letter queue

## Phase 3 — Tests and CI/CD
- [ ] Test strategy (unit / integration)
- [ ] GitHub Actions: lint, tests
- [ ] Build and publish Docker images

## Phase 4 — Evaluation
- [ ] Annotated dataset
- [ ] Per-field accuracy
- [ ] Regression checks
- [ ] Model comparison (public benchmark)
- [ ] Error analysis

## Phase 5 — Agent and MCP
- [ ] Agent for uncertain cases
- [ ] MCP server

## Phase 6 — Observability
- [ ] Structured logs
- [ ] Traces (OpenTelemetry)
- [ ] LLM call tracing
- [ ] Cost per tenant

## Phase 7 — AWS with Terraform
- [ ] S3, SQS, RDS, Secrets Manager
- [ ] ECS (API, worker) and/or Lambda
- [ ] CloudWatch

## Phase 8 — Optional
- [ ] Local Kubernetes
