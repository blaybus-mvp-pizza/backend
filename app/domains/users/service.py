from datetime import timedelta, datetime
import random
import re
import string
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import JSON
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import BusinessError
from app.domains.common.tx import transactional
from app.domains.users.models import (
    PhoneVerificationResult,
    SendSMSResult,
    UserRead,
    UserUpdate,
)
from app.core.security import get_password_hash, verify_password
from app.repositories.user_read import UserReadRepository
from app.repositories.user_write import UserWriteRepository
from app.schemas.users import User as UserEntity
from solapi import SolapiMessageService
from solapi.model import RequestMessage


class UserService:
    def __init__(
        self,
        sesion: Session,
        user_read: UserReadRepository,
        user_write: UserWriteRepository,
    ):
        self.session = sesion
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
        user = self.user_read.get_user_by_email(email)
        if user:
            return UserRead.model_validate(user)
        with transactional(self.session):
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
            raise BusinessError(code=400, message="Phone verification is required")
        if user_data.is_phone_verified:
            verification = (
                self.user_read.get_verified_phone_verification_by_phone_number(
                    phone_number=user_data.phone_number
                )
            )
            if not verification or verification.verified_at is None:
                raise BusinessError(
                    code=400, message="Phone number must be verified before updating"
                )
        with transactional(self.session):
            user = self.user_write.update_user(
                user=user,
                nickname=user_data.nickname,
                phone_number=user_data.phone_number,
                profile_image_url=user_data.profile_image_url,
                is_phone_verified=user_data.is_phone_verified,
            )
            return UserRead.model_validate(user) if user else None

    def send_phone_verification_sms(
        self, phone_number: str, user_id: int
    ) -> SendSMSResult:
        user = self.user_read.get_user_by_id(user_id)
        if not user:
            raise BusinessError(code=400, message="User not found")
        # Accept E.164 or local formats
        regExp = re.compile(r"^(\+?\d{8,15}|(?:0\d{1,2})-?\d{3,4}-?\d{4})$")
        if not regExp.match(phone_number):
            raise BusinessError(code=400, message="Invalid phone number format")

        # 다른 유저의 휴대폰번호 사용을 막습니다
        existing_user = self.user_read.get_user_by_phone_number(phone_number)
        if existing_user and existing_user.id != user_id:
            raise BusinessError(
                code=400, message="Phone number already in use by another user"
            )
        # 휴대폰번호 인증 SMS를 전송합니다
        with transactional(self.session):
            verification_code = "".join(random.choices(string.digits, k=6))
            expires_at = datetime.now() + timedelta(minutes=3)
            self.user_write.create_phone_verification(
                phone_number=phone_number,
                code6=verification_code,
                expires_at=expires_at,
            )
            # In test/integration without real SMS credentials, bypass actual send
            if not settings.SMS_API_KEY:
                return SendSMSResult(success=True, expires_at=expires_at.isoformat())
            else:
                message_service = SolapiMessageService(
                    api_key=settings.SMS_API_KEY, api_secret=settings.SMS_API_SECRET
                )
                message = RequestMessage(
                    from_=settings.SENDER_NUMBER,
                    to=phone_number,
                    text=f"인증번호는 {verification_code}입니다.",
                )
                response = message_service.send(message)
                if response.group_info.count.registered_success > 0:
                    return SendSMSResult(success=True, expires_at=expires_at.isoformat())
                else:
                    raise Exception(status_code=500, detail="Failed to send SMS")

    def verify_phone_verification_sms(
        self, phone_number: str, code6: str, user_id: int
    ) -> PhoneVerificationResult:
        verification = self.user_read.get_resent_phone_verification_by_phone_number(
            phone_number=phone_number
        )
        if not verification or verification.code6 != code6:
            raise BusinessError(code=400, message="Invalid verification code")

        if verification.verified_at is not None:
            raise BusinessError(code=400, message="Phone number already verified")

        if verification.expires_at < datetime.now():
            raise BusinessError(code=400, message="Verification code expired")

        with transactional(self.session):
            self.user_write.set_phone_verification_as_verified(
                verification=verification,
                verified_at=datetime.now(),
            )
            return PhoneVerificationResult(success=True)
