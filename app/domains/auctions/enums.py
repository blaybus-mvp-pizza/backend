from enum import Enum


class AuctionStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"


class PaymentStatusKo(str, Enum):
    PENDING = "대기"
    CONFIRMED = "확인"
    CANCELED = "취소"


class ShipmentStatusKo(str, Enum):
    WAITING = "대기"
    PROCESSING = "처리"
    INQUIRY = "조회"
    COMPLETED = "완료"
