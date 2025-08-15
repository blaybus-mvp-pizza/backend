from sqlalchemy.orm import Session
from app.repositories.user import get_by_username_or_email, create_user
from app.core.security import get_password_hash, verify_password
from app.schemas.users import User as UserEntity


def signup_user(db: Session, *, email: str, username: str, password: str) -> UserEntity:
    existing = get_by_username_or_email(db, username) or get_by_username_or_email(
        db, email
    )
    if existing:
        raise ValueError("User already exists")
    hashed = get_password_hash(password)
    return create_user(db, email=email, username=username, hashed_password=hashed)


def authenticate_user(
    db: Session, *, identifier: str, password: str
) -> UserEntity | None:
    user = get_by_username_or_email(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
