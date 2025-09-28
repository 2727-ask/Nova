from fastapi import FastAPI
from routers.user import router as user_router
from routers.statements import router as statements_router

app = FastAPI(title="Sustainable Financial Advisor")

app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(statements_router, prefix="/statements", tags=["Statements"])

@app.get("/", include_in_schema=False)
def root():
    return {
        "status": "ok",
        "endpoints": [
            "/user/profile",
            "/statements/classify"
            "/statements/save"
        ]
    }