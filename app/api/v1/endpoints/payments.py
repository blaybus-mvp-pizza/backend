from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.auth_deps import get_current_user_id
from app.domains.payments.service import PaymentService
from app.domains.payments.dto import (
    ChargeRequest,
    ChargeResult,
    RefundRequest,
    RefundResult,
)
from app.repositories.payment_write import PaymentWriteRepository


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db, PaymentWriteRepository(db))


class PaymentsAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.post("/charge", response_model=ChargeResult)
        async def charge(
            req: ChargeRequest,
            service: PaymentService = Depends(get_payment_service),
            user_id: int = Depends(get_current_user_id),
        ):
            req.user_id = user_id
            return service.charge(req)

        @self.router.post("/refund", response_model=RefundResult)
        async def refund(
            req: RefundRequest,
            service: PaymentService = Depends(get_payment_service),
        ):
            return service.refund(req)


api = PaymentsAPI().router
