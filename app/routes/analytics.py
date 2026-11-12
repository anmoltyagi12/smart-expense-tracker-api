from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.schemas.analytics import MonthlySummaryResponse
from app.services.auth_service import get_current_user
from app.schemas.analytics import MonthlySummaryResponse, TopExpenseResponse

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get(
    "/monthly-summary",
    response_model=MonthlySummaryResponse
)
def monthly_summary(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2024, le=2100),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Calculate the beginning and end of the month
    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # 1. Calculate total income
    total_income = db.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "income",
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).scalar() or 0

    # 2. Calculate total expenses
    total_expenses = db.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).scalar() or 0

    # 3. Calculate category-wise expenses
    category_expenses = db.query(
        Category.id,
        Category.name,
        func.coalesce(func.sum(Transaction.amount), 0)
    ).join(
        Transaction,
        Transaction.category_id == Category.id
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).group_by(
        Category.id,
        Category.name
    ).all()

    # Store category spending
    category_data = {}

    for category_id, category_name, spent in category_expenses:
        category_data[category_id] = {
            "category_id": category_id,
            "category_name": category_name,
            "spent": int(spent),
            "budget": None
        }

    # 4. Fetch monthly budgets
    budgets = db.query(
        Budget,
        Category.name
    ).join(
        Category,
        Budget.category_id == Category.id
    ).filter(
        Budget.user_id == current_user.id,
        Budget.month == month,
        Budget.year == year
    ).all()

    total_budget = 0
    total_budget_remaining = 0
    over_budget_categories = 0

    # Include categories that have a budget but no expenses
    for budget, category_name in budgets:

        category_id = budget.category_id

        if category_id not in category_data:
            category_data[category_id] = {
                "category_id": category_id,
                "category_name": category_name,
                "spent": 0,
                "budget": None
            }

        category_data[category_id]["budget"] = budget.amount

        total_budget += budget.amount

    # 5. Calculate budget utilization
    category_results = []

    for category in category_data.values():

        spent = category["spent"]
        budget_amount = category["budget"]

        if budget_amount is None:

            remaining = None
            utilization = None
            status = "no_budget"

        else:

            remaining = budget_amount - spent

            utilization = round(
                (spent / budget_amount) * 100, 2
            )

            if spent > budget_amount:
                status = "exceeded"
                over_budget_categories += 1

            elif spent == budget_amount:
                status = "limit_reached"

            elif spent * 100 >= budget_amount * 80:
                status = "warning"

            else:
                status = "within_budget"

            total_budget_remaining += remaining

        category_results.append({
            "category_id": category["category_id"],
            "category_name": category["category_name"],
            "spent": spent,
            "budget": budget_amount,
            "remaining": remaining,
            "utilization_percent": utilization,
            "status": status
        })

    # Sort by highest spending
    category_results.sort(
        key=lambda item: item["spent"],
        reverse=True
    )

    # 6. Calculate net savings
    net_savings = total_income - total_expenses

    return {
        "month": month,
        "year": year,

        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": net_savings,

        "total_budget": total_budget,
        "total_budget_remaining": total_budget_remaining,

        "over_budget_categories": over_budget_categories,

        "categories": category_results
    }


@router.get("/top-expenses", response_model=List[TopExpenseResponse])
def top_expenses(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date"
        )

    expenses = (
        db.query(Transaction, Category.name)
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        .order_by(Transaction.amount.desc())
        .limit(5)
        .all()
    )

    return [
        {
            "transaction_id": transaction.id,
            "amount": transaction.amount,
            "category_id": transaction.category_id,
            "category_name": category_name,
            "date": transaction.date,
            "note": transaction.note,
            "payment_method": transaction.payment_method
        }
        for transaction, category_name in expenses
    ]
