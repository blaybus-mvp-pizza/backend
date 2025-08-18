from sqlalchemy import BigInteger, Column, DateTime, String, func
from app.db.session import Base


class PhoneVerification(Base):
    __tablename__ = "phone_verification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False, index=True)
    code6 = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
