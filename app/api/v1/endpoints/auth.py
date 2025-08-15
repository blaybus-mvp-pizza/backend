from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.security import create_access_token
from app.domains.users.service import authenticate_user, signup_user
from app.domains.users.models import UserCreate
from app.domains.auth.models import Token

router = APIRouter()


@router.post("/login", response_model=Token, summary="Issue JWT access token")
async def login(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db, identifier=payload.username, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.post("/signup", response_model=Token, summary="Simple signup (MVP)")
async def signup(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    try:
        user = signup_user(
            db,
            email=payload.email,
            username=payload.username,
            password=payload.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)
