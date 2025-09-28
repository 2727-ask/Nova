import re

AMOUNT_RE = re.compile(r"^-?\$?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?$")

def to_amount(token: str) -> float:
    """
    Convert a token like "-1,700.41" or "7,065.43" or "$12.00" to float.
    Raises ValueError if not parseable.
    """
    tok = token.strip().replace("$", "")
    # allow "1,234.56" and "-1,234.56"
    if not re.match(r"^-?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?$", tok):
        # also allow simple "123" or "123.45"
        if not re.match(r"^-?\d+(?:\.\d{1,2})?$", tok):
            raise ValueError(f"Not an amount: {token!r}")
    return float(tok.replace(",", ""))