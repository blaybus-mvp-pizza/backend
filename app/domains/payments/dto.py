from pydantic import BaseModel, Field
from typing import Optional


class ChargeRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="결제 사용자 ID (토큰에서 주입)")
    amount: float = Field(..., description="결제 금액")
    provider: str = Field("dummy", description="결제 제공자 식별자")
    note: Optional[str] = Field(None, description="비고")


class ChargeResult(BaseModel):
    payment_id: int = Field(..., description="결제 ID")
    status: str = Field(..., description="결제 상태")


class RefundRequest(BaseModel):
    payment_id: int = Field(..., description="환불할 결제 ID")
    amount: float = Field(..., description="환불 금액")
    reason: Optional[str] = Field(None, description="환불 사유")


class RefundResult(BaseModel):
    refund_id: int = Field(..., description="환불 ID")
    status: str = Field(..., description="환불 상태")
