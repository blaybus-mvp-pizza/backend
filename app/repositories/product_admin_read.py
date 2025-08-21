from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy import select, func, desc, and_
from app.domains.common.paging import Page
from app.domains.products.enums import ProductAdminStatusFilter, StatusFilter
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


class ProductAdminReadRepository:
    def __init__(self, db: Session):
        self.db = db

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

    def get_store_by_id(self, store_id: int) -> PopupStore:
        """Retrieve a store by its ID."""
        return self.db.execute(
            select(PopupStore).where(PopupStore.id == store_id)
        ).scalar_one_or_none()

    def get_product_by_id(self, product_id: int) -> Product:
        """Retrieve a product by its ID."""
        return self.db.execute(
            select(Product).where(Product.id == product_id)
        ).scalar_one_or_none()

    def product_admin_meta(self, product_id: int) -> ProductAdminMeta:
        prod = self.db.execute(
            select(Product).where(Product.id == product_id)
        ).scalar_one()
        store = self.db.execute(
            select(PopupStore).where(PopupStore.id == prod.popup_store_id)
        ).scalar_one()
        auction = self.db.execute(
            select(
                Auction.id, Auction.status, Auction.start_price, Auction.buy_now_price
            ).where(Auction.product_id == product_id)
        ).first()

        if auction:
            order_status = self.db.execute(
                select(Order.status)
                .select_from(AuctionOffer)
                .join(Order, Order.id == AuctionOffer.order_id)
                .where(AuctionOffer.auction_id == auction.id)
            ).scalar_one_or_none()
        else:
            order_status = None
        if not order_status:
            order_status = "N/A"
        images = [
            r[0]
            for r in self.db.execute(
                select(ProductImage.image_url)
                .where(ProductImage.product_id == product_id)
                .order_by(ProductImage.sort_order.asc())
            )
        ]
        from app.schemas.products import Tag, ProductTag

        tags = [
            r[0]
            for r in self.db.execute(
                select(Tag.name)
                .select_from(Tag)
                .join(ProductTag, ProductTag.tag_id == Tag.id)
                .where(ProductTag.product_id == product_id)
            )
        ]
        return ProductAdminMeta(
            id=prod.id,
            name=prod.name,
            summary=prod.summary,
            description=prod.description,
            price=prod.price,
            stock=prod.stock,
            images=images,
            category=prod.category,
            tags=tags,
            specs=ProductSpecs(
                material=prod.material,
                place_of_use=prod.place_of_use,
                width_cm=float(prod.width_cm) if prod.width_cm else None,
                height_cm=float(prod.height_cm) if prod.height_cm else None,
                tolerance_cm=float(prod.tolerance_cm) if prod.tolerance_cm else None,
                edition_info=prod.edition_info,
                condition_note=prod.condition_note,
            ),
            store_id=store.id,
            shipping_base_fee=prod.shipping_base_fee,
            shipping_free_threshold=prod.shipping_free_threshold,
            shipping_extra_note=prod.shipping_extra_note,
            courier_name=prod.courier_name,
            created_at=prod.created_at.isoformat(),
            updated_at=prod.updated_at.isoformat(),
            auction_id=auction.id if auction else None,
            status=(
                ProductAdminStatusFilter.SOLD
                if auction and auction.status == StatusFilter.ENDED
                else ProductAdminStatusFilter.AVAILABLE
            ),
            store_description=store.description,
            store_sales_description=store.sales_description,
            auction_start_price=auction.start_price if auction else None,
            auction_buy_now_price=auction.buy_now_price if auction else None,
            order_status=order_status,
        )

    def product_admin_list(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,  # ALL | available | sold
        category: Optional[str] = None,  # ALL or concrete category string
        q: Optional[str] = None,  # keyword search
    ) -> Tuple[List[ProductAdminListItem], int]:
        rep_img = (
            select(ProductImage.image_url)
            .where(ProductImage.product_id == Product.id)
            .order_by(ProductImage.sort_order.asc())
            .limit(1)
            .correlate(Product)
            .scalar_subquery()
        )
        stmt = select(func.count(Product.id)).join(
            Auction, Auction.product_id == Product.id, isouter=True
        )

        # Apply filters
        if status and status != "ALL":
            if status == ProductAdminStatusFilter.AVAILABLE:
                stmt = stmt.where(
                    or_(Auction.status != StatusFilter.ENDED, Auction.id.is_(None))
                )
            elif status == ProductAdminStatusFilter.SOLD:
                stmt = stmt.where(Auction.status == StatusFilter.ENDED)
        if category and category != "ALL":
            stmt = stmt.where(Product.category == category)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Product.name.like(like),
                    Product.summary.like(like),
                    Product.description.like(like),
                )
            )

        total = self.db.execute(stmt).scalar_one()
        list_stmt = (
            stmt.with_only_columns(
                Product.id,
                Product.name,
                rep_img.label("representative_image"),
                Product.category,
                Product.created_at,
                Product.updated_at,
                Auction.id.label("auction_id"),
                Auction.status.label("auction_status"),
            )
            .order_by(Product.id.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = self.db.execute(list_stmt)
        items = [
            ProductAdminListItem(
                id=row.id,
                name=row.name,
                representative_image=row.representative_image,
                category=row.category,
                created_at=row.created_at.isoformat(),
                updated_at=row.updated_at.isoformat(),
                auction_id=row.auction_id,
                status=(
                    ProductAdminStatusFilter.SOLD
                    if row.auction_status == StatusFilter.ENDED
                    else ProductAdminStatusFilter.AVAILABLE
                ),  # noqa: E501
            )
            for row in rows
        ]

        return items, total
