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
