from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_, or_, exists

from app.schemas.auctions import Auction, Bid
from app.schemas.products import Product, ProductImage
from app.schemas.orders import Order, OrderItem, Shipment
from app.schemas.payments import Payment
from app.domains.auctions.user_dto import (
    UserAuctionDashboard,
    UserRelatedAuctionItem,
    MyAuctionItemStatus,
)


class UserAuctionReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def _rep_image_subq(self):
        return (
            select(ProductImage.image_url)
            .where(ProductImage.product_id == Product.id)
            .order_by(ProductImage.sort_order.asc())
            .limit(1)
            .correlate(Product)
            .scalar_subquery()
        )

    def _highest_bid_subq(self):
        return (
            select(func.max(Bid.amount))
            .where(Bid.auction_id == Auction.id)
            .correlate(Auction)
            .scalar_subquery()
        )

    def _my_highest_bid_subq(self, user_id_subq=None):
        q = select(func.max(Bid.amount))
        if user_id_subq is not None:
            q = q.where(Bid.user_id == user_id_subq)
        return q

    def dashboard_counts(self, *, user_id: int) -> UserAuctionDashboard:
        # running bids: distinct auctions where user has at least one bid and auction is RUNNING
        running_count = (
            self.db.execute(
                select(func.count(func.distinct(Auction.id)))
                .join(Bid, Bid.auction_id == Auction.id)
                .where(Bid.user_id == user_id, Auction.status == "RUNNING")
            ).scalar_one()
        )

        # pre-shipment: user won (has PAID payment or order exists) but no shipment shipped/delivered
        # Criteria: exists order item for user's product with Payment.PAID and Shipment.shipped_at is NULL
        preship_count = (
            self.db.execute(
                select(func.count(func.distinct(Product.id)))
                .select_from(Product)
                .join(Auction, Auction.product_id == Product.id)
                .join(Bid, Bid.auction_id == Auction.id)
                .join(OrderItem, OrderItem.product_id == Product.id, isouter=True)
                .join(Order, Order.id == OrderItem.order_id, isouter=True)
                .join(Shipment, Shipment.order_id == Order.id, isouter=True)
                .join(Payment, Payment.user_id == Bid.user_id, isouter=True)
                .where(
                    Bid.user_id == user_id,
                    Auction.status == "ENDED",
                    Payment.status == "PAID",
                    Shipment.shipped_at.is_(None),
                )
            ).scalar_one()
        )

        # shipping: shipment.shipped_at not null and delivered_at is null
        shipping_count = (
            self.db.execute(
                select(func.count(func.distinct(Product.id)))
                .select_from(Product)
                .join(OrderItem, OrderItem.product_id == Product.id)
                .join(Order, Order.id == OrderItem.order_id)
                .join(Shipment, Shipment.order_id == Order.id)
                .where(Order.user_id == user_id, Shipment.shipped_at.isnot(None), Shipment.delivered_at.is_(None))
            ).scalar_one()
        )

        # delivered: shipment.delivered_at not null
        delivered_count = (
            self.db.execute(
                select(func.count(func.distinct(Product.id)))
                .select_from(Product)
                .join(OrderItem, OrderItem.product_id == Product.id)
                .join(Order, Order.id == OrderItem.order_id)
                .join(Shipment, Shipment.order_id == Order.id)
                .where(Order.user_id == user_id, Shipment.delivered_at.isnot(None))
            ).scalar_one()
        )

        return UserAuctionDashboard(
            running_bid_count=int(running_count),
            pre_shipment_count=int(preship_count),
            shipping_count=int(shipping_count),
            delivered_count=int(delivered_count),
        )

    def list_user_related_items(
        self,
        *,
        user_id: int,
        page: int,
        size: int,
        period_from: Optional[datetime],
        period_to: Optional[datetime],
        keyword: Optional[str],
    ) -> Tuple[List[UserRelatedAuctionItem], int]:
        rep = self._rep_image_subq()
        highest = self._highest_bid_subq()

        # last/my highest bid time per auction
        my_last_bid_at_subq = (
            select(func.max(Bid.created_at))
            .where(Bid.auction_id == Auction.id, Bid.user_id == user_id)
            .correlate(Auction)
            .scalar_subquery()
        )

        stmt = (
            select(
                Product.id.label("product_id"),
                Auction.id.label("auction_id"),
                Product.name.label("product_name"),
                rep.label("image_url"),
                highest.label("current_highest_bid"),
                my_last_bid_at_subq.label("my_last_bid_at"),
            )
            .join(Auction, Auction.product_id == Product.id)
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Bid, Bid.auction_id == Auction.id)
            .where(Bid.user_id == user_id)
        )

        if period_from:
            stmt = stmt.where(Bid.created_at >= period_from)
        if period_to:
            stmt = stmt.where(Bid.created_at <= period_to)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(or_(Product.name.like(like), PopupStore.name.like(like)))

        # sort: latest by my bid time desc
        stmt = stmt.order_by(desc(my_last_bid_at_subq)).limit(size).offset((page - 1) * size)

        rows = self.db.execute(stmt).all()

        # count
        count_stmt = (
            select(func.count(func.distinct(Product.id)))
            .join(Auction, Auction.product_id == Product.id)
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .join(Bid, Bid.auction_id == Auction.id)
            .where(Bid.user_id == user_id)
        )
        if period_from:
            count_stmt = count_stmt.where(Bid.created_at >= period_from)
        if period_to:
            count_stmt = count_stmt.where(Bid.created_at <= period_to)
        if keyword:
            like = f"%{keyword}%"
            count_stmt = count_stmt.where(or_(Product.name.like(like), PopupStore.name.like(like)))
        total = int(self.db.execute(count_stmt).scalar_one())

        # derive my highest bid per auction
        items: List[UserRelatedAuctionItem] = []
        for r in rows:
            my_highest = (
                self.db.execute(
                    select(func.max(Bid.amount)).where(Bid.user_id == user_id, Bid.auction_id == r.auction_id)
                ).scalar_one()
            )

            # status mapping
            # - RUNNING -> 경매 진행중
            # - ENDED with I am winner and payment paid -> 낙찰 확정
            # - ENDED -> 경매 종료
            # - PAUSED -> 경매 일시중지
            # - Shipment: shipped_at -> 배송중, delivered_at -> 배송완료
            auction_status = self.db.execute(
                select(Auction.status).where(Auction.id == r.auction_id)
            ).scalar_one()

            # check my order and shipment
            order_row = self.db.execute(
                select(Order.id)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .where(Order.user_id == user_id, OrderItem.product_id == r.product_id)
            ).first()
            shipment_status: Optional[str] = None
            if order_row:
                order_id = int(order_row[0])
                shipped = self.db.execute(
                    select(func.count(Shipment.id)).where(Shipment.order_id == order_id, Shipment.shipped_at.isnot(None))
                ).scalar_one() > 0
                delivered = self.db.execute(
                    select(func.count(Shipment.id)).where(Shipment.order_id == order_id, Shipment.delivered_at.isnot(None))
                ).scalar_one() > 0
                if delivered:
                    shipment_status = "DELIVERED"
                elif shipped:
                    shipment_status = "SHIPPING"

            if shipment_status == "DELIVERED":
                item_status = MyAuctionItemStatus.DELIVERED
            elif shipment_status == "SHIPPING":
                item_status = MyAuctionItemStatus.SHIPPING
            elif auction_status == "RUNNING":
                item_status = MyAuctionItemStatus.RUNNING
            elif auction_status == "PAUSED":
                item_status = MyAuctionItemStatus.PAUSED
            elif auction_status == "ENDED":
                # am I winner and paid?
                paid = (
                    self.db.execute(
                        select(func.count(Payment.id))
                        .join(Order, Order.user_id == Payment.user_id)
                        .join(OrderItem, OrderItem.order_id == Order.id)
                        .where(
                            Order.user_id == user_id,
                            OrderItem.product_id == r.product_id,
                            Payment.status == "PAID",
                        )
                    ).scalar_one()
                    > 0
                )
                item_status = MyAuctionItemStatus.WON_CONFIRMED if paid else MyAuctionItemStatus.AUCTION_ENDED
            else:
                item_status = MyAuctionItemStatus.AUCTION_ENDED

            items.append(
                UserRelatedAuctionItem(
                    product_id=int(r.product_id),
                    auction_id=int(r.auction_id),
                    image_url=str(r.image_url) if r.image_url else None,
                    product_name=str(r.product_name),
                    current_highest_bid=float(r.current_highest_bid) if r.current_highest_bid is not None else None,
                    my_bid_amount=float(my_highest) if my_highest is not None else None,
                    status=item_status,
                    my_last_bid_at=r.my_last_bid_at.isoformat() if r.my_last_bid_at else "",
                )
            )

        return items, total


