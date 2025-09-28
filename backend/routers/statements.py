from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from db.database import SessionLocal
from services.repository import bulk_insert_transactions
from models.schemas import SummaryResponse
from services.pdf_parser import parse_pdf, extract_transactions
from services.categorizer import summarize_transactions, categorize_transactions

router = APIRouter()

@router.post("/categorize", response_model=SummaryResponse, summary="Upload a Chase PDF to categorize spend")
async def categorize(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file")

    pdf_bytes = await file.read()
    try:
        transactions = parse_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")

    summary, uncategorized_total = summarize_transactions(transactions)
    return SummaryResponse(
        summary=summary,
        uncategorized=round(uncategorized_total, 2),
        transactions_count=len(transactions)
    )
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/save")
async def save(
    file: UploadFile = File(...),
    persist: bool = Query(True, description="Persist into SQLite (default: true)"),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF")

    contents = await file.read()
    txns = extract_transactions(contents)

    rows_db = []
    for t in txns:
        cat, subcat = categorize_transactions(t["description"])
        rows_db.append({
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
        "seen_rows": len(rows_db),
        "inserted_rows": inserted,
        "duplicates_skipped": len(rows_db) - inserted
    }