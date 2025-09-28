from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.database import SessionLocal
from services.emissions import compute_emissions_from_summary

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/categorize/{statement_id}")
def emissions_by_statement(
    statement_id: str,
    mode: str = Query("mid", pattern="^(min|mid|max)$"),
    db: Session = Depends(get_db),
):
    exists = db.execute(
        text("SELECT 1 FROM category_summaries WHERE statement_id=:sid LIMIT 1"),
        {"sid": statement_id}
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="statement_id not found (no summaries stored)")

    return compute_emissions_from_summary(db, statement_id, mode=mode)