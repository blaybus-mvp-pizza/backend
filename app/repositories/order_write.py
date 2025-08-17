from sqlalchemy.orm import Session
from app.schemas.orders import Order, OrderItem


class OrderWriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_order(
        self,
        *,
        user_id: int,
        total_amount: float,
        shipping_fee: float = 0,
        status: str = "PENDING"
    ) -> Order:
        o = Order(
            user_id=user_id,
            total_amount=int(total_amount),
            shipping_fee=int(shipping_fee),
            status=status,
        )
        self.db.add(o)
        self.db.flush()
        return o

    def add_order_item(
        self, *, order_id: int, product_id: int, quantity: int, unit_price: float
    ):
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal_amount=quantity * unit_price,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def update_order_status(self, order_id: int, status: str) -> None:
        o = self.db.get(Order, order_id)
        if o:
            o.status = status
            self.db.flush()
