from app.database import SessionLocal
from app.models import User, Category

db = SessionLocal()

try:
    user = db.query(User).filter(
        User.email == "anmol.test01@gmail.com"
    ).first()

    if not user:
        raise ValueError("Test user not found")

    defaults = [
        ("Food", "expense"),
        ("Transport", "expense"),
        ("Shopping", "expense"),
        ("Salary", "income"),
        ("Freelance", "income")
    ]

    for name, category_type in defaults:
        existing = db.query(Category).filter(
            Category.name == name,
            Category.type == category_type,
            Category.user_id.is_(None)
        ).first()

        if not existing:
            db.add(Category(
                name=name,
                type=category_type,
                user_id=None,
                is_default=True
            ))

    db.commit()
    print("Default categories created successfully!")

finally:
    db.close()
