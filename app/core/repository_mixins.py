"""
Repository에서 자동 시간대 변환을 위한 Mixin
"""
from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy import Row
from app.core.timezone import utc_to_kst


class TimezoneConversionMixin:
    """
    Repository에서 조회 결과의 datetime 필드를 자동으로 UTC → KST 변환
    """
    
    # 변환할 datetime 필드명들 (서브클래스에서 오버라이드 가능)
    DATETIME_FIELDS = [
        'created_at', 'updated_at', 'starts_at', 'ends_at', 'auction_ends_at',
        'sent_at', 'bid_at', 'last_bid_at', 'shipped_at', 'delivered_at'
    ]
    
    def convert_row_datetimes(self, row: Row) -> Dict[str, Any]:
        """단일 Row의 datetime 필드들을 UTC → KST 변환"""
        result = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
        
        for field_name in self.DATETIME_FIELDS:
            if field_name in result and isinstance(result[field_name], datetime):
                result[field_name] = utc_to_kst(result[field_name])
        
        return result
    
    def convert_rows_datetimes(self, rows: List[Row]) -> List[Dict[str, Any]]:
        """여러 Row들의 datetime 필드들을 UTC → KST 변환"""
        return [self.convert_row_datetimes(row) for row in rows]
    
    def convert_entity_datetimes(self, entity: Any) -> Any:
        """SQLAlchemy 엔티티의 datetime 필드들을 UTC → KST 변환"""
        if entity is None:
            return None
        
        for field_name in self.DATETIME_FIELDS:
            if hasattr(entity, field_name):
                value = getattr(entity, field_name)
                if isinstance(value, datetime):
                    setattr(entity, field_name, utc_to_kst(value))
        
        return entity
