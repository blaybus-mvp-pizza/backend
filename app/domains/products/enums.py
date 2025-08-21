from enum import Enum


class SortOption(str, Enum):
    recommended = "recommended"
    popular = "popular"
    latest = "latest"
    ending = "ending"


class StatusFilter(str, Enum):
    ALL = "ALL"
    RUNNING = "RUNNING"
    ENDED = "ENDED"
    SCHEDULED = "SCHEDULED"


class BiddersFilter(str, Enum):
    ALL = "ALL"
    LE_10 = "LE_10"
    BT_10_20 = "BT_10_20"
    GE_20 = "GE_20"


class PriceBucket(str, Enum):
    ALL = "ALL"
    LT_10000 = "LT_10000"
    BT_10000_30000 = "BT_10000_30000"
    BT_30000_50000 = "BT_30000_50000"
    BT_50000_150000 = "BT_50000_150000"
    BT_150000_300000 = "BT_150000_300000"
    BT_300000_500000 = "BT_300000_500000"
    CUSTOM = "CUSTOM"


class ProductCategory(str, Enum):
    # API values aligned to DB product.category codes. Extend as needed.
    ALL = "ALL"
    FURNITURE = "FURNITURE"
    LIGHTING = "LIGHTING"
    DECOR = "DECOR"
    CERAMIC = "CERAMIC"
    CHAIR = "CHAIR"


class ProductAdminStatusFilter(str, Enum):
    ALL = "ALL"
    AVAILABLE = "AVAILABLE"
    SOLD = "SOLD"
