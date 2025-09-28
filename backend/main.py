from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.user import router as user_router
from routers.statements import router as statements_router
from routers.emissions import router as emissions_router
from db.database import Base, engine
from models import orm as orm_models

app = FastAPI(title="Sustainable Financial Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(statements_router, prefix="/statements", tags=["Statements"])
app.include_router(emissions_router, prefix="/emissions", tags=["Emissions"])


@app.get("/", include_in_schema=False)
def root():
    return {
        "status": "ok",
        "endpoints": {
            "/user": [
                "/profile",
                "/analyze"
            ],
            "/statements": [
                "/categorize",
                "/save"
            ],
            "/emissions": [
                "/categorize/{statement_id}"
            ]
        }
    }