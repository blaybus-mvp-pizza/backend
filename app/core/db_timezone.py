"""
SQLAlchemy 레벨에서 시간대 변환을 위한 TypeDecorator와 유틸리티
"""
from datetime import datetime
from sqlalchemy import TypeDecorator, DateTime
from sqlalchemy.types import TypeEngine
from app.core.timezone import utc_to_kst, kst_to_utc


class KSTDateTime(TypeDecorator):
    """
    DB에서는 UTC로 저장하고, Python에서는 KST로 사용하는 DateTime 타입
    
    - DB 저장 시: KST → UTC 변환
    - DB 조회 시: UTC → KST 변환
    """
    impl = DateTime
    cache_ok = True
    
    def process_bind_param(self, value: datetime, dialect) -> datetime:
        """Python → DB 저장 시: KST → UTC 변환"""
        if value is not None:
            return kst_to_utc(value)
        return value
    
    def process_result_value(self, value: datetime, dialect) -> datetime:
        """DB → Python 조회 시: UTC → KST 변환"""
        if value is not None:
            return utc_to_kst(value)
        return value


class AutoKSTDateTime(TypeDecorator):
    """
    읽기 전용으로 UTC → KST 변환만 하는 DateTime 타입
    (기존 UTC 데이터를 그대로 두고 조회 시에만 변환)
    """
    impl = DateTime
    cache_ok = True
    
    def process_result_value(self, value: datetime, dialect) -> datetime:
        """DB → Python 조회 시: UTC → KST 변환"""
        if value is not None:
            return utc_to_kst(value)
        return value


# 편의 함수
def create_kst_datetime_column(*args, **kwargs):
    """KST로 자동 변환되는 DateTime 컬럼 생성"""
    return Column(KSTDateTime, *args, **kwargs)


def create_auto_kst_datetime_column(*args, **kwargs):
    """읽기 시에만 KST로 변환되는 DateTime 컬럼 생성 (기존 DB용)"""
    return Column(AutoKSTDateTime, *args, **kwargs)
