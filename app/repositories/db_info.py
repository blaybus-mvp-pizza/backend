from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


def fetch_database_version(db: Session) -> str:
	result = db.execute(text("SELECT VERSION()"))
	version = result.scalar_one_or_none() or "unknown"
	return str(version)


def fetch_current_database(db: Session) -> Optional[str]:
	result = db.execute(text("SELECT DATABASE()"))
	return result.scalar_one_or_none()


def fetch_tables(db: Session) -> List[str]:
	rows = db.execute(text("SHOW TABLES"))
	return [row[0] for row in rows.fetchall()]
