import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from db.database import SessionLocal
from services.pdf_parser import parse_pdf
from services.categorizer import summarize_transactions
from services.repository import upsert_category_summaries
from services.emission_factors import get_emission_factor

from models.schemas import UserProfile

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

router = APIRouter()

@router.get("/profile", response_model=UserProfile, summary="Get a dummy user profile")
async def get_user_profile():
    monthly_income = 5000
    percentages = {
        "Travel": 10,
        "Food": 15,
        "Shopping": 10,
        "Housing": 30,
        "Health": 8,
        "Entertainment": 7,
        "Education": 5,
        "Finances": 12,
        "Charity": 3
    }
    allocation = {k: round(monthly_income * v / 100, 2) for k, v in percentages.items()}

    return UserProfile(
        name="Alex Doe",
        gender="Male",
        age=25,
        monthly_income=monthly_income,
        allocation=allocation
    )

@router.post(
    "/analyze",
    summary="Upload PDF, categorize spend, and return CO₂ emissions with statement_id"
)
async def categorize_and_emissions(
    file: UploadFile = File(...),
    mode: str = Query("mid", pattern="^(min|mid|max)$", description="Emission factor mode"),
    db: Session = Depends(get_db),
):
    # 1. Validate
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file")

    # 2. Read + statement_id
    pdf_bytes = await file.read()
    statement_id = sha256_hex(pdf_bytes)

    # 3. Parse PDF
    try:
        transactions = parse_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")

    # 4. Categorize transactions
    summary, uncategorized_total = summarize_transactions(transactions)

    # 5. Persist category totals
    rows = []
    for cat, subs in summary.items():
        for sub, amt in subs.items():
            rows.append({
                "statement_id": statement_id,
                "category": cat,
                "subcategory": sub,
                "amount_usd": float(amt),
            })
    upsert_category_summaries(db, rows)

    # 6. Build response summary with emissions
    response_summary = {}
    for cat, subs in summary.items():
        response_summary[cat] = {}
        for sub, amt in subs.items():
            factor = get_emission_factor(cat, sub, mode=mode)  # returns kg CO₂ per $
            emission_val = round(amt * factor, 2) if factor else 0
            response_summary[cat][sub] = {
                "amount": round(amt, 2),
                "emission": emission_val
            }

    # 7. Final output
    return {
        "summary": response_summary,
        "uncategorized": round(uncategorized_total, 2),
        "transactions_count": len(transactions)
    }