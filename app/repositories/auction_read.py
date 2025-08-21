from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_, distinct, or_
from app.schemas.auctions import Auction, Bid
from app.schemas.products import Product, ProductImage
from app.schemas.stores import PopupStore
from app.schemas.users import User
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
            Auction.status,
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
            select(Bid.user_id, Bid.amount, Bid.created_at, User.nickname, User.profile_image_url)
            .join(User, User.id == Bid.user_id)
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
        self,
        product_id: int,
        limit: int = 4,
        offset: int = 0,
        *,
        status: str = "ALL",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort: str = "latest",
        q: Optional[str] = None,
    ) -> Tuple[List[ProductListItem], int]:
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
        stmt_store = select(Product.popup_store_id).where(Product.id == product_id)
        store_id = self.db.execute(stmt_store).scalar_one()

        def apply_filters(stmt):
            # base filters
            stmt = stmt.where(
                Product.popup_store_id == store_id,
                Product.id != product_id,
            )
            # status
            if status and status != "ALL":
                if status == "RUNNING":
                    stmt = stmt.where(Auction.status == "RUNNING")
                elif status == "ENDED":
                    stmt = stmt.where(Auction.status == "ENDED")
            # bidders
            bc = (
                select(func.count(func.distinct(Bid.user_id)))
                .where(Bid.auction_id == Auction.id)
                .correlate(Auction)
                .scalar_subquery()
            )
            if bidders and bidders != "ALL":
                if bidders == "LE_10":
                    stmt = stmt.where(bc <= 10)
                elif bidders == "BT_10_20":
                    stmt = stmt.where(and_(bc >= 10, bc <= 20))
                elif bidders == "GE_20":
                    stmt = stmt.where(bc >= 20)
            # price
            price_expr = func.coalesce(highest_bid, Auction.start_price)
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
            # keyword q
            if q:
                like = f"%{q}%"
                stmt = stmt.where(
                    or_(
                        Product.name.like(like),
                        Product.summary.like(like),
                        Product.description.like(like),
                    )
                )
            return stmt

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
        )
        stmt = apply_filters(stmt)
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

        count_stmt = (
            select(func.count(Product.id))
            .join(Auction, Auction.product_id == Product.id)
            .where(Product.popup_store_id == store_id, Product.id != product_id)
        )
        count_stmt = apply_filters(count_stmt)
        total = self.db.execute(count_stmt).scalar_one()
        return rows_to_product_items(rows), int(total)

    def get_bid_by_auction_and_user(self, auction_id: int, user_id: int) -> Bid | None:
        stmt = select(Bid).where(Bid.auction_id == auction_id, Bid.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_distinct_bidder_user_ids(
        self, auction_id: int, *, exclude_user_id: Optional[int] = None
    ) -> List[int]:
        """경매의 기존 입찰자 사용자 ID 목록을 중복 없이 조회

        :param auction_id: 경매 ID
        :param exclude_user_id: 제외할 사용자 ID(현재 입찰자/구매자 등)
        :return: 사용자 ID 리스트
        """
        stmt = select(distinct(Bid.user_id)).where(Bid.auction_id == auction_id)
        if exclude_user_id is not None:
            stmt = stmt.where(Bid.user_id != exclude_user_id)
        rows = self.db.execute(stmt).all()
        return [int(row[0]) for row in rows]
