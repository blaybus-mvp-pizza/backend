from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import JSON, select
from app.schemas.users import AuthProvider, User
from app.schemas.users.phone_verification import PhoneVerification


class UserReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, identifier: str) -> Optional[User]:
        stmt = select(User).where(User.email == identifier)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_phone_number(self, phone_number: str) -> Optional[User]:
        stmt = select(User).where(User.phone_number == phone_number)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_resent_phone_verification_by_phone_number(
        self, phone_number: str
    ) -> Optional[PhoneVerification]:
        stmt = (
            select(PhoneVerification)
            .where(
                PhoneVerification.phone_number == phone_number,
                PhoneVerification.verified_at.is_(None),
            )
            .order_by(PhoneVerification.created_at.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def get_verified_phone_verification_by_phone_number(
        self, phone_number: str
    ) -> Optional[PhoneVerification]:
        stmt = select(PhoneVerification).where(
            PhoneVerification.phone_number == phone_number,
            PhoneVerification.verified_at.is_not(None),
        )
        return self.db.execute(stmt).scalars().first()
