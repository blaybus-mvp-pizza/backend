from typing import List, Optional
from pydantic import BaseModel


class DBInfo(BaseModel):
    version: str
    database: Optional[str]
    tables: List[str] = []
