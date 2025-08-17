from contextlib import contextmanager
from sqlalchemy.orm import Session


@contextmanager
def transactional(session: Session):
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise
