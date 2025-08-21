from typing import Optional
from sqlalchemy.orm import Session

from app.domains.auctions.user_dto import UserAuctionDashboard, UserRelatedAuctionItem
from app.domains.common.paging import Page, paginate
from app.repositories.user_auction_read import UserAuctionReadRepository


class UserAuctionService:
    def __init__(self, session: Session, user_auction_read: UserAuctionReadRepository):
        self.session = session
        self.user_auction_read = user_auction_read

    def dashboard(self, *, user_id: int) -> UserAuctionDashboard:
        return self.user_auction_read.dashboard_counts(user_id=user_id)

    def list_related(
        self,
        *,
        user_id: int,
        page: int,
        size: int,
        period_from: Optional[str],
        period_to: Optional[str],
        keyword: Optional[str],
    ) -> Page[UserRelatedAuctionItem]:
        items, total = self.user_auction_read.list_user_related_items(
            user_id=user_id,
            page=page,
            size=size,
            period_from=period_from,
            period_to=period_to,
            keyword=keyword,
        )
        return paginate(items, page, size, total)


