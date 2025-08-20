from typing import Tuple, List
from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from app.domains.stories.mappers import rows_to_story_items
from app.domains.stories.product_brief import ProductBrief
from app.domains.stories.story_list_item import StoryListItem
from app.domains.stories.story_meta import StoryMeta
from app.schemas.products.product import Product
from app.schemas.products.product_image import ProductImage
from app.schemas.stories.story import Story
from app.schemas.stories.story_image import StoryImage


class StoryReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def _product_rep_img_select(self):
        rep_img = (
            select(ProductImage.image_url)
            .where(ProductImage.product_id == Product.id)
            .order_by(ProductImage.sort_order.asc())
            .limit(1)
            .correlate(Product)
            .scalar_subquery()
        )
        return rep_img

    def _story_rep_img_select(self):
        rep_img = (
            select(StoryImage.image_url)
            .where(StoryImage.story_id == Story.id)
            .order_by(StoryImage.sort_order.asc())
            .limit(1)
            .correlate(Story)
            .scalar_subquery()
        )
        return rep_img

    def _count_recent_stories(self) -> int:
        stmt = select(func.count(Story.id)).join(
            Product, Product.id == Story.product_id
        )
        total = self.db.execute(stmt).scalar_one()
        return int(total)

    def get_story_meta_with_product_brief(self, story_id: int) -> StoryMeta | None:
        story = self.db.execute(
            select(Story).where(Story.id == story_id)
        ).scalar_one_or_none()
        if not story:
            return None
        story_images = [
            r[0]
            for r in self.db.execute(
                select(StoryImage.image_url)
                .where(StoryImage.story_id == story_id)
                .order_by(StoryImage.sort_order.asc())
            )
        ]
        product_rep_img = self._product_rep_img_select()
        product_brief = self.db.execute(
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Product.summary.label("product_summary"),
                product_rep_img.label("product_image"),
            ).where(Product.id == story.product_id)
        ).first()
        print(product_brief)
        return StoryMeta(
            story_id=story.id,
            product=ProductBrief(
                id=product_brief.product_id,
                name=product_brief.product_name,
                summary=product_brief.product_summary,
                image=product_brief.product_image,
            ),
            title=story.title,
            content=story.content,
            created_at=story.created_at.isoformat(),
            images=story_images,
        )

    def recent_story_items_with_product_brief(
        self,
        limit: int = 9,
        offset: int = 0,
    ) -> Tuple[List[StoryListItem], int]:
        product_rep_img = self._product_rep_img_select()
        story_rep_img = self._story_rep_img_select()
        stmt = (
            select(
                Story.id.label("story_id"),
                Story.title.label("title"),
                Story.content.label("content"),
                Story.created_at.label("created_at"),
                Story.product_id.label("product_id"),
                story_rep_img.label("representative_image"),
                Product.name.label("product_name"),
                Product.summary.label("product_summary"),
                product_rep_img.label("product_image"),
            )
            .join(Product, Product.id == Story.product_id)
            .order_by(Story.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = self.db.execute(stmt)
        total = self._count_recent_stories()
        return rows_to_story_items(rows), int(total)
