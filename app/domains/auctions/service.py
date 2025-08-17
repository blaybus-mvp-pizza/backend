from sqlalchemy.orm import Session
from app.core.errors import BusinessError
from app.core.error_codes import ErrorCode
from app.domains.auctions.verification import BidVerificator
from app.domains.auctions.enums import AuctionStatus
from app.domains.auctions.bid_result import BidResult
from app.domains.auctions.buy_now_result import BuyNowResult
from app.domains.common.tx import transactional
from app.repositories.auction_read import AuctionReadRepository
from app.repositories.auction_write import AuctionWriteRepository
from app.repositories.order_write import OrderWriteRepository
from app.repositories.payment_write import PaymentWriteRepository
from app.repositories.notification_write import NotificationWriteRepository
from app.domains.orders.service import OrderService


class AuctionService:
    def __init__(
        self,
        session: Session,
        auctions_read: AuctionReadRepository,
        auctions_write: AuctionWriteRepository,
        orders: OrderWriteRepository,
        payments: PaymentWriteRepository,
        notifications: NotificationWriteRepository,
    ):
        self.session = session
        self.auctions_read = auctions_read
        self.auctions_write = auctions_write
        self.orders = orders
        self.payments = payments
        self.notifications = notifications

    def place_bid(self, *, auction_id: int, amount: float, user_id: int) -> BidResult:
        """입찰 처리

        - 경매 상태/금액 검증 후 입찰 생성
        - 필요 시 보증금(Deposit) 결제 생성
        :return: BidResult(bid_id, amount)
        """
        verifier = BidVerificator(self.session)
        with transactional(self.session):
            auction = verifier.ensure_auction_exists_and_running(auction_id)
            deposit_amount = verifier.ensure_amount_allowed(
                auction_product_id=auction.product_id, amount=amount
            )
            if deposit_amount > 0:
                self.payments.create_payment(
                    user_id=user_id,
                    amount=deposit_amount,
                    provider="dummy",
                    status="PAID",
                )
            bid = self.auctions_write.place_bid(auction_id, user_id, amount)
            return BidResult(bid_id=bid.id, amount=float(bid.amount))

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
            self.notifications.create(
                user_id=user_id,
                title=f"{auction.product.name}",
                body="즉시구매 완료되었습니다.",
            )
        return BuyNowResult(status="ORDER_PLACED", payment_id=order_result.payment_id)
