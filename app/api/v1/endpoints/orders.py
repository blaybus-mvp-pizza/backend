from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.deps import get_db
from app.core.auth_deps import get_current_user_id
from app.domains.orders.service import OrderService
from app.domains.orders.order_result import OrderResult
from app.repositories.order_write import OrderWriteRepository
from app.repositories.payment_write import PaymentWriteRepository


class BuyNowCheckoutRequest(BaseModel):
    product_id: int
    unit_price: float
    provider: str = "dummy"


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(db, OrderWriteRepository(db), PaymentWriteRepository(db))


router = APIRouter()


@router.post("/checkout/buy-now", response_model=OrderResult)
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
