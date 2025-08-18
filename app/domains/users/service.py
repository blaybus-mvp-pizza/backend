from typing import Optional
from sqlalchemy import JSON
from sqlalchemy.orm import Session
from app.domains.common.tx import transactional
from app.domains.users.models import UserRead, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.repositories.user_read import UserReadRepository
from app.repositories.user_write import UserWriteRepository
from app.schemas.users import User as UserEntity


class UserService:
    def __init__(
        self,
        db: Session,
        user_read: UserReadRepository,
        user_write: UserWriteRepository,
    ):
        self.db = db
        self.user_read = user_read
        self.user_write = user_write

    def signup_user_with_oauth(
        self,
        email: str,
        nickname: str,
        provider: str,
        provider_user_id: str,
        raw_profile_json: JSON,
    ) -> UserRead:
        user = self.user_read.get_user_by_email(self.db, email)
        with transactional(self.session):
            if user:
                return user
            user = self.user_write.create_user(
                email=email,
                nickname=nickname,
                provider=provider,
                provider_user_id=provider_user_id,
                raw_profile_json=raw_profile_json,
            )
            self.user_write.create_auth_provider(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                email=email,
                raw_profile_json=raw_profile_json,
            )
            return UserRead.model_validate(user)

    def get_user_info(self, user_id: int) -> Optional[UserRead]:
        user = self.user_read.get_user_by_id(user_id)
        return UserRead.model_validate(user) if user else None

    def update_user_info(
        self, user_id: int, user_data: UserUpdate
    ) -> Optional[UserRead]:
        user = self.user_read.get_user_by_id(user_id)
        if not user:
            return None
        if (user_data.phone_number is not None) and (
            user_data.is_phone_verified is False
        ):
            raise ValueError("Phone verification is required")
        with transactional(self.session):
            user = self.user_write.update_user(
                user=user,
                nickname=user_data.nickname,
                phone_number=user_data.phone_number,
                profile_image_url=user_data.profile_image_url,
                is_phone_verified=user_data.is_phone_verified,
            )
            return UserRead.model_validate(user) if user else None
