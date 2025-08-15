from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schemas.users import User


def get_by_username_or_email(db: Session, identifier: str) -> Optional[User]:
    stmt = select(User).where(
        (User.username == identifier) | (User.email == identifier)
    )
    return db.execute(stmt).scalar_one_or_none()


def create_user(
    db: Session, *, email: str, username: str, hashed_password: str
) -> User:
    user = User(email=email, username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
