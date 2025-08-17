from pydantic import BaseModel
from typing import Optional


class OrderResult(BaseModel):
    order_id: int
    status: str
    payment_id: Optional[int] = None
