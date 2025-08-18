from sqlalchemy.orm import Session
from app.domains.common.tx import transactional
from app.repositories.order_write import OrderWriteRepository
from app.repositories.payment_write import PaymentWriteRepository
from app.domains.orders.order_result import OrderResult


class OrderService:
    def __init__(
        self,
        session: Session,
        orders_repo: OrderWriteRepository,
        payments_repo: PaymentWriteRepository,
    ):
        self.session = session
        self.orders = orders_repo
        self.payments = payments_repo

    def checkout_buy_now(
        self,
        *,
        user_id: int,
        product_id: int,
        unit_price: float,
        provider: str = "dummy"
    ) -> OrderResult:
        """즉시구매 체크아웃 처리

        - 주문 생성 및 아이템 추가
        - 결제 생성/로그 기록 후 주문 상태를 PAID로 전환
        - 하나의 트랜잭션으로 커밋/롤백

        :param user_id: 사용자 ID
        :param product_id: 상품 ID
        :param unit_price: 단가(결제 금액)
        :param provider: 결제 제공자 식별자
        :return: OrderResult(order_id, status, payment_id)
        """
        with transactional(self.session):
            order = self.orders.create_order(
                user_id=user_id,
                total_amount=unit_price,
                shipping_fee=0,
                status="PENDING",
            )
            self.orders.add_order_item(
                order_id=order.id,
                product_id=product_id,
                quantity=1,
                unit_price=unit_price,
            )
            payment = self.payments.create_payment(
                user_id=user_id, amount=unit_price, provider=provider, status="PAID"
            )
            self.payments.create_payment_log(
                payment_id=payment.id,
                provider=provider,
                amount=unit_price,
                status="PAID",
                log_type="REQUEST",
            )
            self.orders.update_order_status(order.id, status="PAID")
            return OrderResult(order_id=order.id, status="PAID", payment_id=payment.id)

    # Legacy helpers (kept if other flows need them)
    def create_buy_now_order(
        self, *, user_id: int, product_id: int, unit_price: float
    ) -> OrderResult:
        """(레거시) 결제 없이 주문만 생성

        :param user_id: 사용자 ID
        :param product_id: 상품 ID
        :param unit_price: 단가
        :return: OrderResult(order_id, status)
        """
        order = self.orders.create_order(
            user_id=user_id, total_amount=unit_price, shipping_fee=0, status="PENDING"
        )
        self.orders.add_order_item(
            order_id=order.id, product_id=product_id, quantity=1, unit_price=unit_price
        )
        return OrderResult(order_id=order.id, status=order.status)

    def mark_paid(self, order_id: int) -> None:
        """주문 상태를 PAID로 전환"""
        self.orders.update_order_status(order_id, status="PAID")

    def mark_refunded(self, order_id: int) -> None:
        """주문 상태를 REFUNDED로 전환"""
        self.orders.update_order_status(order_id, status="REFUNDED")
