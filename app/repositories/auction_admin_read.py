from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_, or_, exists
from app.schemas.auctions import Auction, Bid
from app.schemas.products import Product, ProductImage
from app.schemas.stores import PopupStore
from app.schemas.orders import Order, OrderItem, Shipment
from app.schemas.payments import Payment
from app.domains.auctions.admin_dto import AdminAuctionListItem, AdminAuctionDetail
from app.domains.auctions.enums import PaymentStatusKo, ShipmentStatusKo


class AuctionAdminReadRepository:
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
            select(func.max(Bid.amount)).where(Bid.auction_id == Auction.id).correlate(Auction).scalar_subquery()
        )

    def _bidder_count_subq(self):
        return (
            select(func.count(func.distinct(Bid.user_id))).where(Bid.auction_id == Auction.id).correlate(Auction).scalar_subquery()
        )

    def _exists_bid_subq(self):
        return exists(select(Bid.id).where(Bid.auction_id == Auction.id)).correlate(Auction)

    def _derive_payment_status(self):
        # Map Payment.status -> ko
        # CASE WHEN exists paid for product -> 확인, when exists refunded -> 취소, else 대기
        paid_exists = (
            select(func.count(Payment.id))
            .where(
                Payment.status == "PAID",
                Payment.user_id == Order.user_id,
                OrderItem.order_id == Order.id,
                OrderItem.product_id == Product.id,
            )
            .correlate(Product, Order, OrderItem, Payment)
            .scalar_subquery()
        )
        refunded_exists = (
            select(func.count(Payment.id))
            .where(
                Payment.status == "REFUNDED",
                Payment.user_id == Order.user_id,
                OrderItem.order_id == Order.id,
                OrderItem.product_id == Product.id,
            )
            .correlate(Product, Order, OrderItem, Payment)
            .scalar_subquery()
        )
        return func.case(
            (paid_exists > 0, PaymentStatusKo.CONFIRMED.value),
            (refunded_exists > 0, PaymentStatusKo.CANCELED.value),
            else_=PaymentStatusKo.PENDING.value,
        )

    def _derive_shipment_status(self):
        # shipment for the order item product
        # if exists delivered -> 완료, else if shipped -> 조회, else if order exists -> 처리, else 대기
        shipped_exists = (
            select(func.count(Shipment.id))
            .where(
                Shipment.order_id == Order.id,
                Shipment.shipped_at.isnot(None),
            )
            .correlate(Order, Shipment)
            .scalar_subquery()
        )
        delivered_exists = (
            select(func.count(Shipment.id))
            .where(
                Shipment.order_id == Order.id,
                Shipment.delivered_at.isnot(None),
            )
            .correlate(Order, Shipment)
            .scalar_subquery()
        )
        order_exists = (
            select(func.count(Order.id))
            .where(Order.id == OrderItem.order_id, OrderItem.product_id == Product.id)
            .correlate(Order, OrderItem, Product)
            .scalar_subquery()
        )
        return func.case(
            (delivered_exists > 0, ShipmentStatusKo.COMPLETED.value),
            (shipped_exists > 0, ShipmentStatusKo.INQUIRY.value),
            (order_exists > 0, ShipmentStatusKo.PROCESSING.value),
            else_=ShipmentStatusKo.WAITING.value,
        )

    def list_auctions(
        self,
        *,
        page: int,
        size: int,
        q: Optional[str],
        product_id: Optional[int],
        store_name: Optional[str],
        status: Optional[str],
        result: Optional[str],
        payment_status: Optional[str],
        shipment_status: Optional[str],
        starts_from: Optional[str],
        starts_to: Optional[str],
        ends_from: Optional[str],
        ends_to: Optional[str],
        sort: str,
    ) -> Tuple[List[AdminAuctionListItem], int]:
        rep = self._rep_image_subq()
        highest = self._highest_bid_subq()
        bidders = self._bidder_count_subq()
        any_bid = self._exists_bid_subq()

        stmt = (
            select(
                Auction.id.label("auction_id"),
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Auction.start_price,
                Auction.buy_now_price,
                Auction.starts_at,
                Auction.ends_at,
                Auction.status,
                highest.label("current_highest_bid"),
                bidders.label("bidder_count"),
            )
            .join(Product, Product.id == Auction.product_id)
        )

        # filters
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Product.name.like(like)))
        if product_id:
            stmt = stmt.where(Product.id == product_id)
        if store_name:
            stmt = stmt.join(PopupStore, PopupStore.id == Product.popup_store_id).where(
                PopupStore.name.like(f"%{store_name}%")
            )
        if status and status != "ALL":
            stmt = stmt.where(Auction.status == status)
        if result and result != "ALL":
            if result == "WON":
                stmt = stmt.where(and_(Auction.status == "ENDED", any_bid))
            elif result == "LOST":
                stmt = stmt.where(and_(Auction.status == "ENDED", ~any_bid))
        if starts_from:
            stmt = stmt.where(Auction.starts_at >= starts_from)
        if starts_to:
            stmt = stmt.where(Auction.starts_at <= starts_to)
        if ends_from:
            stmt = stmt.where(Auction.ends_at >= ends_from)
        if ends_to:
            stmt = stmt.where(Auction.ends_at <= ends_to)

        # sort
        if sort == "ending":
            stmt = stmt.order_by(Auction.ends_at.asc())
        elif sort == "popular":
            stmt = stmt.order_by(desc(bidders))
        elif sort == "recommended":
            price_expr = func.coalesce(highest, Auction.start_price)
            stmt = stmt.order_by(desc(price_expr))
        else:
            stmt = stmt.order_by(Auction.starts_at.desc())

        # 필터링된 total을 위해 기존 stmt를 이용해 count stmt 생성
        count_stmt = stmt.with_only_columns(func.count(Auction.id))
        items_rows = self.db.execute(stmt.limit(size).offset((page - 1) * size)).all()
        total = int(self.db.execute(count_stmt).scalar_one())

        # compute statuses per row lazily (simplify for now)
        result_items: List[AdminAuctionListItem] = []
        for r in items_rows:
            # derive statuses with simplified rules via separate queries if needed
            # Payment: check any PAID payment for this product
            paid = (
                self.db.execute(
                    select(func.count(Payment.id))
                    .join(Order, Order.user_id == Payment.user_id)
                    .join(OrderItem, OrderItem.order_id == Order.id)
                    .where(OrderItem.product_id == r.product_id, Payment.status == "PAID")
                ).scalar_one()
                > 0
            )
            refunded = (
                self.db.execute(
                    select(func.count(Payment.id))
                    .join(Order, Order.user_id == Payment.user_id)
                    .join(OrderItem, OrderItem.order_id == Order.id)
                    .where(OrderItem.product_id == r.product_id, Payment.status == "REFUNDED")
                ).scalar_one()
                > 0
            )
            if paid:
                payment_ko = PaymentStatusKo.CONFIRMED.value
            elif refunded:
                payment_ko = PaymentStatusKo.CANCELED.value
            else:
                payment_ko = PaymentStatusKo.PENDING.value

            # Shipment
            delivered = (
                self.db.execute(
                    select(func.count(Shipment.id))
                    .join(Order, Order.id == Shipment.order_id)
                    .join(OrderItem, OrderItem.order_id == Order.id)
                    .where(OrderItem.product_id == r.product_id, Shipment.delivered_at.isnot(None))
                ).scalar_one()
                > 0
            )
            shipped = (
                self.db.execute(
                    select(func.count(Shipment.id))
                    .join(Order, Order.id == Shipment.order_id)
                    .join(OrderItem, OrderItem.order_id == Order.id)
                    .where(OrderItem.product_id == r.product_id, Shipment.shipped_at.isnot(None))
                ).scalar_one()
                > 0
            )
            order_exists = (
                self.db.execute(
                    select(func.count(Order.id))
                    .join(OrderItem, OrderItem.order_id == Order.id)
                    .where(OrderItem.product_id == r.product_id)
                ).scalar_one()
                > 0
            )
            if delivered:
                shipment_ko = ShipmentStatusKo.COMPLETED.value
            elif shipped:
                shipment_ko = ShipmentStatusKo.INQUIRY.value
            elif order_exists:
                shipment_ko = ShipmentStatusKo.PROCESSING.value
            else:
                shipment_ko = ShipmentStatusKo.WAITING.value

            result_items.append(
                AdminAuctionListItem(
                    auction_id=int(r.auction_id),
                    product_id=int(r.product_id),
                    product_name=str(r.product_name),
                    start_price=float(r.start_price),
                    buy_now_price=float(r.buy_now_price) if r.buy_now_price is not None else None,
                    starts_at=r.starts_at.isoformat(),
                    ends_at=r.ends_at.isoformat(),
                    status=str(r.status),
                    payment_status=payment_ko,
                    shipment_status=shipment_ko,
                    is_won=(str(r.status) == "ENDED" and (
                        self.db.execute(select(func.count(Bid.id)).where(Bid.auction_id == r.auction_id)).scalar_one() > 0
                    )),
                )
            )
        return result_items, total

    def get_auction_detail(self, auction_id: int) -> Optional[AdminAuctionDetail]:
        highest = self._highest_bid_subq()
        bidders = self._bidder_count_subq()
        rep = self._rep_image_subq()
        stmt = (
            select(
                Auction.id.label("auction_id"),
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                PopupStore.name.label("store_name"),
                rep.label("representative_image"),
                Auction.start_price,
                Auction.min_bid_price,
                Auction.buy_now_price,
                Auction.deposit_amount,
                Auction.starts_at,
                Auction.ends_at,
                Auction.status,
                highest.label("current_highest_bid"),
                bidders.label("bidder_count"),
            )
            .join(Product, Product.id == Auction.product_id)
            .join(PopupStore, PopupStore.id == Product.popup_store_id)
            .where(Auction.id == auction_id)
        )
        r = self.db.execute(stmt).first()
        if not r:
            return None

        # derive statuses same as above
        paid = (
            self.db.execute(
                select(func.count(Payment.id))
                .join(Order, Order.user_id == Payment.user_id)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .where(OrderItem.product_id == r.product_id, Payment.status == "PAID")
            ).scalar_one()
            > 0
        )
        refunded = (
            self.db.execute(
                select(func.count(Payment.id))
                .join(Order, Order.user_id == Payment.user_id)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .where(OrderItem.product_id == r.product_id, Payment.status == "REFUNDED")
            ).scalar_one()
            > 0
        )
        if paid:
            payment_ko = PaymentStatusKo.CONFIRMED.value
        elif refunded:
            payment_ko = PaymentStatusKo.CANCELED.value
        else:
            payment_ko = PaymentStatusKo.PENDING.value

        delivered = (
            self.db.execute(
                select(func.count(Shipment.id))
                .join(Order, Order.id == Shipment.order_id)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .where(OrderItem.product_id == r.product_id, Shipment.delivered_at.isnot(None))
            ).scalar_one()
            > 0
        )
        shipped = (
            self.db.execute(
                select(func.count(Shipment.id))
                .join(Order, Order.id == Shipment.order_id)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .where(OrderItem.product_id == r.product_id, Shipment.shipped_at.isnot(None))
            ).scalar_one()
            > 0
        )
        order_exists = (
            self.db.execute(
                select(func.count(Order.id))
                .join(OrderItem, OrderItem.order_id == Order.id)
                .where(OrderItem.product_id == r.product_id)
            ).scalar_one()
            > 0
        )
        if delivered:
            shipment_ko = ShipmentStatusKo.COMPLETED.value
        elif shipped:
            shipment_ko = ShipmentStatusKo.INQUIRY.value
        elif order_exists:
            shipment_ko = ShipmentStatusKo.PROCESSING.value
        else:
            shipment_ko = ShipmentStatusKo.WAITING.value

        return AdminAuctionDetail(
            auction_id=int(r.auction_id),
            product_id=int(r.product_id),
            product_name=str(r.product_name),
            store_name=str(r.store_name) if r.store_name else None,
            representative_image=str(r.representative_image) if r.representative_image else None,
            start_price=float(r.start_price),
            min_bid_price=float(r.min_bid_price),
            buy_now_price=float(r.buy_now_price) if r.buy_now_price is not None else None,
            deposit_amount=float(r.deposit_amount),
            starts_at=r.starts_at.isoformat(),
            ends_at=r.ends_at.isoformat(),
            status=str(r.status),
            current_highest_bid=float(r.current_highest_bid) if r.current_highest_bid is not None else None,
            bidder_count=int(r.bidder_count),
            payment_status=payment_ko,
            shipment_status=shipment_ko,
            is_won=(str(r.status) == "ENDED" and (
                self.db.execute(select(func.count(Bid.id)).where(Bid.auction_id == r.auction_id)).scalar_one() > 0
            )),
        )


