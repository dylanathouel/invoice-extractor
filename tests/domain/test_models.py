"""Tests for the shape of ExtractedDocument (ADR 0001 level 1, ADR 0002)."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from invoice_extractor.domain.models import DocumentType, ExtractedDocument

# The model itself is the source of truth for the list of fields.
ALL_FIELDS = list(ExtractedDocument.model_fields)
NULLABLE_FIELDS = [f for f in ALL_FIELDS if f != "document_type"]


def error_types(exc_info: pytest.ExceptionInfo[ValidationError]) -> list[str]:
    """Return the Pydantic error codes, e.g. ["missing"]."""
    return [error["type"] for error in exc_info.value.errors()]


def test_valid_payload_is_accepted(valid_payload):
    doc = ExtractedDocument(**valid_payload)

    assert doc.total == Decimal("14160.00")
    assert isinstance(doc.total, Decimal)
    assert doc.issue_date == date(2026, 3, 15)
    assert doc.document_type == DocumentType.TAX_INVOICE


# parametrize runs the same test once per field: 13 tests from 1 function.
@pytest.mark.parametrize("field", NULLABLE_FIELDS)
def test_null_value_is_accepted(field, valid_payload):
    valid_payload[field] = None

    doc = ExtractedDocument(**valid_payload)

    assert getattr(doc, field) is None


def test_document_type_cannot_be_null(valid_payload):
    valid_payload["document_type"] = None

    with pytest.raises(ValidationError):
        ExtractedDocument(**valid_payload)


@pytest.mark.parametrize("field", ALL_FIELDS)
def test_missing_key_is_rejected(field, valid_payload):
    del valid_payload[field]

    with pytest.raises(ValidationError) as exc_info:
        ExtractedDocument(**valid_payload)

    assert error_types(exc_info) == ["missing"]


def test_extra_key_is_rejected(valid_payload):
    valid_payload["discount"] = "100.00"

    with pytest.raises(ValidationError) as exc_info:
        ExtractedDocument(**valid_payload)

    assert error_types(exc_info) == ["extra_forbidden"]


def test_unknown_document_type_is_rejected(valid_payload):
    valid_payload["document_type"] = "credit_note"

    with pytest.raises(ValidationError) as exc_info:
        ExtractedDocument(**valid_payload)

    assert error_types(exc_info) == ["enum"]


def test_invalid_money_is_rejected(valid_payload):
    valid_payload["total"] = "fourteen thousand"

    with pytest.raises(ValidationError):
        ExtractedDocument(**valid_payload)


def test_document_is_immutable(valid_payload):
    doc = ExtractedDocument(**valid_payload)

    with pytest.raises(ValidationError):
        doc.total = Decimal(0)
