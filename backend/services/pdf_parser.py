import re
from typing import List, Optional, Dict
from io import BytesIO
import pdfplumber
from models.schemas import Transaction
from utils.text import to_amount

DATE_RE = re.compile(r"^\d{2}/\d{2}\b")

def _parse_transaction_line(line: str) -> Optional[Transaction]:
    """
    Parse a single Chase statement transaction line like:
      06/16 Card Purchase           06/14 Sq *Vigneshwara LLC Tempe AZ Card 4781 -11.94 7,122.53

    Heuristic:
    - First token looks like MM/DD -> date
    - Last token is balance
    - Second-last token is amount (may be negative)
    - Everything between date and amount is description
    """
    raw = " ".join(line.split())
    if not DATE_RE.match(raw):
        return None

    parts = raw.split(" ")
    if len(parts) < 4:
        return None

    date = parts[0]
    balance_token = parts[-1]
    amount_token = parts[-2]
    description_tokens = parts[1:-2]
    description = " ".join(description_tokens)

    try:
        amount = to_amount(amount_token)
        balance = to_amount(balance_token)
    except ValueError:
        # sometimes the last token may not be a pure balance; try alternative:
        # If we can't parse, we skip the line.
        return None

    return Transaction(date=date, description=description, amount=amount, balance=balance)

def parse_pdf(pdf_bytes: bytes) -> List[Transaction]:
    """
    Extract transactions from a Chase PDF statement.
    Strategy:
      - Iterate relevant pages (Chase typically has 'TRANSACTION DETAIL' on page 2+)
      - Extract text lines; parse ones that look like transactions
    """
    txns: List[Transaction] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if not text:
                continue
            # Only lines that look like transactions (start with MM/DD)
            for line in text.splitlines():
                line = line.strip()
                if not line or not DATE_RE.match(line):
                    continue
                t = _parse_transaction_line(line)
                if t:
                    txns.append(t)

    # Deduplicate if needed (some PDFs repeat lines across "Page of" artifacts)
    # Here we just return as-is.
    return txns


# One money token: -1,700.41 or 7,065.43
MONEY = r"-?\d{1,3}(?:,\d{3})*(?:\.\d{2})"
# Full transaction line:
#  06/16 <desc...> -242.96 6,855.70
LINE_RE = re.compile(
    rf"^(?P<date>\d{{2}}/\d{{2}})\s+(?P<desc>.*?)\s+(?P<amount>{MONEY})\s+(?P<balance>{MONEY})$"
)

# Lines that we should ignore even if they slip through
IGNORE_SUBSTRINGS = (
    "Deposits and Additions",
    "ATM & Debit Card Withdrawals",
    "Electronic Withdrawals",
    "Beginning Balance",
    "Ending Balance",
    "Page of",
    "JPMorgan Chase",
    "P O Box",
    "Member FDIC",
    "IN CASE OF ERRORS",
    "This Page Intentionally Left Blank",
    "Account Number",
    "Chase College Checking",
)

def _looks_like_noise(line: str) -> bool:
    if not line:
        return True
    # obvious headers (e.g., "June 13, 2025 through July 14, 2025")
    if line[0].isalpha():
        return True
    for s in IGNORE_SUBSTRINGS:
        if s.lower() in line.lower():
            return True
    return False

def _clean_spaces(s: str) -> str:
    # collapse internal whitespace
    return " ".join(s.split())

def extract_transactions(pdf_bytes: bytes) -> List[Dict[str, str]]:
    """
    Extract Chase transactions as a list of dicts:
      {date: MM/DD, description: str, amount: float, balance: float}
    We rely on the transcript-like lines that end with two money tokens:
    ... <amount> <balance>
    """
    res: List[Dict[str, str]] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            # Slightly tighter tolerances can keep columns aligned in some PDFs
            text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            for raw in text.splitlines():
                line = _clean_spaces(raw.strip())
                if not line or _looks_like_noise(line):
                    continue

                # The exact match: MM/DD ... AMOUNT BALANCE
                m = LINE_RE.match(line)
                if not m:
                    # Sometimes the balance token is glued; try to salvage by splitting at the end.
                    # As a fallback, try to find the LAST TWO money tokens, treat them as amount/balance.
                    money_tokens = re.findall(MONEY, line)
                    if len(money_tokens) >= 2 and re.match(r"^\d{2}/\d{2}\b", line):
                        date = line.split()[0]
                        amount_str, balance_str = money_tokens[-2], money_tokens[-1]
                        # description is what's between date and amount_str (first index of amount_str)
                        try:
                            idx_amt = line.rfind(amount_str)
                            desc = line[len(date):idx_amt].strip()
                        except Exception:
                            continue
                    else:
                        continue
                else:
                    date = m.group("date")
                    desc = m.group("desc").strip()
                    amount_str = m.group("amount")
                    balance_str = m.group("balance")

                # Normalize numbers
                def to_float(x: str) -> float:
                    return float(x.replace(",", ""))

                try:
                    amount = to_float(amount_str)
                    balance = to_float(balance_str)
                except ValueError:
                    continue

                # Skip pure deposits in CSV if you only want spend — or keep them; your call.
                # Here we keep all transactions; CSV consumer can filter later.
                res.append({
                    "date": date,
                    "description": desc,
                    "amount": amount,
                    "balance": balance,
                })

    return res