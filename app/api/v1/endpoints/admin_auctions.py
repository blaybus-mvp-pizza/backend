from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional
from app.core.deps import get_db
from app.core.auth_deps import require_admin
from app.domains.common.paging import Page
from app.domains.auctions.admin_dto import (
    AdminAuctionListItem,
    AdminAuctionDetail,
    AdminAuctionUpsertRequest,
    AdminAuctionStatusUpdateRequest,
    AdminAuctionShipmentInfo,
)
from app.domains.auctions.admin_service import AuctionAdminService
from app.repositories.auction_admin_read import AuctionAdminReadRepository
from app.repositories.auction_admin_write import AuctionAdminWriteRepository
from app.repositories.auction_read import AuctionReadRepository
from app.domains.notifications.service import NotificationService
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse
from app.domains.auctions.buy_now_result import BuyNowResult
from app.domains.auctions.service import AuctionService as AuctionDomainService


def get_admin_service(db: Session = Depends(get_db)) -> AuctionAdminService:
    return AuctionAdminService(
        db,
        AuctionAdminReadRepository(db),
        AuctionAdminWriteRepository(db),
        AuctionReadRepository(db),
        NotificationService(db),
    )


class AdminAuctionsAPI:
    def __init__(self):
        self.router = APIRouter(dependencies=[Depends(require_admin)])

        @self.router.get(
            "",
            response_model=Page[AdminAuctionListItem],
            summary="경매 목록 조회(관리자)",
            description="페이지/필터/정렬 조건으로 관리자 경매 목록을 조회합니다.",
            response_description="경매 리스트",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                401: {"model": BusinessErrorResponse, "description": "관리자 인증 실패"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def list_auctions(
            service: AuctionAdminService = Depends(get_admin_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(20, ge=1, le=100, description="페이지 크기(기본 20, 최대 100)"),
            q: Optional[str] = Query(None, description="상품명 키워드 검색"),
            product_id: Optional[int] = Query(None, description="상품 ID 검색"),
            store_name: Optional[str] = Query(None, description="스토어명 검색"),
            status: Optional[str] = Query(None, description="상태 ALL|SCHEDULED|RUNNING|ENDED|CANCELLED"),
            result: Optional[str] = Query(None, description="WON|LOST|ALL"),
            payment_status: Optional[str] = Query(None, description="결제 상태(대기/확인/취소)"),
            shipment_status: Optional[str] = Query(None, description="배송 상태(대기/처리/조회/완료)"),
            starts_from: Optional[str] = Query(None, description="시작일시 FROM(UTC ISO8601)"),
            starts_to: Optional[str] = Query(None, description="시작일시 TO(UTC ISO8601)"),
            ends_from: Optional[str] = Query(None, description="종료일시 FROM(UTC ISO8601)"),
            ends_to: Optional[str] = Query(None, description="종료일시 TO(UTC ISO8601)"),
            sort: str = Query("latest", description="정렬 recommended|popular|latest|ending"),
        ):
            return service.list(
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

        @self.router.get(
            "/{auction_id}",
            response_model=AdminAuctionDetail,
            summary="경매 상세 조회(관리자)",
            description="경매 설정, 상품 메타, 현재 입찰 요약 등 상세 정보를 조회합니다.",
            response_description="경매 상세",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                401: {"model": BusinessErrorResponse, "description": "관리자 인증 실패"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def get_detail(
            auction_id: int = Path(..., description="경매 ID"),
            service: AuctionAdminService = Depends(get_admin_service),
        ):
            return service.detail(auction_id)

        @self.router.post(
            "",
            response_model=AdminAuctionDetail,
            summary="경매 등록/수정(관리자)",
            description="단일 POST로 경매를 등록 또는 수정합니다. product_id당 1개만 허용. 입력 시간은 KST.",
            response_description="저장된 경매 상세",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                401: {"model": BusinessErrorResponse, "description": "관리자 인증 실패"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def upsert_auction(
            req: AdminAuctionUpsertRequest,
            service: AuctionAdminService = Depends(get_admin_service),
        ):
            return service.upsert(req)

        @self.router.patch(
            "/{auction_id}",
            response_model=AdminAuctionDetail,
            summary="경매 수정(관리자)",
            description="경매 ID로 지정하여 수정합니다. 시작 전이며 SCHEDULED일 때만 허용. 입력 시간은 KST.",
            response_description="수정된 경매 상세",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                401: {"model": BusinessErrorResponse, "description": "관리자 인증 실패"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def update_auction(
            auction_id: int = Path(..., description="경매 ID"),
            req: AdminAuctionUpsertRequest = ...,  # 전체 필드 기준 수정 (부분 수정 필요 시 알려주세요)
            service: AuctionAdminService = Depends(get_admin_service),
        ):
            # reuse upsert validations by injecting id
            payload = req.model_dump()
            payload["id"] = auction_id
            req_with_id = AdminAuctionUpsertRequest(**payload)
            return service.upsert(req_with_id)

        @self.router.patch(
            "/{auction_id}/status",
            response_model=AdminAuctionDetail,
            summary="경매 상태 변경(관리자)",
            description="진행중일 때만 일시중단(PAUSED) 가능, 진행 기간 내에서만 재개(RUNNING) 가능. 변경 시 관련 사용자에게 알림 전송.",
            response_description="변경 후 경매 상세",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                401: {"model": BusinessErrorResponse, "description": "관리자 인증 실패"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def update_status(
            auction_id: int = Path(..., description="경매 ID"),
            req: AdminAuctionStatusUpdateRequest = ...,
            service: AuctionAdminService = Depends(get_admin_service),
        ):
            return service.update_status(auction_id, req)

        @self.router.get(
            "/{auction_id}/shipping",
            response_model=AdminAuctionShipmentInfo,
            summary="배송 상태 조회(관리자)",
            description="배송 상태는 조회만 가능합니다.",
            response_description="배송 정보",
        )
        async def get_shipping(
            auction_id: int = Path(..., description="경매 ID"),
            service: AuctionAdminService = Depends(get_admin_service),
        ):
            return service.shipment_info(auction_id)

        @self.router.post(
            "/{auction_id}/finalize",
            response_model=BuyNowResult,
            summary="낙찰 처리(관리자)",
            description="종료된 경매의 최고 입찰자를 낙찰자로 확정하고 자동 결제를 수행합니다.",
            response_description="낙찰 처리 결과",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                401: {"model": BusinessErrorResponse, "description": "관리자 인증 실패"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def finalize(
            auction_id: int = Path(..., description="경매 ID"),
            domain: AuctionDomainService = Depends(lambda db=Depends(get_db): AuctionDomainService(
                db,
                AuctionReadRepository(db),
                __import__('app.repositories.auction_write', fromlist=['AuctionWriteRepository']).AuctionWriteRepository(db),
                __import__('app.repositories.order_write', fromlist=['OrderWriteRepository']).OrderWriteRepository(db),
                __import__('app.repositories.payment_write', fromlist=['PaymentWriteRepository']).PaymentWriteRepository(db),
                __import__('app.repositories.auction_deposit', fromlist=['AuctionDepositRepository']).AuctionDepositRepository(db),
                __import__('app.domains.notifications.service', fromlist=['NotificationService']).NotificationService(db),
            )),
        ):
            return domain.finalize_winner_and_charge(auction_id=auction_id)


api = AdminAuctionsAPI().router


