from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_db
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse
from app.domains.stories.service import StoryService
from app.domains.stories.story_list_item import StoryListItem
from app.domains.stories.story_meta import StoryMeta


def get_story_service(db: Session = Depends(get_db)) -> StoryService:
    return StoryService(db)


class StoryAPI:
    def __init__(self) -> None:
        self.router = APIRouter()

        @self.router.get(
            "/",
            response_model=List[StoryListItem],
            summary="스토리 목록 조회",
            description="스토리 목록을 페이징 조회합니다.",
            response_description="스토리 리스트",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                },
                500: {
                    "model": ServerErrorResponse,
                    "description": "서버 내부 오류",
                    "content": {
                        "application/json": {
                            "examples": {
                                "INTERNAL_SERVER_ERROR": {
                                    "value": {
                                        "code": "INTERNAL_SERVER_ERROR",
                                        "message": "서버 내부 오류",
                                    }
                                }
                            }
                        }
                    },
                },
            },
        )
        def get_stories(
            service: StoryService = Depends(get_story_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(
                9, ge=1, le=100, description="페이지 크기(기본 9, 최대 100)"
            ),
        ):
            return service.get_stories(page=page, size=size)

        @self.router.get(
            "/{story_id}",
            response_model=StoryMeta,
            summary="스토리 상세 조회",
            description="스토리 ID로 스토리 상세 정보를 조회합니다.",
            response_description="스토리 상세 정보",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def get_story_meta(
            story_id: int, service: StoryService = Depends(get_story_service)
        ) -> StoryMeta:
            return service.get_story_meta(story_id=story_id)


api = StoryAPI().router
