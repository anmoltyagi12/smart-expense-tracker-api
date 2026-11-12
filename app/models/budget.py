from sqlalchemy import (Column, Integer, ForeignKey, CheckConstraint, UniqueConstraint)
from sqlalchemy.orm import relationship
from app.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)

    amount = Column(Integer, nullable=False)
    # Amount stored in paise

    month = Column(Integer, nullable=False)

    year = Column(Integer, nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="budgets"
    )

    category = relationship(
        "Category",
        back_populates="budgets"
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_budget"),
        CheckConstraint("month BETWEEN 1 AND 12", name="valid_month"),
        UniqueConstraint(
            "user_id",
            "category_id",
            "month",
            "year",
            name="unique_monthly_budget"
        ),
    )
