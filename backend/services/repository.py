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
  

def upsert_category_summaries(db: Session, rows: Iterable[Dict]) -> int:
    """
    rows: dicts with keys: statement_id, category, subcategory, amount_usd
    Uses SQLite ON CONFLICT DO UPDATE (sum overwrite).
    Returns number of rows affected (inserted+updated).
    """
    rows = list(rows)
    if not rows:
        return 0

    sql = text("""
        INSERT INTO category_summaries (statement_id, category, subcategory, amount_usd)
        VALUES (:statement_id, :category, :subcategory, :amount_usd)
        ON CONFLICT(statement_id, category, subcategory)
        DO UPDATE SET amount_usd = excluded.amount_usd
    """)
    res = db.execute(sql, rows)
    db.commit()
    return res.rowcount