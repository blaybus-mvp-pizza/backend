from typing import Optional
from sqlalchemy import JSON
from sqlalchemy.orm import Session
from app.domains.users.models import UserRead, UserUpdate
from app.repositories import user
from app.repositories.user import (
    get_user_by_email,
    create_user,
    get_user_by_id,
    update_user,
)
from app.core.security import get_password_hash, verify_password
from app.schemas.users import User as UserEntity


def signup_user_with_oauth(
    db: Session,
    *,
    email: str,
    nickname: str,
    provider: str,
    provider_user_id: str,
    raw_profile_json: JSON
) -> UserRead:
    user = get_user_by_email(db, email)
    if user:
        return user
    return create_user(
        db,
        email=email,
        nickname=nickname,
        provider=provider,
        provider_user_id=provider_user_id,
        raw_profile_json=raw_profile_json,
    )


def get_user_info(db: Session, user_id: int) -> Optional[UserRead]:
    user = get_user_by_id(db, user_id)
    return UserRead.model_validate(user) if user else None


def update_user_info(
    db: Session, user_id: int, user_data: UserUpdate
) -> Optional[UserRead]:
    # 핸드폰번호 변경 시 핸드폰 인증 여부를 확인합니다.
    if (user_data.phone_number is not None) and (user_data.is_phone_verified is False):
        raise ValueError("Phone verification is required")
    user = update_user(
        db,
        user_id=user_id,
        nickname=user_data.nickname,
        phone_number=user_data.phone_number,
        profile_image_url=user_data.profile_image_url,
        is_phone_verified=user_data.is_phone_verified,
    )
    return UserRead.model_validate(user) if user else None
