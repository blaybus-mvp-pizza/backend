from pydantic import BaseModel
from typing import Optional


class BuyNowResult(BaseModel):
    status: str
    payment_id: Optional[int] = None
