import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "secret_santa.db")
)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _connection_record):
    # 让 SQLite 真正执行外键约束（默认关闭），保证级联删除生效
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
