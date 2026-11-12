from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.user import User
from app.models.budget import Budget
from app.models.category import Category
from app.schemas.budget import (BudgetCreate, BudgetUpdate, BudgetResponse)
from app.services.auth_service import get_current_user


router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
)


# HELPER: VALIDATE CATEGORY
def validate_expense_category(category_id, current_user, db):

    category = db.query(Category).filter(
        Category.id == category_id,
        (Category.user_id == current_user.id) |
        (Category.user_id.is_(None))
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    if category.type != "expense":
        raise HTTPException(
            status_code=400,
            detail="Budgets can only be assigned to expense categories"
        )

    return category


# CREATE BUDGET
@router.post(
    "/",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED
)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    validate_expense_category(
        data.category_id, current_user, db
    )

    existing = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.category_id == data.category_id,
        Budget.month == data.month,
        Budget.year == data.year
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Budget already exists for this category and month"
        )

    budget = Budget(
        amount=data.amount,
        month=data.month,
        year=data.year,
        category_id=data.category_id,
        user_id=current_user.id
    )

    db.add(budget)

    try:
        db.commit()
        db.refresh(budget)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="A budget already exists for this category and month"
        )

    return budget


# GET ALL USER BUDGETS
@router.get(
    "/",
    response_model=list[BudgetResponse]
)
def get_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return db.query(Budget).filter(
        Budget.user_id == current_user.id
    ).order_by(
        Budget.year.desc(),
        Budget.month.desc()
    ).all()


# GET SINGLE BUDGET
@router.get(
    "/{budget_id}",
    response_model=BudgetResponse
)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Budget not found"
        )

    return budget


# UPDATE BUDGET
@router.put(
    "/{budget_id}",
    response_model=BudgetResponse
)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Budget not found"
        )

    updates = data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No update data provided"
        )

    if updates.get("amount") is None:
        raise HTTPException(
            status_code=400,
            detail="Budget amount cannot be null"
        )

    for key, value in updates.items():
        setattr(budget, key, value)

    db.commit()
    db.refresh(budget)

    return budget


# DELETE BUDGET
@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Budget not found"
        )

    db.delete(budget)
    db.commit()

    return {
        "message": "Budget deleted successfully"
    }
