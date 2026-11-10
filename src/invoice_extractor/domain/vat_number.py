"""Israeli business / ID number check digit (ח.פ, ע.מ, ת.ז).

See docs/domain-rules.md for the algorithm.
"""


def is_valid_vat_number(number: str) -> bool:
    """Return True if `number` is a well-formed Israeli VAT number.

    Accepts 1 to 9 digits only (shorter numbers are left-padded with zeros).
    Anything else (letters, spaces, hyphens, empty string) is invalid.
    """
    # 1. Validate the raw input. isascii() is needed because isdigit() also
    #    accepts Unicode digits like "²" or "١", which int() cannot always parse.
    #    The empty string is rejected here too: "".isdigit() is False.
    if not number.isascii() or not number.isdigit() or len(number) > 9:
        return False

    # 2. Normalize: left-pad to 9 digits.
    number = number.zfill(9)

    # 3. All zeros passes the check digit maths but is never a real number
    #    (and is a typical placeholder an LLM could return).
    if number == "000000000":
        return False

    # 4. Check digit: weights 1, 2, 1, 2...; products > 9 are reduced to the
    #    sum of their digits; the total must be divisible by 10.
    total = 0
    for i, char in enumerate(number):
        num = int(char)
        if i % 2 == 0:
            total += num
        else:
            helper = num * 2
            if helper > 9:
                total += helper % 10 + helper // 10
            else:
                total += helper
    return total % 10 == 0
