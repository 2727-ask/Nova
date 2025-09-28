from typing import Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from services.emission_factors import factor_for

def aggregate_spend_by_subcategory(db: Session, statement_id: str) -> Dict[Tuple[str, str], float]:
    """
    Returns absolute spend per (category, subcategory) for a given statement_id.
    Only expenses (negative amounts) are counted toward spend.
    """
    rows = db.execute(text("""
        SELECT category, subcategory, SUM(ABS(CASE WHEN amount < 0 THEN amount ELSE 0 END)) as spend
        FROM transactions
        WHERE statement_id = :sid
        GROUP BY category, subcategory
    """), {"sid": statement_id}).fetchall()

    out: Dict[Tuple[str, str], float] = {}
    for cat, sub, spend in rows:
        out[(cat, sub)] = float(spend or 0.0)
    return out

def compute_emissions_from_summary(db: Session, statement_id: str, mode: str = "mid") -> Dict:
    rows = db.execute(text("""
        SELECT category, subcategory, amount_usd
        FROM category_summaries
        WHERE statement_id = :sid
    """), {"sid": statement_id}).fetchall()

    if not rows:
        return {"statement_id": statement_id, "total_emissions_kg": 0.0, "by_category": {}}

    out: Dict[str, Dict[str, float]] = {}
    total = 0.0

    for cat, sub, usd in rows:
        # USD is already a positive total per subcategory
        f = factor_for(cat, sub, mode=mode)  # kg per USD
        kg = float(usd or 0.0) * f
        out.setdefault(cat, {})[sub] = round(kg, 3)
        total += kg

    return {
        "statement_id": statement_id,
        "mode": mode,
        "total_emissions_kg": round(total, 3),
        "by_category": out
    }