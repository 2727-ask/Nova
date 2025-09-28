from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.database import SessionLocal
from services.emissions import compute_emissions_from_summary
from services.recommendations import recommendation_engine

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

@router.post("/recommendations")
async def generate_recommendations(analysis_data: dict):
    """
    Generate carbon reduction recommendations from analysis data
    """
    try:
        print("🔄 Received request for recommendations")
        
        # Validate input
        if not analysis_data or not isinstance(analysis_data, dict):
            return {
                "recommendations": [],
                "total_suggestions": 0,
                "error": "Invalid input data"
            }
        
        # Generate recommendations
        recommendations = recommendation_engine.get_recommendations(analysis_data)
        
        # Ensure everything is JSON serializable
        safe_recommendations = []
        for rec in recommendations:
            safe_rec = {
                "category": str(rec.get("category", "")),
                "problem": str(rec.get("problem", "")),
                "suggestions": []
            }
            
            for suggestion in rec.get("suggestions", []):
                safe_suggestion = {
                    "source": str(suggestion.get("source", "")),
                    "advice": str(suggestion.get("advice", "")),
                    "pages": str(suggestion.get("pages", ""))
                }
                safe_rec["suggestions"].append(safe_suggestion)
            
            safe_recommendations.append(safe_rec)
        
        response = {
            "recommendations": safe_recommendations,
            "total_suggestions": sum(len(rec["suggestions"]) for rec in safe_recommendations)
        }
        
        print(f"✅ Returning {len(safe_recommendations)} recommendations")
        return response
        
    except Exception as e:
        print(f"❌ Error in generate_recommendations: {e}")
        # Return empty but safe response
        return {
            "recommendations": [],
            "total_suggestions": 0,
            "error": "Failed to generate recommendations"
        }