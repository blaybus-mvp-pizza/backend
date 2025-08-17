from typing import Callable
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.repositories.product_read import ProductReadRepository
from app.repositories.auction_read import AuctionReadRepository
from app.repositories.auction_write import AuctionWriteRepository
from app.repositories.order_write import OrderWriteRepository
from app.repositories.payment_write import PaymentWriteRepository
from app.repositories.notification_write import NotificationWriteRepository
from app.repositories.auction_deposit import AuctionDepositRepository


class SqlAlchemyUnitOfWork:
    """Unit of Work: manages a session and exposes repos bound to that session."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal):
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        # bind repositories
        self.products = ProductReadRepository(self.session)
        self.auctions_read = AuctionReadRepository(self.session)
        self.auctions_write = AuctionWriteRepository(self.session)
        self.orders = OrderWriteRepository(self.session)
        self.payments = PaymentWriteRepository(self.session)
        self.notifications = NotificationWriteRepository(self.session)
        self.auction_deposits = AuctionDepositRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            self.session.close()

    # optional explicit API
    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
