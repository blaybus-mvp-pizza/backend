from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schemas.payments import Payment, PaymentLog, PaymentRefund


class PaymentWriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_payment(
        self,
        *,
        user_id: int,
        amount: float,
        provider: str,
        external_tid: str | None = None,
        status: str = "PENDING"
    ) -> Payment:
        p = Payment(
            user_id=user_id,
            amount=amount,
            provider=provider,
            external_tid=external_tid,
            status=status,
        )
        self.db.add(p)
        self.db.flush()
        return p

    def update_payment_status(self, payment_id: int, status: str) -> None:
        p = self.db.get(Payment, payment_id)
        if p:
            p.status = status
            self.db.flush()

    def create_payment_log(
        self,
        *,
        payment_id: int,
        provider: str,
        amount: float,
        status: str,
        log_type: str,
        external_tid: str | None = None,
        fail_reason: str | None = None
    ) -> PaymentLog:
        log = PaymentLog(
            payment_id=payment_id,
            provider=provider,
            amount=amount,
            status=status,
            log_type=log_type,
            external_tid=external_tid,
            fail_reason=fail_reason,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def create_refund(
        self, *, payment_id: int, amount: float, reason: str | None = None
    ) -> PaymentRefund:
        r = PaymentRefund(payment_id=payment_id, amount=amount, reason=reason)
        self.db.add(r)
        self.db.flush()
        return r
