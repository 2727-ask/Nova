from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import SummaryResponse
from services.pdf_parser import parse_pdf, extract_chase_transactions
from services.categorizer import summarize_transactions, categorize
import csv
from io import StringIO, BytesIO

router = APIRouter()

@router.post("/classify", response_model=SummaryResponse, summary="Upload a Chase PDF to categorize spend")
async def classify(file: UploadFile = File(...)):
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
    

@router.post("/save")
async def save(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF")

    contents = await file.read()
    # Parse transactions (date, description, amount, balance)
    txns = extract_chase_transactions(contents)

    # Build rows with categorization
    rows = []
    for t in txns:
        cat, subcat = categorize(t["description"])
        rows.append([
            t["date"], t["description"], t["amount"], cat, subcat
        ])

    # CSV to memory (text → bytes)
    text_buf = StringIO(newline="")
    writer = csv.writer(text_buf)
    writer.writerow(["Date", "Description", "Amount", "Category", "Subcategory"])
    writer.writerows(rows)
    data = text_buf.getvalue().encode("utf-8")

    return StreamingResponse(
        BytesIO(data),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'}
    )