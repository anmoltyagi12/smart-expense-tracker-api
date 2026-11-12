from fastapi import FastAPI
from app.database import engine, Base
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.transaction import router as transactions_router
from app.routes.category import router as categories_router
from app.routes.budget import router as budgets_router
from app.routes.analytics import router as analytics_router
from app.models.ai_insight import AIInsight
from app.routes.ai_insights import router as ai_insights_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Expense Tracker API",
    description="An API to manage income, expenses and budgets.",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(transactions_router)
app.include_router(categories_router)
app.include_router(budgets_router)
app.include_router(analytics_router)
app.include_router(ai_insights_router)


@app.get("/")
def home():
    return {
        "message": "Smart Expense Tracker API is running!",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
