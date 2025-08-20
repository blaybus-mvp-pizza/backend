from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, DateTime
from app.db.session import Base
from sqlalchemy.sql import func


class Story(Base):
    __tablename__ = "story"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("product.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
