from typing import List
from app.domains.common.paging import Page, paginate
from sqlalchemy.orm import Session

from app.repositories.product_read import ProductReadRepository
from app.repositories.auction_read import AuctionReadRepository

from app.domains.products.product_list_item import ProductListItem
from app.domains.products.store_meta import StoreMeta
from app.domains.products.store_with_products import StoreWithProducts
from app.domains.auctions.auction_info import AuctionInfo
from app.domains.auctions.bid_rules import BidRules
from app.domains.products.product_meta import ProductMeta

from app.domains.products.mappers import rows_to_product_items


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.products = ProductReadRepository(db)
        self.auctions = AuctionReadRepository(db)

    def ending_soon(
        self,
        *,
        page: int,
        size: int,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: float | None = None,
        price_max: float | None = None,
        sort: str = "ending",
    ) -> Page[ProductListItem]:
        """마감임박 상품 조회 (페이지네이션)

        - 경매 상태가 진행중이며 종료 임박 순 정렬
        :return: ProductListItem 리스트
        """
        offset = (page - 1) * size
        items, total = self.products.ending_soon_products(
            limit=size,
            offset=offset,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            sort=sort,
        )
        return paginate(items, page, size, total)

    def recommended(
        self,
        *,
        page: int,
        size: int,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: float | None = None,
        price_max: float | None = None,
        sort: str = "recommended",
    ) -> Page[ProductListItem]:
        """MD 추천 상품 조회 (페이지네이션)"""
        offset = (page - 1) * size
        items, total = self.products.recommended_products(
            limit=size,
            offset=offset,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            sort=sort,
        )
        return paginate(items, page, size, total)

    def newest(
        self,
        *,
        page: int,
        size: int,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: float | None = None,
        price_max: float | None = None,
        sort: str = "latest",
    ) -> Page[ProductListItem]:
        """신규 상품 조회 (페이지네이션)"""
        offset = (page - 1) * size
        items, total = self.products.new_products(
            limit=size,
            offset=offset,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            sort=sort,
        )
        return paginate(items, page, size, total)

    def stores_recent(
        self,
        *,
        page: int,
        stores: int,
        size: int,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: float | None = None,
        price_max: float | None = None,
        sort: str = "latest",
    ) -> Page[StoreWithProducts]:
        """최근 오픈 스토어들 + 각 스토어별 최신 상품 묶음 조회"""
        offset = (page - 1) * stores
        pairs, total_stores = self.products.recent_stores_with_products(
            per_store_products=size,
            offset=offset,
            limit_stores=stores,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            sort=sort,
        )
        result: List[StoreWithProducts] = []
        for store, rows in pairs:
            result.append(
                StoreWithProducts(
                    store=StoreMeta(
                        store_id=store.id,
                        image_url=store.image_url,
                        name=store.name,
                        description=store.description,
                        sales_description=store.sales_description,
                    ),
                    products=rows,
                )
            )
        # here, "stores" is the per-page size for stores
        return paginate(result, page, stores, total_stores)

    def store_list(self, *, page: int, size: int) -> Page[StoreMeta]:
        """스토어 목록 조회 (간략 메타)"""
        offset = (page - 1) * size
        items, total = self.products.store_list(limit=size, offset=offset)
        return paginate(items, page, size, total)

    def store_meta(self, *, store_id: int) -> StoreMeta:
        """스토어 메타데이터 상세 조회"""
        return self.products.store_meta(store_id)

    def products_by_store(
        self,
        *,
        store_id: int,
        sort: str,
        page: int,
        size: int,
        status: str = "RUNNING",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: float | None = None,
        price_max: float | None = None,
    ) -> Page[ProductListItem]:
        """특정 스토어 내 상품 목록 조회 (정렬/페이징)"""
        items, total = self.products.products_by_store(
            store_id=store_id,
            sort=sort,
            page=page,
            size=size,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
        )
        return paginate(items, page, size, total)

    def product_meta(self, *, product_id: int) -> ProductMeta:
        """상품 메타데이터 상세 조회"""
        return self.products.product_meta(product_id)

    def product_auction_info(self, *, product_id: int) -> AuctionInfo:
        """상품의 경매 핵심 정보 조회 및 입찰 스텝 계산"""
        info = self.auctions.get_auction_info_by_product(product_id)
        if not info:
            return AuctionInfo(
                auction_id=0,
                buy_now_price=None,
                current_highest_bid=None,
                bid_steps=[],
                starts_at="",
                ends_at="",
                start_price=0,
                min_bid_price=0,
                deposit_amount=0,
                bidder_count=0,
                status="CANCELLED",
            )
        current = (
            float(info.current_highest_bid)
            if info.current_highest_bid is not None
            else float(info.min_bid_price)
        )
        steps = BidRules.make_bid_steps(
            current,
            float(info.buy_now_price) if info.buy_now_price is not None else None,
        )
        info.bid_steps = steps
        return info

    def product_bids(self, *, product_id: int, page: int, size: int) -> Page:
        """상품의 입찰 내역 조회 (페이지네이션)"""
        offset = (page - 1) * size
        items, total = self.auctions.list_bids_by_product(
            product_id, limit=size, offset=offset
        )
        return paginate(items, page, size, total)

    def product_similar(
        self,
        *,
        product_id: int,
        page: int,
        size: int,
        status: str = "ALL",
        bidders: str = "ALL",
        price_bucket: str = "ALL",
        price_min: float | None = None,
        price_max: float | None = None,
        sort: str = "latest",
    ) -> Page[ProductListItem]:
        """같은 스토어 내 유사 상품 조회 (페이지네이션)"""
        offset = (page - 1) * size
        items, total = self.auctions.similar_products_in_same_store(
            product_id,
            limit=size,
            offset=offset,
            status=status,
            bidders=bidders,
            price_bucket=price_bucket,
            price_min=price_min,
            price_max=price_max,
            sort=sort,
        )
        return paginate(items, page, size, total)
