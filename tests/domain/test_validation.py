"""Tests for business validation (ADR 0001 level 2, ADR 0004)."""

import pytest

from invoice_extractor.domain.models import DocumentType, ExtractedDocument
from invoice_extractor.domain.validation import (
    REQUIRED_FIELDS,
    IssueCode,
    validate_business,
)


def issue_codes(payload: dict) -> list[IssueCode]:
    """Build the document, validate it, and return only the issue codes."""
    doc = ExtractedDocument(**payload)
    return [issue.code for issue in validate_business(doc)]


def issue_pairs(payload: dict) -> list[tuple[IssueCode, str | None]]:
    """Like issue_codes, but with the field: [(code, field), ...]."""
    doc = ExtractedDocument(**payload)
    return [(issue.code, issue.field) for issue in validate_business(doc)]


def test_valid_document_has_no_issue(valid_payload):
    assert issue_codes(valid_payload) == []


# --- _check_totals ---------------------------------------------------------
# valid_payload: subtotal 12000.00 + VAT 2160.00 = total 14160.00


def test_total_within_tolerance_is_accepted(valid_payload):
    valid_payload["total"] = "14160.01"
    assert IssueCode.TOTAL_MISMATCH not in issue_codes(valid_payload)


def test_total_mismatch_is_reported(valid_payload):
    valid_payload["total"] = "14160.02"
    assert IssueCode.TOTAL_MISMATCH in issue_codes(valid_payload)


def test_total_check_is_skipped_when_an_amount_is_missing(valid_payload):
    valid_payload["total"] = None
    assert IssueCode.TOTAL_MISMATCH not in issue_codes(valid_payload)


# --- _check_vat_amount -----------------------------------------------------
# valid_payload: subtotal 12000.00 x rate 0.18 = VAT 2160.00


def test_vat_amount_within_tolerance_is_accepted(valid_payload):
    valid_payload["vat_amount"] = "2160.01"
    assert IssueCode.VAT_AMOUNT_MISMATCH not in issue_codes(valid_payload)


def test_vat_amount_rounded_to_the_agora_is_accepted(valid_payload):
    # 100.03 x 0.18 = 18.0054, printed as 18.01 on a real invoice.
    valid_payload["subtotal"] = "100.03"
    valid_payload["vat_amount"] = "18.01"
    assert IssueCode.VAT_AMOUNT_MISMATCH not in issue_codes(valid_payload)


def test_vat_amount_mismatch_is_reported(valid_payload):
    valid_payload["vat_amount"] = "2160.02"
    assert IssueCode.VAT_AMOUNT_MISMATCH in issue_codes(valid_payload)


def test_vat_amount_check_is_skipped_when_a_value_is_missing(valid_payload):
    valid_payload["vat_rate"] = None
    assert IssueCode.VAT_AMOUNT_MISMATCH not in issue_codes(valid_payload)


# --- _check_missing_fields -------------------------------------------------

TAX_INVOICE_REQUIRED = REQUIRED_FIELDS[DocumentType.TAX_INVOICE]


@pytest.mark.parametrize("field", TAX_INVOICE_REQUIRED)
def test_missing_required_field_is_reported(valid_payload, field):
    valid_payload[field] = None
    assert (IssueCode.MISSING_FIELD, field) in issue_pairs(valid_payload)


def test_missing_customer_is_not_reported(valid_payload):
    # A sale to a private person has no customer details.
    valid_payload["customer_name"] = None
    valid_payload["customer_vat_number"] = None
    assert IssueCode.MISSING_FIELD not in issue_codes(valid_payload)


def test_clean_receipt_has_no_issue(valid_payload):
    # A receipt has no VAT breakdown and never needs an allocation number.
    valid_payload["document_type"] = "receipt"
    valid_payload["subtotal"] = None
    valid_payload["vat_rate"] = None
    valid_payload["vat_amount"] = None
    valid_payload["allocation_number"] = None
    assert issue_codes(valid_payload) == []


def test_receipt_without_payment_method_is_reported(valid_payload):
    valid_payload["document_type"] = "receipt"
    valid_payload["payment_method"] = None
    assert (IssueCode.MISSING_FIELD, "payment_method") in issue_pairs(valid_payload)


# --- _check_negative_amounts -----------------------------------------------


@pytest.mark.parametrize("field", ["subtotal", "vat_amount", "total"])
def test_negative_amount_is_reported(valid_payload, field):
    valid_payload[field] = "-1.00"
    assert (IssueCode.NEGATIVE_AMOUNT, field) in issue_pairs(valid_payload)


def test_zero_amount_is_not_negative(valid_payload):
    valid_payload["vat_amount"] = "0.00"
    assert IssueCode.NEGATIVE_AMOUNT not in issue_codes(valid_payload)


# --- _check_vat_rate --------------------------------------------------------
# Boundary: 17% until 2024-12-31, 18% from 2025-01-01.


@pytest.mark.parametrize(
    ("issue_date", "rate", "reported"),
    [
        ("2024-12-31", "0.17", False),  # last day of 17%
        ("2024-12-31", "0.18", True),  # new rate used too early
        ("2025-01-01", "0.18", False),  # first day of 18%
        ("2025-01-01", "0.17", True),  # old rate used too late
        ("2026-03-15", "0.00", True),  # 0% is legal but needs a human check
        ("2014-06-01", "0.99", False),  # before our table: we do not guess
    ],
)
def test_vat_rate_uses_the_issue_date(valid_payload, issue_date, rate, reported):
    valid_payload["issue_date"] = issue_date
    valid_payload["vat_rate"] = rate
    assert (IssueCode.UNEXPECTED_VAT_RATE in issue_codes(valid_payload)) is reported


# --- _check_vat_numbers -----------------------------------------------------


@pytest.mark.parametrize("field", ["issuer_vat_number", "customer_vat_number"])
def test_invalid_vat_number_is_reported(valid_payload, field):
    valid_payload[field] = "515555556"  # wrong check digit
    assert (IssueCode.INVALID_VAT_NUMBER, field) in issue_pairs(valid_payload)


def test_missing_customer_vat_number_is_not_invalid(valid_payload):
    valid_payload["customer_vat_number"] = None
    assert IssueCode.INVALID_VAT_NUMBER not in issue_codes(valid_payload)


# --- _check_allocation_number -----------------------------------------------
# valid_payload: B2B tax invoice, 2026-03-15, subtotal 12000 > threshold 10000.


def test_missing_allocation_number_is_reported(valid_payload):
    valid_payload["allocation_number"] = None
    assert IssueCode.MISSING_ALLOCATION_NUMBER in issue_codes(valid_payload)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"subtotal": "10000.00"}, "exactly at the threshold, not above"),
        ({"customer_vat_number": None}, "sale to a private person (B2C)"),
        ({"document_type": "receipt"}, "a receipt never needs one"),
        ({"currency": "USD"}, "threshold is in ILS, no exchange rate in v1"),
        ({"issue_date": "2024-05-04"}, "the day before the reform"),
        ({"issue_date": "2026-06-01", "subtotal": "5000.00"}, "at the new 5000"),
    ],
)
def test_allocation_number_not_required(valid_payload, change, reason):
    valid_payload["allocation_number"] = None
    valid_payload.update(change)
    assert IssueCode.MISSING_ALLOCATION_NUMBER not in issue_codes(valid_payload), reason


def test_allocation_threshold_uses_the_issue_date(valid_payload):
    # 6000 is below the 10000 threshold in March 2026,
    # but above the 5000 threshold from June 2026.
    valid_payload["allocation_number"] = None
    valid_payload["subtotal"] = "6000.00"
    valid_payload["issue_date"] = "2026-06-01"
    assert IssueCode.MISSING_ALLOCATION_NUMBER in issue_codes(valid_payload)
