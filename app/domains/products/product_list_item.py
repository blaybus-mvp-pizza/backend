from pydantic import BaseModel
from typing import Optional


class ProductListItem(BaseModel):
    product_id: int
    popup_store_name: str
    product_name: str
    current_highest_bid: Optional[float] = None
    buy_now_price: Optional[float] = None
    representative_image: Optional[str] = None
    auction_ends_at: Optional[str] = None
