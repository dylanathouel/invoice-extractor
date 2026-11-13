"""Tests for business validation (ADR 0001 level 2, ADR 0004)."""

from invoice_extractor.domain.models import ExtractedDocument
from invoice_extractor.domain.validation import IssueCode, validate_business


def issue_codes(payload: dict) -> list[IssueCode]:
    """Build the document, validate it, and return only the issue codes."""
    doc = ExtractedDocument(**payload)
    return [issue.code for issue in validate_business(doc)]


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
