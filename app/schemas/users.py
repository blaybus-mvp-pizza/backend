from sqlalchemy import (
    JSON,
    Column,
    BigInteger,
    Enum,
    ForeignKey,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from app.db.session import Base


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    nickname = Column(String(60), nullable=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    profile_image_url = Column(Text, nullable=True)
    is_phone_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuthProvider(Base):
    __tablename__ = "auth_provider"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)

    provider = Column(
        Enum("google", "kakao", "naver", name="provider_enum"), nullable=False
    )
    provider_user_id = Column(String(191), nullable=False)
    email = Column(String(255), nullable=True)
    raw_profile_json = Column(JSON, nullable=True)

    linked_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint(provider, provider_user_id),)


class PhoneVerification(Base):
    __tablename__ = "phone_verification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone_e164 = Column(String(20), nullable=False, index=True)
    code6 = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Address(Base):
    __tablename__ = "address"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)

    recipient_name = Column(String(60), nullable=False)
    phone_e164 = Column(String(20), nullable=False)
    postcode = Column(String(10), nullable=True)
    address1 = Column(String(255), nullable=False)
    address2 = Column(String(255), nullable=True)

    is_default = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PaymentMethod(Base):
    __tablename__ = "payment_method"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)

    provider = Column(
        Enum(
            "tosspay",
            "card",
            "naverpay",
            "kakaopay",
            "virtual",
            name="payment_provider_enum",
        ),
        nullable=False,
    )
    external_key = Column(String(191), nullable=False)
    masked_info = Column(String(191), nullable=True)

    is_default = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint(user_id, provider, external_key),)
