from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    DateTime,
    DECIMAL,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Product(Base):
    __tablename__ = "product"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    popup_store_id = Column(BigInteger, ForeignKey("popup_store.id"), nullable=False)
    category = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    summary = Column(String(500))
    description = Column(String(1024))
    material = Column(String(120))
    place_of_use = Column(String(120))
    width_cm = Column(DECIMAL(6, 2))
    height_cm = Column(DECIMAL(6, 2))
    tolerance_cm = Column(DECIMAL(5, 2))
    edition_info = Column(String(120))
    condition_note = Column(String(255))
    price = Column(DECIMAL(12, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    shipping_base_fee = Column(Integer, nullable=False, default=2500)
    shipping_free_threshold = Column(Integer, default=30000)
    shipping_extra_note = Column(String(1024))
    courier_name = Column(String(60), default="CJ대한통운")
    is_active = Column(Integer, nullable=False, default=1)
    is_sold = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    store = relationship("PopupStore", backref="products")
    images = relationship("ProductImage", backref="product")
    # many-to-many with Tag via ProductTag
