"""Domain models: the shape of the data extracted from a document.

This module checks SHAPE only (ADR 0001, level 1). Business rules
(totals, VAT number check digit, allocation threshold...) live elsewhere.
See ADR 0002: every field is required as a key, but may be null.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class DocumentType(StrEnum):
    TAX_INVOICE = "tax_invoice"
    TAX_INVOICE_RECEIPT = "tax_invoice_receipt"
    RECEIPT = "receipt"


class Currency(StrEnum):
    # ISO 4217 codes. ILS covers most documents; USD and EUR are common
    # for foreign suppliers.
    ILS = "ILS"
    USD = "USD"
    EUR = "EUR"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CHEQUE = "cheque"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    # A method we did not plan for (Bit, PayBox...) is valid data, not an
    # LLM error, so it must not fail the schema and trigger a retry.
    OTHER = "other"


class ExtractedDocument(BaseModel):
    # extra="forbid": an unknown key means the LLM did not follow the schema.
    # frozen=True: an extraction result must not be changed after validation.
    model_config = ConfigDict(extra="forbid", frozen=True)

    # The only field that can never be null: every document has a type.
    document_type: DocumentType

    # All other fields: required key, nullable value (ADR 0002).
    document_number: str | None
    issue_date: date | None

    issuer_name: str | None
    # str, not int: VAT numbers can start with 0, and we never do maths on them.
    issuer_vat_number: str | None

    customer_name: str | None
    customer_vat_number: str | None

    # Money is Decimal, never float (ADR 0001). Negative amounts are allowed
    # here: they are checked by business rules, not by the schema.
    subtotal: Decimal | None
    # Stored as a fraction: 0.18 means 18%, so vat_amount = subtotal * vat_rate.
    vat_rate: Decimal | None
    vat_amount: Decimal | None
    total: Decimal | None
    currency: Currency | None

    # str: an identifier, not a number we compute with.
    allocation_number: str | None
    payment_method: PaymentMethod | None
