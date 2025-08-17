from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import JSON, select
from app.schemas.users import AuthProvider, User


class UserReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, identifier: str) -> Optional[User]:
        stmt = select(User).where(User.email == identifier)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()
