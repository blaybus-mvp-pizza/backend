from datetime import datetime
from app.core.errors import BusinessError
from app.core.timezone import kst_to_utc


def str_to_datetime(date_str: str | None) -> datetime | None:
    """
    문자열을 datetime으로 변환
    입력된 문자열을 KST로 가정하고 UTC로 변환하여 반환 (DB 저장용)
    """
    if date_str is None:
        return None
    try:
        # ISO 형식 문자열을 datetime으로 파싱
        dt = datetime.fromisoformat(date_str)
        
        # KST로 가정하고 UTC로 변환 (DB 저장용)
        return kst_to_utc(dt)
    except ValueError:
        raise BusinessError(code=400, message="날짜 형식이 올바르지 않습니다.")
