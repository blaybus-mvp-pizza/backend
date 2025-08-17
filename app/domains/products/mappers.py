from typing import Iterable, List
from app.domains.products.product_list_item import ProductListItem


def rows_to_product_items(rows: Iterable) -> List[ProductListItem]:
    items: List[ProductListItem] = []
    for r in rows:
        m = r._mapping if hasattr(r, "_mapping") else r
        items.append(
            ProductListItem(
                product_id=m["product_id"],
                popup_store_name=m["popup_store_name"],
                product_name=m["product_name"],
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
                auction_ends_at=(
                    m["auction_ends_at"].isoformat()
                    if m.get("auction_ends_at")
                    else None
                ),
            )
        )
    return items
