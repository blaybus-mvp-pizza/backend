from typing import Iterable, List
from app.core.repository_mixins import TimezoneConversionMixin
from app.domains.auctions.auction_info import AuctionInfo
from app.domains.auctions.bid_item import BidItem, UserBrief


def row_to_auction_info(row) -> AuctionInfo:
    timezone_converter = TimezoneConversionMixin()
    
    r = row._mapping if hasattr(row, "_mapping") else row
    m = timezone_converter.convert_row_datetimes(r)
    return AuctionInfo(
        auction_id=m["id"],
        buy_now_price=(
            float(m["buy_now_price"]) if m.get("buy_now_price") is not None else None
        ),
        current_highest_bid=(
            float(m["current_highest_bid"])
            if m.get("current_highest_bid") is not None
            else None
        ),
        bid_steps=[],  # steps are strategy-derived, not from row
        starts_at=m["starts_at"].isoformat(),
        ends_at=m["ends_at"].isoformat(),
        start_price=float(m["start_price"]),
        min_bid_price=float(m["min_bid_price"]),
        deposit_amount=float(m.get("deposit_amount", 0) or 0),
        bidder_count=int(m["bidder_count"]) if m.get("bidder_count") is not None else 0,
        status=m.get("status", "SCHEDULED"),
    )


def rows_to_bid_items(rows: Iterable) -> List[BidItem]:
    items: List[BidItem] = []
    for r in rows:
        user_id, amount, created_at, nickname, profile_image_url = r[0], r[1], r[2], r[3], r[4]
        items.append(
            BidItem(
                user=UserBrief(
                    id=int(user_id), name=nickname, profile_image=profile_image_url
                ),
                bid_amount=float(amount),
                bid_at=created_at.isoformat(),
            )
        )
    return items
