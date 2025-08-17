from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.deps import get_db
from app.core.auth_deps import get_current_user_id
from app.domains.orders.service import OrderService
from app.domains.orders.order_result import OrderResult
from app.repositories.order_write import OrderWriteRepository
from app.repositories.payment_write import PaymentWriteRepository
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse


class BuyNowCheckoutRequest(BaseModel):
    """즉시구매 체크아웃 요청 바디

    - product_id: 상품 ID (필수)
    - unit_price: 단가/결제 금액 (필수)
    - provider: 결제 제공자 식별자 (기본값 dummy)
    """

    product_id: int
    unit_price: float
    provider: str = "dummy"


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(db, OrderWriteRepository(db), PaymentWriteRepository(db))


router = APIRouter()


@router.post(
    "/checkout/buy-now",
    response_model=OrderResult,
    summary="즉시구매 체크아웃",
    description="주문 생성과 결제를 한 번에 처리합니다. 요청자 토큰의 사용자 기준으로 결제됩니다.",
    response_description="주문 결과",
    responses={
        400: {
            "model": BusinessErrorResponse,
            "description": "비즈니스 에러",
            "content": {
                "application/json": {
                    "examples": {
                        "BUY_NOT_ALLOWED": {
                            "summary": "즉시구매 불가",
                            "value": {
                                "code": "BUY_NOT_ALLOWED",
                                "message": "즉시구매를 진행할 수 없습니다.",
                            },
                        }
                    }
                }
            },
        },
        500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
    },
)
async def checkout_buy_now(
    req: BuyNowCheckoutRequest,
    service: OrderService = Depends(get_order_service),
    user_id: int = Depends(get_current_user_id),
):
    return service.checkout_buy_now(
        user_id=user_id,
        product_id=req.product_id,
        unit_price=req.unit_price,
        provider=req.provider,
    )
