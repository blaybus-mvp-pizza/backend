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

        @self.router.post(
            "/charge",
            response_model=ChargeResult,
            summary="결제 승인",
            description="사용자 토큰 기준으로 결제를 생성하고 승인합니다.",
            response_description="결제 결과",
        )
        async def charge(
            req: ChargeRequest,
            service: PaymentService = Depends(get_payment_service),
            user_id: int = Depends(get_current_user_id),
        ):
            req.user_id = user_id
            return service.charge(req)

        @self.router.post(
            "/refund",
            response_model=RefundResult,
            summary="환불",
            description="결제 건에 대한 환불을 처리합니다.",
            response_description="환불 결과",
        )
        async def refund(
            req: RefundRequest,
            service: PaymentService = Depends(get_payment_service),
        ):
            return service.refund(req)


api = PaymentsAPI().router
