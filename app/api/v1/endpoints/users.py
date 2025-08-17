from fastapi import APIRouter, Depends, HTTPException, Header
from requests import Session

from app.core.deps import get_db
from app.core.security import require_auth
from app.domains.users.models import UserRead, UserUpdate
from app.domains.users.service import get_user_info, update_user_info


class UsersAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get("/me", summary="[required auth] Get current user")
        async def get_current_user(
            user_id: int = Depends(require_auth),
            db: Session = Depends(get_db),
        ) -> UserRead:
            current_user = get_user_info(db, user_id=user_id)
            if not current_user:
                raise HTTPException(status_code=404, detail="User not found")
            return current_user

        @self.router.put("/me", summary="[required auth] Update current user")
        async def update_current_user(
            user_data: UserUpdate,
            user_id: int = Depends(require_auth),
            db: Session = Depends(get_db),
        ) -> UserRead:
            try:
                user = update_user_info(db, user_id=user_id, user_data=user_data)
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            return user


api = UsersAPI().router
