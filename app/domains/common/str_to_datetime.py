from datetime import datetime
from app.core.errors import BusinessError


def str_to_datetime(date_str: str | None) -> datetime | None:
    """문자열을 datetime으로 변환"""
    if date_str is None:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        raise BusinessError(code=400, message="날짜 형식이 올바르지 않습니다.")
