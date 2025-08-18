from pydantic import BaseModel


class BidResult(BaseModel):
    bid_id: int
    amount: float
