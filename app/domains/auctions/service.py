from sqlalchemy.orm import Session
from app.core.errors import BusinessError
from app.core.error_codes import ErrorCode
from app.domains.auctions.verification import BidVerificator
from app.domains.auctions.enums import AuctionStatus
from app.domains.auctions.bid_result import BidResult
from app.domains.auctions.buy_now_result import BuyNowResult
from app.domains.common.tx import transactional
from app.schemas.auctions import Auction
from app.repositories.auction_read import AuctionReadRepository
from app.repositories.auction_write import AuctionWriteRepository
from app.repositories.order_write import OrderWriteRepository
from app.repositories.payment_write import PaymentWriteRepository
from app.repositories.auction_deposit import AuctionDepositRepository
from app.domains.notifications.service import NotificationService
from app.domains.notifications.dto import NotifyRequest
from app.domains.orders.service import OrderService
from app.schemas.auctions import AuctionOffer
from app.schemas.auctions.bid import Bid


class AuctionService:
    def __init__(
        self,
        session: Session,
        auctions_read: AuctionReadRepository,
        auctions_write: AuctionWriteRepository,
        orders: OrderWriteRepository,
        payments: PaymentWriteRepository,
        deposits: AuctionDepositRepository,
        notifications: NotificationService,
    ):
        self.session = session
        self.auctions_read = auctions_read
        self.auctions_write = auctions_write
        self.orders = orders
        self.payments = payments
        self.deposits = deposits
        self.notifications = notifications

    def place_bid(self, *, auction_id: int, amount: float, user_id: int) -> BidResult:
        """입찰 처리

        - 경매 상태/금액 검증 후 입찰 생성
        - 필요 시 보증금(Deposit) 결제 생성
        :return: BidResult(bid_id, amount)
        """
        verifier = BidVerificator(self.session)
        with transactional(self.session):
            print("검증")
            auction = verifier.ensure_auction_exists_and_running(auction_id)
            deposit_amount = verifier.ensure_amount_allowed(
                auction_product_id=auction.product_id, amount=amount
            )
            verifier.ensure_not_already_bid(auction_id, user_id)
            print("검증완료")
            if deposit_amount > 0:
                payment = self.payments.create_payment(
                    user_id=user_id,
                    amount=float(deposit_amount),
                    provider="dummy",
                    status="PAID",
                )
                self.payments.create_payment_log(
                    payment_id=payment.id,
                    provider="dummy",
                    amount=float(deposit_amount),
                    status="PAID",
                    log_type="REQUEST",
                )
                self.deposits.create(
                    auction_id=auction_id,
                    user_id=user_id,
                    payment_id=payment.id,
                    amount=float(deposit_amount),
                    status="PAID",
                )
                self.send_bid_notification(auction, user_id, amount)
            bid = self.auctions_write.place_bid(auction_id, user_id, amount)

            return BidResult(bid_id=bid.id, amount=float(bid.amount))

    def send_bid_notification(self, auction: Auction, user_id: int, amount: float):
        print("알림 발송")
        # Notifications
        store_name = (
            auction.product.store.name
            if auction.product and auction.product.store
            else ""
        )
        product_name = auction.product.name if auction.product else ""
        title = f"{store_name} 팝업스토어 {product_name}"

        # 1) 현재 최고 입찰자 알림 (본인)
        self.notifications.send(
            NotifyRequest(
                user_id=user_id,
                title=f"{title} 현재 최고 입찰자입니다.",
                body="",
                product_id=auction.product_id,
            )
        )

        # 2) 이전 입찰자들에게 추월 알림
        previous_bidder_ids = self.auctions_read.list_distinct_bidder_user_ids(
            auction.id, exclude_user_id=user_id
        )
        formatted_amount = f"{int(round(float(amount))):,}원"
        for previous_user_id in previous_bidder_ids:
            self.notifications.send(
                NotifyRequest(
                    user_id=previous_user_id,
                    title=f"{title} 다른 사용자가 {formatted_amount}으로 추월했어요.",
                    body="",
                    product_id=auction.product_id,
                )
            )

    def buy_now(self, *, auction_id: int, user_id: int) -> BuyNowResult:
        """즉시구매 처리

        - OrderService로 주문+결제를 한 번에 처리
        - 이후 경매 종료/상품 판매 플래그/알림 기록
        :return: BuyNowResult(status, payment_id)
        """
        verifier = BidVerificator(self.session)
        auction = self.auctions_write.get_auction_by_id(auction_id)
        if not auction:
            raise BusinessError(ErrorCode.AUCTION_NOT_FOUND, "경매를 찾을 수 없습니다.")
        verifier.verify_buy_now(auction)
        # Order + Payment in one transaction
        order_service = OrderService(self.session, self.orders, self.payments)
        order_result = order_service.checkout_buy_now(
            user_id=user_id,
            product_id=auction.product_id,
            unit_price=float(auction.buy_now_price),
            provider="dummy",
        )
        # Update auction status and notify in a separate small transaction
        with transactional(self.session):
            auction.status = AuctionStatus.ENDED.value
            auction.product.is_sold = 1
            # TODO: 이전 입찰자들 환불 처리
            store_name = (
                auction.product.store.name
                if auction.product and auction.product.store
                else ""
            )
            product_name = auction.product.name if auction.product else ""
            title = f"{store_name} 팝업스토어 {product_name}"

            # 3) 즉시구매로 종료: 이전 입찰자 전체 알림
            previous_bidder_ids = self.auctions_read.list_distinct_bidder_user_ids(
                auction_id, exclude_user_id=user_id
            )
            for previous_user_id in previous_bidder_ids:
                self.notifications.send(
                    NotifyRequest(
                        user_id=previous_user_id,
                        title=f"{title} 경매가 즉시구매로 종료됐어요.",
                        body="",
                        product_id=auction.product_id,
                    )
                )

            # 4) 즉시구매자에게 주문 접수 알림
            self.notifications.send(
                NotifyRequest(
                    user_id=user_id,
                    title=f"{title} 주문이 접수됐어요.",
                    body="",
                    product_id=auction.product_id,
                )
            )
        return BuyNowResult(status="ORDER_PLACED", payment_id=order_result.payment_id)

    def finalize_winner_and_charge(self, *, auction_id: int) -> BuyNowResult:
        """낙찰 처리: 현재 최고 입찰자를 낙찰자로 확정하고 자동 결제/오퍼 생성.

        - ENDED 상태에서만 허용
        - 최고 입찰자 선택 → Payment 승인 → AuctionOffer 생성
        """
        with transactional(self.session):
            auction = self.auctions_write.get_auction_by_id(auction_id)
            if not auction:
                raise BusinessError(
                    ErrorCode.AUCTION_NOT_FOUND, "경매를 찾을 수 없습니다."
                )
            if auction.status != AuctionStatus.ENDED.value:
                raise BusinessError(
                    ErrorCode.INVALID_AUCTION_STATUS,
                    "종료된 경매만 낙찰 처리 가능합니다.",
                )
            # 최고 입찰자 조회
            from sqlalchemy import select

            winner_row = self.session.execute(
                select(Bid)
                .where(Bid.auction_id == auction_id)
                .order_by(Bid.amount.desc(), Bid.created_at.desc())
                .limit(1)
            ).first()
            if not winner_row:
                raise BusinessError(
                    ErrorCode.WINNER_NOT_FOUND, "낙찰자를 찾을 수 없습니다."
                )
            winner_bid: Bid = winner_row[0]

            # 결제 승인(즉시구매가 없으면 최고가로 결제)
            unit_price = float(winner_bid.amount)
            order_service = OrderService(self.session, self.orders, self.payments)
            order_result = order_service.checkout_buy_now(
                user_id=winner_bid.user_id,
                product_id=auction.product_id,
                unit_price=unit_price,
                provider="dummy",
            )

            # 오퍼 생성
            offer = AuctionOffer(
                auction_id=auction_id,
                bid_id=winner_bid.id,
                user_id=winner_bid.user_id,
                rank_order=1,
                status="ACCEPTED",
                order_id=order_result.order_id,
                expires_at=winner_bid.created_at,  # placeholder; no expiry for auto-accept
            )
            self.session.add(offer)
            # 알림
            title = f"{auction.product.store.name if auction.product and auction.product.store else ''} {auction.product.name if auction.product else ''}"
            self.notifications.send(
                NotifyRequest(
                    user_id=winner_bid.user_id,
                    title=f"{title} 낙찰되었습니다.",
                    body="",
                    product_id=auction.product_id,
                )
            )
            return BuyNowResult(
                status="ORDER_PLACED", payment_id=order_result.payment_id
            )
