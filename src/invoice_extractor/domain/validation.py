"""Business validation (ADR 0001, level 2).

Checks the CONTENT of an ExtractedDocument. Never raises and never rejects:
it returns a list of issues. An empty list means the document is clean;
otherwise the document goes to `needs_review`.

Each rule is a small private function that returns its own list of issues,
so it can be read and tested on its own. `validate_business` runs them all.
"""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from invoice_extractor.domain.models import ExtractedDocument

# Amounts are rounded to the agora, so a 0.01 ILS gap is normal rounding.
AMOUNT_TOLERANCE = Decimal("0.01")


class IssueCode(StrEnum):
    MISSING_FIELD = "missing_field"
    NEGATIVE_AMOUNT = "negative_amount"
    TOTAL_MISMATCH = "total_mismatch"
    VAT_AMOUNT_MISMATCH = "vat_amount_mismatch"
    UNEXPECTED_VAT_RATE = "unexpected_vat_rate"
    INVALID_VAT_NUMBER = "invalid_vat_number"
    MISSING_ALLOCATION_NUMBER = "missing_allocation_number"


class ValidationIssue(BaseModel):
    """One problem found in a document (ADR 0004)."""

    model_config = ConfigDict(frozen=True)

    code: IssueCode
    field: str | None  # the field concerned, None if it concerns several
    message: str  # for humans


def validate_business(doc: ExtractedDocument) -> list[ValidationIssue]:
    """Run every business rule and return all issues found."""
    return [
        *_check_totals(doc),
        # Other rules are added here, one per line, as we write them.
    ]


def _check_totals(doc: ExtractedDocument) -> list[ValidationIssue]:
    """total must equal subtotal + vat_amount, within AMOUNT_TOLERANCE."""
    if doc.total is None or doc.subtotal is None or doc.vat_amount is None:
        return []
    gap = abs(doc.total - (doc.subtotal + doc.vat_amount))
    if gap > AMOUNT_TOLERANCE:
        return [
            ValidationIssue(
                code=IssueCode.TOTAL_MISMATCH,
                field="total",
                message=f"the expected total is {doc.subtotal + doc.vat_amount}, got {doc.total}",
            )
        ]
    return []
