"""
시간대 변환 유틸리티

DB는 UTC로 저장하고, 애플리케이션에서는 한국 시간(KST)으로 처리
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# 시간대 정의 (Python 표준 라이브러리 사용)
UTC = timezone.utc
KST = timezone(timedelta(hours=9))  # UTC+9


def utc_to_kst(utc_dt: Optional[datetime]) -> Optional[datetime]:
    """UTC 시간을 KST로 변환"""
    if utc_dt is None:
        return None
    
    if utc_dt.tzinfo is None:
        # timezone 정보가 없으면 UTC로 가정
        utc_dt = utc_dt.replace(tzinfo=UTC)
    
    return utc_dt.astimezone(KST)


def kst_to_utc(kst_dt: Optional[datetime]) -> Optional[datetime]:
    """KST 시간을 UTC로 변환"""
    if kst_dt is None:
        return None
    
    if kst_dt.tzinfo is None:
        # timezone 정보가 없으면 KST로 가정
        kst_dt = kst_dt.replace(tzinfo=KST)
    
    return kst_dt.astimezone(UTC).replace(tzinfo=None)  # DB에는 naive datetime으로 저장


def now_kst() -> datetime:
    """현재 KST 시간 반환"""
    return datetime.now(KST)


def now_utc() -> datetime:
    """현재 UTC 시간 반환 (DB 저장용)"""
    return datetime.utcnow()


def format_kst(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """datetime을 KST로 변환 후 포맷팅"""
    if dt is None:
        return None
    
    kst_dt = utc_to_kst(dt)
    return kst_dt.strftime(format_str) if kst_dt else None
