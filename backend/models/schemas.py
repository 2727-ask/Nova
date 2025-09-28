from typing import Dict, List, Optional
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    gender: str
    age: int
    monthly_income: int
    allocation: Dict[str, float]  # dollars per category

class Transaction(BaseModel):
    date: str                    # e.g., "06/13"
    description: str
    amount: float                # negative = expense, positive = deposit
    balance: Optional[float] = None

class SummaryResponse(BaseModel):
    summary: Dict[str, Dict[str, float]]  # {Category: {Subcategory: total_spend}}
    uncategorized: float                  # total spend that didn't match rules
    transactions_count: int