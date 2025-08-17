from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.schemas.auctions import Auction, Bid
from app.schemas.products import Product, ProductImage
from app.schemas.stores import PopupStore
from app.domains.auctions.mappers import row_to_auction_info, rows_to_bid_items
from app.domains.auctions.auction_info import AuctionInfo
from app.domains.auctions.bid_item import BidItem
from app.domains.products.mappers import rows_to_product_items
from app.domains.products.product_list_item import ProductListItem


class AuctionReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def highest_bid_amount_subq(self, auction_id_subq=None):
        from sqlalchemy import select, func

        q = select(func.max(Bid.amount))
        if auction_id_subq is not None:
            q = q.where(Bid.auction_id == auction_id_subq)
        return q.scalar_subquery()

    def bidder_count_subq(self, auction_id_subq=None):
        from sqlalchemy import select, func

        q = select(func.count(func.distinct(Bid.user_id)))
        if auction_id_subq is not None:
            q = q.where(Bid.auction_id == auction_id_subq)
        return q.scalar_subquery()

    def get_auction_info_by_product(self, product_id: int) -> AuctionInfo | None:
        highest = self.highest_bid_amount_subq(Auction.id)
        bidders = self.bidder_count_subq(Auction.id)
        stmt = select(
            Auction.id,
            Auction.buy_now_price,
            highest.label("current_highest_bid"),
            Auction.starts_at,
            Auction.ends_at,
            Auction.start_price,
            Auction.min_bid_price,
            Auction.deposit_amount,
            bidders.label("bidder_count"),
        ).where(Auction.product_id == product_id)
        row = self.db.execute(stmt).first()
        return row_to_auction_info(row) if row else None

    def list_bids_by_product(
        self, product_id: int, limit: int = 3, offset: int = 0
    ) -> Tuple[List[BidItem], int]:
        stmt = (
            select(Bid.user_id, Bid.amount, Bid.created_at)
            .join(Auction, Auction.id == Bid.auction_id)
            .where(Auction.product_id == product_id)
            .order_by(Bid.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = self.db.execute(stmt)
        total = self.db.execute(
            select(func.count(Bid.id))
            .join(Auction, Auction.id == Bid.auction_id)
            .where(Auction.product_id == product_id)
        ).scalar_one()
        return rows_to_bid_items(rows), int(total)

    def similar_products_in_same_store(
        self, product_id: int, limit: int = 4, offset: int = 0
    ) -> Tuple[List[ProductListItem], int]:
        rep_img = (
            select(ProductImage.image_url)
            .where(ProductImage.product_id == Product.id)
            .order_by(ProductImage.sort_order.asc())
            .limit(1)
            .correlate(Product)
            .scalar_subquery()
        )
        stmt_store = select(Product.popup_store_id).where(Product.id == product_id)
        store_id = self.db.execute(stmt_store).scalar_one()
        stmt = (
            select(
                Product.id.label("product_id"),
                PopupStore.name.label("popup_store_name"),
                Product.name.label("product_name"),
                None,
                None,
                rep_img.label("representative_image"),
                None,
            )
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .where(Product.popup_store_id == store_id, Product.id != product_id)
            .order_by(Product.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = self.db.execute(stmt)
        total = self.db.execute(
            select(func.count(Product.id)).where(
                Product.popup_store_id == store_id, Product.id != product_id
            )
        ).scalar_one()
        return rows_to_product_items(rows), int(total)
