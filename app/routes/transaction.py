from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import (TransactionCreate, TransactionUpdate, TransactionResponse)
from app.services.auth_service import get_current_user
from math import ceil
from sqlalchemy import or_
from fastapi import Query
from app.schemas.transaction_search import TransactionSearchResponse


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = db.query(Category).filter(
        Category.id == data.category_id,
        (Category.user_id == current_user.id) |
        (Category.user_id.is_(None)),
        Category.type == data.type
    ).first()

    if not category:
        raise HTTPException(
            status_code=400,
            detail="Invalid category for this transaction"
        )

    transaction = Transaction(
        amount=data.amount,
        type=data.type,
        date=data.date,
        note=data.note,
        payment_method=data.payment_method,
        category_id=data.category_id,
        user_id=current_user.id
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).all()


# SEARCH, FILTER, SORT AND PAGINATE TRANSACTIONS


@router.get(
    "/search",
    response_model=TransactionSearchResponse
)
def search_transactions(
    search: str = Query(None, max_length=100),
    transaction_type: str = Query(
        None,
        pattern="^(income|expense)$"
    ),
    category_id: int = Query(None, gt=0),
    payment_method: str = Query(None, max_length=50),
    start_date: date = Query(None),
    end_date: date = Query(None),

    min_amount: int = Query(None, ge=1),
    max_amount: int = Query(None, ge=1),

    sort_by: str = Query(
        "date",
        pattern="^(date|amount)$"
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$"
    ),

    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date"
        )

    if (
        min_amount is not None
        and max_amount is not None
        and min_amount > max_amount
    ):
        raise HTTPException(
            status_code=400,
            detail="Minimum amount cannot exceed maximum amount"
        )

    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    )

    if search:
        query = query.join(
            Category,
            Transaction.category_id == Category.id
        ).filter(
            or_(
                Transaction.note.ilike(f"%{search}%"),
                Category.name.ilike(f"%{search}%")
            )
        )

    if transaction_type:
        query = query.filter(
            Transaction.type == transaction_type
        )

    if category_id:
        query = query.filter(
            Transaction.category_id == category_id
        )

    if payment_method:
        query = query.filter(
            Transaction.payment_method == payment_method
        )

    if start_date:
        query = query.filter(
            Transaction.date >= start_date
        )

    if end_date:
        query = query.filter(
            Transaction.date <= end_date
        )

    if min_amount is not None:
        query = query.filter(
            Transaction.amount >= min_amount
        )

    if max_amount is not None:
        query = query.filter(
            Transaction.amount <= max_amount
        )

    total = query.count()

    sort_column = getattr(Transaction, sort_by)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    offset = (page - 1) * page_size

    transactions = query.offset(offset).limit(
        page_size
    ).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size),
        "items": transactions
    }


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    updates = data.model_dump(exclude_unset=True)

    new_type = updates.get("type", transaction.type)
    new_category_id = updates.get(
        "category_id",
        transaction.category_id
    )

    if "category_id" in updates or "type" in updates:
        category = db.query(Category).filter(
            Category.id == new_category_id,
            (Category.user_id == current_user.id) |
            (Category.user_id.is_(None)),
            Category.type == new_type
        ).first()

        if not category:
            raise HTTPException(
                status_code=400,
                detail="Invalid category for this transaction"
            )

    for key, value in updates.items():
        setattr(transaction, key, value)

    db.commit()
    db.refresh(transaction)

    return transaction


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transaction deleted successfully"
    }
