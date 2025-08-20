from typing import Iterable, List

from app.domains.stories.product_brief import ProductBrief
from app.domains.stories.story_list_item import StoryListItem


def rows_to_story_items(rows: Iterable) -> List[StoryListItem]:
    items: List[StoryListItem] = []
    for r in rows:
        m = r._mapping if hasattr(r, "_mapping") else r
        items.append(
            StoryListItem(
                story_id=m["story_id"],
                product=ProductBrief(
                    id=m["product_id"],
                    name=m["product_name"],
                    summary=m["product_summary"],
                    image=m.get("product_image", ""),
                ),
                title=m["title"],
                content=m["content"],
                representative_image=m.get("representative_image", ""),
            )
        )
    return items
