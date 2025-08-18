from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import JSON, select
from app.schemas.users import AuthProvider, User
from app.schemas.users.phone_verification import PhoneVerification


class UserWriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        email: str,
        nickname: str,
        provider: str,
        provider_user_id: str,
        raw_profile_json: JSON,
    ) -> User:
        user = User(
            email=email,
            nickname=nickname,
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def update_user(
        self,
        user: User,
        nickname: str,
        phone_number: Optional[str] = None,
        profile_image_url: Optional[str] = None,
        is_phone_verified: bool = False,
    ) -> Optional[User]:
        user.nickname = nickname
        user.phone_number = phone_number
        user.profile_image_url = profile_image_url
        user.is_phone_verified = is_phone_verified
        self.db.refresh(user)
        return user

    def create_auth_provider(
        self,
        user_id: int,
        provider: str,
        provider_user_id: str,
        email: str,
        raw_profile_json: JSON,
    ) -> AuthProvider:
        auth = AuthProvider(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            raw_profile_json=raw_profile_json,
        )
        self.db.add(auth)
        self.db.flush()
        return auth

    def create_phone_verification(
        self,
        phone_number: str,
        code6: str,
        expires_at: datetime,
        verified_at: Optional[datetime] = None,
    ) -> PhoneVerification:
        phone_verification = PhoneVerification(
            phone_number=phone_number,
            code6=code6,
            expires_at=expires_at,
            verified_at=verified_at,
        )
        self.db.add(phone_verification)
        self.db.flush()
        return phone_verification

    def set_phone_verification_as_verified(
        self, verification: PhoneVerification, verified_at: datetime
    ) -> PhoneVerification:
        verification.verified_at = verified_at
        self.db.refresh(verification)
        return verification
