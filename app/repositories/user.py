from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import JSON, select
from app.schemas.users import AuthProvider, User


def get_user_by_email(db: Session, identifier: str) -> Optional[User]:
    stmt = select(User).where(User.email == identifier)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def create_user(
    db: Session,
    *,
    email: str,
    nickname: str,
    provider: str,
    provider_user_id: str,
    raw_profile_json: JSON
) -> User:
    user = User(
        email=email,
        nickname=nickname,
    )
    db.add(user)
    db.flush()

    auth = AuthProvider(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
        raw_profile_json=raw_profile_json,
    )
    db.add(auth)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user_id: int,
    nickname: str,
    phone_number: Optional[str] = None,
    profile_image_url: Optional[str] = None,
    is_phone_verified: bool = False,
) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.nickname = nickname
    user.phone_number = phone_number
    user.profile_image_url = profile_image_url
    user.is_phone_verified = is_phone_verified
    db.commit()
    db.refresh(user)
    return user
