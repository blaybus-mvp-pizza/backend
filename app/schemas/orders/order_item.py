from sqlalchemy import Column, BigInteger, Integer, DECIMAL, ForeignKey
from app.db.session import Base


class OrderItem(Base):
    __tablename__ = "order_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("order.id"), nullable=False)
    product_id = Column(BigInteger, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    subtotal_amount = Column(DECIMAL(12, 2), nullable=False)
