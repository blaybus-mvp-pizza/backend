from typing import List
from sqlalchemy.orm import Session

from app.core.errors import BusinessError
from app.domains.stories.story_list_item import StoryListItem
from app.domains.stories.story_meta import StoryMeta
from app.repositories.story_read import StoryReadRepository


class StoryService:
    def __init__(self, db: Session):
        self.db = db
        self.story_read = StoryReadRepository(db)

    def get_stories(self, *, page: int, size: int) -> List[StoryListItem]:
        """스토리 목록 조회 (페이지네이션)"""
        offset = (page - 1) * size
        stories = self.story_read.recent_story_items_with_product_brief(
            limit=size, offset=offset
        )
        return stories

    def get_story_meta(self, story_id: int) -> StoryMeta | None:
        """스토리 상세 조회"""
        story = self.story_read.get_story_meta_with_product_brief(story_id)
        if not story:
            raise BusinessError(400, "스토리를 찾을 수 없습니다.")
        return story
