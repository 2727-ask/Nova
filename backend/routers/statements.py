from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.database import SessionLocal
from services.repository import bulk_insert_transactions, upsert_category_summaries
from models.schemas import SummaryResponse
from services.pdf_parser import parse_pdf, extract_transactions
from services.categorizer import summarize_transactions, categorize_transactions

import hashlib

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

@router.post("/categorize", response_model=SummaryResponse, summary="Upload a Chase PDF to categorize spend")
async def categorize(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file")

    pdf_bytes = await file.read()
    statement_id = sha256_hex(pdf_bytes)

    try:
        transactions = parse_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")

    summary, uncategorized_total = summarize_transactions(transactions)
    # summary is expected like: { "Travel": {"Flights": 1000.0, "Ride-hailing": 25.0}, ... }

    # Flatten and upsert into SQLite
    rows = []
    for cat, subs in summary.items():
        for sub, amt in subs.items():
            rows.append({
                "statement_id": statement_id,
                "category": cat,
                "subcategory": sub,
                "amount_usd": float(amt),
            })
    upserted = upsert_category_summaries(db, rows)

    # Return the same payload + statement_id so you can reference it later
    return SummaryResponse(
        summary=summary,
        uncategorized=round(uncategorized_total, 2),
        transactions_count=len(transactions)
    ).model_dump() | {  # add statement_id & upserted without touching your Pydantic model
        "statement_id": statement_id,
        "rows_persisted": upserted
    }

@router.post("/save")
async def save(
    file: UploadFile = File(...),
    persist: bool = Query(True, description="Persist into SQLite (default: true)"),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF")

    contents = await file.read()
    statement_id = sha256_hex(contents)
    txns = extract_transactions(contents)

    rows_db = []
    for t in txns:
        cat, subcat = categorize_transactions(t["description"])
        rows_db.append({
            "statement_id": statement_id,
            "date": t["date"],
            "description": t["description"],
            "amount": t["amount"],
            "balance": t.get("balance"),
            "category": cat,
            "subcategory": subcat,
            "source": "chase_pdf",
        })

    inserted = 0
    if persist:
        inserted = bulk_insert_transactions(db, rows_db)

    return {
        "message": "Data saved successfully",
        "statement_id": statement_id,
        "seen_rows": len(rows_db),
        "inserted_rows": inserted,
        "duplicates_skipped": len(rows_db) - inserted
    }

@router.get("/statements", summary="Get all saved statement_ids")
def list_statement_ids(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT DISTINCT statement_id FROM category_summaries")).fetchall()
    return {"statement_ids": [r[0] for r in rows]}


@router.get("/statements/latest", summary="Get the most recent statement_id")
def latest_statement_id(db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT statement_id, MAX(id) 
        FROM category_summaries
    """)).fetchone()
    if not row or not row[0]:
        return {"message": "No statements found"}
    return {"latest_statement_id": row[0]}