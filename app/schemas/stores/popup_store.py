from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class PopupStore(Base):
    __tablename__ = "popup_store"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    description = Column(String(1024))
    sales_description = Column(String(1024))
    image_url = Column(String(1024))
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
