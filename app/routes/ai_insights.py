import json
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.ai_insight import AIInsight
from app.schemas.ai_insight import AIInsightResponse
from app.services.auth_service import get_current_user
from app.services.ai_service import (generate_spending_insights, AIServiceError)

router = APIRouter(
    prefix="/ai-insights",
    tags=["AI Spending Insights"]
)


@router.get("/monthly", response_model=AIInsightResponse)
def monthly_ai_insights(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2024, le=2100),
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cached_insight = (
        db.query(AIInsight)
        .filter(
            AIInsight.user_id == current_user.id,
            AIInsight.month == month,
            AIInsight.year == year
        )
        .first()
    )

    if cached_insight and not force_refresh:
        result = json.loads(cached_insight.insights_json)

        return {
            "id": cached_insight.id,
            "month": month,
            "year": year,
            **result,
            "cached": True,
            "generated_at": cached_insight.generated_at.isoformat()
        }

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    total_income = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "income",
            Transaction.date >= start_date,
            Transaction.date < end_date
        )
        .scalar()
    )

    total_expenses = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= start_date,
            Transaction.date < end_date
        )
        .scalar()
    )

    category_totals = (
        db.query(
            Category.name,
            func.sum(Transaction.amount).label("spent")
        )
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= start_date,
            Transaction.date < end_date
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    financial_data = {
        "month": month,
        "year": year,
        "currency": "INR",
        "total_income": round(total_income / 100, 2),
        "total_expenses": round(total_expenses / 100, 2),
        "net_savings": round(
            (total_income - total_expenses) / 100, 2
        ),
        "category_spending": [
            {
                "category": category_name,
                "amount": round(spent / 100, 2)
            }
            for category_name, spent in category_totals
        ]
    }

    try:
        ai_result = generate_spending_insights(financial_data)
    except AIServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc)
        )

    if cached_insight:
        cached_insight.insights_json = json.dumps(ai_result)
    else:
        cached_insight = AIInsight(
            user_id=current_user.id,
            month=month,
            year=year,
            insights_json=json.dumps(ai_result)
        )
        db.add(cached_insight)

    db.commit()
    db.refresh(cached_insight)

    return {
        "id": cached_insight.id,
        "month": month,
        "year": year,
        **ai_result,
        "cached": False,
        "generated_at": cached_insight.generated_at.isoformat()
    }
