from typing import Callable
from sqlalchemy import select
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.schemas.auctions import Auction, Bid
from app.domains.auctions.enums import AuctionStatus
from app.domains.payments.service import PaymentService
from app.domains.payments.dto import RefundRequest
from app.domains.notifications.service import NotificationService
from app.domains.notifications.dto import NotifyRequest
from app.infrastructure.db.uow import SqlAlchemyUnitOfWork


class AuctionSettlementBatch:
    def __init__(
        self,
        uow_factory: Callable[[], SqlAlchemyUnitOfWork] = SqlAlchemyUnitOfWork,
        payment_service_factory: (
            Callable[[SqlAlchemyUnitOfWork], PaymentService] | None
        ) = None,
        notification_service_factory: (
            Callable[[SqlAlchemyUnitOfWork], NotificationService] | None
        ) = None,
    ):
        """경매 정산 배치

        DI 정책:
        - uow_factory: UoW 스코프 세션/레포 제공
        - payment_service_factory: UoW 바운드 PaymentService 생성 팩토리
        - notification_service_factory: UoW 바운드 NotificationService 생성 팩토리
        """
        self.uow_factory = uow_factory
        # 기본 팩토리: UoW에 바인딩된 세션/레포로 서비스 생성
        self.payment_service_factory = payment_service_factory or (
            lambda uow: PaymentService(uow.session, uow.payments)
        )
        self.notification_service_factory = notification_service_factory or (
            lambda uow: NotificationService(uow.session, uow.notifications)
        )

    def run_once(self):
        # 전체 배치 처리 한 사이클 = 하나의 트랜잭션 경계로 묶음
        with self.uow_factory() as uow:
            stmt = select(Auction).where(
                Auction.status == AuctionStatus.RUNNING.value,
                Auction.ends_at <= datetime.now(timezone.utc),
            )
            for row in uow.session.execute(stmt):
                auction = row[0]
                self._settle_auction(uow, auction)

    def _settle_auction(self, uow: SqlAlchemyUnitOfWork, auction: Auction):
        # 개별 경매 정산은 동일 UoW 세션 내에서 진행되어 하나의 커밋으로 묶임
        winner_row = uow.session.execute(
            select(Bid)
            .where(Bid.auction_id == auction.id)
            .order_by(Bid.amount.desc(), Bid.created_at.desc())
            .limit(1)
        ).first()
        if not winner_row:
            auction.status = AuctionStatus.ENDED.value
            uow.session.flush()
            return
        winner: Bid = winner_row[0]
        # 환불 처리: 낙찰자 외 보증금 환불
        payment_service = self.payment_service_factory(uow)
        for dep in uow.auction_deposits.list_by_auction(auction.id):
            if (
                dep.user_id != winner.user_id
                and dep.status != "REFUNDED"
                and dep.payment_id
            ):
                payment_service.refund(
                    RefundRequest(payment_id=dep.payment_id, amount=float(dep.amount))
                )
                uow.auction_deposits.mark_refunded(dep.id)
        # 알림 전송
        self.notification_service_factory(uow).send(
            NotifyRequest(
                user_id=winner.user_id,
                title=f"{auction.product.name}",
                body="낙찰되었습니다. 결제를 진행해 주세요.",
            )
        )
        auction.status = AuctionStatus.ENDED.value
        uow.session.flush()
