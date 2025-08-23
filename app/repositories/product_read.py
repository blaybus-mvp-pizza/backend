from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy import select, func, desc, and_
from app.domains.common.paging import Page
from app.domains.products.admin_product import ProductAdminListItem, ProductAdminMeta
from app.domains.products.admin_store import StoreAdminMeta
from app.schemas.auctions.auction_offer import AuctionOffer
from app.schemas.orders.order import Order
from app.schemas.products import Product, ProductImage
from app.schemas.stores import PopupStore
from app.schemas.auctions import Auction, Bid
from app.domains.products.mappers import rows_to_product_items
from app.domains.products.store_meta import StoreMeta
from app.domains.products.product_meta import ProductMeta, ProductSpecs
from app.domains.products.product_list_item import ProductListItem
from app.domains.products.store_with_products import StoreWithProducts
from app.core.repository_mixins import TimezoneConversionMixin


class ProductReadRepository(TimezoneConversionMixin):
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
        bidder_count = (
            select(func.count(func.distinct(Bid.user_id)))
            .where(Bid.auction_id == Auction.id)
            .correlate(Auction)
            .scalar_subquery()
        )
        return rep_img, highest_bid, bidder_count

    def _apply_common_filters(
        self,
        stmt,
        *,
        status: Optional[str] = None,  # ALL | RUNNING | ENDED
        bidders: Optional[str] = None,  # ALL | LE_10 | BT_10_20 | GE_20
        price_bucket: Optional[
            str
        ] = None,  # ALL | LT_10000 | BT_10000_30000 | BT_30000_50000 | BT_50000_150000 | BT_150000_300000 | BT_300000_500000 | CUSTOM
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        highest_bid_subq=None,
        category: Optional[str] = None,  # ALL or concrete category string
        q: Optional[str] = None,
    ):
        # Status filter
        if status and status != "ALL":
            if status == "RUNNING":
                stmt = stmt.where(Auction.status == "RUNNING")
            elif status == "ENDED":
                stmt = stmt.where(Auction.status == "ENDED")
            elif status == "SCHEDULED":
                stmt = stmt.where(Auction.status == "SCHEDULED")

        # Bidder count filter (requires bidder_count subquery present in select or available via correlate)
        # We'll recompute bidder_count scalar_subquery for safety
        bidder_count_subq = (
            select(func.count(func.distinct(Bid.user_id)))
            .where(Bid.auction_id == Auction.id)
            .correlate(Auction)
            .scalar_subquery()
        )
        if bidders and bidders != "ALL":
            if bidders == "LE_10":
                stmt = stmt.where(bidder_count_subq <= 10)
            elif bidders == "BT_10_20":
                stmt = stmt.where(
                    and_(bidder_count_subq >= 10, bidder_count_subq <= 20)
                )
            elif bidders == "GE_20":
                stmt = stmt.where(bidder_count_subq >= 20)

        # Price filter using coalesce(current_highest_bid, Auction.start_price)
        price_expr = func.coalesce(
            (
                highest_bid_subq
                if highest_bid_subq is not None
                else (
                    select(func.max(Bid.amount))
                    .where(Bid.auction_id == Auction.id)
                    .correlate(Auction)
                    .scalar_subquery()
                )
            ),
            Auction.start_price,
        )

        bucket_to_range = {
            "LT_10000": (None, 10000),
            "BT_10000_30000": (10000, 30000),
            "BT_30000_50000": (30000, 50000),
            "BT_50000_150000": (50000, 150000),
            "BT_150000_300000": (150000, 300000),
            "BT_300000_500000": (300000, 500000),
        }
        if price_bucket and price_bucket != "ALL" and price_bucket != "CUSTOM":
            lo, hi = bucket_to_range.get(price_bucket, (None, None))
            if lo is not None:
                stmt = stmt.where(price_expr >= lo)
            if hi is not None:
                stmt = stmt.where(price_expr < hi)
        elif price_bucket == "CUSTOM":
            if price_min is not None:
                stmt = stmt.where(price_expr >= price_min)
            if price_max is not None:
                stmt = stmt.where(price_expr < price_max)

        # Category filter
        if category and category != "ALL":
            stmt = stmt.where(Product.category == category)

        # Keyword search (LIKE on product/store text fields)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Product.name.like(like),
                    Product.summary.like(like),
                    Product.description.like(like),
                    PopupStore.name.like(like),
                )
            )

        return stmt

    def _count_products_with_filters(
        self,
        *,
        base_where,
        status: Optional[str] = None,
        bidders: Optional[str] = None,
        price_bucket: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        category: Optional[str] = None,
        q: Optional[str] = None,
    ) -> int:
        # Build count select mirroring filters
        stmt = (
            select(func.count(Product.id))
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(*base_where)
        )
        stmt = self._apply_common_filters(
            stmt,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            highest_bid_subq=(
                select(func.max(Bid.amount))
                .where(Bid.auction_id == Auction.id)
                .correlate(Auction)
                .scalar_subquery()
            ),
            category=category,
            q=q,
        )
        total = self.db.execute(stmt).scalar_one()
        return int(total)

    def ending_soon_products(
        self,
        *,
        limit: int = 4,
        offset: int = 0,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort: str = "ending",
        category: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Tuple[List[ProductListItem], int]:
        rep_img, highest_bid, bidder_count = self._base_product_select()
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                highest_bid.label("current_highest_bid"),
                Auction.buy_now_price.label("buy_now_price"),
                rep_img.label("representative_image"),
                Auction.ends_at.label("auction_ends_at"),
                bidder_count.label("bidder_count"),
                Product.created_at.label("product_created_at"),
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(
                Product.is_active == 1,
                Product.is_sold == 0,
            )
        )
        stmt = self._apply_common_filters(
            stmt,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            highest_bid_subq=highest_bid,
            category=category,
            q=q,
        )
        # Sorting
        if sort == "recommended":
            price_expr = func.coalesce(highest_bid, Auction.start_price)
            stmt = stmt.order_by(desc(price_expr))
        elif sort == "popular":
            # use bidder_count
            stmt = stmt.order_by(desc(bidder_count))
        elif sort == "latest":
            stmt = stmt.order_by(Product.created_at.desc())
        else:  # ending
            stmt = stmt.order_by(Auction.ends_at.asc())
        stmt = stmt.limit(limit).offset(offset)
        rows = self.db.execute(stmt)
        total = self._count_products_with_filters(
            base_where=(Product.is_active == 1, Product.is_sold == 0),
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            category=category,
            q=q,
        )
        return rows_to_product_items(rows), total

    def recommended_products(
        self,
        *,
        limit: int = 4,
        offset: int = 0,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort: str = "recommended",
        category: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Tuple[List[ProductListItem], int]:
        rep_img, highest_bid, bid_count = self._base_product_select()
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                highest_bid.label("current_highest_bid"),
                Auction.buy_now_price.label("buy_now_price"),
                rep_img.label("representative_image"),
                Auction.ends_at.label("auction_ends_at"),
                bid_count.label("bidder_count"),
                Product.created_at.label("product_created_at"),
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(
                Product.is_active == 1,
                Product.is_sold == 0,
            )
        )
        stmt = self._apply_common_filters(
            stmt,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            highest_bid_subq=highest_bid,
            category=category,
            q=q,
        )
        # Sorting
        if sort == "recommended":
            price_expr = func.coalesce(highest_bid, Auction.start_price)
            stmt = stmt.order_by(desc(price_expr))
        elif sort == "popular":
            stmt = stmt.order_by(desc(bid_count))
        elif sort == "ending":
            stmt = stmt.order_by(Auction.ends_at.asc())
        else:
            stmt = stmt.order_by(Product.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        rows = self.db.execute(stmt)
        total = self._count_products_with_filters(
            base_where=(Product.is_active == 1, Product.is_sold == 0),
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            category=category,
            q=q,
        )
        return rows_to_product_items(rows), total

    def new_products(
        self,
        *,
        limit: int = 4,
        offset: int = 0,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort: str = "latest",
        category: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Tuple[List[ProductListItem], int]:
        rep_img, highest_bid, bidder_count = self._base_product_select()
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                highest_bid.label("current_highest_bid"),
                Auction.buy_now_price.label("buy_now_price"),
                rep_img.label("representative_image"),
                Auction.ends_at.label("auction_ends_at"),
                bidder_count.label("bidder_count"),
                Product.created_at.label("product_created_at"),
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(
                Product.is_active == 1,
                Product.is_sold == 0,
            )
        )
        stmt = self._apply_common_filters(
            stmt,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            highest_bid_subq=highest_bid,
            category=category,
            q=q,
        )
        if sort == "recommended":
            price_expr = func.coalesce(highest_bid, Auction.start_price)
            stmt = stmt.order_by(desc(price_expr))
        elif sort == "popular":
            stmt = stmt.order_by(desc(bidder_count))
        elif sort == "ending":
            stmt = stmt.order_by(Auction.ends_at.asc())
        else:
            stmt = stmt.order_by(Product.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        rows = self.db.execute(stmt)
        total = self._count_products_with_filters(
            base_where=(Product.is_active == 1, Product.is_sold == 0),
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            category=category,
            q=q,
        )
        return rows_to_product_items(rows), total

    def recent_stores_with_products(
        self,
        per_store_products: int = 4,
        offset: int = 0,
        limit_stores: int = 10,
        *,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort: str = "latest",
        category: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Tuple[List[tuple], int]:
        rep_img, highest_bid, bidder_count = self._base_product_select()
        stores_stmt = (
            select(PopupStore)
            .order_by(PopupStore.id.desc())
            .limit(limit_stores)
            .offset(offset)
        )
        stores = [row[0] for row in self.db.execute(stores_stmt)]
        total_stores = self.db.execute(select(func.count(PopupStore.id))).scalar_one()
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
                    bidder_count.label("bidder_count"),
                    Product.created_at.label("product_created_at"),
                )
                .join(PopupStore, PopupStore.id == Product.popup_store_id)
                .join(Auction, Auction.product_id == Product.id)
                .where(
                    Product.popup_store_id == store.id,
                    Product.is_active == 1,
                    Product.is_sold == 0,
                )
            )
            stmt = self._apply_common_filters(
                stmt,
                status=status,
                bidders=bidders,
                price_bucket=price_bucket,
                price_min=price_min,
                price_max=price_max,
                highest_bid_subq=highest_bid,
                category=category,
                q=q,
            )
            if sort == "recommended":
                price_expr = func.coalesce(highest_bid, Auction.start_price)
                stmt = stmt.order_by(desc(price_expr))
            elif sort == "popular":
                stmt = stmt.order_by(desc(bidder_count))
            elif sort == "ending":
                stmt = stmt.order_by(Auction.ends_at.asc())
            else:
                stmt = stmt.order_by(Product.created_at.desc())
            stmt = stmt.limit(per_store_products)
            products_rows = self.db.execute(stmt)
            result.append(
                (
                    store,
                    rows_to_product_items(products_rows),
                )
            )
        return result, int(total_stores)

    def store_list(
        self, limit: int = 20, offset: int = 0
    ) -> Tuple[List[StoreMeta], int]:
        stmt = (
            select(
                PopupStore.id,
                PopupStore.image_url,
                PopupStore.name,
                PopupStore.description,
                PopupStore.sales_description,
            )
            .order_by(PopupStore.id.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = list(self.db.execute(stmt))
        items = [
            StoreMeta(
                store_id=r[0],
                image_url=r[1],
                name=r[2],
                description=r[3],
                sales_description=r[4],
            )
            for r in rows
        ]
        total = self.db.execute(select(func.count(PopupStore.id))).scalar_one()
        return items, int(total)

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
        self,
        *,
        store_id: int,
        sort: str,
        page: int,
        size: int,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        category: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Tuple[List[ProductListItem], int]:
        rep_img, highest_bid, bid_count = self._base_product_select()
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                highest_bid.label("current_highest_bid"),
                Auction.buy_now_price.label("buy_now_price"),
                rep_img.label("representative_image"),
                Auction.ends_at.label("auction_ends_at"),
                bid_count.label("bidder_count"),
                Product.created_at.label("product_created_at"),
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(
                Product.popup_store_id == store_id,
                Product.is_active == 1,
                Product.is_sold == 0,
            )
        )
        stmt = self._apply_common_filters(
            stmt,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            highest_bid_subq=highest_bid,
            category=category,
            q=q,
        )
        if sort == "recommended":
            price_expr = func.coalesce(highest_bid, Auction.start_price)
            stmt = stmt.order_by(desc(price_expr))
        elif sort == "popular":
            stmt = stmt.order_by(desc(bid_count))
        elif sort == "ending":
            stmt = stmt.order_by(Auction.ends_at.asc())
        else:
            stmt = stmt.order_by(Product.created_at.desc())
        stmt = stmt.limit(size).offset((page - 1) * size)
        rows = self.db.execute(stmt)
        total = self._count_products_with_filters(
            base_where=(
                Product.popup_store_id == store_id,
                Product.is_active == 1,
                Product.is_sold == 0,
            ),
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            category=category,
            q=q,
        )
        return rows_to_product_items(rows), int(total)

    def upcoming_products(
        self,
        *,
        limit: int = 4,
        offset: int = 0,
        status: str = "SCHEDULED",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort: str = "ending",
        category: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Tuple[List[ProductListItem], int]:
        rep_img, highest_bid, bidder_count = self._base_product_select()
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                highest_bid.label("current_highest_bid"),
                Auction.buy_now_price.label("buy_now_price"),
                rep_img.label("representative_image"),
                Auction.starts_at.label("auction_ends_at"),
                bidder_count.label("bidder_count"),
                Product.created_at.label("product_created_at"),
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Auction, Auction.product_id == Product.id)
            .where(
                Product.is_active == 1,
                Product.is_sold == 0,
            )
        )
        stmt = self._apply_common_filters(
            stmt,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            highest_bid_subq=highest_bid,
            category=category,
            q=q,
        )
        # Sorting: reuse keys; for "ending" interpret as starts_at asc (오픈 임박)
        if sort == "recommended":
            price_expr = func.coalesce(highest_bid, Auction.start_price)
            stmt = stmt.order_by(desc(price_expr))
        elif sort == "popular":
            stmt = stmt.order_by(desc(bidder_count))
        elif sort == "latest":
            stmt = stmt.order_by(Product.created_at.desc())
        else:  # ending -> opening soon
            stmt = stmt.order_by(Auction.starts_at.asc())
        stmt = stmt.limit(limit).offset(offset)
        rows = self.db.execute(stmt)
        total = self._count_products_with_filters(
            base_where=(Product.is_active == 1, Product.is_sold == 0),
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            category=category,
            q=q,
        )
        return rows_to_product_items(rows), total

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
