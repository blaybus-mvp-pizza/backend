from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.schemas.products import Product, ProductImage
from app.schemas.stores import PopupStore
from app.schemas.auctions import Auction, Bid
from app.domains.products.mappers import rows_to_product_items
from app.domains.products.store_meta import StoreMeta
from app.domains.products.product_meta import ProductMeta, ProductSpecs
from app.domains.products.product_list_item import ProductListItem
from app.domains.products.store_with_products import StoreWithProducts


class ProductReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def _base_product_select(self):
        rep_img = (
            select(ProductImage.image_url)
            .where(ProductImage.product_id == Product.id)
            .order_by(ProductImage.sort_order.asc())
            .limit(1)
            .correlate(Product)
            .scalar_subquery()
        )
        highest_bid = (
            select(func.max(Bid.amount))
            .where(Bid.auction_id == Auction.id)
            .correlate(Auction)
            .scalar_subquery()
        )
        return rep_img, highest_bid

    def ending_soon_products(
        self, limit: int = 4, offset: int = 0
    ) -> List[ProductListItem]:
        rep_img, highest_bid = self._base_product_select()
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                highest_bid.label("current_highest_bid"),
                Auction.buy_now_price.label("buy_now_price"),
                rep_img.label("representative_image"),
                Auction.ends_at.label("auction_ends_at"),
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(
                Auction.status == "RUNNING",
                Product.is_active == 1,
                Product.is_sold == 0,
            )
            .order_by(Auction.ends_at.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = self.db.execute(stmt)
        return rows_to_product_items(rows)

    def recommended_products(
        self, limit: int = 4, offset: int = 0
    ) -> List[ProductListItem]:
        rep_img, highest_bid = self._base_product_select()
        bid_count = (
            select(func.count(Bid.id))
            .where(Bid.auction_id == Auction.id)
            .correlate(Auction)
            .scalar_subquery()
        )
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                highest_bid.label("current_highest_bid"),
                Auction.buy_now_price.label("buy_now_price"),
                rep_img.label("representative_image"),
                Auction.ends_at.label("auction_ends_at"),
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(
                Auction.status == "RUNNING",
                Product.is_active == 1,
                Product.is_sold == 0,
            )
            .order_by(desc(bid_count))
            .limit(limit)
            .offset(offset)
        )
        rows = self.db.execute(stmt)
        return rows_to_product_items(rows)

    def new_products(self, limit: int = 4, offset: int = 0) -> List[ProductListItem]:
        rep_img, highest_bid = self._base_product_select()
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                highest_bid.label("current_highest_bid"),
                Auction.buy_now_price.label("buy_now_price"),
                rep_img.label("representative_image"),
                Auction.ends_at.label("auction_ends_at"),
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(
                Auction.status == "RUNNING",
                Product.is_active == 1,
                Product.is_sold == 0,
            )
            .order_by(Product.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = self.db.execute(stmt)
        return rows_to_product_items(rows)

    def recent_stores_with_products(
        self, per_store_products: int = 4, offset: int = 0, limit_stores: int = 10
    ) -> List[StoreWithProducts]:
        rep_img, highest_bid = self._base_product_select()
        stores_stmt = (
            select(PopupStore)
            .order_by(PopupStore.id.desc())
            .limit(limit_stores)
            .offset(offset)
        )
        stores = [row[0] for row in self.db.execute(stores_stmt)]
        result: List[tuple] = []
        for store in stores:
            stmt = (
                select(
                    Product.id.label("product_id"),
                    PopupStore.name.label("popup_store_name"),
                    Product.name.label("product_name"),
                    highest_bid.label("current_highest_bid"),
                    Auction.buy_now_price.label("buy_now_price"),
                    rep_img.label("representative_image"),
                    Auction.ends_at.label("auction_ends_at"),
                )
                .where(Product.popup_store_id == store.id)
                .join(PopupStore, PopupStore.id == Product.popup_store_id)
                .join(Auction, Auction.product_id == Product.id)
                .where(
                    Auction.status == "RUNNING",
                    Product.is_active == 1,
                    Product.is_sold == 0,
                )
                .order_by(Product.created_at.desc())
                .limit(per_store_products)
            )
            products_rows = self.db.execute(stmt)
            result.append(
                (
                    store,
                    rows_to_product_items(products_rows),
                )
            )
        return result

    def store_list(self, limit: int = 20, offset: int = 0) -> List[StoreMeta]:
        stmt = (
            select(PopupStore.id, PopupStore.image_url, PopupStore.name)
            .order_by(PopupStore.id.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = list(self.db.execute(stmt))
        return [
            StoreMeta(
                store_id=r[0],
                image_url=r[1],
                name=r[2],
                description=None,
                sales_description=None,
            )
            for r in rows
        ]

    # --- DTO-returning methods ---
    def store_meta(self, store_id: int) -> StoreMeta:
        store = self.db.execute(
            select(PopupStore).where(PopupStore.id == store_id)
        ).scalar_one()
        return StoreMeta(
            store_id=store.id,
            image_url=store.image_url,
            name=store.name,
            description=store.description,
            sales_description=store.sales_description,
        )

    def products_by_store(
        self, *, store_id: int, sort: str, page: int, size: int
    ) -> List[ProductListItem]:
        rep_img, highest_bid = self._base_product_select()
        bid_count = (
            select(func.count(func.distinct(Auction.id)))
            .where(Auction.product_id == Product.id)
            .correlate(Product)
            .scalar_subquery()
        )
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                highest_bid.label("current_highest_bid"),
                Auction.buy_now_price.label("buy_now_price"),
                rep_img.label("representative_image"),
                Auction.ends_at.label("auction_ends_at"),
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(
                Product.popup_store_id == store_id,
                Product.is_active == 1,
                Product.is_sold == 0,
            )
        )
        if sort == "recommended":
            stmt = stmt.order_by(desc(Product.price))
        elif sort == "popular":
            stmt = stmt.order_by(desc(bid_count))
        elif sort == "ending":
            stmt = stmt.order_by(Auction.ends_at.asc())
        else:
            stmt = stmt.order_by(Product.created_at.desc())
        stmt = stmt.limit(size).offset((page - 1) * size)
        rows = self.db.execute(stmt)
        return rows_to_product_items(rows)

    def product_meta(self, product_id: int) -> ProductMeta:
        prod = self.db.execute(
            select(Product).where(Product.id == product_id)
        ).scalar_one()
        store = self.db.execute(
            select(PopupStore).where(PopupStore.id == prod.popup_store_id)
        ).scalar_one()
        images = [
            r[0]
            for r in self.db.execute(
                select(ProductImage.image_url)
                .where(ProductImage.product_id == product_id)
                .order_by(ProductImage.sort_order.asc())
            )
        ]
        from app.schemas.products import Tag, ProductTag  # local import to avoid cycles

        tags = [
            r[0]
            for r in self.db.execute(
                select(Tag.name)
                .select_from(Tag)
                .join(ProductTag, ProductTag.tag_id == Tag.id)
                .where(ProductTag.product_id == product_id)
            )
        ]
        return ProductMeta(
            id=prod.id,
            name=prod.name,
            images=images,
            tags=tags,
            title=prod.summary,
            description=prod.description,
            category=prod.category,
            store=StoreMeta(
                store_id=store.id,
                name=store.name,
                description=store.description,
                image_url=store.image_url,
            ),
            specs=ProductSpecs(
                material=prod.material,
                place_of_use=prod.place_of_use,
                width_cm=float(prod.width_cm) if prod.width_cm else None,
                height_cm=float(prod.height_cm) if prod.height_cm else None,
                tolerance_cm=float(prod.tolerance_cm) if prod.tolerance_cm else None,
                edition_info=prod.edition_info,
                condition_note=prod.condition_note,
            ),
        )
