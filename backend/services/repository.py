from typing import Iterable, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

def bulk_insert_transactions(db: Session, rows: Iterable[Dict]) -> int:
    """
    Efficiently insert rows with SQLite 'INSERT OR IGNORE' so duplicates are skipped.
    Returns number of inserted rows.
    """
    rows = list(rows)
    if not rows:
        return 0

    for r in rows:
        r.setdefault("balance", None)
        r.setdefault("source", "chase_pdf")

    sql = text("""
        INSERT OR IGNORE INTO transactions
          (date, description, amount, balance, category, subcategory, source)
        VALUES
          (:date, :description, :amount, :balance, :category, :subcategory, :source)
    """)
    res = db.execute(sql, rows)
    db.commit()
    return res.rowcount