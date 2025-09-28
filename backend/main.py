from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import csv
import io


app = FastAPI()

class UserProfile(BaseModel):
    name: str
    gender: str
    age: int
    monthly_income: int
    allocation: Dict[str, float]

@app.get("/user/profile", response_model=UserProfile, summary="Get a dummy user profile")
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
    allocation = {k: monthly_income * v / 100 for k, v in percentages.items()}

    return UserProfile(
        name="Alex Doe",
        gender="Male",
        age=25,
        monthly_income=monthly_income,
        allocation=allocation
    )


def parse_csv(file_bytes: bytes, encoding: str = "utf-8", delimiter: Optional[str] = None) -> List[Dict[str, str]]:
    text = file_bytes.decode(encoding, errors="replace")
    sample = text[:2048]
    if delimiter is None:
        try:
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = [dict(row) for row in reader]
    return rows

@app.post(
    "/upload/transactions",
    response_model=None,
    summary="Upload a CSV of transactions and get categories"
)
async def upload_transactions(
    file: UploadFile = File(..., description="CSV with headers like date,description,amount,merchant,currency"),
    encoding: str = "utf-8",
    delimiter: Optional[str] = None
):
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Please upload a .csv or .txt file")

    content = await file.read()
    try:
        rows = parse_csv(content, encoding=encoding, delimiter=delimiter)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    return None


@app.get("/", include_in_schema=False)
def root():
    return JSONResponse({"status": "ok", "endpoints": ["/user/profile", "/transactions/categorize"]})
