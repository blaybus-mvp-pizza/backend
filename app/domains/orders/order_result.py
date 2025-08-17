from pydantic import BaseModel, Field
from typing import Optional


class OrderResult(BaseModel):
    order_id: int = Field(..., description="주문 ID")
    status: str = Field(..., description="주문 상태")
    payment_id: Optional[int] = Field(None, description="결제 ID (있을 경우)")
