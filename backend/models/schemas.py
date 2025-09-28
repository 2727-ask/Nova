from typing import Dict, Optional
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    gender: str
    age: int
    monthly_income: int
    allocation: Dict[str, float]

class Transaction(BaseModel):
    date: str
    description: str
    amount: float
    balance: Optional[float] = None

class SummaryResponse(BaseModel):
    summary: Dict[str, Dict[str, float]]
    uncategorized: float
    transactions_count: int