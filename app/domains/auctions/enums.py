from enum import Enum


class AuctionStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"
