from fastapi import APIRouter
from models.schemas import UserProfile

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