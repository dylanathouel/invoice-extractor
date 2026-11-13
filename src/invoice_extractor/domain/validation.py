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

from invoice_extractor.domain.models import Currency, DocumentType, ExtractedDocument
from invoice_extractor.domain.tax_rules import allocation_threshold_at, vat_rate_at
from invoice_extractor.domain.vat_number import is_valid_vat_number

# Amounts are rounded to the agora, so a 0.01 ILS gap is normal rounding.
AMOUNT_TOLERANCE = Decimal("0.01")

# Fields every document must have, whatever its type.
_COMMON_REQUIRED = (
    "document_number",
    "issue_date",
    "issuer_name",
    "issuer_vat_number",
    "total",
    "currency",
)
_VAT_FIELDS = ("subtotal", "vat_rate", "vat_amount")

# Required fields per document type. See docs/domain-rules.md.
# customer_* fields are never required: a sale to a private person has no
# customer VAT number. allocation_number has its own rule.
REQUIRED_FIELDS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.TAX_INVOICE: (*_COMMON_REQUIRED, *_VAT_FIELDS),
    DocumentType.TAX_INVOICE_RECEIPT: (
        *_COMMON_REQUIRED,
        *_VAT_FIELDS,
        "payment_method",
    ),
    DocumentType.RECEIPT: (*_COMMON_REQUIRED, "payment_method"),
}

# Document types that let the customer deduct input VAT.
_TAX_INVOICE_TYPES = (DocumentType.TAX_INVOICE, DocumentType.TAX_INVOICE_RECEIPT)


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
        *_check_missing_fields(doc),
        *_check_negative_amounts(doc),
        *_check_totals(doc),
        *_check_vat_amount(doc),
        *_check_vat_rate(doc),
        *_check_vat_numbers(doc),
        *_check_allocation_number(doc),
    ]


def _check_missing_fields(doc: ExtractedDocument) -> list[ValidationIssue]:
    """Fields required for this document type must not be null (ADR 0002)."""
    return [
        ValidationIssue(
            code=IssueCode.MISSING_FIELD,
            field=name,
            message=f"{name} is required on a {doc.document_type} but was not found",
        )
        for name in REQUIRED_FIELDS[doc.document_type]
        if getattr(doc, name) is None
    ]


def _check_negative_amounts(doc: ExtractedDocument) -> list[ValidationIssue]:
    """Amounts must not be negative (credit notes are out of scope in v1)."""
    issues = []
    for name in ("subtotal", "vat_amount", "total"):
        value = getattr(doc, name)
        if value is not None and value < 0:
            issues.append(
                ValidationIssue(
                    code=IssueCode.NEGATIVE_AMOUNT,
                    field=name,
                    message=f"{name} is negative: {value}",
                )
            )
    return issues


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


def _check_vat_amount(doc: ExtractedDocument) -> list[ValidationIssue]:
    """vat_amount must equal subtotal x vat_rate, within AMOUNT_TOLERANCE."""
    if doc.vat_rate is None or doc.subtotal is None or doc.vat_amount is None:
        return []
    vat = doc.subtotal * doc.vat_rate
    gap = abs(doc.vat_amount - vat)
    if gap > AMOUNT_TOLERANCE:
        return [
            ValidationIssue(
                code=IssueCode.VAT_AMOUNT_MISMATCH,
                field="vat_amount",
                message=f"the expected vat_amount is {vat}, got {doc.vat_amount}",
            )
        ]
    return []


def _check_vat_rate(doc: ExtractedDocument) -> list[ValidationIssue]:
    """vat_rate must be the rate in force on the issue date (ADR 0001, n°4).

    The issue date is used, never today's date: a December 2024 invoice is
    checked against 17% even if it is processed in 2026.
    A 0% rate is legal in some cases (Eilat, exports) but still reported:
    a human should confirm it.
    """
    if doc.vat_rate is None or doc.issue_date is None:
        return []
    expected = vat_rate_at(doc.issue_date)
    if expected is None:
        # Date before our rate table: we cannot check, so we do not guess.
        return []
    if doc.vat_rate != expected:
        return [
            ValidationIssue(
                code=IssueCode.UNEXPECTED_VAT_RATE,
                field="vat_rate",
                message=(
                    f"the VAT rate on {doc.issue_date} is {expected}, "
                    f"got {doc.vat_rate}"
                ),
            )
        ]
    return []


def _check_vat_numbers(doc: ExtractedDocument) -> list[ValidationIssue]:
    """Issuer and customer VAT numbers, when present, must pass the check digit."""
    issues = []
    for name in ("issuer_vat_number", "customer_vat_number"):
        number = getattr(doc, name)
        if number is not None and not is_valid_vat_number(number):
            issues.append(
                ValidationIssue(
                    code=IssueCode.INVALID_VAT_NUMBER,
                    field=name,
                    message=f"{name} {number!r} fails the check digit",
                )
            )
    return issues


def _check_allocation_number(doc: ExtractedDocument) -> list[ValidationIssue]:
    """A B2B tax invoice above the threshold needs an allocation number.

    The rule applies only when ALL of these are true:
    - the document is a tax invoice (a receipt does not let the customer
      deduct VAT, so it never needs one);
    - the customer has a VAT number (B2B; a private person cannot deduct VAT);
    - the amount is in ILS (the threshold is in ILS; converting a foreign
      currency would need an exchange rate, out of scope in v1);
    - the subtotal (before VAT) is above the threshold on the issue date.
    """
    if doc.allocation_number is not None:
        return []
    if doc.document_type not in _TAX_INVOICE_TYPES:
        return []
    if doc.customer_vat_number is None:
        return []
    if doc.currency != Currency.ILS:
        return []
    if doc.subtotal is None or doc.issue_date is None:
        return []
    threshold = allocation_threshold_at(doc.issue_date)
    if threshold is None or doc.subtotal <= threshold:
        return []
    return [
        ValidationIssue(
            code=IssueCode.MISSING_ALLOCATION_NUMBER,
            field="allocation_number",
            message=(
                f"subtotal {doc.subtotal} ILS is above the {threshold} ILS "
                f"threshold on {doc.issue_date}: an allocation number is required"
            ),
        )
    ]
