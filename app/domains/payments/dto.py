from pydantic import BaseModel
from typing import Optional


class ChargeRequest(BaseModel):
    user_id: int
    amount: float
    provider: str = "dummy"
    note: Optional[str] = None


class ChargeResult(BaseModel):
    payment_id: int
    status: str


class RefundRequest(BaseModel):
    payment_id: int
    amount: float
    reason: Optional[str] = None


class RefundResult(BaseModel):
    refund_id: int
    status: str
