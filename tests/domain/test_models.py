"""Tests for the shape of ExtractedDocument (ADR 0001 level 1, ADR 0002)."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from invoice_extractor.domain.models import DocumentType, ExtractedDocument


def valid_payload() -> dict:
    """A complete, valid LLM output, as a plain dict (like parsed JSON)."""
    return {
        "document_type": "tax_invoice",
        "document_number": "2026-0042",
        "issue_date": "2026-03-15",
        "issuer_name": "Acme Software Ltd",
        "issuer_vat_number": "515555555",
        "customer_name": "Beta Consulting Ltd",
        "customer_vat_number": "514321983",
        "subtotal": "12000.00",
        "vat_rate": "0.18",
        "vat_amount": "2160.00",
        "total": "14160.00",
        "currency": "ILS",
        "allocation_number": "123456789",
        "payment_method": "bank_transfer",
    }


ALL_FIELDS = list(valid_payload())
NULLABLE_FIELDS = [f for f in ALL_FIELDS if f != "document_type"]


def error_types(exc_info: pytest.ExceptionInfo[ValidationError]) -> list[str]:
    """Return the Pydantic error codes, e.g. ["missing"]."""
    return [error["type"] for error in exc_info.value.errors()]


def test_valid_payload_is_accepted():
    doc = ExtractedDocument(**valid_payload())

    assert doc.total == Decimal("14160.00")
    assert isinstance(doc.total, Decimal)
    assert doc.issue_date == date(2026, 3, 15)
    assert doc.document_type == DocumentType.TAX_INVOICE


# parametrize runs the same test once per field: 13 tests from 1 function.
@pytest.mark.parametrize("field", NULLABLE_FIELDS)
def test_null_value_is_accepted(field):
    payload = valid_payload()
    payload[field] = None

    doc = ExtractedDocument(**payload)

    assert getattr(doc, field) is None


def test_document_type_cannot_be_null():
    payload = valid_payload()
    payload["document_type"] = None

    with pytest.raises(ValidationError):
        ExtractedDocument(**payload)


@pytest.mark.parametrize("field", ALL_FIELDS)
def test_missing_key_is_rejected(field):
    payload = valid_payload()
    del payload[field]

    with pytest.raises(ValidationError) as exc_info:
        ExtractedDocument(**payload)

    assert error_types(exc_info) == ["missing"]


def test_extra_key_is_rejected():
    payload = valid_payload()
    payload["discount"] = "100.00"

    with pytest.raises(ValidationError) as exc_info:
        ExtractedDocument(**payload)

    assert error_types(exc_info) == ["extra_forbidden"]


def test_unknown_document_type_is_rejected():
    payload = valid_payload()
    payload["document_type"] = "credit_note"

    with pytest.raises(ValidationError) as exc_info:
        ExtractedDocument(**payload)

    assert error_types(exc_info) == ["enum"]


def test_invalid_money_is_rejected():
    payload = valid_payload()
    payload["total"] = "fourteen thousand"

    with pytest.raises(ValidationError):
        ExtractedDocument(**payload)


def test_document_is_immutable():
    doc = ExtractedDocument(**valid_payload())

    with pytest.raises(ValidationError):
        doc.total = Decimal(0)
