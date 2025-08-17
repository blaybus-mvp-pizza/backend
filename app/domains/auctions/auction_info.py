from pydantic import BaseModel
from typing import List, Optional


class AuctionInfo(BaseModel):
    auction_id: int
    buy_now_price: Optional[float]
    current_highest_bid: Optional[float]
    bid_steps: List[float]
    starts_at: str
    ends_at: str
    start_price: float
    min_bid_price: float
    deposit_amount: float
    bidder_count: int
