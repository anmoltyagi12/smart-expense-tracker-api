from sqlalchemy import (Column, Integer, String, Date, ForeignKey, CheckConstraint)
from sqlalchemy.orm import relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    amount = Column(Integer, nullable=False)
    # Amount stored in paise

    type = Column(String(20), nullable=False)
    # income or expense

    date = Column(Date, nullable=False)

    note = Column(String(500), nullable=True)

    payment_method = Column(String(50), nullable=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
        index=True
    )

    user = relationship(
        "app.models.user.User",
        back_populates="transactions"
    )

    category = relationship(
        "app.models.category.Category",
        back_populates="transactions"
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_amount"),
    )
