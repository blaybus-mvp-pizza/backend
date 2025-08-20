import os
import pathlib
import pymysql
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


def _run_seed_once():
    seed_path = str(pathlib.Path(__file__).resolve().parents[0] / "integration_seed.sql")
    db_url = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
    assert db_url and db_url.startswith(
        "mysql+pymysql://"
    ), "DATABASE_URL must be set (mysql+pymysql://...)"

    url = db_url[len("mysql+pymysql://") :]
    creds, host_db = url.split("@", 1)
    user, password = creds.split(":", 1)
    host_port, db = host_db.split("/", 1)
    if "?" in db:
        db = db.split("?", 1)[0]
    host, port = host_port.split(":", 1)

    with open(seed_path, "r", encoding="utf-8") as f:
        sql_text = f.read()

    statements = []
    buff = []
    for line in sql_text.splitlines():
        l = line.strip()
        if not l or l.startswith("--"):
            continue
        buff.append(line)
        check = l
        if "--" in check:
            check = check.split("--", 1)[0].rstrip()
        if check.endswith(";"):
            statements.append("\n".join(buff))
            buff = []
    if buff:
        statements.append("\n".join(buff))

    conn = pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=db,
        autocommit=True,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def seed_db():
    _run_seed_once()
    yield


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
