from sqlalchemy.orm import Session
from app.domains.payments.dto import (
    ChargeRequest,
    ChargeResult,
    RefundRequest,
    RefundResult,
)
from app.repositories.payment_write import PaymentWriteRepository
from app.domains.common.tx import transactional


class PaymentService:
    def __init__(self, session: Session, payments_repo: PaymentWriteRepository):
        self.session = session
        self.payments = payments_repo

    def charge(self, req: ChargeRequest) -> ChargeResult:
        """결제 승인 처리

        - 결제/로그 생성 후 PAID 반환
        :return: ChargeResult(payment_id, status)
        """
        with transactional(self.session):
            p = self.payments.create_payment(
                user_id=req.user_id,
                amount=req.amount,
                provider=req.provider,
                status="PAID",
            )
            self.payments.create_payment_log(
                payment_id=p.id,
                provider=req.provider,
                amount=req.amount,
                status="PAID",
                log_type="REQUEST",
            )
            return ChargeResult(payment_id=p.id, status="PAID")

    def refund(self, req: RefundRequest) -> RefundResult:
        """환불 처리

        - 환불 레코드/로그 생성 후 결제 상태를 REFUNDED로 전환
        :return: RefundResult(refund_id, status)
        """
        with transactional(self.session):
            r = self.payments.create_refund(
                payment_id=req.payment_id, amount=req.amount, reason=req.reason or ""
            )
            self.payments.create_payment_log(
                payment_id=req.payment_id,
                provider="dummy",
                amount=req.amount,
                status="REFUNDED",
                log_type="REFUND",
            )
            self.payments.update_payment_status(req.payment_id, status="REFUNDED")
            return RefundResult(refund_id=r.id, status="REFUNDED")
