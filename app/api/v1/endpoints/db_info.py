from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.repositories.db_info import (
    fetch_database_version,
    fetch_current_database,
    fetch_tables,
)
from app.domains.system.models import DBInfo

router = APIRouter()


@router.get("/metadata", response_model=DBInfo, summary="Get MySQL database info")
async def get_db_info(db: Session = Depends(get_db)) -> DBInfo:
    version = fetch_database_version(db)
    database = fetch_current_database(db)
    tables = fetch_tables(db)
    return DBInfo(version=version, database=database, tables=tables)
