"""Shared pytest fixtures.

pytest loads this file automatically before the tests of this folder and
its sub-folders. A test gets a fixture by naming it as a parameter.
"""

import pytest


@pytest.fixture
def valid_payload() -> dict:
    """A complete, valid LLM output for a tax invoice, as a plain dict.

    Values are strings, like parsed JSON. The document is clean: it must
    pass both schema validation and business validation with no issue.
    A new dict is built for each test, so a test can modify it freely.
    """
    return {
        "document_type": "tax_invoice",
        "document_number": "2026-0042",
        "issue_date": "2026-03-15",
        "issuer_name": "Acme Software Ltd",
        "issuer_vat_number": "515555555",  # valid check digit
        "customer_name": "Beta Consulting Ltd",
        "customer_vat_number": "514321983",  # valid check digit
        "subtotal": "12000.00",  # above the 10,000 ILS threshold of March 2026
        "vat_rate": "0.18",
        "vat_amount": "2160.00",
        "total": "14160.00",
        "currency": "ILS",
        "allocation_number": "123456789",  # required: subtotal above threshold
        "payment_method": "bank_transfer",
    }
