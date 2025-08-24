from typing import Iterable, List
from datetime import datetime, timedelta
from app.domains.products.product_list_item import ProductListItem
from app.core.repository_mixins import TimezoneConversionMixin


def rows_to_product_items(rows: Iterable) -> List[ProductListItem]:
    items: List[ProductListItem] = []
    now = datetime.utcnow()
    timezone_converter = TimezoneConversionMixin()
    
    for r in rows:
        # 시간대 변환 적용
        m = timezone_converter.convert_row_datetimes(r)
        labels: List[str] = []
        # 신규상품: 생성일 10일 이내
        created_at = m.get("product_created_at") or m.get("created_at")
        if created_at and isinstance(created_at, datetime):
            if now - created_at <= timedelta(days=10):
                labels.append("신규상품")
        # 베스트: 입찰자 1명 이상
        bidder_count = m.get("bidder_count") or m.get("bid_count")
        try:
            if bidder_count is not None and int(bidder_count) >= 1:
                labels.append("베스트")
        except Exception:
            pass
        items.append(
            ProductListItem(
                product_id=m["product_id"],
                popup_store_name=m["popup_store_name"],
                product_name=m["product_name"],
                auction_status=m.get("auction_status"),
                current_highest_bid=(
                    float(m["current_highest_bid"])
                    if m.get("current_highest_bid") is not None
                    else None
                ),
                buy_now_price=(
                    float(m["buy_now_price"])
                    if m.get("buy_now_price") is not None
                    else None
                ),
                representative_image=m.get("representative_image"),
                auction_starts_at=m.get("auction_starts_at"),
                auction_ends_at=m.get("auction_ends_at"),
                labels=labels,
            )
        )
    return items
