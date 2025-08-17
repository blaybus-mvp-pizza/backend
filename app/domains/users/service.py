from sqlalchemy.orm import Session
from app.repositories.user import get_by_username_or_email, create_user
from app.core.security import get_password_hash, verify_password
from app.schemas.users import User as UserEntity


def signup_user(db: Session, *, email: str, username: str, password: str) -> UserEntity:
    """신규 사용자 등록

    - 이메일/사용자명 중복 검사 후 생성
    - 비밀번호는 해시하여 저장
    """
    existing = get_by_username_or_email(db, username) or get_by_username_or_email(
        db, email
    )
    if existing:
        raise ValueError("User already exists")
    hashed = get_password_hash(password)
    return create_user(db, email=email, username=username, hashed_password=hashed)


def authenticate_user(
    db: Session, *, identifier: str, password: str
) -> UserEntity | None:
    """사용자 인증 (아이디/이메일 + 비밀번호)

    - 유효하면 사용자 엔티티 반환, 아니면 None
    """
    user = get_by_username_or_email(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
