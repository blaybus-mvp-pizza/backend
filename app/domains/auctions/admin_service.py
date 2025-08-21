from __future__ import annotations
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.core.errors import BusinessError
from app.core.error_codes import ErrorCode
from app.domains.common.paging import Page, paginate
from app.domains.auctions.admin_dto import (
    AdminAuctionListItem,
    AdminAuctionDetail,
    AdminAuctionUpsertRequest,
    AdminAuctionStatusUpdateRequest,
    AdminAuctionShipmentInfo,
)
from app.repositories.auction_admin_read import AuctionAdminReadRepository
from app.repositories.auction_admin_write import AuctionAdminWriteRepository
from app.repositories.auction_read import AuctionReadRepository
from app.domains.auctions.enums import AuctionStatus
from app.schemas.auctions import Auction
from app.domains.notifications.service import NotificationService
from app.domains.notifications.dto import NotifyRequest


class AuctionAdminService:
    def __init__(
        self,
        session: Session,
        auctions_admin_read: AuctionAdminReadRepository,
        auctions_admin_write: AuctionAdminWriteRepository,
        auctions_read: AuctionReadRepository,
        notifications: NotificationService | None = None,
    ):
        self.session = session
        self.read_admin = auctions_admin_read
        self.write_admin = auctions_admin_write
        self.read = auctions_read
        self.notifications = notifications or NotificationService(session)

    def list(
        self,
        *,
        page: int = 1,
        size: int = 20,
        q: Optional[str] = None,
        product_id: Optional[int] = None,
        store_name: Optional[str] = None,
        status: Optional[str] = None,
        result: Optional[str] = None,
        payment_status: Optional[str] = None,
        shipment_status: Optional[str] = None,
        starts_from: Optional[str] = None,
        starts_to: Optional[str] = None,
        ends_from: Optional[str] = None,
        ends_to: Optional[str] = None,
        sort: str = "latest",
    ) -> Page[AdminAuctionListItem]:
        items, total = self.read_admin.list_auctions(
            page=page,
            size=size,
            q=q,
            product_id=product_id,
            store_name=store_name,
            status=status,
            result=result,
            payment_status=payment_status,
            shipment_status=shipment_status,
            starts_from=starts_from,
            starts_to=starts_to,
            ends_from=ends_from,
            ends_to=ends_to,
            sort=sort,
        )
        return paginate(items, page, size, total)

    def detail(self, auction_id: int) -> AdminAuctionDetail:
        detail = self.read_admin.get_auction_detail(auction_id)
        if not detail:
            raise BusinessError(ErrorCode.AUCTION_NOT_FOUND, "경매를 찾을 수 없습니다.")
        return detail

    def upsert(self, req: AdminAuctionUpsertRequest) -> AdminAuctionDetail:
        # validations
        if req.min_bid_price > req.start_price:
            raise BusinessError(ErrorCode.INVALID_AUCTION_PRICE_RULE, "최소입찰가가 시작가보다 큽니다.")
        if req.buy_now_price is not None and req.start_price > req.buy_now_price:
            raise BusinessError(ErrorCode.INVALID_AUCTION_PRICE_RULE, "시작가가 즉시구매가보다 큽니다.")
        starts = self._parse_kst_to_utc(req.starts_at)
        ends = self._parse_kst_to_utc(req.ends_at)
        if starts >= ends:
            raise BusinessError(ErrorCode.INVALID_AUCTION_TIME_RANGE, "시작일시는 종료일시보다 빨라야 합니다.")

        # product unique auction constraint handled via query: if exists and different id
        existing = self.session.execute(
            self.session.query(Auction).filter(Auction.product_id == req.product_id).statement
        ).scalar_one_or_none()
        if existing and (req.id is None or existing.id != req.id):
            raise BusinessError(ErrorCode.PRODUCT_ALREADY_HAS_AUCTION, "해당 상품의 경매가 이미 존재합니다.")

        # Update-only constraint: allow modifications only before starts_at and status SCHEDULED
        target = None
        if req.id is not None:
            target = self.session.get(Auction, req.id)
        if target is None:
            target = existing
        if target is not None:
            now_utc = datetime.now(timezone.utc)
            if not (target.status == AuctionStatus.SCHEDULED.value and now_utc < target.starts_at):
                raise BusinessError(
                    ErrorCode.INVALID_AUCTION_STATUS,
                    "수정은 시작일시 이전이면서 SCHEDULED 상태에서만 가능합니다.",
                )

        a = self.write_admin.upsert(
            id=req.id,
            product_id=req.product_id,
            start_price=float(req.start_price),
            min_bid_price=float(req.min_bid_price),
            buy_now_price=float(req.buy_now_price) if req.buy_now_price is not None else None,
            deposit_amount=float(req.deposit_amount),
            starts_at=starts,
            ends_at=ends,
            status=req.status or AuctionStatus.SCHEDULED.value,
        )
        return self.detail(a.id)

    def update_status(self, auction_id: int, req: AdminAuctionStatusUpdateRequest) -> AdminAuctionDetail:
        a = self.session.get(Auction, auction_id)
        if not a:
            raise BusinessError(ErrorCode.AUCTION_NOT_FOUND, "경매를 찾을 수 없습니다.")
        if req.status == AuctionStatus.CANCELLED.value:
            if a.status != AuctionStatus.RUNNING.value:
                raise BusinessError(ErrorCode.CANNOT_CANCEL_NON_RUNNING, "진행중 경매만 중단할 수 있습니다.")
        elif req.status == AuctionStatus.RUNNING.value:
            now = datetime.now(timezone.utc)
            if not (a.starts_at <= now <= a.ends_at):
                raise BusinessError(
                    ErrorCode.CANNOT_RESUME_EXPIRED_AUCTION, "진행 기간 내에서만 재개할 수 있습니다."
                )
        elif req.status == AuctionStatus.PAUSED.value:
            # RUNNING -> PAUSED only
            if a.status != AuctionStatus.RUNNING.value:
                raise BusinessError(ErrorCode.INVALID_AUCTION_STATUS, "진행중일 때만 일시중단할 수 있습니다.")
        else:
            raise BusinessError(ErrorCode.INVALID_AUCTION_STATUS, "허용되지 않는 상태입니다.")
        self.write_admin.update_status(auction_id, req.status)

        # Notifications for pause/resume
        try:
            title = f"{a.product.store.name if a.product and a.product.store else ''} {a.product.name if a.product else ''}"
            message = None
            if req.status == AuctionStatus.PAUSED.value:
                message = f"‘{title}’ 경매가 일시중단됐어요."
            elif req.status == AuctionStatus.RUNNING.value:
                message = f"‘{title}’ 경매가 재개됐어요."
            if message:
                # send to all distinct bidders so far
                for uid in self.read.list_distinct_bidder_user_ids(auction_id):
                    self.notifications.send(NotifyRequest(user_id=uid, title=message, body="5일", product_id=a.product_id))
        except Exception:
            # do not break main flow on notification failures
            pass
        return self.detail(auction_id)

    def shipment_info(self, auction_id: int) -> AdminAuctionShipmentInfo:
        # reuse detail and project fields; for now return minimal placeholders
        d = self.detail(auction_id)
        return AdminAuctionShipmentInfo(
            shipment_status=d.shipment_status,
            courier_name=None,
            tracking_number=None,
            shipped_at=None,
            delivered_at=None,
        )

    def _parse_kst_to_utc(self, s: str) -> datetime:
        """Parse input assumed as KST (UTC+9) unless explicit offset provided, then convert to UTC."""
        s_norm = s.strip()
        if s_norm.endswith("Z") or "+" in s_norm[10:] or "-" in s_norm[10:]:
            dt = datetime.fromisoformat(s_norm.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                # Treat as KST if naive
                dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
        else:
            # Naive -> KST
            dt = datetime.fromisoformat(s_norm)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
        return dt.astimezone(timezone.utc)


