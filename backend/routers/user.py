import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from db.database import SessionLocal
from services.pdf_parser import parse_pdf
from services.categorizer import summarize_transactions
from services.repository import upsert_category_summaries
from services.emission_factors import get_emission_factor, category_factor
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

# --- Keep your profile endpoint as-is ---
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

def _get_budget_allocation_dollars() -> dict:
    """
    Mirrors /user/profile allocation (in dollars).
    If you later make /user/profile dynamic, import from a service
    instead of hardcoding this.
    """
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
    return {k: round(monthly_income * v / 100, 2) for k, v in percentages.items()}

@router.post(
    "/analyze",
    summary="Upload PDF, categorize spend, and return emissions vs budget"
)
async def categorize_and_emissions(
    file: UploadFile = File(...),
    mode: str = Query("mid", pattern="^(min|mid|max)$", description="Emission factor mode"),
    db: Session = Depends(get_db),
):
    # 1) Validate
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file")

    # 2) Read + statement_id
    pdf_bytes = await file.read()
    statement_id = sha256_hex(pdf_bytes)

    # 3) Parse PDF
    try:
        transactions = parse_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")

    # 4) Categorize transactions (your existing function)
    summary, uncategorized_total = summarize_transactions(transactions)
    # summary: {Category: {Subcategory: amount_usd, ...}, ...} amounts are positive USD spend totals

    # 5) Persist category totals (so other endpoints can reuse)
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

    # 6) Build response summary with emissions per subcategory
    response_summary = {}
    actual_emissions_by_cat = {}
    for cat, subs in summary.items():
        response_summary[cat] = {}
        for sub, amt in subs.items():
            factor = get_emission_factor(cat, sub, mode=mode)  # kg CO2 per USD
            emission_val = round(amt * factor, 2) if factor else 0.0
            response_summary[cat][sub] = {
                "amount": round(amt, 2),
                "emission": emission_val
            }
            actual_emissions_by_cat[cat] = actual_emissions_by_cat.get(cat, 0.0) + emission_val

    total_actual_emission = round(sum(actual_emissions_by_cat.values()), 2)

    # 7) Compute budgeted emissions per category based on /user/profile dollars
    allocation_dollars = _get_budget_allocation_dollars()
    budget_emissions_by_cat = {}
    for cat, dollars in allocation_dollars.items():
        f = category_factor(cat, mode=mode)  # kg/USD (averaged from subcats)
        budget_emissions_by_cat[cat] = round(dollars * f, 2)

    total_allotted_emission = round(sum(budget_emissions_by_cat.values()), 2)

    # 8) Compare budget vs actual per category
    comparison = {}
    all_cats = set(allocation_dollars.keys()) | set(actual_emissions_by_cat.keys())
    for cat in sorted(all_cats):
        budget_kg = budget_emissions_by_cat.get(cat, 0.0)
        actual_kg = actual_emissions_by_cat.get(cat, 0.0)
        delta_kg = round(actual_kg - budget_kg, 2)
        delta_pct = round((delta_kg / budget_kg * 100.0), 1) if budget_kg > 0 else None
        status = "over" if delta_kg > 0 else ("under" if delta_kg < 0 else "on_target")
        comparison[cat] = {
            "budgeted_kg": budget_kg,
            "actual_kg": actual_kg,
            "delta_kg": delta_kg,
            "delta_pct": delta_pct,
            "status": status
        }

    # 9) Final payload in your requested style + added totals & statement_id
    return {
        "summary": response_summary,                 # per-subcategory {amount, emission}
        "uncategorized": round(uncategorized_total, 2),
        "transactions_count": len(transactions),
        "statement_id": statement_id,
        "totals": {
            "total_allotted_emission": total_allotted_emission,  # budget sum (kg)
            "total_actual_emission": total_actual_emission,      # actual sum (kg)
            "delta_kg": round(total_actual_emission - total_allotted_emission, 2)
        },
        "budget_comparison_by_category": comparison
    }