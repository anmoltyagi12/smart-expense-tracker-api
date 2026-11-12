from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import (CategoryCreate, CategoryUpdate, CategoryResponse)
from app.services.auth_service import get_current_user


router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


# CREATE CATEGORY
@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    existing = db.query(Category).filter(
        Category.user_id == current_user.id,
        func.lower(Category.name) == data.name.strip().lower()
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Category already exists"
        )

    category = Category(
        name=data.name.strip(),
        type=data.type,
        user_id=current_user.id,
        is_default=False
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


# GET ALL AVAILABLE CATEGORIES
@router.get(
    "/",
    response_model=list[CategoryResponse]
)
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return db.query(Category).filter(
        (Category.user_id == current_user.id) |
        (Category.user_id.is_(None))
    ).order_by(Category.name.asc()).all()


# UPDATE CATEGORY
@router.put(
    "/{category_id}",
    response_model=CategoryResponse
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Custom category not found"
        )

    updates = data.model_dump(exclude_unset=True)

    if "name" in updates:
        updates["name"] = updates["name"].strip()

        if not updates["name"]:
            raise HTTPException(
                status_code=400,
                detail="Category name cannot be empty"
            )

        duplicate = db.query(Category).filter(
            Category.user_id == current_user.id,
            Category.id != category_id,
            func.lower(Category.name) == updates["name"].lower()
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="Category name already exists"
            )

    if "type" in updates:
        if updates["type"] != category.type:
            used = db.query(Transaction).filter(
                Transaction.category_id == category_id
            ).first()

            if used:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot change category type while transactions use it"
                )

    for key, value in updates.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)

    return category


# DELETE CATEGORY
@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Custom category not found"
        )

    used = db.query(Transaction).filter(
        Transaction.category_id == category_id
    ).first()

    if used:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete category linked to transactions"
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully"
    }
